"""
سورس حمزة | يوزربوت تيليثون
كل شيء في ملف واحد | تخزين JSON | بدون بوت خارجي | بدون قواعد بيانات
"""

import asyncio
import gzip
import html
import http.client
import io
import json
import os
import random
import re
import string
import subprocess
import sys
import time
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    import brotli
except ImportError:
    brotli = None

try:
    from getids import get_date_as_string
except ImportError:
    import subprocess, sys
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "git+https://github.com/AmanoTeam/python-getids.git",
             "--break-system-packages", "--quiet"],
            timeout=60,
        )
        from getids import get_date_as_string
    except Exception:
        get_date_as_string = None

from telethon import TelegramClient, events, functions, types
from telethon.errors import (
    ChatAdminRequiredError,
    FloodWaitError,
    MessageIdInvalidError,
    MessageNotModifiedError,
    UserAdminInvalidError,
    UsernameNotOccupiedError,
    ChannelPrivateError,
    ChannelBannedError,
    UserIdInvalidError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    UserBannedInChannelError,
    UsersTooMuchError,
)
from telethon.sessions import StringSession
from telethon.tl.functions.channels import EditAdminRequest, EditBannedRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.types import (
    ChatAdminRights,
    ChatBannedRights,
    MessageEntityMentionName,
    ChatInvite,
    ChatInviteAlready,
    User,
    Channel,
    Chat,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = {}
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg["API_ID"] = int(cfg.get("API_ID") or os.environ.get("API_ID") or 0)
    cfg["API_HASH"] = cfg.get("API_HASH") or os.environ.get("API_HASH") or ""
    _PLACEHOLDER_HASHES = ("", "your_api_hash_here", "YOUR_API_HASH_HERE", "0123456789abcdef0123456789abcdef")
    if cfg["API_HASH"].strip() in _PLACEHOLDER_HASHES:
        cfg["API_HASH"] = ""
    if cfg["API_ID"] in (0, 1234567):
        cfg["API_ID"] = 0
    cfg["STRING_SESSION"] = (
        cfg.get("STRING_SESSION") or os.environ.get("STRING_SESSION") or ""
    )
    cfg["PREFIX"] = cfg.get("PREFIX") or "."
    cfg["OWNER_NAME"] = cfg.get("OWNER_NAME") or "حمزة"
    if not cfg["API_ID"] or not cfg["API_HASH"]:
        print("=" * 45)
        print("  إعداد سورس حمزة — أدخل بياناتك:")
        print("=" * 45)
        try:
            aid = input("* API_ID: ").strip()
            ahash = input("* API_HASH: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("تم الإلغاء")
            sys.exit(1)
        cfg["API_ID"] = int(aid) if aid.isdigit() else 0
        cfg["API_HASH"] = ahash
        if not cfg["API_ID"] or not cfg["API_HASH"]:
            print("بيانات غير صحيحة")
            sys.exit(1)
        _save_cfg_basic(cfg)
        print("✓ تم حفظ API_ID و API_HASH")
    return cfg


def _save_cfg_basic(cfg):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data["API_ID"] = cfg["API_ID"]
    data["API_HASH"] = cfg["API_HASH"]
    data["PREFIX"] = cfg["PREFIX"]
    data["OWNER_NAME"] = cfg["OWNER_NAME"]
    data["STRING_SESSION"] = cfg.get("STRING_SESSION", "")
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def save_session(session_str):
    """حفظ كود السيشن المولّد تلقائياً في config.json"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data["STRING_SESSION"] = session_str
    data.setdefault("API_ID", CONFIG["API_ID"])
    data.setdefault("API_HASH", CONFIG["API_HASH"])
    data.setdefault("PREFIX", CONFIG["PREFIX"])
    data.setdefault("OWNER_NAME", CONFIG["OWNER_NAME"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


CONFIG = load_config()
PREFIX = CONFIG["PREFIX"]
OWNER_NAME = CONFIG["OWNER_NAME"]



def _path(name):
    return os.path.join(DATA_DIR, f"{name}.json")


def db_read(name, default=None):
    """قراءة ملف json | كل ميزة لها ملفها الخاص"""
    p = _path(name)
    if not os.path.exists(p):
        return {} if default is None else default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {} if default is None else default


def db_write(name, data):
    """كتابة ملف json"""
    with open(_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def db_get(name, key, default=None):
    return db_read(name).get(str(key), default)


def db_set(name, key, value):
    data = db_read(name)
    data[str(key)] = value
    db_write(name, data)


def db_del(name, key):
    data = db_read(name)
    if str(key) in data:
        del data[str(key)]
        db_write(name, data)
        return True
    return False



client = TelegramClient(
    StringSession(CONFIG["STRING_SESSION"]),
    CONFIG["API_ID"],
    CONFIG["API_HASH"],
    device_model="Hamza Userbot",
    system_version="Android 12",
    app_version="Hamza 2.3",
    lang_code="ar",
    system_lang_code="ar",
    auto_reconnect=True,
    connection_retries=10,
    retry_delay=2,
    flood_sleep_threshold=60,
)

START_TIME = time.time()
CMD_SECTIONS = {}




def cmd(pattern, groups_only=False, private_only=False, edited=True):
    """
    ديكوريتر تسجيل امر جديد
    pattern: النمط بعد البادئة | مثال: r"حظر(?:\\s|$)([\\s\\S]*)"
    """
    reg = re.compile("^\\" + PREFIX + pattern)

    def decorator(func):
        async def wrapper(event):
            if groups_only and not event.is_group:
                return await edit_delete(event, "- هذا الأمر للمجموعات فقط", 8)
            if private_only and not event.is_private:
                return await edit_delete(event, "- هذا الأمر للخاص فقط", 8)
            try:
                await func(event)
            except events.StopPropagation:
                raise
            except MessageNotModifiedError:
                pass
            except MessageIdInvalidError:
                pass
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 3)
            except ChatAdminRequiredError:
                await edit_delete(event, "- لا أملك صلاحيات كافية هنا", 8)
            except Exception as e:
                await edit_delete(event, f"- خطأ:\n`{e}`", 12)

        client.add_event_handler(
            wrapper, events.NewMessage(pattern=reg, outgoing=True)
        )
        if edited:
            client.add_event_handler(
                wrapper, events.MessageEdited(pattern=reg, outgoing=True)
            )
        return wrapper

    return decorator




async def edit_or_reply(event, text, link_preview=False, **kwargs):
    """يعدّل رسالتك أو يرد | يتعامل مع النص الطويل كملف | مع fallback عند فشل الإرسال"""
    text = str(text)
    try:
        if len(text) < 4096:
            try:
                return await event.edit(text, link_preview=link_preview, **kwargs)
            except Exception:
                return await event.reply(text, link_preview=link_preview, **kwargs)
        return await _send_as_file(event, text)
    except MessageNotModifiedError:
        return event
    except Exception:
        try:
            return await _send_as_file(event, text)
        except Exception:
            return event


async def _send_as_file(event, text):
    """يرسل النص كملف نصي مع تجنّب خطأ الإرسال"""
    try:
        file = io.BytesIO(text.encode("utf-8"))
        file.name = "result.txt"
        reply = await event.get_reply_message()
        target = reply or event
        sent = await target.reply("الناتج طويل/كبير — تم إرساله كملف ", file=file)
        try:
            await event.delete()
        except Exception:
            pass
        return sent
    except Exception as e:
        return await _send_chunks(event, text, str(e))


async def _send_chunks(event, text, err=""):
    limit = 4000
    parts = [text[i:i + limit] for i in range(0, len(text), limit)]
    out = []
    for i, p in enumerate(parts, 1):
        prefix = f"(جزء {i}/{len(parts)}) " if len(parts) > 1 else ""
        try:
            out.append(await event.reply(prefix + p))
        except Exception:
            pass
    if not out and err:
        try:
            await event.reply(f"تعذّر الإرسال: {err}")
        except Exception:
            pass
    return out


async def edit_delete(event, text, seconds=8, link_preview=False):
    """يعدّل الرسالة ثم يحذفها بعد وقت"""
    try:
        msg = await event.edit(text, link_preview=link_preview)
    except Exception:
        try:
            msg = await event.reply(text, link_preview=link_preview)
        except Exception:
            return
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except Exception:
        pass


async def get_target_user(event):
    """يجلب المستخدم المستهدف: بالرد أو بالمعرف/الايدي مع الأمر"""
    reply = await event.get_reply_message()
    if reply:
        try:
            user = await event.client.get_entity(reply.sender_id)
            return user, reply.sender_id
        except Exception:
            return None, reply.sender_id
    args = event.pattern_match.group(1)
    if args and args.strip():
        arg = args.strip().split()[0]
        try:
            if arg.isdigit() or (arg.startswith("-") and arg[1:].isdigit()):
                user = await event.client.get_entity(int(arg))
            else:
                user = await event.client.get_entity(arg)
            return user, user.id
        except Exception:
            return None, None
    return None, None


def get_display_name(user):
    if user is None:
        return "مجهول"
    name = user.first_name or ""
    if getattr(user, "last_name", None):
        name += f" {user.last_name}"
    return name.strip() or "مجهول"


def mention(user):
    if user is None:
        return "مجهول"
    return f"[{get_display_name(user)}](tg://user?id={user.id})"


def readable_time(seconds):
    seconds = int(seconds)
    result = ""
    for unit, count in (("ي", 86400), ("س", 3600), ("د", 60), ("ث", 1)):
        if seconds >= count:
            val = seconds // count
            seconds %= count
            result += f"{val}{unit} "
    return result.strip() or "0ث"



MENU_MAIN = f"""✦ ────『قـائـمـة اوامر سورس حـمـزة』──── ✦
مرحبا بك عزيزي {OWNER_NAME}

• `{PREFIX}م1` ➪ اوامـر الاداره
• `{PREFIX}م2` ➪ اوامـر المجموعه
• `{PREFIX}م3` ➪ اوامـر الكشف والايدي
• `{PREFIX}م4` ➪ اوامـر الردود
• `{PREFIX}م5` ➪ اوامـر الترحيب
• `{PREFIX}م6` ➪ اوامـر حمايه الخاص
• `{PREFIX}م7` ➪ اوامـر الاذاعه
• `{PREFIX}م8` ➪ اوامـر البوت
• `{PREFIX}م9` ➪ اوامـر المنع والترجمه
• `{PREFIX}م10` ➪ اوامـر السبام والصملات
• `{PREFIX}م11` ➪ اوامـر البروفايل
• `{PREFIX}م12` ➪ اوامـر الصيغ
• `{PREFIX}م13` ➪ اوامـر التسليه
• `{PREFIX}م14` ➪ اوامـر التحكم
• `{PREFIX}م15` ➪ اوامـر الذكاء الاصطناعي
• `{PREFIX}م16` ➪ اوامـر التحديثات
• `{PREFIX}م17` ➪ اوامـر الفحص والبلاغات
• `{PREFIX}م18` ➪ اوامـر الاسم الوقتي
• `{PREFIX}م19` ➪ اوامـر محوّل الصوت
• `{PREFIX}م20` ➪ اوامـر الكتم
• `{PREFIX}م21` ➪ اوامـر التفليش
• `{PREFIX}م22` ➪ اوامـر التحميل

✦ ─────────────────────────── ✦"""


def _fmt_section(txt):
    """يحوّل قوالب `{p}` و `{header_opa ...}` و `{b}` و `{e}` و `{cmd}` إلى نص منسق"""
    txt = re.sub(r"\{header_opa\s+(.+?)\}", r"╭─────────────────────╮\n    ◆ \1\n╰─────────────────────╯", txt)
    txt = txt.replace("{b}", "  • ")
    txt = txt.replace("{cmd}", PREFIX)
    txt = txt.replace("{e}", "")
    return txt

MENU = {
    "م1": """{header_opa امر الاداره}

{b}`{cmd}حظر`{e} — بالرد أو المعرف لحظر شخص
{b}`{cmd}الغاء حظر`{e} — لفك حظر شخص
{b}`{cmd}طرد`{e} — طرد شخص من المجموعة
{b}`{cmd}رفع مشرف`{e} — رفع شخص مشرف
{b}`{cmd}تنزيل مشرف`{e} — تنزيل مشرف
{b}`{cmd}تثبيت`{e} — تثبيت رسالة بالرد
{b}`{cmd}الغاء تثبيت`{e} — إلغاء التثبيت
{b}`{cmd}مسح`{e} — حذف رسائل بالعدد
{b}`{cmd}تحذير`{e} — تحذير عضو
{b}`{cmd}التحذيرات`{e} — عرض تحذيرات عضو
{b}`{cmd}حذف التحذيرات`{e} — مسح تحذيرات عضو""",
    "م2": """{header_opa امر المجموعه}

{b}`{cmd}المشرفين`{e} — عرض مشرفي المجموعة
{b}`{cmd}الاعضاء`{e} — عرض عدد الأعضاء
{b}`{cmd}معلومات`{e} — عرض معلومات المجموعة
{b}`{cmd}البوتات`{e} — عرض البوتات في المجموعة""",
    "م3": """{header_opa امر الكشف والايدي}

{b}`{cmd}الايدي`{e} — بالرد أو المعرف لعرض الايدي
{b}`{cmd}كشف`{e} — عرض معلومات مستخدم
{b}`{cmd}صورة`{e} — جلب صورة مستخدم
{b}`{cmd}انشاء`{e} — بالرد/المعرف لعرض تاريخ الإنشاء ودولة الحساب""",
    "م4": """{header_opa امر الردود}

{b}`{cmd}اضف رد`{e} — بالرد لإضافة رد على كلمة
{b}`{cmd}حذف رد`{e} — حذف رد
{b}`{cmd}الردود`{e} — عرض جميع الردود
{b}`{cmd}مسح الردود`{e} — حذف كل الردود""",
    "م5": """{header_opa امر الترحيب}

{b}`{cmd}ضبط ترحيب`{e} — ضبط رسالة ترحيب
{b}`{cmd}الترحيب`{e} — عرض الترحيب الحالي
{b}`{cmd}حذف الترحيب`{e} — إلغاء الترحيب""",
    "م6": """{header_opa امر حمايه الخاص}

{b}`{cmd}الحماية تشغيل`{e} — تشغيل حماية الخاص
{b}`{cmd}الحماية تعطيل`{e} — تعطيل حماية الخاص
{b}`{cmd}سماح`{e} — السماح لشخص بالخاص
{b}`{cmd}رفض`{e} — رفض شخص من الخاص
{b}`{cmd}المسموحين`{e} — عرض المسموح لهم""",
    "م7": """{header_opa امر الاذاعه}

{b}`{cmd}للكروبات`{e} — نشر رسالة بكل مجموعاتك
{b}`{cmd}للخاص`{e} — إرسال رسالة لكل محادثاتك الخاصة""",
    "م8": """{header_opa امر البوت}

{b}`{cmd}فحص`{e} — عرض معلومات السورس
{b}`{cmd}بنك`{e} — عرض سرعة الاستجابة
{b}`{cmd}اعادة تشغيل`{e} — إعادة تشغيل السورس
{b}`{cmd}الوقت`{e} — عرض مدة التشغيل""",
    "م9": """{header_opa امر المنع والترجمه}

{b}`{cmd}منع`{e} — منع كلمة في المجموعة
{b}`{cmd}الغاء منع`{e} — إلغاء منع كلمة
{b}`{cmd}قائمة المنع`{e} — عرض الكلمات الممنوعة
{b}`{cmd}ترجمة`{e} — بالرد لترجمة النص""",
    "م10": """{header_opa امر السبام والصملات}

{b}`{cmd}نيكه`{e} — سبام بتحديد أكثر من هدف (يوزرات/رد)
{b}`{cmd}خلاص`{e} — إيقاف السبام من كل الأهداف
{b}`{cmd}الأهداف`{e} — عرض أهداف الإرسال الجارية
{b}`{cmd}سرعه`{e} — ضبط سرعة الإرسال
{b}`{cmd}دفعة`{e} — عدد رسائل كل دفعة (مثل 1 ~ 10)
{b}`{cmd}سب ذكاء`{e} — توغل السب بـ AI بدل المولّد المحلي
{b}`{cmd}تتبع`{e} — رد تلقائي على رسائل شخص في الخاص أو المجموعات
{b}`{cmd}كافي`{e} — إيقاف الرد التلقائي
{b}`{cmd}معاينة سب`{e} — عرض عينات من المولّد
{b}`{cmd}عدد السب`{e} — عرض عدد التركيبات الممكنة
{b}`{cmd}اضف سب`{e} — لإثراء المكتبة
{b}`{cmd}حماية الفلود`{e} — تشغيل/إيقاف الحماية
{b}`{cmd}الفلود`{e} — عرض إحصائيات الحماية
{b}`{cmd}تحديد`{e} — بالرد لإضافة رسالة من المحفوظات (بدون حدود)
{b}`{cmd}الغاء تحديد`{e} — بالرد لإزالة رسالة محددة
{b}`{cmd}المحددات`{e} — عرض كل الرسائل المحددة
{b}`{cmd}مسح كل محدد`{e} — مسح كل الرسائل المحددة
{b}`{cmd}تشغيل التحويل`{e} — بدء التحويل من المحفوظات
{b}`{cmd}ايقاف التحويل`{e} — إيقاف التحويل
{b}`{cmd}ديلاي`{e} — ضبط زمن التحويل""",
    "م11": """{header_opa امر البروفايل}

{b}`{cmd}تغيير اسم`{e} — تغيير اسمك
{b}`{cmd}تغيير بايو`{e} — تغيير نبذتك
{b}`{cmd}تغيير صورة`{e} — بالرد لتغيير صورتك
{b}`{cmd}حسابي`{e} — عرض معلومات حسابك""",
    "م12": """{header_opa امر الصيغ}

{b}`{cmd}ملصق`{e} — بالرد على صورة لتحويلها ملصق
{b}`{cmd}صورة`{e} — بالرد على ملصق لتحويله صورة
{b}`{cmd}صوت`{e} — بالرد على مقطع لتحويله بصمة صوت""",
    "م13": """{header_opa امر التسليه}

{b}`{cmd}نسبة الحب`{e} — عرض نسبة الحب
{b}`{cmd}نسبة الغباء`{e} — عرض نسبة الغباء
{b}`{cmd}قلوب`{e} — عرض قلوب متحركة
{b}`{cmd}عد`{e} — العد التنازلي
{b}`{cmd}نرد`{e} — رمي النرد""",
    "م14": """{header_opa امر التحكم}

{b}`{cmd}التحكم تشغيل`{e} — تفعيل تحكم مستخدمين آخرين
{b}`{cmd}التحكم تعطيل`{e} — تعطيل التحكم
{b}`{cmd}اضف متحكم`{e} — بالرد لإضافة متحكم
{b}`{cmd}ازالة متحكم`{e} — بالرد لإزالة متحكم
{b}`{cmd}المتحكمين`{e} — عرض المتحكمين""",
    "م15": """{header_opa امر الذكاء الاصطناعي}

{b}`{cmd}ذكاء`{e} — محادثة تفاعلية + تنفيذ أدوات
{b}`{cmd}ذكاء مفعل`{e} — تفعيل الوضع الشامل
{b}`{cmd}ذكاء تشغيل`{e} — رد تلقائي بالخاص
{b}`{cmd}ذكاء تعطيل`{e} — إيقاف الرد التلقائي
{b}`{cmd}ذكاء سياق`{e} — عدد رسائل السياق
{b}`{cmd}ذكاء ذاكرة`{e} — عرض/مسح الذاكرة
{b}`{cmd}ذكاء جلسة`{e} — عرض/مسح جلسة المحادثة
{b}`{cmd}دليل الذكاء`{e} — توليد دليل السورس
{b}`{cmd}ادوات الذكاء`{e} — عرض الأدوات
{b}`{cmd}تعليمات الذكاء`{e} — عرض/تعديل التعليمات""",
    "م16": """{header_opa امر التحديثات}

{b}`{cmd}تحديث`{e} — تنزيل آخر تحديث وإعادة التشغيل
{b}`{cmd}تحديثات`{e} — عرض آخر التحديثات
{b}`{cmd}اخر_تحديث`{e} — عرض آخر إصدار منشور""",
    "م17": """{header_opa امر الفحص والبلاغات}

{b}`{cmd}فحص`{e} — فحص قناة/حساب
{b}`{cmd}فحص_دفعه`{e} — فحص رابط دعوة
{b}`{cmd}فحص_مجموعه`{e} — فحص المجموعة الحالية
{b}`{cmd}شد_هدف`{e} — ضبط هدف البلاغ
{b}`{cmd}شد_نوع`{e} — نوع البلاغ
{b}`{cmd}شد_رساله`{e} — نص البلاغ
{b}`{cmd}شد_سرعه`{e} — التأخير بين البلاغات
{b}`{cmd}شد`{e} — بدء بلاغ مستمر
{b}`{cmd}شد_ايقاف`{e} — إيقاف البلاغ
{b}`{cmd}شد_اعداد`{e} — عرض الإعدادات""",
    "م18": """{header_opa امر الاسم الوقتي}

{b}`{cmd}وقتي`{e} — عرض الحالة والمعاينة والتوقيت
{b}`{cmd}وقتي تشغيل`{e} — يفعّل التحديث كل دقيقة
{b}`{cmd}وقتي ايقاف`{e} — يوقفه
{b}`{cmd}وقتي شكل`{e} — يختار شكل زخرفة الأرقام
{b}`{cmd}وقتي توقيت`{e} — يختار التوقيت""",
    "م19": """{header_opa امر محوّل الصوت}

{b}`{cmd}صوتي`{e} — عرض قائمة التأثيرات
{b}`{cmd}صوتي`{e} — بالرد على مقطع لتطبيق التأثير
{b}`{cmd}صوتي سجل`{e} — التسجيل في خادم الصوت""",
    "م20": """{header_opa امر الكتم}

{b}`{cmd}كتم`{e} — لكتم شخص تُحذف رسائله تلقائياً
{b}`{cmd}الغاء كتم`{e} — لفك كتم شخص
{b}`{cmd}المكتومين`{e} — عرض قائمة المكتومين
{b}`{cmd}مسح كل المكتومين`{e} — فك كتم الجميع""",
    "م21": """{header_opa امر التفليش}

{b}`{cmd}تفليش`{e} — مسح الأعضاء عبر API مباشر
{b}`{cmd}تفلش`{e} — مسح الأعضاء عبر بوت (بالآيدي)
{b}`{cmd}تفلش2`{e} — مسح الأعضاء عبر بوت (باليوزر)
{b}`{cmd}وقف`{e} — إيقاف عملية التفليش""",
    "م22": """{header_opa امر التحميل}

{b}`{cmd}تيك`{e} — تحميل من تيك توك (فيديو/صورة/مزيكا)
{b}`{cmd}يوت`{e} — بحث في يوتيوب وتحميل الأغنية MP3""",
}


@cmd(r"الاوامر$")
async def _(event):
    await edit_or_reply(event, MENU_MAIN)


for _sec, _txt in MENU.items():
    def _make(txt):
        async def handler(event):
            await edit_or_reply(event, _fmt_section(txt))
        return handler
    client.add_event_handler(
        _make(_txt),
        events.NewMessage(pattern=re.compile("^\\" + PREFIX + _sec + "$"), outgoing=True),
    )
    client.add_event_handler(
        _make(_txt),
        events.MessageEdited(pattern=re.compile("^\\" + PREFIX + _sec + "$"), outgoing=True),
    )



BAN_RIGHTS = ChatBannedRights(until_date=None, view_messages=True)
UNBAN_RIGHTS = ChatBannedRights(
    until_date=None, view_messages=False, send_messages=False,
    send_media=False, send_stickers=False, send_gifs=False,
    send_games=False, send_inline=False, embed_links=False,
)
MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)
UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)


@cmd(r"حظر(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    try:
        await event.client(EditBannedRequest(event.chat_id, uid, BAN_RIGHTS))
    except Exception as e:
        return await edit_delete(event, f"- تعذر الحظر: `{e}`", 8)
    await edit_or_reply(event, f"تم حظر {mention(user)} ✓")


@cmd(r"الغاء حظر(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    try:
        await event.client(EditBannedRequest(event.chat_id, uid, UNBAN_RIGHTS))
    except Exception as e:
        return await edit_delete(event, f"- تعذر فك الحظر: `{e}`", 8)
    await edit_or_reply(event, f"تم فك حظر {mention(user)} ✓")


def _mutes_read():
    return db_read("mutes", {})


def _mutes_write(data):
    db_write("mutes", data)


def _muted_global_ids():
    return set(int(k) for k in _mutes_read().keys())


@cmd(r"كتم(?:\s|$)([\s\S]*)")
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    data = _mutes_read()
    data[str(uid)] = get_display_name(user)
    _mutes_write(data)
    await edit_or_reply(event, f"تم كتم {mention(user)} — ستُحذف رسائله في كل الأماكن ✓")


@cmd(r"الغاء كتم(?:\s|$)([\s\S]*)")
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    data = _mutes_read()
    if str(uid) in data:
        del data[str(uid)]
        _mutes_write(data)
        await edit_or_reply(event, f"تم فك كتم {mention(user)} ✓")
    else:
        await edit_delete(event, "- هذا الشخص ليس مكتوماً", 8)


@cmd(r"المكتومين$")
async def _(event):
    data = _mutes_read()
    if not data:
        return await edit_or_reply(event, "- لا يوجد مكتومون")
    lines = []
    for uid, name in data.items():
        lines.append(f"• {name} — `{uid}`")
    await edit_or_reply(event, "**| المكتومون (تُحذف رسائلهم في كل الأماكن):**\n\n" + "\n".join(lines))


@cmd(r"مسح كل المكتومين$")
async def _(event):
    _mutes_write({})
    await edit_or_reply(event, "تم فك كتم جميع المكتومين ✓")


@client.on(events.NewMessage(incoming=True))
async def _mutes_watcher(event):
    if not event.sender_id:
        return
    if event.sender_id in _muted_global_ids():
        try:
            await event.delete()
        except Exception:
            pass


@cmd(r"طرد(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    try:
        await event.client.kick_participant(event.chat_id, uid)
    except Exception as e:
        return await edit_delete(event, f"- تعذر الطرد: `{e}`", 8)
    await edit_or_reply(event, f"تم طرد {mention(user)} ✓")


@cmd(r"رفع مشرف(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    reply = await event.get_reply_message()
    title = OWNER_NAME
    args = event.pattern_match.group(1)
    uid = None
    if reply:
        uid = reply.sender_id
        if args and args.strip():
            title = args.strip()
    elif args and args.strip():
        parts = args.strip().split(maxsplit=1)
        try:
            uid = (await event.client.get_entity(parts[0])).id
        except Exception:
            return await edit_delete(event, "- لم أجد المستخدم", 8)
        if len(parts) > 1:
            title = parts[1]
    if not uid:
        return await edit_delete(event, "- رد على شخص لرفعه", 8)
    rights = ChatAdminRights(
        change_info=True, post_messages=True, edit_messages=True,
        delete_messages=True, ban_users=True, invite_users=True,
        pin_messages=True, add_admins=False, manage_call=True,
    )
    try:
        await event.client(EditAdminRequest(event.chat_id, uid, rights, title[:16]))
    except Exception as e:
        return await edit_delete(event, f"- تعذر الرفع: `{e}`", 8)
    user, _ = await get_target_user(event)
    await edit_or_reply(event, f"تم رفع {mention(user)} مشرفاً ✓")


@cmd(r"تنزيل مشرف(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    rights = ChatAdminRights(
        change_info=False, post_messages=False, edit_messages=False,
        delete_messages=False, ban_users=False, invite_users=False,
        pin_messages=False, add_admins=False,
    )
    try:
        await event.client(EditAdminRequest(event.chat_id, uid, rights, ""))
    except Exception as e:
        return await edit_delete(event, f"- تعذر التنزيل: `{e}`", 8)
    await edit_or_reply(event, f"تم تنزيل {mention(user)} من الإشراف ✓")


@cmd(r"تثبيت$", groups_only=True)
async def _(event):
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "- رد على رسالة لتثبيتها", 8)
    try:
        await event.client.pin_message(event.chat_id, reply.id, notify=True)
    except Exception as e:
        return await edit_delete(event, f"- تعذر التثبيت: `{e}`", 8)
    await edit_delete(event, "تم التثبيت ✓", 5)


@cmd(r"الغاء تثبيت$", groups_only=True)
async def _(event):
    reply = await event.get_reply_message()
    try:
        if reply:
            await event.client.unpin_message(event.chat_id, reply.id)
        else:
            await event.client.unpin_message(event.chat_id)
    except Exception as e:
        return await edit_delete(event, f"- تعذر الإلغاء: `{e}`", 8)
    await edit_delete(event, "تم إلغاء التثبيت ✓", 5)


@cmd(r"مسح(?:\s|$)(?!كل محدد)([\s\S]*)", groups_only=True)
async def _(event):
    reply = await event.get_reply_message()
    args = event.pattern_match.group(1)
    count = 0
    if reply:
        msgs = []
        async for msg in event.client.iter_messages(
            event.chat_id, min_id=reply.id - 1, reverse=True
        ):
            msgs.append(msg.id)
            if len(msgs) >= 500:
                break
        if msgs:
            await event.client.delete_messages(event.chat_id, msgs)
            count = len(msgs)
    elif args and args.strip().isdigit():
        n = int(args.strip())
        msgs = []
        async for msg in event.client.iter_messages(event.chat_id, limit=n + 1):
            msgs.append(msg.id)
        if msgs:
            await event.client.delete_messages(event.chat_id, msgs)
            count = len(msgs)
    else:
        return await edit_delete(event, "- رد على رسالة أو ضع عدداً", 8)
    m = await event.client.send_message(event.chat_id, f"تم حذف {count} رسالة ✓")
    await asyncio.sleep(4)
    await m.delete()


@cmd(r"تحذير(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص لتحذيره", 8)
    key = f"{event.chat_id}"
    warns = db_read("warns")
    chat = warns.get(key, {})
    chat[str(uid)] = chat.get(str(uid), 0) + 1
    warns[key] = chat
    db_write("warns", warns)
    n = chat[str(uid)]
    text = f"تم تحذير {mention(user)}\nعدد التحذيرات: {n}/3"
    if n >= 3:
        try:
            await event.client(EditBannedRequest(event.chat_id, uid, MUTE_RIGHTS))
            text += "\nتم كتمه لتجاوزه الحد ✓"
        except Exception:
            pass
        chat[str(uid)] = 0
        warns[key] = chat
        db_write("warns", warns)
    await edit_or_reply(event, text)


@cmd(r"التحذيرات(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص", 8)
    n = db_read("warns").get(f"{event.chat_id}", {}).get(str(uid), 0)
    await edit_or_reply(event, f"تحذيرات {mention(user)}: {n}/3")


@cmd(r"حذف التحذيرات(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    user, uid = await get_target_user(event)
    if not uid:
        return await edit_delete(event, "- رد على شخص", 8)
    warns = db_read("warns")
    key = f"{event.chat_id}"
    if key in warns and str(uid) in warns[key]:
        warns[key][str(uid)] = 0
        db_write("warns", warns)
    await edit_or_reply(event, f"تم حذف تحذيرات {mention(user)} ✓")




@cmd(r"الايدي(?:\s|$)([\s\S]*)")
async def _(event):
    args = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if args and args.strip():
        try:
            p = await event.client.get_entity(args.strip())
        except Exception as e:
            return await edit_delete(event, f"`{e}`", 6)
        name = getattr(p, "title", None) or get_display_name(p)
        return await edit_or_reply(event, f"ايدي `{name}` هو `{p.id}`")
    if reply:
        txt = f"**ايدي الدردشة:** `{event.chat_id}`\n**ايدي المرسل:** `{reply.sender_id}`"
        if reply.media:
            txt += "\n**نوع:** ميديا"
        return await edit_or_reply(event, txt)
    await edit_or_reply(event, f"**ايدي الدردشة:** `{event.chat_id}`")


@cmd(r"كشف(?:\s|$)([\s\S]*)")
async def _(event):
    user, uid = await get_target_user(event)
    if not user:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    txt = f"""**| كشف المستخدم :**
**الاسم:** {get_display_name(user)}
**الايدي:** `{user.id}`
**المعرف:** @{user.username if user.username else 'لا يوجد'}
**بوت:** {'نعم' if user.bot else 'لا'}
**مقيد:** {'نعم' if getattr(user, 'restricted', False) else 'لا'}
**الرابط:** [هنا](tg://user?id={user.id})"""
    await edit_or_reply(event, txt)


_ID_DATES = [
    (1, 1376448000), (1000000, 1383264000), (5000000, 1384905600),
    (10000000, 1389744000), (50000000, 1404950400), (100000000, 1425513600),
    (200000000, 1462060800), (500000000, 1515542400), (1000000000, 1573776000),
    (1500000000, 1604188800), (2000000000, 1634256000), (2500000000, 1648771200),
    (3000000000, 1663200000), (3500000000, 1675209600), (4000000000, 1688169600),
    (4500000000, 1701388800), (5000000000, 1714521600), (5500000000, 1727740800),
    (6000000000, 1740787200), (8956099155, 1750958248),
]


def _now_date():
    return datetime.now().strftime("%Y-%m-%d")


def _estimate_id_date(uid):
    pts = sorted(_ID_DATES, key=lambda x: x[0])
    for pid, ptime in pts:
        if uid == pid:
            dt = datetime.fromtimestamp(ptime)
            return (dt.strftime("%Y-%m-%d"), "ضبط") if dt <= datetime.now() else (_now_date(), "جديد")
    if uid < pts[0][0]:
        return datetime.fromtimestamp(pts[0][1]).strftime("%Y-%m-%d"), "قديم"
    if uid > pts[-1][0]:
        return _now_date(), "جديد"
    for i in range(len(pts) - 1):
        if pts[i][0] < uid < pts[i + 1][0]:
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            frac = (uid - x0) / (x1 - x0) if x1 != x0 else 0
            ts = y0 + (y1 - y0) * frac
            dt = datetime.fromtimestamp(ts)
            if dt > datetime.now():
                return _now_date(), "جديد"
            return dt.strftime("%Y-%m-%d"), "aprox"
    return _now_date(), "جديد"


def _flag_from_country(code):
    if not code or len(code) != 2:
        return ""
    return chr(0x1F1E6 + ord(code[0]) - 65) + chr(0x1F1E6 + ord(code[1]) - 65)


@cmd(r"انشاء(?:\s|$)([\s\S]*)")
async def _(event):
    user, uid = await get_target_user(event)
    if not user:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    m = await event.edit("- جاري جلب المعلومات...")
    try:
        result = await client(functions.users.GetFullUserRequest(user))
        settings = result.settings
    except Exception:
        settings = None
    reg = getattr(settings, "registration_month", None) if settings else None
    country_code = getattr(settings, "phone_country", None) if settings else None
    flag = _flag_from_country(country_code) if country_code else ""
    est_date, est_status = _estimate_id_date(user.id)
    lines = [f"• تاريخ الانشاء هو"]
    lines.append(f"• {est_date} ({est_status})")
    if country_code:
        lines.append(f"• دولة: {flag} {country_code}")
    await edit_or_reply(m, "\n".join(lines))


@cmd(r"صورة(?:\s|$)([\s\S]*)")
async def _(event):
    user, uid = await get_target_user(event)
    if not user:
        return await edit_delete(event, "- رد على شخص أو ضع معرفه", 8)
    m = await event.edit("- جاري الجلب...")
    try:
        photo = await event.client.download_profile_photo(user.id)
        if not photo:
            return await edit_delete(event, "- لا يوجد صورة", 6)
        await event.client.send_file(
            event.chat_id, photo, caption=f"صورة {mention(user)}"
        )
        os.remove(photo)
        await m.delete()
    except Exception as e:
        await edit_delete(event, f"`{e}`", 6)


@cmd(r"المشرفين$", groups_only=True)
async def _(event):
    admins = []
    async for u in event.client.iter_participants(
        event.chat_id, filter=types.ChannelParticipantsAdmins
    ):
        admins.append(f"• {mention(u)} — `{u.id}`")
    txt = "**| مشرفو المجموعة :**\n\n" + "\n".join(admins)
    await edit_or_reply(event, txt)


@cmd(r"الاعضاء$", groups_only=True)
async def _(event):
    chat = await event.get_chat()
    full = await event.client.get_participants(event.chat_id, limit=0)
    await edit_or_reply(
        event, f"**عدد أعضاء** {chat.title}: `{full.total}`"
    )


@cmd(r"البوتات$", groups_only=True)
async def _(event):
    bots = []
    async for u in event.client.iter_participants(event.chat_id):
        if u.bot:
            bots.append(f"• {mention(u)} — `{u.id}`")
    if not bots:
        return await edit_or_reply(event, "- لا يوجد بوتات في هذه المجموعة")
    await edit_or_reply(event, "**| البوتات :**\n\n" + "\n".join(bots))


@cmd(r"معلومات$", groups_only=True)
async def _(event):
    chat = await event.get_chat()
    full = await event.client.get_participants(event.chat_id, limit=0)
    txt = f"""**| معلومات المجموعة :**
**الاسم:** {chat.title}
**الايدي:** `{event.chat_id}`
**عدد الأعضاء:** `{full.total}`
**المعرف:** @{chat.username if getattr(chat, 'username', None) else 'خاصة'}"""
    await edit_or_reply(event, txt)




@cmd(r"اضف رد(?:\s|$)([\s\S]*)")
async def _(event):
    reply = await event.get_reply_message()
    word = event.pattern_match.group(1)
    if not reply or not word or not word.strip():
        return await edit_delete(event, "- رد على النص واكتب: اضف رد <الكلمة>", 8)
    if not reply.text:
        return await edit_delete(event, "- الرد يجب أن يكون نصاً", 8)
    db_set("replies", word.strip(), reply.text)
    await edit_or_reply(event, f"تم إضافة رد على: `{word.strip()}` ✓")


@cmd(r"حذف رد(?:\s|$)([\s\S]*)")
async def _(event):
    word = event.pattern_match.group(1)
    if not word or not word.strip():
        return await edit_delete(event, "- اكتب: حذف رد <الكلمة>", 8)
    if db_del("replies", word.strip()):
        await edit_or_reply(event, f"تم حذف الرد: `{word.strip()}` ✓")
    else:
        await edit_delete(event, "- لا يوجد رد بهذا الاسم", 8)


@cmd(r"الردود$")
async def _(event):
    data = db_read("replies")
    if not data:
        return await edit_or_reply(event, "- لا يوجد ردود مضافة")
    txt = "**| الردود المضافة :**\n\n" + "\n".join(f"• `{k}`" for k in data)
    await edit_or_reply(event, txt)


@cmd(r"مسح الردود$")
async def _(event):
    db_write("replies", {})
    await edit_or_reply(event, "تم حذف جميع الردود ✓")


@client.on(events.NewMessage(incoming=True))
async def _replies_watcher(event):
    if not event.text:
        return
    data = db_read("replies")
    if not data:
        return
    reply = data.get(event.raw_text.strip())
    if reply:
        try:
            await event.reply(reply)
        except Exception:
            pass




@cmd(r"ضبط ترحيب(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    text = event.pattern_match.group(1)
    if not text or not text.strip():
        return await edit_delete(event, "- اكتب نص الترحيب بعد الأمر", 8)
    db_set("welcome", event.chat_id, text.strip())
    await edit_or_reply(event, "تم ضبط رسالة الترحيب ✓")


@cmd(r"الترحيب$", groups_only=True)
async def _(event):
    w = db_get("welcome", event.chat_id)
    if not w:
        return await edit_or_reply(event, "- لا يوجد ترحيب مضبوط")
    await edit_or_reply(event, f"**الترحيب الحالي:**\n\n{w}")


@cmd(r"حذف الترحيب$", groups_only=True)
async def _(event):
    if db_del("welcome", event.chat_id):
        await edit_or_reply(event, "تم حذف الترحيب ✓")
    else:
        await edit_or_reply(event, "- لا يوجد ترحيب أصلاً")


@client.on(events.ChatAction)
async def _welcome_watcher(event):
    if not (event.user_joined or event.user_added):
        return
    w = db_get("welcome", event.chat_id)
    if not w:
        return
    try:
        user = await event.get_user()
        chat = await event.get_chat()
        count = (await event.client.get_participants(event.chat_id, limit=0)).total
        msg = w.replace("{name}", get_display_name(user))
        msg = msg.replace("{title}", chat.title)
        msg = msg.replace("{count}", str(count))
        await event.client.send_message(event.chat_id, msg)
    except Exception:
        pass




@cmd(r"منع(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    word = event.pattern_match.group(1)
    if not word or not word.strip():
        return await edit_delete(event, "- اكتب: منع <الكلمة>", 8)
    data = db_read("locked")
    key = f"{event.chat_id}"
    words = data.get(key, [])
    if word.strip() not in words:
        words.append(word.strip())
    data[key] = words
    db_write("locked", data)
    await edit_or_reply(event, f"تم منع الكلمة: `{word.strip()}` ✓")


@cmd(r"الغاء منع(?:\s|$)([\s\S]*)", groups_only=True)
async def _(event):
    word = event.pattern_match.group(1)
    if not word or not word.strip():
        return await edit_delete(event, "- اكتب: الغاء منع <الكلمة>", 8)
    data = db_read("locked")
    key = f"{event.chat_id}"
    words = data.get(key, [])
    if word.strip() in words:
        words.remove(word.strip())
        data[key] = words
        db_write("locked", data)
        await edit_or_reply(event, f"تم إلغاء منع: `{word.strip()}` ✓")
    else:
        await edit_delete(event, "- الكلمة غير ممنوعة", 8)


@cmd(r"قائمة المنع$", groups_only=True)
async def _(event):
    words = db_read("locked").get(f"{event.chat_id}", [])
    if not words:
        return await edit_or_reply(event, "- لا يوجد كلمات ممنوعة")
    txt = "**| الكلمات الممنوعة :**\n\n" + "\n".join(f"• `{w}`" for w in words)
    await edit_or_reply(event, txt)


@client.on(events.NewMessage(incoming=True))
async def _locked_watcher(event):
    if not event.text or not event.is_group:
        return
    words = db_read("locked").get(f"{event.chat_id}", [])
    if not words:
        return
    low = event.raw_text.lower()
    if any(w.lower() in low for w in words):
        try:
            await event.delete()
        except Exception:
            pass



PM_WARN_TEXT = (
    f"**| حماية الخاص — سورس حمزة**\n\n"
    "هذا حساب محمي، انتظر موافقة صاحب الحساب.\n"
    "تكرار الرسائل سيؤدي لحظرك."
)
PM_LIMIT = 5


@cmd(r"الحماية تشغيل$")
async def _(event):
    db_set("settings", "pmpermit", True)
    await edit_or_reply(event, "تم تشغيل حماية الخاص ✓")


@cmd(r"الحماية تعطيل$")
async def _(event):
    db_set("settings", "pmpermit", False)
    await edit_or_reply(event, "تم تعطيل حماية الخاص ✓")


@cmd(r"سماح(?:\s|$)([\s\S]*)", private_only=True)
async def _(event):
    uid = event.chat_id
    allowed = db_read("pm_allowed")
    allowed[str(uid)] = True
    db_write("pm_allowed", allowed)
    counts = db_read("pm_counts")
    counts.pop(str(uid), None)
    db_write("pm_counts", counts)
    await edit_or_reply(event, "تم السماح لهذا الشخص بالخاص ✓")


@cmd(r"رفض(?:\s|$)([\s\S]*)", private_only=True)
async def _(event):
    uid = event.chat_id
    allowed = db_read("pm_allowed")
    allowed.pop(str(uid), None)
    db_write("pm_allowed", allowed)
    await edit_or_reply(event, "تم رفض هذا الشخص من الخاص ✓")


@cmd(r"المسموحين$")
async def _(event):
    allowed = db_read("pm_allowed")
    if not allowed:
        return await edit_or_reply(event, "- لا يوجد مسموح لهم")
    txt = "**| المسموح لهم بالخاص :**\n\n" + "\n".join(
        f"• `{k}`" for k in allowed
    )
    await edit_or_reply(event, txt)


@client.on(events.NewMessage(incoming=True))
async def _pmpermit_watcher(event):
    if not event.is_private:
        return
    if not db_get("settings", "pmpermit", False):
        return
    sender = await event.get_sender()
    if sender is None or sender.bot or getattr(sender, "verified", False):
        return
    if event.chat_id == (await event.client.get_me()).id:
        return
    uid = str(event.chat_id)
    if db_read("pm_allowed").get(uid):
        return
    if getattr(sender, "is_self", False):
        return
    contact = getattr(sender, "contact", False)
    if contact:
        return
    counts = db_read("pm_counts")
    n = counts.get(uid, 0) + 1
    counts[uid] = n
    db_write("pm_counts", counts)
    if n >= PM_LIMIT:
        try:
            await event.client(BlockRequest(event.chat_id))
            await event.respond("تم حظرك لتكرار الرسائل.")
        except Exception:
            pass
        counts.pop(uid, None)
        db_write("pm_counts", counts)
        return
    try:
        await event.respond(f"{PM_WARN_TEXT}\n\nتحذير {n}/{PM_LIMIT}")
    except Exception:
        pass




@cmd(r"للكروبات(?:\s|$)([\s\S]*)")
async def _(event):
    reply = await event.get_reply_message()
    text = event.pattern_match.group(1)
    if not reply and not (text and text.strip()):
        return await edit_delete(event, "- اكتب نصاً أو رد على رسالة", 8)
    m = await event.edit("- جاري النشر بالمجموعات...")
    done, failed = 0, 0
    async for dialog in event.client.iter_dialogs():
        if dialog.is_group:
            try:
                if reply:
                    await event.client.send_message(dialog.id, reply)
                else:
                    await event.client.send_message(dialog.id, text.strip())
                done += 1
                await asyncio.sleep(0.5)
            except Exception:
                failed += 1
    await m.edit(f"تم النشر ✓\nنجح: {done} | فشل: {failed}")


@cmd(r"للخاص(?:\s|$)([\s\S]*)")
async def _(event):
    reply = await event.get_reply_message()
    text = event.pattern_match.group(1)
    if not reply and not (text and text.strip()):
        return await edit_delete(event, "- اكتب نصاً أو رد على رسالة", 8)
    m = await event.edit("- جاري النشر بالخاص...")
    done, failed = 0, 0
    async for dialog in event.client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot:
            try:
                if reply:
                    await event.client.send_message(dialog.id, reply)
                else:
                    await event.client.send_message(dialog.id, text.strip())
                done += 1
                await asyncio.sleep(0.5)
            except Exception:
                failed += 1
    await m.edit(f"تم النشر ✓\nنجح: {done} | فشل: {failed}")




@cmd(r"بنك$")
async def _(event):
    start = time.time()
    m = await event.edit("...")
    ms = (time.time() - start) * 1000
    await m.edit(f"**السرعة:** `{ms:.2f}` ms")


@cmd(r"الوقت$")
async def _(event):
    up = readable_time(time.time() - START_TIME)
    await edit_or_reply(event, f"**مدة التشغيل:** {up}")


@cmd(r"اعادة تشغيل$")
async def _(event):
    await event.edit("- جاري إعادة التشغيل...")
    db_set("settings", "restart_chat", event.chat_id)
    db_set("settings", "restart_msg", event.id)
    await event.client.disconnect()
    os.execl(sys.executable, sys.executable, os.path.abspath(__file__))




@cmd(r"تغيير اسم(?:\s|$)([\s\S]*)")
async def _(event):
    name = event.pattern_match.group(1)
    if not name or not name.strip():
        return await edit_delete(event, "- اكتب الاسم بعد الأمر", 8)
    parts = name.strip().split(maxsplit=1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    try:
        await event.client(
            functions.account.UpdateProfileRequest(
                first_name=first, last_name=last
            )
        )
    except Exception as e:
        return await edit_delete(event, f"`{e}`", 8)
    await edit_or_reply(event, "تم تغيير الاسم ✓")


@cmd(r"تغيير بايو(?:\s|$)([\s\S]*)")
async def _(event):
    bio = event.pattern_match.group(1)
    if not bio or not bio.strip():
        return await edit_delete(event, "- اكتب البايو بعد الأمر", 8)
    try:
        await event.client(
            functions.account.UpdateProfileRequest(about=bio.strip())
        )
    except Exception as e:
        return await edit_delete(event, f"`{e}`", 8)
    await edit_or_reply(event, "تم تغيير البايو ✓")


@cmd(r"تغيير صورة$")
async def _(event):
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        return await edit_delete(event, "- رد على صورة", 8)
    m = await event.edit("- جاري التغيير...")
    try:
        photo = await event.client.download_media(reply.media)
        up = await event.client.upload_file(photo)
        await event.client(functions.photos.UploadProfilePhotoRequest(file=up))
        os.remove(photo)
        await m.edit("تم تغيير الصورة ✓")
    except Exception as e:
        await m.edit(f"`{e}`")


@cmd(r"حسابي$")
async def _(event):
    me = await event.client.get_me()
    txt = f"""**| معلومات حسابك :**
**الاسم:** {get_display_name(me)}
**الايدي:** `{me.id}`
**المعرف:** @{me.username if me.username else 'لا يوجد'}
**الرقم:** `+{me.phone if me.phone else 'مخفي'}`
**بريميوم:** {'نعم' if getattr(me, 'premium', False) else 'لا'}"""
    await edit_or_reply(event, txt)




@cmd(r"ترجمة(?:\s|$)([\s\S]*)")
async def _(event):
    reply = await event.get_reply_message()
    arg = event.pattern_match.group(1)
    lang = (arg.strip() or "ar") if arg else "ar"
    if reply and reply.text:
        text = reply.text
    elif arg and len(arg.strip().split(maxsplit=1)) > 1:
        lang, text = arg.strip().split(maxsplit=1)
    else:
        return await edit_delete(event, "- رد على نص | مثال: ترجمة en", 8)
    try:
        from googletrans import Translator
        tr = Translator()
        res = tr.translate(text, dest=lang)
        await edit_or_reply(
            event, f"**الترجمة ({res.src} | {lang}):**\n\n{res.text}"
        )
    except Exception as e:
        await edit_delete(event, f"- تعذر الترجمة (ثبّت googletrans): `{e}`", 10)



spam_targets = {}
spam_delay_min = 3.0
spam_delay_max = 5.0
spam_batch_min = 1
spam_batch_max = 1
spam_ai_enabled = False
spam_ai_target = ""
follow_running = False
forward_running = False
forward_task = None
forward_delay_min = 0.5
forward_delay_max = 0.5
selected_saved_msgs = []
flood_guard_enabled = False
flood_guard = None


_DEFAULT_INSULTS = {
    "qrayb": [
        "امك", "ابوك", "اختك", "اخوك", "خالتك", "عمتك", "جدتك", "مرتك",
        "خواتك", "اهلك", "عيلتك", "بنت امك", "ولد عمك", "عمك", "خالك",
    ],
    "feal": [
        "تتناك", "تتوسك", "ترضع الزباب", "تفتح رجليها", "تبيع نفسها",
        "تشتغل قحبه", "تلحق الرجال", "تتمرمغ", "تركع للكل", "تشحت نيك",
    ],
    "jomla": [
        "بالشارع", "بكل رخص", "قدام الكل", "بالمجان", "من غير ما تستحي",
        "بطابور طويل", "بكل الكروبات", "وانت تتفرج", "بارخص سعر",
        "لكل من هب ودب",
    ],
    "sifat": [
        "كسش جعلني فداه", "توكسك", "منيوك", "خرا عليك", "يا معفن",
        "يا وسخ", "قحبه", "ديوث", "معرص", "يا حقير", "يا زفت", "يا قليل الاصل",
    ],
    "laheq": [
        "وش فيه", "جان شنو", "شكو", "ليش هيك", "عاد", "بعد", "ولك",
        "يا كلب", "يا خنزير", "ولا شلون", "", "", "",
    ],
    "sakhira": [
        "انت ماشي على موال الي يرفع لك سيقان اختك تقعد تمجد له ولا شلون",
        "من كثر ما انت ذليل صرت تعتبر رفع سيقان محارمك انجاز تفتخر فيه",
        "كل ما ضاقت عليك الدنيا تروح تنيك اهلك وترجع مبسوط",
        "لو الذل شخص جان انت ابوه يا ابن الشرموطه الغبيه",
    ],
    "templates": [
        "{qrayb} {feal} {jomla} {sifat}",
        "{qrayb} {feal} {jomla} {laheq}",
        "{qrayb} {feal} {jomla}",
        "{qrayb} {sifat} {laheq}",
        "{qrayb} {feal} {jomla}، {sifat} {laheq}",
        "والله {qrayb} {feal} {jomla} {sifat}",
        "{sifat} {laheq}، {qrayb} {feal} {jomla}",
        "{qrayb} {feal} {jomla} وانت ساكت يا {sifat}",
        "{sakhira}",
        "{sakhira} {sifat}",
        "على فكرة؟ {sakhira} {laheq}",
        "{sifat}، {sakhira}",
        "تعرف انت ايش؟ {sakhira}",
    ],
    "حشوات": [
        "منفوخ", "ممزق", "متسع", "ضيق", "أسود", "متورم", "منكمش", "مبلل",
        "مقرف", "منتن", "لزج", "ساخن", "ملتهب", "محروق", "منهار",
    ],
    "قوالب_فتحات": [
        "تعرف امك كانت فتحتها كذا ( )، بعد ما شافت زبي صار كذا ( )",
        "امك يوم شافت زبي قالت ( )، اختك قالت ( )، انا قلت ( )",
        "كس امك قبل كان ( )، بعد ما سويته صار ( )",
        "اختك تقول فتحتها ( )، وانا اقولها لا ( )",
    ],
}

INSULTS = {}


def _load_insults():
    """يحمّل مكتبة السب من data/insults.json، وينشئها افتراضياً إن لم توجد"""
    global INSULTS
    if not os.path.exists(_path("insults")):
        db_write("insults", _DEFAULT_INSULTS)
    data = db_read("insults", _DEFAULT_INSULTS)
    for k, v in _DEFAULT_INSULTS.items():
        data.setdefault(k, v)
    INSULTS = data


def insult_combos():
    """يحسب عدد التركيبات الممكنة"""
    n = len(INSULTS.get("templates", [1]))
    for k in ("qrayb", "feal", "jomla", "sifat", "laheq", "sakhira"):
        n *= max(len(INSULTS.get(k, [""])), 1)
    fillers = len(INSULTS.get("حشوات") or [1])
    for ftpl in INSULTS.get("قوالب_فتحات") or []:
        slots = ftpl.count("(")
        n += fillers ** max(slots, 1)
    return n


def _fill_blanks(text):
    """يملأ كل (     ) في النص بعنصر عشوائي من حشوات ويزيل المسافات داخلها"""
    fillers = INSULTS.get("حشوات") or [""]
    while "(" in text and ")" in text:
        text = re.sub(r"\(\s*\)", random.choice(fillers), text, count=1)
    return text


def generate_insult():
    """يولّد جملة سب عشوائية من القوالب والمكوّنات (من JSON)"""
    if not INSULTS:
        _load_insults()
    ftpl = INSULTS.get("قوالب_فتحات") or []
    use_fillable = ftpl and random.random() < 0.4
    if use_fillable:
        text = random.choice(ftpl)
        text = _fill_blanks(text)
    else:
        tpl = random.choice(INSULTS["templates"])
        text = tpl.format(
            qrayb=random.choice(INSULTS.get("qrayb") or [""]),