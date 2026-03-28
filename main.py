import os
import telebot
import requests
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Buscador Online"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

# --- 1. COMANDO START (Sempre no topo) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔍 BUSCAR AGORA", switch_inline_query_current_chat="")
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        "✅ **BOT PRONTO PARA USO!**\n\nClique no botão abaixo para abrir a janelinha de busca. Quando você escolher o filme, eu mando os IDs aqui no chat.", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# --- 2. PROCESSADOR DE LISTA (O que envia os IDs no chat) ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/get"))
def processar_detalhes(message):
    try:
        # Pega o comando: /get_movie_12345
        dados = message.text.split('_')
        tipo = dados[1] # movie ou tv
        tmdb_id = dados[2]

        url_info = f"https://api.themoviedb.org/3/{tipo}/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
        info = requests.get(url_info).json()
        titulo = info.get('title') or info.get('name')

        if tipo == 'movie':
            link = f"{BASE_EMBED}{tmdb_id}"
            bot.send_message(message.chat.id, f"🎬 **FILME: {titulo}**\n🆔 ID: `{tmdb_id}`\n🔗 `{link}`", parse_mode="Markdown")
        
        else:
            bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo}**\n🆔 ID: `{tmdb_id}`\n\n_Buscando todas as temporadas..._")
            
            for season in info.get('seasons', []):
                s_num = season.get('season_number')
                if s_num == 0: continue
                
                url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                eps_data = requests.get(url_eps).json().get('episodes', [])
                
                texto_temp = f"📅 **TEMPORADA {s_num}**\n\n"
                for ep in eps_data:
                    e_num = ep.get('episode_number')
                    link_ep = f"{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}"
                    texto_temp += f"🔹 Ep {e_num} | ID: `{tmdb_id}`\n🔗 `{link_ep}`\n\n"
                
                bot.send_message(message.chat.id, texto_temp, parse_mode="Markdown")
                time.sleep(0.4)

    except Exception as e:
        print(f"Erro no processador: {e}")

# --- 3. FUNÇÃO DA JANELINHA (INLINE) ---
@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    try:
        nome = inline_query.query
        # Busca específica para garantir que encontre filmes E séries
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome}&language=pt-BR"
        res = requests.get(url).json().get('results', [])[:10]

        results = []
        for i, item in enumerate(res):
            tmdb_id = item.get('id')
            tipo = item.get('media_type')
            
            # Se o TMDB não mandar o tipo, a gente tenta descobrir pelo nome
            if not tipo or tipo == 'person':
                if 'title' in item: tipo = 'movie'
                elif 'name' in item: tipo = 'tv'
                else: continue
            
            titulo = item.get('title') or item.get('name')
            thumb = f"https://image.tmdb.org/t/p/w92{item.get('poster_path')}" if item.get('poster_path') else None
            
            # Este comando vai pro chat e ativa a função de cima
            trigger = f"/get_{tipo}_{tmdb_id}"

            r = types.InlineQueryResultArticle(
                id=str(i),
                title=f"{'🎬' if tipo == 'movie' else '📺'} {titulo}",
                description=f"Clique para pegar todos os IDs",
                thumbnail_url=thumb,
                input_message_content=types.InputTextMessageContent(trigger)
            )
            results.append(r)
        
        bot.answer_inline_query(inline_query.id, results, cache_time=1)
    except Exception as e:
        print(f"Erro Inline: {e}")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    print("Bot Ligado!")
    bot.infinity_polling(skip_pending=True)
            
