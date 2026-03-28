import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "BOT ONLINE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO DIRETA (SEM ERRO) ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = '169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("Recebi um /start!")
    bot.reply_to(message, "✅ **BOT CONECTADO COM SUCESSO!**\n\nDigite o nome do filme ou série abaixo:")

@bot.message_handler(func=lambda message: True)
def buscar_ids(message):
    query = message.text
    print(f"Buscando por: {query}")
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
            bot.send_message(message.chat.id, f"🎬 **{titulo}**\n🆔 `{tmdb_id}`\n🔗 `{link}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo}**\n🆔 `{tmdb_id}`")
            # Loop de temporadas simplificado
            url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
            detalhes = requests.get(url_tv).json()
            for s in detalhes.get('seasons', []):
                if s.get('season_number') == 0: continue
                bot.send_message(message.chat.id, f"📅 Temp {s.get('season_number')}: `{BASE_EMBED}{tmdb_id}/{s.get('season_number')}/1` (Ep 1)")

    except Exception as e:
        print(f"Erro na busca: {e}")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    print("Bot tentando ligar...")
    bot.infinity_polling(skip_pending=True)
                
