import os
import telebot
import requests
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB PARA O RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Buscador Full IDs Ativo!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = '169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

# --- 1. COMANDO START (O QUE FALTAVA) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup()
    # Este botão ativa a janelinha de busca automaticamente
    btn = types.InlineKeyboardButton("🔍 BUSCAR FILME OU SÉRIE", switch_inline_query_current_chat="")
    markup.add(btn)
    
    texto_start = (
        "👋 **BEM-VINDO AO BUSCADOR DE IDs**\n\n"
        "Para obter todos os IDs e links de uma vez:\n"
        "1️⃣ Clique no botão abaixo.\n"
        "2️⃣ Digite o nome do filme ou série.\n"
        "3️⃣ Toque no resultado e o bot enviará tudo aqui!"
    )
    bot.reply_to(message, texto_start, reply_markup=markup, parse_mode="Markdown")

# --- 2. FUNÇÃO DA JANELINHA (INLINE QUERY) ---
@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    try:
        nome = inline_query.query
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={nome}&language=pt-BR"
        res = requests.get(url).json().get('results', [])[:10]

        results = []
        for i, item in enumerate(res):
            tmdb_id = item.get('id')
            tipo = item.get('media_type', 'movie')
            if tipo not in ['movie', 'tv']: continue # Ignora pessoas/atores
            
            titulo = item.get('title') or item.get('name')
            thumb = f"https://image.tmdb.org/t/p/w92{item.get('poster_path')}" if item.get('poster_path') else None
            
            # O bot vai "ouvir" este comando secreto quando clicares no resultado
            trigger = f"/get_full {tipo} {tmdb_id}"

            r = types.InlineQueryResultArticle(
                id=str(i),
                title=f"{'🎬' if tipo == 'movie' else '📺'} {titulo}",
                description="Clique para listar todos os IDs e Episódios",
                thumbnail_url=thumb,
                input_message_content=types.InputTextMessageContent(trigger)
            )
            results.append(r)
        
        bot.answer_inline_query(inline_query.id, results, cache_time=1)
    except Exception as e:
        print(f"Erro Inline: {e}")

# --- 3. PROCESSADOR QUE ENVIA TODOS OS IDs E EPISÓDIOS ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/get_full"))
def processar_full_ids(message):
    try:
        # Apaga o comando de gatilho para manter o chat limpo
        try: bot.delete_message(message.chat.id, message.message_id)
        except: pass

        partes = message.text.split()
        tipo = partes[1]
        tmdb_id = partes[2]

        # Busca detalhes no TMDB
        url_info = f"https://api.themoviedb.org/3/{'movie' if tipo == 'movie' else 'tv'}/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
        info = requests.get(url_info).json()
        titulo = info.get('title') or info.get('name')

        if tipo == 'movie':
            link = f"{BASE_EMBED}{tmdb_id}"
            bot.send_message(message.chat.id, f"🎬 **FILME: {titulo}**\n🆔 TMDB: `{tmdb_id}`\n🔗 `{link}`", parse_mode="Markdown")
        
        else:
            bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo}**\n🆔 TMDB: `{tmdb_id}`\n\n_A extrair temporadas e episódios..._")
            
            # Loop por todas as temporadas
            for season in info.get('seasons', []):
                s_num = season.get('season_number')
                if s_num == 0: continue # Ignora extras/especiais
                
                url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                eps_data = requests.get(url_eps).json().get('episodes', [])
                
                texto_temp = f"📅 **TEMPORADA {s_num}**\n\n"
                for ep in eps_data:
                    e_num = ep.get('episode_number')
                    link_ep = f"{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}"
                    # Formato que pediste: Nome, ID da série e Link do Ep
                    texto_temp += f"🔹 Ep {e_num}: `{link_ep}` (ID: `{tmdb_id}`)\n"
                
                bot.send_message(message.chat.id, texto_temp, parse_mode="Markdown")
                time.sleep(0.5) # Pausa curta para não ser bloqueado pelo Telegram

    except Exception as e:
        print(f"Erro: {e}")
        bot.send_message(message.chat.id, "⚠️ Erro ao procurar detalhes.")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling(skip_pending=True)
    
