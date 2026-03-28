import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread
from telebot import types # Importante para o modo Inline

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Buscador Cloud Filmes Ativo!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"
IMG_URL = "https://image.tmdb.org/t/p/w500" # w500 é melhor para miniaturas inline

bot = telebot.TeleBot(TOKEN)

def get_classification(tmdb_id, tipo):
    url = f"https://api.themoviedb.org/3/{tipo}/{tmdb_id}/{'release_dates' if tipo == 'movie' else 'content_ratings'}?api_key={TMDB_KEY}"
    try:
        res = requests.get(url).json()
        results = res.get('results', [])
        for r in results:
            if r.get('iso_3166_1') == 'BR':
                if tipo == 'movie':
                    return r['release_dates'][0].get('certification', 'L')
                else:
                    return r.get('rating', 'L')
        return "N/A"
    except: return "N/A"

# --- LÓGICA DO MODO INLINE (A JANELINHA) ---
@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={inline_query.query}&language=pt-BR"
        res = requests.get(url).json()
        resultados = res.get('results', [])[:10] # Limita a 10 resultados para ser rápido
        
        results_list = []
        for i, item in enumerate(resultados):
            if item.get('media_type') not in ['movie', 'tv']: continue
            
            tmdb_id = item.get('id')
            tipo = item.get('media_type')
            titulo = item.get('title') or item.get('name')
            ano = (item.get('release_date') or item.get('first_air_date') or "----")[:4]
            thumb = f"{IMG_URL}{item.get('poster_path')}" if item.get('poster_path') else "https://via.placeholder.com/500x750?text=Sem+Foto"
            
            # Criando o resultado que aparece na janelinha
            r = types.InlineQueryResultArticle(
                id=str(i),
                title=f"{'🎬' if tipo == 'movie' else '📺'} {titulo} ({ano})",
                description="Clique para ver detalhes e links",
                thumbnail_url=thumb,
                input_message_content=types.InputTextMessageContent(
                    message_text=f"/detalhes_{tipo}_{tmdb_id}" # Envia um comando oculto ao clicar
                )
            )
            results_list.append(r)
        
        bot.answer_inline_query(inline_query.id, results_list, cache_time=1)
    except Exception as e:
        print(f"Erro Inline: {e}")

# --- COMANDO PARA PROCESSAR O CLIQUE NO RESULTADO ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('/detalhes_'))
def processar_escolha(message):
    try:
        _, tipo, tmdb_id = message.text.split('_')
        # Aqui chamamos a sua função de busca original adaptada para o ID direto
        enviar_detalhes_por_id(message, tmdb_id, tipo)
    except: pass

def enviar_detalhes_por_id(message, tmdb_id, tipo):
    # Busca detalhes específicos do filme/série por ID
    url = f"https://api.themoviedb.org/3/{tipo}/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
    item = requests.get(url).json()
    
    titulo = item.get('title') or item.get('name')
    ano = (item.get('release_date') or item.get('first_air_date') or "----")[:4]
    sinopse = item.get('overview') or "Sinopse não disponível."
    nota = item.get('vote_average', 0.0)
    backdrop = f"https://image.tmdb.org/t/p/w1280{item.get('backdrop_path')}" if item.get('backdrop_path') else None
    classificacao = get_classification(tmdb_id, tipo)

    header_text = (
        f"🎬 **{titulo.upper()}**\n\n"
        f"📅 **Ano:** {ano}\n"
        f"⭐️ **Avaliação:** {nota}/10\n"
        f"🔞 **Classificação:** {classificacao}\n\n"
        f"📖 **Sinopse:** {sinopse}\n\n"
    )

    if tipo == 'movie':
        link = f"{BASE_EMBED}{tmdb_id}"
        footer = f"🔗 **LINK EMBED:**\n`{link}`"
        if backdrop:
            bot.send_photo(message.chat.id, backdrop, caption=header_text + footer, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, header_text + footer, parse_mode="Markdown")
    else:
        # Lógica de temporadas que você já tem
        if backdrop:
            bot.send_photo(message.chat.id, backdrop, caption=header_text, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, header_text, parse_mode="Markdown")
        
        bot.send_message(message.chat.id, "⏳ _Organizando episódios..._")
        for s in item.get('seasons', []):
            s_num = s.get('season_number')
            if s_num == 0: continue
            url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
            dados_temp = requests.get(url_eps).json()
            bot.send_message(message.chat.id, f"📂 --- **TEMPORADA {s_num}** --- 📂")
            for ep in dados_temp.get('episodes', []):
                e_num = ep.get('episode_number')
                texto_ep = (
                    f"🔹 **EPISÓDIO {e_num}: {(ep.get('name') or '').upper()}**\n\n"
                    f"📝 **Sinopse do Ep:** {ep.get('overview') or 'Sem sinopse.'}\n\n"
                    f"🔗 **LINK EMBED:**\n`{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}`\n"
                    f"────────────────────"
                )
                bot.send_message(message.chat.id, texto_ep, parse_mode="Markdown")
                time.sleep(0.5)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🔍 **BUSCADOR PROFISSIONAL**\n\nPara pesquisar, digite `@SeuBotNome` seguido do nome do filme em qualquer chat!")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling(skip_pending=True)
            
