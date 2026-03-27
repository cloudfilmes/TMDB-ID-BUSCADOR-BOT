import os
import telebot
import requests
import time

# --- CONFIGURAÇÃO ---
# O bot tenta ler do Render, se não encontrar, usa os valores abaixo
TOKEN = os.environ.get('TOKEN', '8291779593:AAExSoK_DlVo6vbyU0BvWwfK790MvSTaI5g')
TMDB_KEY = os.environ.get('TMDB_KEY', '169d710b2eca204f9db290256828d05')
BASE_EMBED = "https://embedplayapi.site/embed/"

bot = telebot.TeleBot(TOKEN)

print("--- BOT TMDB ID BUSCADOR INICIADO ---")

# --- COMANDO START ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    texto = (
        "🔍 **TMDB ID BUSCADOR - CLOUD FILMES**\n\n"
        "Envie o nome de um filme ou série para obter os links de embed.\n\n"
        "💡 *Dica: Toque no link cinza para copiar apenas o link.*"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

# --- BUSCA DE CONTEÚDO ---
@bot.message_handler(func=lambda message: True)
def buscar_ids(message):
    query = message.text
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={query}&language=pt-BR"
    
    try:
        res = requests.get(url).json()
        resultados = res.get('results', [])
        
        if not resultados:
            bot.reply_to(message, "❌ Nada encontrado no TMDB.")
            return

        item = resultados[0]
        tmdb_id = item.get('id')
        tipo = item.get('media_type', 'movie')
        titulo = item.get('title') or item.get('name')
        data = item.get('release_date') or item.get('first_air_date') or "----"
        ano = data[:4]

        # SE FOR FILME
        if tipo == 'movie':
            link_f = f"{BASE_EMBED}{tmdb_id}"
            bot.reply_to(message, 
                f"🎬 **FILME: {titulo} ({ano})**\n\n🆔 ID: `{tmdb_id}`\n🔗 `{link_f}`", 
                parse_mode="Markdown")

        # SE FOR SÉRIE
        else:
            bot.send_chat_action(message.chat.id, 'typing')
            url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
            detalhes = requests.get(url_tv).json()
            
            bot.send_message(message.chat.id, f"📺 **SÉRIE: {titulo} ({ano})**\n🆔 ID: `{tmdb_id}`")

            for season in detalhes.get('seasons', []):
                s_num = season.get('season_number')
                if s_num == 0: continue
                
                texto_temp = f"📅 **TEMPORADA {s_num}**\n\n"
                url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                eps_data = requests.get(url_eps).json().get('episodes', [])
                
                for ep in eps_data:
                    e_num = ep.get('episode_number')
                    link_ep = f"{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}"
                    texto_temp += f"🔹 Ep {e_num}: `{link_ep}`\n"
                
                bot.send_message(message.chat.id, texto_temp, parse_mode="Markdown")
                time.sleep(1)

    except Exception as e:
        print(f"Erro: {e}")
        bot.reply_to(message, "⚠️ Ocorreu um erro ao processar os dados.")

# LIGA O BOT (Modo Python Direto)
bot.infinity_polling()
  
