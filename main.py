import telebot
import requests
import os
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
TELEGRAM_TOKEN = '8455878492:AAHZvk6fOjuHihfaJXpBZm7i4okSWy63BbU'
GOOGLE_API_KEY = 'AIzaSyBdww3w_lvPXCnBmVe3FWc4yV-jtgfOxc4'
SEARCH_ENGINE_ID = '2287c31f5b9174d59'
GEMINI_API_KEY = 'AIzaSyAw_HK2uD1ZHLLk4OFutTaeAZPEy3bSjh0'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- WEB SERVER FOR RENDER (To keep it alive) ---
@app.route('/')
def home():
    return "Bot is Running!"

def run_web_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- LOGIC ---
def get_google_search_results(query):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
    try:
        response = requests.get(url).json()
        search_items = response.get('items', [])
        context_text = ""
        for item in search_items[:5]:
            context_text += f"Title: {item['title']}\nSnippet: {item['snippet']}\n\n"
        return context_text
    except Exception as e:
        print(f"Search Error: {e}")
        return ""

def get_gemini_response(user_query, search_context):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = (
        f"User Query: {user_query}\n\n"
        f"Web Search Data:\n{search_context}\n\n"
        f"Please provide a comprehensive answer in Malayalam using this data."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return "ക്ഷമിക്കണം, മറുപടി തയ്യാറാക്കുന്നതിൽ ഒരു പിശക് സംഭവിച്ചു."

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "സ്വാഗതം! ഏത് വിഷയത്തെക്കുറിച്ചും ചോദിക്കൂ, ഞാൻ വെബ്സൈറ്റുകൾ പരിശോധിച്ച് ഉത്തരം നൽകാം.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text
    status_msg = bot.reply_to(message, "വിവരങ്ങൾ ശേഖരിക്കുന്നു... 🔍")
    
    context = get_google_search_results(query)
    if not context:
        bot.edit_message_text("വിവരങ്ങൾ ഒന്നും കണ്ടെത്താനായില്ല.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    answer = get_gemini_response(query, context)
    try:
        bot.edit_message_text(answer, chat_id=message.chat.id, message_id=status_msg.message_id)
    except:
        bot.send_message(message.chat.id, answer)

# --- START BOT ---
if __name__ == "__main__":
    # Start web server in a separate thread
    t = Thread(target=run_web_server)
    t.start()
    
    print("Bot is starting...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
