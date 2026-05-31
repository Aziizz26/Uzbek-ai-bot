import telebot
import requests
import io
import PyPDF2
import docx
import google.generativeai as genai
from groq import Groq
from datetime import datetime
import json
import os

TELEGRAM_TOKEN = "8908187925:AAHXae2QT30AydTzSjFWa1oANIAU9v_InyU"
GROQ_API_KEY = "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"
HF_API_KEY = "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"
GEMINI_API_KEY = "AQ.Ab8RN6LCLuBBfszuYANrAswK-UxXHwtmn14g8iWY3RzLboTwHw"
ADMIN_ID =   883268095# o'z Telegram ID ingizni yozing

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-pro")
groq_client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

conversations = {}
user_profiles = {}
reminders = {}
stats = {"total_users": 0, "total_messages": 0}

SYSTEM_PROMPT = """Siz — "Ziyrak", O'zbekistonning eng aqlli AI assistanti!
Qoidalar:
- Foydalanuvchini ismi bilan murojaat qiling
- Matematik, fizika, kimyo masalalarini bosqichma-bosqich yeching
- Formulalarni chiroyli tushuntiring
- Kodni yozing va xatolarni toping
- Qaysi tilda yozilsa, o'sha tilda javob bering
- Har doim do'stona, qiziqarli va foydali bo'ling
- Javoblarni emoji bilan bezating
- Foydalanuvchi ma'lumotlarini eslab qoling"""

def get_user_context(uid):
    if uid in user_profiles:
        p = user_profiles[uid]
        return f"\nFoydalanuvchi ma'lumotlari: Ismi={p.get('name','?')}, Yoshi={p.get('age','?')}, Qiziqishlari={p.get('interests','?')}"
    return ""

def ask_groq(uid, text):
    if uid not in conversations:
        conversations[uid] = []
    conversations[uid].append({"role": "user", "content": text})
    res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT + get_user_context(uid)}] + conversations[uid],
        max_tokens=2048
    )
    reply = res.choices[0].message.content
    conversations[uid].append({"role": "assistant", "content": reply})
    if len(conversations[uid]) > 30:
        conversations[uid] = conversations[uid][-30:]
    stats["total_messages"] += 1
    return reply

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    if uid not in user_profiles:
        user_profiles[uid] = {"name": name, "joined": str(datetime.now())}
        stats["total_users"] += 1
    bot.reply_to(message,
        f"Salom {name}! 👋\n\n"
        "Men — *Ziyrak* 🧠\n"
        "O'zbekistonning eng aqlli AI assistanti!\n\n"
        "📌 *Buyruqlar:*\n"
        "💬 Savol — shunchaki yozing\n"
        "🎨 /rasm — rasm yaratish\n"
        "🌤 /havo — ob-havo\n"
        "💱 /kurs — valyuta kursi\n"
        "🎮 /test — viktorina\n"
        "📝 /sher — she'r yozish\n"
        "📖 /hikoya — hikoya\n"
        "⏰ /eslatma — eslatma\n"
        "🌐 /tarjima — tarjima\n"
        "😄 /latifa — latifa\n"
        "👤 /profil — profilim\n"
        "🔄 /clear — tozalash\n\n"
        "Savolingizni bering! 🚀",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['profil'])
