import os
import telebot
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
conversations = {}

@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    bot.reply_to(message, f"Salom {name}! 👋\nMen O'zbek AI Assistantman!\nIstalgan savolingizni bering 😊\n\n🔄 Tozalash: /clear")

@bot.message_handler(commands=['clear'])
def clear(message):
    conversations[message.from_user.id] = []
    bot.reply_to(message, "✅ Suhbat tozalandi!")

@bot.message_handler(func=lambda m: True)
def handle(message):
    uid = message.from_user.id
    if uid not in conversations:
        conversations[uid] = []
    conversations[uid].append({"role": "user", "content": message.text})
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": "Siz O'zbek tilidagi AI assistantsiz. Foydalanuvchi qaysi tilda yozsa o'sha tilda javob bering. Har doim do'stona va foydali bo'ling."}] + conversations[uid],
            max_tokens=1024
        )
        reply = res.choices[0].message.content
        conversations[uid].append({"role": "assistant", "content": reply})
        if len(conversations[uid]) > 20:
            conversations[uid] = conversations[uid][-20:]
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

print("✅ Bot ishga tushdi!")
bot.polling(none_stop=True)
