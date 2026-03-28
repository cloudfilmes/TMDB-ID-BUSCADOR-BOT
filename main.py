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
def home(): return "Buscador de IDs Online"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

# --- 1. COMANDO START ---
@bot.message_handler(commands=['start', 'ajuda'])
def welcome(message):
    texto = (
        "🔍 **BUSCADOR DE IDs TMDB**\n\n"
        "Comandos disponíveis:\n"
        "👉 `/buscar NomeDoFilme` - Para pesquisar\n"
        "👉 Ou apenas digite o nome do filme/série aqui."
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

# --- 2. COMANDO BUSCAR ---
@bot.message_handler(commands=['buscar'])
def comando_buscar(message):
    query = message.text.replace('/buscar', '').strip()
    if query:
        realizar_busca(message, query)
    else:
        bot.reply_to(message, "⚠️ Digite o nome após o comando. Ex: `/buscar Rambo`")

# --- 3. BUSCA DIRETA (SE ESCREVER SÓ O NOME) ---
@bot.message_handler(func=lambda message: True)
def busca_texto(message):
    if not message.text.startswith('/'):
        realizar_busca(message, message.text)

# --- 4. FUNÇÃO PRINCIPAL DE BUSCA ---
def realizar_busca(message, query):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={query}&language=pt-BR"
    try:
        res = requests.get(url).json().get('results', [])
        if not res:
            bot.reply_to(message, "❌ Nada encontrado.")
            return

        for item in res[:3]: # Mostra os 3 primeiros resultados
            tmdb_id = item.get('id')
            tipo = item.get('media_type', 'movie')
            titulo = item.get('title') or item.get('name')
            ano = (item.get('release_date') or item.get('first_air_date') or "----")[:4]

            if tipo == 'movie':
                link = f"{BASE_EMBED}{tmdb_id}"
                bot.send_message(message.chat.id, f"🎬 **FILME: {titulo} ({ano})**\n🆔 ID: `{tmdb_id}`\n🔗 `{link}`", parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo} ({ano})**\n🆔 ID: `{tmdb_id}`\n\n_Buscando episódios..._")
                
                # Busca temporadas da série
                url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
                detalhes = requests.get(url_tv).json()
                
                for s in detalhes.get('seasons', []):
                    s_num = s.get('season_number')
                    if s_num == 0: continue
                    
                    url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                    eps = requests.get(url_eps).json().get('episodes', [])
                    
                    texto_temp = f"📅 **TEMPORADA {s_num}**\n"
                    for ep in eps:
                        e_num = ep.get('episode_number')
                        link_ep = f"{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}"
                        texto_temp += f"🔹 Ep {e_num} | ID: `{tmdb_id}` | Link: `{link_ep}`\n"
                    
                    bot.send_message(message.chat.id, texto_temp, parse_mode="Markdown")
                    time.sleep(0.5)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Erro na busca.")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling(skip_pending=True)
        
