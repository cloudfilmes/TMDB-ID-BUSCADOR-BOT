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
TMDB_KEY = 'a169d710b2eca204f9db290256828d05'
BASE_EMBED = "https://embedplayapi.site/embed/"
IMG_URL = "https://image.tmdb.org/t/p/w1280" # URL para imagens de alta qualidade

bot = telebot.TeleBot(TOKEN)

# Função para pegar a classificação de idade
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

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🔍 **BUSCADOR PROFISSIONAL ATIVO**\n\nEnvie o nome do filme ou série abaixo para ver os detalhes e IDs!")

@bot.message_handler(func=lambda message: True)
def buscar_ids(message):
    query = message.text
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
        if tipo not in ['movie', 'tv']: return # Pula se for pessoa/ator

        # Detalhes principais
        titulo = item.get('title') or item.get('name')
        ano = (item.get('release_date') or item.get('first_air_date') or "----")[:4]
        sinopse = item.get('overview') or "Sinopse não disponível."
        nota = item.get('vote_average', 0.0)
        backdrop = f"{IMG_URL}{item.get('backdrop_path')}" if item.get('backdrop_path') else None
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
            # Envia o "Capa" da série primeiro
            if backdrop:
                bot.send_photo(message.chat.id, backdrop, caption=header_text, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, header_text, parse_mode="Markdown")
            
            bot.send_message(message.chat.id, "⏳ _Organizando episódios por temporadas..._")

            # Busca detalhes das temporadas
            url_tv = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&language=pt-BR"
            detalhes = requests.get(url_tv).json()
            
            for s in detalhes.get('seasons', []):
                s_num = s.get('season_number')
                if s_num == 0: continue 
                
                url_eps = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_KEY}&language=pt-BR"
                dados_temp = requests.get(url_eps).json()
                episodes = dados_temp.get('episodes', [])
                
                # Cabeçalho da Temporada
                bot.send_message(message.chat.id, f"📂 --- **TEMPORADA {s_num}** --- 📂")
                
                for ep in episodes:
                    e_num = ep.get('episode_number')
                    e_nome = ep.get('name') or f"Episódio {e_num}"
                    e_sinopse = ep.get('overview') or "Sem sinopse para este episódio."
                    link_ep = f"{BASE_EMBED}{tmdb_id}/{s_num}/{e_num}"
                    
                    texto_ep = (
                        f"🔹 **EPISÓDIO {e_num}: {e_nome.upper()}**\n\n"
                        f"📝 **Sinopse do Ep:** {e_sinopse}\n\n"
                        f"🔗 **LINK EMBED:**\n`{link_ep}`\n"
                        f"────────────────────" # Linha separadora
                    )
                    
                    bot.send_message(message.chat.id, texto_ep, parse_mode="Markdown")
                    time.sleep(0.8) # Pausa para o Telegram não travar e as mensagens ficarem separadas

    except Exception as e:
        print(f"ERRO: {e}")
        bot.send_message(message.chat.id, "⚠️ Ocorreu um erro ao processar os dados.")

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling(skip_pending=True)
        
