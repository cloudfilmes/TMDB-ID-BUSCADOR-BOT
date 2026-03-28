import os
import telebot
import requests
import time
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "Buscador Cloud Filmes Ativo!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÃO ---
TOKEN = '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g'
# CORREÇÃO: Chave TMDB agora com o 'a' no início
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

# 1. Responde ao /start e /ajuda
@bot.message_handler(commands=['start', 'ajuda'])
def welcome(message):
    bot.reply_to(message, "🔍 **BUSCADOR DE IDs ATIVO**\n\nPara conseguir o ID, basta digitar o nome do filme ou série abaixo!")

# 2. Responde ao comando /buscar nome
@bot.message_handler(commands=['buscar'])
def comando_buscar(message):
    query = message.text.replace('/buscar', '').strip()
    if query:
        executar_busca(message, query)
    else:
        bot.reply_to(message, "⚠️ Digite o nome após o comando. Ex: `/buscar Rambo`")

# 3. Responde se digitar apenas o nome (Busca Direta)
@bot.message_handler(func=lambda message: True)
def busca_direta(message):
    if not message.text.startswith('/'):
        executar_busca(message, message.text)

# --- FUNÇÃO DE BUSCA (A que pega os IDs) ---
def executar_busca(message, query):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={query}&language=pt-BR"
    
    try:
        res = requests.get(url).json()
        resultados = res.get('results', [])
        
        if not resultados:
            bot.reply_to(message, "❌ Nada encontrado. Verifique o nome.")
            return

        # Pega os 3 primeiros resultados para não poluir o chat
        for item in resultados[:3]:
            tmdb_id = item.get('id')
            tipo = item.get('media_type', 'movie')
            titulo = item.get('title') or item.get('name')
            ano = (item.get('release_date') or item.get('first_air_date') or "----")[:4]

            if tipo == 'movie':
                link = f"{BASE_EMBED}{tmdb_id}"
                bot.send_message(message.chat.id, f"🎬 **FILME: {titulo} ({ano})**\n🆔 ID: `{tmdb_id}`\n🔗 `{link}`", parse_mode="Markdown")
            else:
                # Se for série, manda o ID principal e o link do primeiro ep
                link_serie = f"{BASE_EMBED}{tmdb_id}/1/1"
                bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo} ({ano})**\n🆔 ID: `{tmdb_id}`\n🔗 Link Ep 1: `{link_serie}`", parse_mode="Markdown")

    except Exception as e:
        print(f"ERRO: {e}")
        bot.send_message(message.chat.id, "⚠️ Erro ao conectar com o TMDB.")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling(skip_pending=True)