def profil(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    if uid not in user_profiles:
        user_profiles[uid] = {"name": name}
    p = user_profiles[uid]
    bot.reply_to(message,
        f"👤 *Profilingiz:*\n\n"
        f"📛 Ism: {p.get('name', name)}\n"
        f"🎂 Yosh: {p.get('age', 'Kiritilmagan')}\n"
        f"❤️ Qiziqishlar: {p.get('interests', 'Kiritilmagan')}\n\n"
        "Yangilash uchun yozing:\n"
        "/yosh 20\n"
        "/qiziqish sport, musiqa",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['yosh'])
def set_age(message):
    uid = message.from_user.id
    yosh = message.text.replace('/yosh', '').strip()
    if uid not in user_profiles:
        user_profiles[uid] = {}
    user_profiles[uid]['age'] = yosh
    bot.reply_to(message, f"✅ Yoshingiz {yosh} deb saqlandi!")

@bot.message_handler(commands=['qiziqish'])
def set_interests(message):
    uid = message.from_user.id
    qiziqish = message.text.replace('/qiziqish', '').strip()
    if uid not in user_profiles:
        user_profiles[uid] = {}
    user_profiles[uid]['interests'] = qiziqish
    bot.reply_to(message, f"✅ Qiziqishlaringiz saqlandi: {qiziqish}")

@bot.message_handler(commands=['clear'])
def clear(message):
    conversations[message.from_user.id] = []
    bot.reply_to(message, "✅ Suhbat tozalandi!")

@bot.message_handler(commands=['latifa'])
def latifa(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = gemini.generate_content("O'zbek tilidagi kulgili va qisqa latifa ayt")
        bot.reply_to(message, "😄 " + r.text)
    except:
        bot.reply_to(message, ask_groq(message.from_user.id, "Kulgili o'zbek latifasi ayt"))

@bot.message_handler(commands=['sher'])
def sher(message):
    mavzu = message.text.replace('/sher', '').strip() or "bahor"
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = gemini.generate_content(f"'{mavzu}' mavzusida chiroyli o'zbek she'ri yoz")
        bot.reply_to(message, "📝 " + r.text)
    except:
        bot.reply_to(message, ask_groq(message.from_user.id, f"{mavzu} haqida she'r yoz"))

@bot.message_handler(commands=['hikoya'])
def hikoya(message):
    mavzu = message.text.replace('/hikoya', '').strip() or "qahramonlik"
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = gemini.generate_content(f"'{mavzu}' mavzusida qisqa va qiziqarli hikoya yoz")
        bot.reply_to(message, "📖 " + r.text)
    except:
        bot.reply_to(message, ask_groq(message.from_user.id, f"{mavzu} haqida qisqa hikoya yoz"))

@bot.message_handler(commands=['tarjima'])
def tarjima(message):
    matn = message.text.replace('/tarjima', '').strip()
    if not matn:
        bot.reply_to(message, "✏️ Misol: /tarjima Hello world")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = gemini.generate_content(f"Quyidagi matnni o'zbek tiliga tarjima qil, faqat tarjimani yoz: {matn}")
        bot.reply_to(message, "🌐 " + r.text)
    except:
        bot.reply_to(message, ask_groq(message.from_user.id, f"O'zbek tiliga tarjima qil: {matn}"))

@bot.message_handler(commands=['test'])
def test(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = gemini.generate_content(
            "O'zbek tilida qiziqarli viktorina savoli yoz. "
            "Format: Savol, keyin A B C D variantlar, keyin To'g'ri javob: X"
        )
        bot.reply_to(message, "🎮 " + r.text)
    except:
        bot.reply_to(message, ask_groq(message.from_user.id, "Qiziqarli viktorina savoli yoz, 4 variant bilan"))

@bot.message_handler(commands=['havo'])
def havo(message):
    shahar = message.text.replace('/havo', '').strip() or "Toshkent"
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = requests.get(
            f"https://wttr.in/{shahar}?format=3&lang=uz",
            timeout=10
        )
        bot.reply_to(message, f"🌤 {r.text}")
    except:
        bot.reply_to(message, f"❌ {shahar} ob-havosini ololmadim!")

@bot.message_handler(commands=['kurs'])
def kurs(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/", timeout=10)
        data = r.json()
        usd = next((x for x in data if x['Ccy'] == 'USD'), None)
        eur = next((x for x in data if x['Ccy'] == 'EUR'), None)
        rub = next((x for x in data if x['Ccy'] == 'RUB'), None)
        msg = "💱 *Valyuta kurslari (CBU):*\n\n"
        if usd: msg += f"🇺🇸 1 USD = {float(usd['Rate']):,.0f} so'm\n"
        if eur: msg += f"🇪🇺 1 EUR = {float(eur['Rate']):,.0f} so'm\n"
        if rub: msg += f"🇷🇺 1 RUB = {float(rub['Rate']):,.2f} so'm\n"
        bot.reply_to(message, msg, parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Kursni ololmadim, keyinroq urining!")

@bot.message_handler(commands=['eslatma'])
def eslatma(message):
    parts = message.text.replace('/eslatma', '').strip().split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "✏️ Misol: /eslatma 30 dori ich\n(30 = daqiqa)")
        return
    try:
        daqiqa = int(parts[0])
        xabar = parts[1]
        bot.reply_to(message, f"⏰ {daqiqa} daqiqadan keyin eslataman: {xabar}")
        import threading
        def remind():
            import time
            time.sleep(daqiqa * 60)
            bot.send_message(message.chat.id, f"⏰ Eslatma: {xabar}")
        threading.Thread(target=remind, daemon=True).start()
    except:
        bot.reply_to(message, "❌ Format: /eslatma 30 dori ich")

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Faqat admin uchun!")
        return
    bot.reply_to(message,
        f"📊 *Statistika:*\n\n"
        f"👥 Foydalanuvchilar: {stats['total_users']}\n"
        f"💬 Xabarlar: {stats['total_messages']}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Faqat admin uchun!")
        return
    xabar = message.text.replace('/broadcast', '').strip()
    if not xabar:
        bot.reply_to(message, "✏️ Misol: /broadcast Salom hammaga!")
        return
    yuborildi = 0
    for uid in user_profiles:
        try:
            bot.send_message(uid, f"📢 {xabar}")
            yuborildi += 1
        except:
            pass
    bot.reply_to(message, f"✅ {yuborildi} ta foydalanuvchiga yuborildi!")

@bot.message_handler(commands=['rasm'])
def generate_image(message):
    prompt = message.text.replace('/rasm', '').strip()
    if not prompt:
        bot.reply_to(message, "✏️ Misol: /rasm tog'da qor yog'ayapti")
        return
    bot.reply_to(message, "🎨 Rasm yaratilmoqda... 30-60 sekund kuting!")
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers=headers,
            json={"inputs": prompt},
            timeout=60
        )
        if response.status_code == 200:
            bot.send_photo(message.chat.id, response.content, caption=f"🎨 {prompt}")
        else:
            bot.reply_to(message, "❌ Xatolik, qayta urining!")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "🖼 Rasm tahlil qilinmoqda...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}")
        image_data = {"mime_type": "image/jpeg", "data": file.content}
        caption = message.caption or "Bu rasmda nima bor? Batafsil tushuntir"
        response = gemini.generate_content([caption, image_data])
        bot.reply_to(message, "🖼 " + response.text)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    bot.reply_to(message, "📄 Fayl o'qilmoqda...")
    try:
        file_info = bot.get_file(message.document.file_id)
        file = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}")
        file_name = message.document.file_name.lower()
        text = ""
        if file_name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(io.BytesIO(file.content))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif file_name.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file.content))
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif file_name.endswith('.txt'):
            text = file.content.decode('utf-8')
        else:
            bot.reply_to(message, "❌ PDF, Word yoki TXT fayl yuboring!")
            return
        caption = message.caption or "Bu faylni tahlil qil va xulosa chiqar"
        response = gemini.generate_content(f"{caption}\n\nFayl:\n{text[:4000]}")
        bot.reply_to(message, "📄 " + response.text)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

@bot.message_handler(func=lambda m: True)
def handle(message):
    uid = message.from_user.id
    name = message.from_user.first_name
    if uid not in user_profiles:
        user_profiles[uid] = {"name": name}
        stats["total_users"] += 1
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        reply = ask_groq(uid, message.text)
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {str(e)}")

print("✅ Ziyrak Bot ishga tushdi!")
bot.polling(none_stop=True)
