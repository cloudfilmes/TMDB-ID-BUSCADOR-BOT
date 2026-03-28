import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB (IGUAL AO PEDIDOS-BOT) ---
app = Flask('')
@app.route('/')
def home(): return "Buscador Cloud Filmes Ativo!"

def run():
    # Usando a mesma porta 8080 que deu certo no outro
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
# Troquei pelos dados do seu buscador novo
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
TMDB_KEY = '169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

# Comando Start (O que você quer que responda)
@bot.message_handler(commands=['start'])
def welcome(message):
    print("LOG: Recebi um /start")
    bot.reply_to(message, "🔍 **BUSCADOR DE IDs ATIVO**\n\nEnvie o nome do filme ou série abaixo!")

# Lógica de Busca de IDs
@bot.message_handler(func=lambda message: True)
def buscar_ids(message):
    query = message.text
    print(f"LOG: Buscando por {query}")
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={query}&language=pt-BR"
    
    try:
        res = requests.get(url).json()
        resultados = res.get('results', [])
        
        if not resultados:
            bot.reply_to(message, "❌ Nada encontrado.")
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
            # Busca temporadas
            url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
            detalhes = requests.get(url_tv).json()
            for s in detalhes.get('seasons', []):
                s_num = s.get('season_number')
                if s_num == 0: continue
                bot.send_message(message.chat.id, f"📅 Temp {s_num}: `{BASE_EMBED}{tmdb_id}/{s_num}/1`", parse_mode="Markdown")

    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    # O skip_pending=True evita que o bot tente responder mensagens velhas e trave
    bot.infinity_polling(skip_pending=True)
            
