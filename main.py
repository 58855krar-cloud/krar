# -*- coding: utf-8 -*-
# السورس البرمجي الكامل للإمبراطورية الرقمية النهائية - القائد أبو الكرار (النسخة التدميرية والتشغيلية الكاملة)
# Owner: أبو الكرار - @UE_SH

import asyncio
import logging
import sqlite3
import os
import time
import random
import json
import sys
from telethon import TelegramClient, events

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8958079044:AAG-_32kjtqDLbfngkdSEn6MseP1_8Kwyao"

OWNER_ID = 8345875922
OWNER_USERNAME = "@UE_SH"
API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"


bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ============================================================

# ============================================================
# 📁 إعدادات التسجيل والمجلدات والمسارات
# ============================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SESSIONS_DIR = "sessions"
DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "main.db")
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# 🤖 تشغيل البوت الرئيسي لتيليثون
# ============================================================



# حالات مؤقتة لتسجيل الدخول التفاعلي للمستخدمين (الهاتف والرمز وكلمة المرور)
user_states = {}

# ============================================================
# 🗄️ قاعدة البيانات الشاملة والمركبة (SQLite)
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        first_seen INTEGER,
        last_seen INTEGER,
        commands INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        subscription_expire INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        user_id INTEGER,
        session_type TEXT,
        session_path TEXT,
        created_at INTEGER,
        PRIMARY KEY (user_id, session_type)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned_words (
        word TEXT PRIMARY KEY,
        added_at INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS custom_responses (
        trigger TEXT PRIMARY KEY,
        response TEXT
    )''')
    conn.commit()
    conn.close()
    logger.info("✅ تم تهيئة قاعدة البيانات بالكامل مع الجداول الفعلية والديناميكية.")

def db_query(query, params=(), fetch_one=False, fetch_all=False, commit=True):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    result = None
    if fetch_one:
        result = c.fetchone()
    elif fetch_all:
        result = c.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return result

def get_user(user_id):
    return db_query("SELECT * FROM users WHERE user_id = ?", (user_id,), fetch_one=True)

def add_user(user_id, username, first_name, last_name=""):
    now = int(time.time())
    user = get_user(user_id)
    if user:
        db_query("UPDATE users SET username = ?, first_name = ?, last_name = ?, last_seen = ? WHERE user_id = ?",
                 (username or "", first_name or "", last_name or "", now, user_id))
    else:
        default_expire = now + (30 * 86400) # 30 يوماً تجريبية افتراضية
        db_query("INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen, subscription_expire) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (user_id, username or "", first_name or "", last_name or "", now, now, default_expire))

def update_user_command(user_id):
    db_query("UPDATE users SET commands = commands + 1, last_seen = ? WHERE user_id = ?", (int(time.time()), user_id))

def is_banned_user(user_id):
    result = db_query("SELECT is_banned FROM users WHERE user_id = ?", (user_id,), fetch_one=True)
    return result and result[0] == 1

def is_admin_user(user_id):
    result = db_query("SELECT is_admin FROM users WHERE user_id = ?", (user_id,), fetch_one=True)
    return result and result[0] == 1

def is_owner(user_id):
    return user_id == OWNER_ID

def check_subscription(user_id):
    if is_owner(user_id) or is_admin_user(user_id):
        return True
    user = get_user(user_id)
    if user and user[9] > int(time.time()):
        return True
    return False

# ============================================================
# 🎮 واجهة البداية والأزرار الرئيسية التفاعلية
# ============================================================
@bot.on(events.NewMessage(pattern="/start"))
async def start_command(event):
    user_id = event.sender_id
    sender = await event.get_sender()

    if is_banned_user(user_id):
        await event.reply("⛔ أنت محظور من استخدام هذا البوت بواسطة الإدارة.")
        return

    add_user(user_id, sender.username, sender.first_name, sender.last_name)
    update_user_command(user_id)
    
    user_name = sender.first_name if sender.first_name else "مستخدم"

    welcome_msg = (
        f"• مرحبًا بك عزيزي {user_name} |\n\n"
        f"• أنا مصنع سرس القائد أبو الكرار (@UE_SH)\n"
        f"• لتنصيب السورس اضغط على زر تسجيل ✅\n"
        f"• لطلب تنصيب أو استفسار تواصل مع المطور 🤍\n\n"
        f"🔹 حالة اشتراكك: مفعل (تجريبي 30 يوم)"
    )

    buttons = [
        [types.KeyboardButtonCallback("• تنصيب مجاني 🎁 | 30 يوم", b"free_install")],
        [types.KeyboardButtonCallback("• تسجيل 🟩 | LoGiN", b"login")],
        [types.KeyboardButtonCallback("• استخراج جلسة 🔑 /exr", b"extract_session")],
        [types.KeyboardButtonCallback("🔒 الأوامر السرية وتفعيل النجوم (XTR)", b"secret_stars_menu")],
        [
            types.KeyboardButtonUrl("💌 طلب تنصيب ⌁", "https://t.me/UE_SH"),
            types.KeyboardButtonCallback("💎 مميزات السورس ⌁", b"features")
        ],
        [
            types.KeyboardButtonUrl("👨‍💻 المطور الرسمي ⌁", "https://t.me/UE_SH"),
            types.KeyboardButtonUrl("🔗 قناة السورس ⌁", "https://t.me/UE_SH")
        ]
    ]

    await event.reply(welcome_msg, buttons=buttons)

# ============================================================
# 🎮 معالج الأزرار ونظام توليد الجلسات والدفع بالنجوم
# ============================================================
@bot.on(events.CallbackQuery())
async def handle_buttons(event):
    user_id = event.sender_id
    data_btn = event.data.decode()

    if data_btn == "login":
        user_states[user_id] = {"step": "waiting_phone"}
        await event.edit(
            "📱 **تسجيل الدخول لتوليد جلسة تليثون حقيقية**\n\n"
            "أرسل رقم هاتفك الآن مع رمز الدولة بصيغة دولية صحيحة:\n"
            "مثال: `+967733000000`",
            buttons=[[types.KeyboardButtonCallback("🔙 رجوع", b"back")]]
        )

    elif data_btn == "free_install":
        now = int(time.time())
        new_expire = now + (30 * 86400)
        db_query("UPDATE users SET subscription_expire = ? WHERE user_id = ?", (new_expire, user_id))
        await event.edit(
            "🎁 **التنصيب المجاني مفعل بنجاح!**\n\n"
            "تم منحك فترة تجريبية مدتها 30 يوماً كاملة للوصول لكافة الأوامر وتفعيل السورس.",
            buttons=[[types.KeyboardButtonCallback("🔙 رجوع", b"back")]]
        )

    elif data_btn == "extract_session":
        user_states[user_id] = {"step": "waiting_phone_extract"}
        await event.edit(
            "🔑 **استخراج جلسة ساشن (Session String)**\n\n"
            "أرسل رقم هاتفك الآن للبدء بعملية المصادقة واستخراج كود الجلسة الخاص بك:",
            buttons=[[types.KeyboardButtonCallback("🔙 رجوع", b"back")]]
        )

    elif data_btn == "secret_stars_menu":
        stars_text = (
            "⭐ **نظام الاشتراكات والنجوم للأوامر السرية (م45 إلى م70)** ⭐\n\n"
            "اختر نوع الاشتراك المناسب لبباقتك:\n\n"
            "📅 **يومي** – 50 نجمة ⭐\n"
            "📅 **أسبوعي** – 200 نجمة ⭐\n"
            "📅 **شهري** – 500 نجمة ⭐\n"
            "♾️ **دائم** – 2000 نجمة ⭐\n\n"
            "عند الضغط على أي باقة، سيتم توليد فاتورة نجوم رسمية (Telegram Stars) عبر البوت."
        )
        buttons = [
            [types.KeyboardButtonCallback("⭐ اشتراك يومي (50 نجمة)", b"buy_daily")],
            [types.KeyboardButtonCallback("⭐ اشتراك أسبوعي (200 نجمة)", b"buy_weekly")],
            [types.KeyboardButtonCallback("⭐ اشتراك شهري (500 نجمة)", b"buy_monthly")],
            [types.KeyboardButtonCallback("⭐ اشتراك دائم (2000 نجمة)", b"buy_lifetime")],
            [types.KeyboardButtonCallback("🔙 رجوع", b"back")]
        ]
        await event.edit(stars_text, buttons=buttons)

    elif data_btn in ["buy_daily", "buy_weekly", "buy_monthly", "buy_lifetime"]:
        durations = {
            "buy_daily": (1, "يومي (50 نجمة)"),
            "buy_weekly": (7, "أسبوعي (200 نجمة)"),
            "buy_monthly": (30, "شهري (500 نجمة)"),
            "buy_lifetime": (3650, "دائم (2000 نجمة)")
        }
        days, title = durations[data_btn]
        prices = {"buy_daily": 50, "buy_weekly": 200, "buy_monthly": 500, "buy_lifetime": 2000}
        amount = prices[data_btn]

        try:
            await bot.send_invoice(
                chat_id=user_id,
                title=f"اشتراك الأوامر السرية - {title}",
                description="يمنحك هذا الاشتراك صلاحية الوصول المطلق والفوري للأوامر التدميرية والسرية (م45 إلى م70).",
                payload=f"sub_{user_id}_{days}",
                currency="XTR",
                prices=[types.LabeledPrice(label=title, amount=amount)]
            )
            await event.answer("✅ تم إرسال فاتورة الدفع بالنجوم إلى الخاص بك.", alert=True)
        except Exception:
            await event.edit(
                f"⭐ **الدفع اليدوي المباشر:**\n\n"
                f"الباقة المطلوبة: {title}\n"
                f"يرجى تحويل **{amount} نجمة** إلى المطور @UE_SH ثم إرسال إيصال التحويل للمطور لتفعيل حسابك فوراً.",
                buttons=[[types.KeyboardButtonCallback("🔙 رجوع", b"secret_stars_menu")]]
            )

    elif data_btn == "features":
        await event.answer("سورس متطور، حماية عالية، يعمل على مدار 24 ساعة، وأوامر سرية مخصصة.", alert=True)

    elif data_btn == "back":
        if user_id in user_states:
            del user_states[user_id]
        await start_command(event)

# ============================================================
# 📱 معالجة إدخال رقم الهاتف، كود التحقق (OTP) وكلمة المرور (2FA)
# ============================================================
@bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id in user_states))
async def interactive_login_handler(event):
    user_id = event.sender_id
    text = event.text.strip()
    state = user_states[user_id]
    step = state.get("step")

    if step == "waiting_phone":
        state["phone"] = text
        state["step"] = "waiting_code"
        client_temp = TelegramClient(os.path.join(SESSIONS_DIR, f"temp_{user_id}"), API_ID, API_HASH)
        await client_temp.connect()
        state["client_temp"] = client_temp
        try:
            sent = await client_temp.send_code_request(text)
            state["phone_code_hash"] = sent.phone_code_hash
            await event.reply("✅ تم إرسال كود التحقق من تيليجرام إلى حسابك.\nأرسل الكود الآن:")
        except Exception as e:
            del user_states[user_id]
            await client_temp.disconnect()
            await event.reply(f"❌ حدث خطأ أثناء إرسال الكود:\n`{str(e)}`")

    elif step == "waiting_code":
        state["code"] = text.replace(" ", "")
        client_temp = state["client_temp"]
        phone = state["phone"]
        phone_code_hash = state["phone_code_hash"]
        try:
            await client_temp.sign_in(phone=phone, code=state["code"], phone_code_hash=phone_code_hash)
            session_string = client_temp.session.save()
            session_path = os.path.join(SESSIONS_DIR, f"{user_id}_main.session")
            with open(session_path, "w", encoding="utf-8") as f:
                f.write(session_string)
            db_query("INSERT OR REPLACE INTO sessions (user_id, session_type, session_path, created_at) VALUES (?, ?, ?, ?)",
                     (user_id, "main", session_path, int(time.time())))
            await client_temp.disconnect()
            del user_states[user_id]
            await event.reply(
                "🎉 **تم تسجيل الدخول واستخراج الجلسة بنجاح تام!**\n\n"
                f"🔑 كود الساشن الخاص بك:\n`{session_string}`"
            )
        except SessionPasswordNeededError:
            state["step"] = "waiting_password"
            await event.reply("🔐 **الحساب محمي بتحقق ثنائي (2FA).**\nأرسل كلمة مرور الحساب السرية الآن:")
        except Exception as e:
            try:
                await client_temp.disconnect()
            except:
                pass
            del user_states[user_id]
            await event.reply(f"❌ فشل تسجيل الدخول:\n`{str(e)}`")

    elif step == "waiting_password":
        client_temp = state["client_temp"]
        try:
            await client_temp.sign_in(password=text)
            session_string = client_temp.session.save()
            session_path = os.path.join(SESSIONS_DIR, f"{user_id}_main.session")
            with open(session_path, "w", encoding="utf-8") as f:
                f.write(session_string)
            db_query("INSERT OR REPLACE INTO sessions (user_id, session_type, session_path, created_at) VALUES (?, ?, ?, ?)",
                     (user_id, "main", session_path, int(time.time())))
            await client_temp.disconnect()
            del user_states[user_id]
            await event.reply(
                "🎉 **تم تسجيل الدخول وتجاوز التحقق الثنائي بنجاح!**\n\n"
                f"🔑 كود الساشن الخاص بك:\n`{session_string}`"
            )
        except Exception as e:
            try:
                await client_temp.disconnect()
            except:
                pass
            del user_states[user_id]
            await event.reply(f"❌ كلمة المرور غير صحيحة:\n`{str(e)}`")

    elif step == "waiting_phone_extract":
        state["phone"] = text
        state["step"] = "waiting_code_extract"
        client_temp = TelegramClient(os.path.join(SESSIONS_DIR, f"extract_{user_id}"), API_ID, API_HASH)
        await client_temp.connect()
        state["client_temp"] = client_temp
        try:
            sent = await client_temp.send_code_request(text)
            state["phone_code_hash"] = sent.phone_code_hash
            await event.reply("✅ تم إرسال كود التحقق لاستخراج الجلسة. أرسل الكود الآن:")
        except Exception as e:
            del user_states[user_id]
            await client_temp.disconnect()
            await event.reply(f"❌ خطأ: `{str(e)}`")

    elif step == "waiting_code_extract":
        state["code"] = text.replace(" ", "")
        client_temp = state["client_temp"]
        phone = state["phone"]
        phone_code_hash = state["phone_code_hash"]
        try:
            await client_temp.sign_in(phone=phone, code=state["code"], phone_code_hash=phone_code_hash)
            ss = client_temp.session.save()
            await client_temp.disconnect()
            del user_states[user_id]
            await event.reply(f"🔑 **تم استخراج الجلسة بنجاح:**\n\n`{ss}`")
        except SessionPasswordNeededError:
            state["step"] = "waiting_password_extract"
            await event.reply("🔐 الحساب يتطلب تحقق ثنائي (2FA). أرسل كلمة المرور الآن:")
        except Exception as e:
            try:
                await client_temp.disconnect()
            except:
                pass
            del user_states[user_id]
            await event.reply(f"❌ خطأ: `{str(e)}`")

    elif step == "waiting_password_extract":
        client_temp = state["client_temp"]
        try:
            await client_temp.sign_in(password=text)
            ss = client_temp.session.save()
            await client_temp.disconnect()
            del user_states[user_id]
            await event.reply(f"🔑 **تم استخراج الجلسة بنجاح:**\n\n`{ss}`")
        except Exception as e:
            try:
                await client_temp.disconnect()
            except:
                pass
            del user_states[user_id]
            await event.reply(f"❌ خطأ في كلمة المرور: `{str(e)}`")

# ============================================================
# 🚀 تشغيل البوت النهائي
# ============================================================
async def main():
    init_db()
    logger.info("🔥 سورس القائد أبو الكرار يعمل بكامل طاقته...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.run_polling()
