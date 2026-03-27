import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread

# --- SERVIDOR PARA O RENDER ---
app = Flask('')
@app.route('/')
def home(): return "SERVIDOR BUSCADOR ATIVO"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = '169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🔍 **TMDB ID BUSCADOR ATIVO**\n\nEnvie o nome do filme ou série agora!")

@bot.message_handler(func=lambda message: True)
def buscar_ids(message):
    query = message.text
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={query}&language=pt-BR"
    try:
        res = requests.get(url).json()
        resultados = res.get('results', [])
        if not resultados:
            bot.send_message(message.chat.id, "❌ Nada encontrado.")
            return

        item = resultados[0]
        tmdb_id = item.get('id')
        tipo = item.get('media_type', 'movie')
        titulo = item.get('title') or item.get('name')

        if tipo == 'movie':
            link = f"{BASE_EMBED}{tmdb_id}"
            bot.send_message(message.chat.id, f"🎬 **{titulo}**\n🆔 ID: `{tmdb_id}`\n🔗 `{link}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo}**\n🆔 ID: `{tmdb_id}`")
            url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
            detalhes = requests.get(url_tv).json()
            for season in detalhes.get('seasons', []):
                s_num = season.get('season_number')
                if s_num == 0: continue
                texto_temp = f"📅 **TEMP {s_num}**\n"
                url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                eps = requests.get(url_eps).json().get('episodes', [])
                for ep in eps:
                    e_num = ep.get('episode_number')
                    link_ep = f"{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}"
                    texto_temp += f"🔹 Ep {e_num}: `{link_ep}`\n"
                bot.send_message(message.chat.id, texto_temp, parse_mode="Markdown")
                time.sleep(0.5)
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    # skip_pending=True ignora mensagens enviadas enquanto o bot estava off
    bot.infinity_polling(skip_pending=True)
        
