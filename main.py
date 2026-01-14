import telebot
import requests
import json

# --- CONFIGURATION ---
TELEGRAM_TOKEN = '8455878492:AAHZvk6fOjuHihfaJXpBZm7i4okSWy63BbU'
GOOGLE_API_KEY = 'AIzaSyBdww3w_lvPXCnBmVe3FWc4yV-jtgfOxc4'
SEARCH_ENGINE_ID = '2287c31f5b9174d59'
GEMINI_API_KEY = 'AIzaSyAw_HK2uD1ZHLLk4OFutTaeAZPEy3bSjh0'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def get_google_search_results(query):
    """Fetches search snippets from Google Custom Search API"""
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
    try:
        response = requests.get(url).json()
        search_items = response.get('items', [])
        
        context_text = ""
        for item in search_items[:5]:  # Limit to top 5 results
            context_text += f"Title: {item['title']}\nSnippet: {item['snippet']}\n\n"
        return context_text
    except Exception as e:
        print(f"Error fetching Google results: {e}")
        return ""

def get_gemini_response(user_query, search_context):
    """Sends context to Gemini AI and gets a summarized answer in Malayalam"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = (
        f"You are a helpful AI assistant. A user asked: '{user_query}'.\n"
        f"Here is some information found on the web:\n{search_context}\n"
        f"Please provide a detailed, accurate answer in Malayalam based ONLY on the provided information."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        return response_data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "ക്ഷമിക്കണം, മറുപടി തയ്യാറാക്കുന്നതിൽ ഒരു സാങ്കേതിക തകരാർ ഉണ്ടായി."

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am your AI Search Assistant. Ask me anything, and I will search the web for you.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    query = message.text
    # Sending a temporary status message
    status_msg = bot.reply_to(message, "Searching the web... 🔍")
    
    # Step 1: Search Google
    context = get_google_search_results(query)
    
    if not context:
        bot.edit_message_text("No relevant information found on the web.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    # Step 2: Get AI Summary
    answer = get_gemini_response(query, context)
    
    # Step 3: Send Final Answer
    try:
        bot.edit_message_text(answer, chat_id=message.chat.id, message_id=status_msg.message_id)
    except:
        # Fallback if the answer is too long for edit
        bot.send_message(message.chat.id, answer)

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)
