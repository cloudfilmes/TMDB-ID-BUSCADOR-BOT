import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread
from telebot import types

app = Flask('')
@app.route('/')
def home(): return "Buscador Cloud Filmes Ativo!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"
IMG_URL = "https://image.tmdb.org/t/p/w1280"

bot = telebot.TeleBot(TOKEN)

# Função para ícone de classificação quadrada
def get_class_icon(age):
    icons = {
        "L": "🟢 [L]",
        "10": "🔵 [10]",
        "12": "🟡 [12]",
        "14": "🟠 [14]",
        "16": "🔴 [16]",
        "18": "⚫ [18]"
    }
    return icons.get(age, "⚪ [N/A]")

def get_details(tmdb_id, tipo):
    url = f"https://api.themoviedb.org/3/{tipo}/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR&append_to_response=credits,release_dates,content_ratings"
    try:
        data = requests.get(url).json()
        
        # Elenco (Top 3)
        cast = ", ".join([actor['name'] for actor in data.get('credits', {}).get('cast', [])[:3]])
        # Gêneros
        genres = ", ".join([g['name'] for g in data.get('genres', [])])
        # Duração
        runtime = data.get('runtime') or data.get('episode_run_time', [0])[0]
        duration = f"{runtime} min" if runtime else "N/A"
        
        # Classificação
        age = "N/A"
        if tipo == 'movie':
            for r in data.get('release_dates', {}).get('results', []):
                if r['iso_3166_1'] == 'BR':
                    age = r['release_dates'][0].get('certification', 'L')
        else:
            for r in data.get('content_ratings', {}).get('results', []):
                if r['iso_3166_1'] == 'BR':
                    age = r.get('rating', 'L')
        
        return cast, genres, duration, get_class_icon(age)
    except:
        return "N/A", "N/A", "N/A", "⚪ [N/A]"

@bot.inline_handler(lambda query: len(query.query) > 2)
def query_text(inline_query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={inline_query.query}&language=pt-BR"
        res = requests.get(url).json()
        resultados = res.get('results', [])[:10]
        
        results_list = []
        for i, item in enumerate(resultados):
            if item.get('media_type') not in ['movie', 'tv']: continue
            tmdb_id = item.get('id')
            tipo = item.get('media_type')
            titulo = item.get('title') or item.get('name')
            thumb = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else "https://via.placeholder.com/500"
            
            results_list.append(types.InlineQueryResultArticle(
                id=str(i),
                title=f"{titulo}",
                thumbnail_url=thumb,
                input_message_content=types.InputTextMessageContent(f"/detalhes_{tipo}_{tmdb_id}")
            ))
        bot.answer_inline_query(inline_query.id, results_list, cache_time=1)
    except: pass

@bot.message_handler(func=lambda m: m.text and m.text.startswith('/detalhes_'))
def processar_escolha(message):
    try:
        _, tipo, tmdb_id = message.text.split('_')
        url = f"https://api.themoviedb.org/3/{tipo}/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
        item = requests.get(url).json()
        
        cast, genres, duration, class_icon = get_details(tmdb_id, tipo)
        titulo = item.get('title') or item.get('name')
        ano = (item.get('release_date') or item.get('first_air_date') or "----")[:4]
        sinopse = item.get('overview') or "Sem sinopse."
        backdrop = f"{IMG_URL}{item.get('backdrop_path')}" if item.get('backdrop_path') else None

        msg_body = (
            f"🎬 {titulo.upper()}\n\n"
            f"📅 Ano: {ano}\n"
            f"⏳ Duração: {duration}\n"
            f"🎭 Gênero: {genres}\n"
            f"👥 Elenco: {cast}\n"
            f"🔞 Classificação: {class_icon}\n"
            f"📦 Tamanho: [Preencher no Painel Admin]\n\n"
            f"📖 Sinopse: {sinopse}\n\n"
        )

        if tipo == 'movie':
            link = f"{BASE_EMBED}{tmdb_id}"
            footer = f"🔗 LINK EMBED:\n`{link}`"
            if backdrop: bot.send_photo(message.chat.id, backdrop, caption=msg_body + footer, parse_mode="Markdown")
            else: bot.send_message(message.chat.id, msg_body + footer, parse_mode="Markdown")
        else:
            if backdrop: bot.send_photo(message.chat.id, backdrop, caption=msg_body, parse_mode="Markdown")
            else: bot.send_message(message.chat.id, msg_body, parse_mode="Markdown")
            
            bot.send_message(message.chat.id, "Organizando episódios...")
            
            # Busca temporadas
            url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
            detalhes = requests.get(url_tv).json()
            for s in detalhes.get('seasons', []):
                s_num = s.get('season_number')
                if s_num == 0: continue
                
                url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                dados_temp = requests.get(url_eps).json()
                
                bot.send_message(message.chat.id, f"📂 TEMPORADA {s_num}")
                for ep in dados_temp.get('episodes', []):
                    e_num = ep.get('episode_number')
                    texto_ep = (
                        f"🔹 EPISÓDIO {e_num}: {(ep.get('name') or '').upper()}\n\n"
                        f"📝 Sinopse: {ep.get('overview') or 'Sem sinopse.'}\n\n"
                        f"🔗 LINK EMBED:\n`{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}`\n"
                        f"────────────────────"
                    )
                    bot.send_message(message.chat.id, texto_ep, parse_mode="Markdown")
                    time.sleep(0.4)
    except: pass

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Buscador Profissional Ativo\n\nDigite o nome de um filme ou série para começar.")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling(skip_pending=True)
        
