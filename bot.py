import os
import sqlite3
import logging
import asyncio
import json
import re
import time
import requests
import random
import uuid
import shutil
import zipfile
import aiohttp
import threading
from datetime import datetime, timedelta
from urllib.parse import quote
import pytz
import jdatetime
from flask import Flask, request, jsonify
from hijridate import Gregorian
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler
from telegram.request import HTTPXRequest
from telethon import TelegramClient, events, types
from telethon.tl.types import PeerUser, PeerChannel, PeerChat, MessageMediaPhoto, MessageMediaDocument, ReactionEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityStrike, MessageEntityBlockquote, MessageEntitySpoiler, MessageEntityItalic, MessageEntityCode, MessageEntityPre
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest, SetTypingRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest, GetUserPhotosRequest
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import MessageDeleteForbiddenError, FloodWaitError, SessionPasswordNeededError, FloodWaitError as TelethonFloodWaitError

# ========== تنظیمات گوگل سرچ ==========
GOOGLE_SEARCH_API_KEY = "AIzaSyCMYOU0NpU5xfu7GrffyywVUugd1yD2uDU"
GOOGLE_CSE_ID = "3185e48756dfd482f"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# ========== تنظیمات لاگ ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== تنظیمات وب سرور ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": "Telegram SelfBot",
        "version": "4.5.0"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run_web_server():
    """اجرای سرور وب برای Render"""
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 وب سرور روی پورت {port} در حال اجراست")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== لیست API های ثابت ==========
API_CONFIGS = [
    {"api_id": 22409632, "api_hash": "b74c1ee200ad9ced6315859e9bd4125a"},
    {"api_id": 28297221, "api_hash": "8d682eb5c41a9762ef73f9ebe06c4eff"},
    {"api_id": 28039994, "api_hash": "00877cdcd706564a4de6abf7f7d64349"},
    {"api_id": 29031463, "api_hash": "64f122a7094dbab7e32b911eae6589e9"},
    {"api_id": 12832882, "api_hash": "1953c708cb3c47ecba74dc618b209e22"},
    {"api_id": 26645489, "api_hash": "6a212d0a400c97264600b3f932de5c2f"},
]

def get_user_api(user_id):
    """دریافت یا اختصاص API به کاربر - هر کاربر یک API ثابت"""
    conn = sqlite3.connect('main_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT api_id, api_hash FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row and row[0] is not None and row[1] is not None:
        conn.close()
        return {"api_id": row[0], "api_hash": row[1]}
    
    api_count = {}
    for api in API_CONFIGS:
        cursor.execute('SELECT COUNT(*) FROM users WHERE api_id = ?', (api["api_id"],))
        api_count[api["api_id"]] = cursor.fetchone()[0]
    
    best_api = min(API_CONFIGS, key=lambda x: api_count.get(x["api_id"], 0))
    
    cursor.execute('UPDATE users SET api_id = ?, api_hash = ? WHERE user_id = ?', 
                   (best_api["api_id"], best_api["api_hash"], user_id))
    conn.commit()
    conn.close()
    
    logger.info(f"API اختصاص یافته به کاربر {user_id}: {best_api['api_id']}")
    return best_api

BOT_TOKEN = "8304449635:AAGJCoQihoxvS-Wh-sPMa69PQV6ygAssFFc"
ADMIN_ID = 6443963679
BOT_USERNAME = "Gap_5_bot"

# ========== پوشه سشن‌ها ==========
SESSIONS_FOLDER = 'user_sessions'
BACKUP_FOLDER = 'session_backups'
if not os.path.exists(SESSIONS_FOLDER):
    os.makedirs(SESSIONS_FOLDER)
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)

# ========== تنظیمات سلف‌بات ==========
GROUP_ID = -1002817019483

# ========== تنظیمات ۳ هوش مصنوعی ==========
FREE_AI_URL = "https://hoshi-app.ir/api/chat-gpt.php?text="
PAXSENIX_API_KEY = "sk-paxsenix-Xo_BAFNGgWVZ_ymWd02Rk1JHbyoDSEzfPhiolJ3F12cY6XZG"
PAXSENIX_API_URL = "https://api.paxsenix.org/v1/chat/completions"
DEEPSEEK_FREE_URL = "https://deepseek.api-sina-free.workers.dev/?text="

# ========== فایل‌های تنظیمات ==========
MEDIA_FOLDER = 'media_storage'
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

REPORT_CONFIG_FILE = "report_config.json"
REPORT_MEDIA_FOLDER = 'reported_media'
if not os.path.exists(REPORT_MEDIA_FOLDER):
    os.makedirs(REPORT_MEDIA_FOLDER)

# ========== لیست ایموجی‌های مجاز ==========
ALLOWED_EMOJIS = [
    "🤯", "🐳", "😍", "💩", "👏", "🍌", "🤓", "😢", "🙉", "🤩",
    "🤝", "👀", "🌚", "🗿", "🤡", "😐", "👨‍💻", "😭", "🙈", "❤",
    "🙏", "😴", "💋", "🥰", "🤪", "✍️", "🥱", "👻", "🤣", "🌭",
    "😨", "🍓", "🔥", "🖕", "🤗", "🤔", "🤬", "😁", "🎄", "🫡",
    "⚡", "🥴", "😈", "🏆", "😇", "🎃", "☃️", "🤮", "👍", "👎",
    "😱", "😖", "🕊", "💯", "💔", "🤨", "❤️‍🔥", "💘", "😘", "💊",
    "🆒", "🤷‍♂", "🤷‍♀", "🎅"
]

# ========== لیست فونت‌های کلاسیک ==========
classic_fonts = [
    "⊘𝟷ϩӠ4ƼϬ7𝟾९",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    "⓿①❷③❹⑤❻⑦❽⑨",
    "₀₁₂₃₄₅₆₇₈₉",
    "⁰¹²³⁴⁵⁶⁷⁸⁹",
    "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    "₀¹²³⁴⁵⁶₇₈₉",
    "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "０１２３４５６７８９",
    "₀₁₂₃₄₅₆₇₈₉",
    "⁰¹²³⁴⁵⁶⁷⁸⁹",
    "0123456789",
    "⓪①②③④⑤⑥⑦⑧⑨",
    "⓿❶❷❸❹❺❻❼❽❾",
    "🄀🄁🄂🄃🄄🄅🄆🄇🄈🄉",
    "🄞🄟🄠🄡🄢🄣🄤🄥🄦🄧🄨",
    "０１２３４５６７８９",
    "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    "𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫",
    "０１２３４５６７８۹",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', ':': ':'},
    {'0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗', ':': ':'},
    {'0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿', ':': ':'},
    {'0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨', ':': ':'},
    {'0': '🄋', '1': '➊', '2': '➋', '3': '➌', '4': '➍', '5': '➎', '6': '➏', '7': '➐', '8': '➑', '9': '➒', ':': ':'},
    {'0': '⓿', '1': '❶', '2': '❷', '3': '❸', '4': '❹', '5': '❺', '6': '❻', '7': '❼', '8': '❽', '9': '❾', ':': ':'},
    {'0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜', '5': '𝟝', '6': '𝟞', '7': '𝟟', '8': '𝟠', '9': '𝟡', ':': ':'},
    {'0': '⒒', '1': '⑴', '2': '⑵', '3': '⑶', '4': '⑷', '5': '⑸', '6': '⑹', '7': '⑺', '8': '⑻', '9': '⑼', ':': ':'},
    {'0': '０', '1': '１', '2': '２', '3': '３', '4': '４', '5': '５', '6': '６', '7': '７', '8': '８', '9': '９', ':': '：'},
    {'0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵', ':': ':'},
    {'0': '〇', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九', ':': ':'}
]

# ========== لیست پرچم‌ها ==========
flags = [
    "🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇼", "🇦🇼", "🇦🇹", "🇦🇿", "🇧🇸", "🇧🇭",
    "🇧🇩", "🇧🇧", "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇴", "🇧🇦", "🇧🇼",
    "🇧🇷", "🇮🇴", "🇻🇬", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦",
    "🇨🇻", "🇰🇾", "🇨🇫", "🇹🇩", "🇨🇱", "🇨🇴", "🇰🇲", "🇨🇬", "🇨🇩", "🇨🇽",
    "🇨🇨", "🇨🇴", "🇰🇲", "🇨🇬", "🇨🇩", "🇨🇰", "🇨🇰", "🕋"
]

# ========== لیست پیام‌های اسپم ==========
SPAM_MESSAGES = [
    "مادربزرگت کسده، کسشو تو قبرم اجاره داده",
    "پدربزرگت کونی، هنوزم تو گور کونشو به شیاطین می‌سپره",
    "کس ننت چنان بازه، کل شهر توش چادر زدن",
    "بابات کسکش، تو خیابون کونشو به موتورسوارا نشون می‌ده",
    "خواهرت فاحشه، تو کلوپ شبانه کسشو به حراج گذاشته",
    "برادرت کیرکش، تو کوچه کونشو به گربه‌ها می‌ده",
    "بچه‌هات جنده‌ان، تو پارک کسشونو به نیمکت‌ها می‌مالن",
    "عمه‌ت کس‌کش، کسشو تو حموم عمومی به همه نشون می‌ده",
    "خاله‌ت کونی، کیر هر غریبه‌ای رو تو کوچه می‌گیره",
    "جدت کسده، تو گور هم کسشو به فرشته‌ها اجاره می‌ده",
    "یا الله کیرم به قلب مادرت",
    "مادرتو میدم سگ بگاد",
    "با کیرم ناموستو پاره میکنم",
    "کیرمو حلقه میکنم دور گردن مادرت",
    "کسخارتو بتن ریزی کردم",
    "ننتو تو پورن هاب دیدم",
    "کیر و خایه هام به کل اجدادت",
    "فیلم ننت فروشی",
    "کسننت پدرتم",
    "میرم تو کسمادرت با بیل پارش میکنم",
    "کیر به ناموس گشادت",
    "خسته نشدی ننتو گاییدم؟",
    "کیرم شلاقی به ناموس جندت",
    "با ناموست تریسام زدم",
    "برج خلیفه تو مادرت",
    "دو پایی میرم تو کسمادرت",
    "داگی استایل ننتو گاییدم",
    "هندل زدم به کون مادرت گاییدمش",
    "یگام دو گام ننتو میگام",
    "کیرمو نکن تو کسمادرت",
    "کیر و خایم به توان دو تو کسمادرت",
    "قمه تو کسمادرت",
    "نود ننتو دارم مادرکسده",
    "با کله میرم تو کسمادرت",
    "دستام تو کسمادرت",
    "کیرم به استخون های ننت",
    "مادرتو حراج زدم مادرجنده",
    "بریم برای راند بعد با ننت",
    "کیرم به رحم نجس ننت",
    "کیرم به چش و چال ننت",
    "کیروم به فرق سر ناموست",
    "مادرجنده کیری ناموس",
    "با کون ننت ناگت درست کردم",
    "خایه هام به کسمادرت",
    "برج میلاد تو کسمادرت",
    "یخچال تو کسمادرت",
    "کیرم به پوزه مادرت",
    "مادرتو زدم به سیخ",
    "کسمادرت","کیر شتر تو ناموست","نودا ننت فروشی","خایه با پرزش تو ننت","چشای ننت تو کون خارت بره","ننتو ریدم","لال شو مادرجنده اوبنه ای","اوب از کون ننت میباره","ماهی تو کسمادرت","کیر هرچی خره تو کسمادرت","کیر رونالدو به کس خار و مادرت","مادرت زیر کیرم شهید شد","اسپنک زدم به کون مادر جندت","کیرم یهویی به مردع و زندت","کیر به فیس ننت","برو مادرجنده بی غیرت","استخون های مرده هات تو کسمادرت","اسپرمم تو نوامیست","مادرتو با پوزیشن های مختلف گاییدم","میز و صندلی تو کسمادرت","کیر به ناموس دلقکت","دمپایی تو کون ننت","دماغ پینوکیو رو گذاشتم جلو کص مادرت و بهش گفتم که بگه مادرت جنده نیست تا با دراز شدن دماغش کص مادرت پاره بشه","مادر فلش شده جوری با کیر میزنم ب فرق سر ننت ک حافظش بپره","كيرم شيك تو كس ننت","مادرتو کردم تو بشکه نفت از بالا کوه قل دادم پایین","با کیرم مادرتو هیپنوتیزم کردم","ناموستو تو کوچه موقع عید دیدنی دیدم رفتم خونه به یادش جق زدم","با خیسی عرق کون مادرت جقیدم","با سرعت نور تو فضا حرکت میکنم تا پیر نشم و بزارم آبجی کوچیکت بزرگ بشه تا وقتی بزرگ شد باهاش سکس کنم","مادرتو پودر میکنم ازش سنگ توالت میسازم هر روز صبح رو مادرت میرینم","مادرتو مجبور میکنم خودکشی کوانتومی کنه تا در بی نهایت جهان موازی یتیم بشی","دیدی چه لگدی به مادرت زدم ؟","فرشی که مادرت روش کونشو گذاشته بو کردم","مادرتو جوری گاییدم که همسایه ها فکر کردن اسب ترکمن اومده خونتون"
]

# ========== تنظیمات پیش‌فرض قفل رسانه ==========
DEFAULT_LOCK_SETTINGS = {
    'link': False,
    'photo': False,
    'video': False,
    'sticker': False,
    'gif': False,
    'emoji': False,
    'emoji_premium': False
}

# ========== اطلاعات بات ==========
BOT_VERSION = "4.5.0"
BOT_CREATOR = "Self-Bot AI Assistant"

# ========== لیست‌های انیمیشن ==========
HEARTS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤍"]
MOONS = ["🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]

# ========== متغیرهای گزارش‌گیری ==========
media_cache = {}
message_cache = {}
user_inline_messages = {}

# ========== لیست اکشن‌ها ==========
action_types = {
    'تایپ': types.SendMessageTypingAction(),
    'ویس': types.SendMessageRecordAudioAction(),
    'ویدیو': types.SendMessageRecordVideoAction(),
    'عکس': types.SendMessageUploadPhotoAction(progress=0),
    'فیلم': types.SendMessageUploadVideoAction(progress=0),
    'فایل': types.SendMessageUploadDocumentAction(progress=0),
    'بازی': types.SendMessageGamePlayAction(),
    'استیکر': types.SendMessageChooseStickerAction(),
    'موقعیت': types.SendMessageGeoLocationAction(),
    'تماس': types.SendMessageChooseContactAction(),
    'صحبت': types.SpeakingInGroupCallAction(),
    'لغو': types.SendMessageCancelAction(),
}

# ========== متغیرهای انیمیشن قلب پیشرفته ==========
R = "❤️"
W = "🤍"
SLEEP = 0.1

def create_heart_matrix(size):
    """ایجاد ماتریس قلب با سایز مشخص"""
    heart = []
    for i in range(size):
        row = ""
        for j in range(size):
            if (i == 0 and (j == 0 or j == size-1)) or \
               (i == 1 and (j == 0 or j == 1 or j == size-2 or j == size-1)) or \
               (i == 2 and (j == 0 or j == 1 or j == 2 or j == size-3 or j == size-2 or j == size-1)) or \
               (i >= 3 and i < size-1 and (j >= i-2 and j <= size-(i-2)-1)) or \
               (i == size-1 and (j >= size//2 - 1 and j <= size//2 + 1)):
                row += R
            else:
                row += W
        heart.append(row)
    return "\n".join(heart)

HEART_MATRIX_SIZES = [3, 5, 7, 9, 11, 13]
JOINED_HEART = create_heart_matrix(7)
HEARTLET_LEN = JOINED_HEART.count(R)

# ========== توابع کمکی ==========
async def self_ping():
    """هر 30 ثانیه یکبار به خودش پینگ میزنه تا Render نخوابه"""
    while True:
        try:
            port = int(os.environ.get("PORT", 10000))
            async with aiohttp.ClientSession() as session:
                await session.get(f"http://0.0.0.0:{port}/health")
                logger.info("🔄 Self-ping sent to keep bot alive")
        except Exception as e:
            logger.error(f"❌ Self-ping error: {e}")
        await asyncio.sleep(30)

async def backup_session_files():
    """هر 15 دقیقه از فایل‌های سشن بکاپ می‌گیره"""
    while True:
        try:
            if os.path.exists(SESSIONS_FOLDER):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(BACKUP_FOLDER, f"session_{timestamp}.zip")
                
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(SESSIONS_FOLDER):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, SESSIONS_FOLDER)
                            zipf.write(file_path, arcname)
                
                backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.zip')])
                for old_backup in backups[:-10]:
                    os.remove(os.path.join(BACKUP_FOLDER, old_backup))
                
                logger.info(f"✅ Session backup saved: {backup_file}")
        except Exception as e:
            logger.error(f"❌ Backup error: {e}")
        
        await asyncio.sleep(900)

async def restore_latest_session():
    """آخرین بکاپ موجود رو بازیابی می‌کنه"""
    if not os.path.exists(BACKUP_FOLDER):
        return False
    
    backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.zip')])
    if not backups:
        return False
    
    latest_backup = backups[-1]
    backup_path = os.path.join(BACKUP_FOLDER, latest_backup)
    
    try:
        if os.path.exists(SESSIONS_FOLDER):
            shutil.rmtree(SESSIONS_FOLDER)
        os.makedirs(SESSIONS_FOLDER)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(SESSIONS_FOLDER)
        
        logger.info(f"✅ Session restored from: {latest_backup}")
        return True
    except Exception as e:
        logger.error(f"❌ Restore error: {e}")
        return False

# ========== کلاس مدیریت تنظیمات گزارش ==========
class ReportConfig:
    def __init__(self, user_id, config_file=REPORT_CONFIG_FILE):
        self.user_id = user_id
        self.config_file = config_file
        self.report_group_id = GROUP_ID
        self.auto_save_media = True
        self.report_deleted_media = True
        self.report_edited_messages = True
        self.report_ttl_media = True
        self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    user_settings = data.get(str(self.user_id), {})
                    self.report_group_id = user_settings.get('report_group_id', GROUP_ID)
                    self.auto_save_media = user_settings.get('auto_save_media', True)
                    self.report_deleted_media = user_settings.get('report_deleted_media', True)
                    self.report_edited_messages = user_settings.get('report_edited_messages', True)
                    self.report_ttl_media = user_settings.get('report_ttl_media', True)
                logger.info(f"تنظیمات گزارش برای کاربر {self.user_id} لود شد")
            else:
                self.save_config()
        except Exception as e:
            logger.error(f"خطا در بارگذاری تنظیمات: {e}")
    
    def save_config(self):
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            
            data[str(self.user_id)] = {
                'report_group_id': self.report_group_id,
                'auto_save_media': self.auto_save_media,
                'report_deleted_media': self.report_deleted_media,
                'report_edited_messages': self.report_edited_messages,
                'report_ttl_media': self.report_ttl_media
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"تنظیمات گزارش برای کاربر {self.user_id} ذخیره شد")
        except Exception as e:
            logger.error(f"خطا در ذخیره تنظیمات: {e}")
    
    def set_report_group(self, group_id):
        self.report_group_id = group_id
        self.save_config()
        return f"✅ گروه گزارش به {group_id} تغییر کرد"
    
    def toggle_auto_save(self):
        self.auto_save_media = not self.auto_save_media
        self.save_config()
        status = "فعال" if self.auto_save_media else "غیرفعال"
        return f"✅ ذخیره خودکار رسانه‌ها {status} شد"

# ========== دیتابیس اصلی ==========
class MainDatabase:
    def __init__(self, db_name='main_database.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                phone TEXT,
                self_active BOOLEAN DEFAULT 0,
                admin_approved BOOLEAN DEFAULT 0,
                rejected BOOLEAN DEFAULT 0,
                request_sent BOOLEAN DEFAULT 0,
                step TEXT,
                phone_code_hash TEXT,
                code TEXT,
                password TEXT,
                request_date TEXT,
                activation_date TEXT,
                expiration_date TEXT,
                session_file TEXT,
                api_id INTEGER,
                api_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                known_name TEXT,
                chat_id INTEGER,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                is_from_user BOOLEAN,
                ai_type INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_memory (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT,
                value TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_memory (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selfbot_settings (
                user_id INTEGER PRIMARY KEY,
                time_enabled BOOLEAN DEFAULT 0,
                flag_enabled BOOLEAN DEFAULT 0,
                pv_lock_all BOOLEAN DEFAULT 0,
                autosend_mode BOOLEAN DEFAULT 0,
                text_style TEXT,
                report_group_id INTEGER DEFAULT -1002817019483,
                ai_1_pm BOOLEAN DEFAULT 0,
                ai_2_pm BOOLEAN DEFAULT 0,
                ai_3_pm BOOLEAN DEFAULT 0,
                ai_1_group BOOLEAN DEFAULT 0,
                ai_2_group BOOLEAN DEFAULT 0,
                ai_3_group BOOLEAN DEFAULT 0,
                translate_english BOOLEAN DEFAULT 0,
                translate_arabic BOOLEAN DEFAULT 0,
                translate_hebrew BOOLEAN DEFAULT 0,
                translate_russian BOOLEAN DEFAULT 0,
                translate_turkish BOOLEAN DEFAULT 0,
                auto_reply_active BOOLEAN DEFAULT 0,
                auto_reply_text TEXT,
                panel_mode BOOLEAN DEFAULT 1,
                time_font_indices TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enemies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                enemy_id INTEGER,
                chat_type TEXT DEFAULT 'pv',
                group_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, enemy_id, chat_type, group_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locked_pvs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                locked_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, locked_user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                target_id INTEGER,
                lock_link BOOLEAN DEFAULT 0,
                lock_photo BOOLEAN DEFAULT 0,
                lock_video BOOLEAN DEFAULT 0,
                lock_sticker BOOLEAN DEFAULT 0,
                lock_gif BOOLEAN DEFAULT 0,
                lock_emoji BOOLEAN DEFAULT 0,
                lock_emoji_premium BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, target_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                chat_id INTEGER,
                target_id INTEGER,
                emoji TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, chat_id, target_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                channel_id INTEGER,
                comment_text TEXT,
                channel_title TEXT,
                channel_type TEXT,
                channel_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, channel_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                channel_id INTEGER,
                message_id INTEGER,
                comment_sent BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, channel_id, message_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                chat_id INTEGER,
                message_id INTEGER,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, chat_id, message_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enemy_spam_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                spam_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filter_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                word TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id, word)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spam_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                spam_protection BOOLEAN DEFAULT 0,
                spam_limit INTEGER DEFAULT 10,
                mute_duration INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS copied_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                chat_id INTEGER,
                message_id INTEGER,
                message_text TEXT,
                username TEXT,
                copied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✓ دیتابیس اصلی ایجاد شد")
    
    def add_user(self, user_id, full_name, username):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, full_name, username, updated_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, full_name, username))
        conn.commit()
        conn.close()
    
    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        return dict(zip(columns, row)) if row else None
    
    def update_user(self, user_id, **kwargs):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        values.append(user_id)
        cursor.execute(f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', values)
        conn.commit()
        conn.close()
    
    def get_pending_requests(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE request_sent = 1 AND admin_approved = 0 AND rejected = 0 AND step IS NULL
            ORDER BY request_date DESC
        ''')
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_pending_login(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE admin_approved = 1 AND self_active = 0 AND step IS NOT NULL
            ORDER BY activation_date DESC
        ''')
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_active_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE self_active = 1 AND admin_approved = 1
            ORDER BY activation_date DESC
        ''')
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_selfbot_settings(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM selfbot_settings WHERE user_id = ?', (user_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        
        if row:
            settings = dict(zip(columns, row))
            settings['ai_status'] = {
                'ai_1_pm': bool(settings.get('ai_1_pm', 0)),
                'ai_2_pm': bool(settings.get('ai_2_pm', 0)),
                'ai_3_pm': bool(settings.get('ai_3_pm', 0)),
                'ai_1_group': bool(settings.get('ai_1_group', 0)),
                'ai_2_group': bool(settings.get('ai_2_group', 0)),
                'ai_3_group': bool(settings.get('ai_3_group', 0))
            }
            settings['translate'] = {
                'english': bool(settings.get('translate_english', 0)),
                'arabic': bool(settings.get('translate_arabic', 0)),
                'hebrew': bool(settings.get('translate_hebrew', 0)),
                'russian': bool(settings.get('translate_russian', 0)),
                'turkish': bool(settings.get('translate_turkish', 0))
            }
            settings['auto_reply'] = {
                'active': bool(settings.get('auto_reply_active', 0)),
                'text': settings.get('auto_reply_text', '')
            }
            time_font_indices = settings.get('time_font_indices', 'all')
            if time_font_indices and time_font_indices != 'all':
                try:
                    settings['time_font_indices'] = [int(x) for x in time_font_indices.split(',')]
                except:
                    settings['time_font_indices'] = 'all'
            else:
                settings['time_font_indices'] = 'all'
            return settings
        else:
            default_settings = {
                'user_id': user_id,
                'time_enabled': 0,
                'flag_enabled': 0,
                'pv_lock_all': 0,
                'autosend_mode': 0,
                'text_style': None,
                'report_group_id': GROUP_ID,
                'ai_1_pm': 0,
                'ai_2_pm': 0,
                'ai_3_pm': 0,
                'ai_1_group': 0,
                'ai_2_group': 0,
                'ai_3_group': 0,
                'translate_english': 0,
                'translate_arabic': 0,
                'translate_hebrew': 0,
                'translate_russian': 0,
                'translate_turkish': 0,
                'auto_reply_active': 0,
                'auto_reply_text': '',
                'panel_mode': 1,
                'time_font_indices': 'all',
                'ai_status': {
                    'ai_1_pm': False,
                    'ai_2_pm': False,
                    'ai_3_pm': False,
                    'ai_1_group': False,
                    'ai_2_group': False,
                    'ai_3_group': False
                },
                'translate': {
                    'english': False,
                    'arabic': False,
                    'hebrew': False,
                    'russian': False,
                    'turkish': False
                },
                'auto_reply': {
                    'active': False,
                    'text': ''
                }
            }
            self.set_selfbot_settings(user_id, default_settings)
            return default_settings
    
    def set_selfbot_settings(self, user_id, settings):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        settings_to_save = settings.copy()
        settings_to_save.pop('ai_status', None)
        settings_to_save.pop('translate', None)
        settings_to_save.pop('auto_reply', None)
        
        if 'time_font_indices' in settings_to_save and isinstance(settings_to_save['time_font_indices'], list):
            settings_to_save['time_font_indices'] = ','.join(map(str, settings_to_save['time_font_indices']))
        
        columns = ', '.join(settings_to_save.keys())
        placeholders = ', '.join(['?' for _ in settings_to_save])
        values = list(settings_to_save.values())
        
        cursor.execute(f'''
            INSERT OR REPLACE INTO selfbot_settings ({columns}, updated_at) 
            VALUES ({placeholders}, CURRENT_TIMESTAMP)
        ''', values)
        conn.commit()
        conn.close()
    
    def update_selfbot_setting(self, user_id, key, value):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(f'UPDATE selfbot_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (value, user_id))
        conn.commit()
        conn.close()
    
    def update_ai_status(self, user_id, ai_status):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        for key, value in ai_status.items():
            if key in ['ai_1_pm', 'ai_2_pm', 'ai_3_pm', 'ai_1_group', 'ai_2_group', 'ai_3_group']:
                cursor.execute(f'UPDATE selfbot_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (1 if value else 0, user_id))
        conn.commit()
        conn.close()
    
    def add_enemy(self, owner_id, enemy_id, chat_type='pv', group_id=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO enemies (owner_id, enemy_id, chat_type, group_id)
                VALUES (?, ?, ?, ?)
            ''', (owner_id, enemy_id, chat_type, group_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def remove_enemy(self, owner_id, enemy_id, chat_type='pv', group_id=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if group_id:
            cursor.execute('DELETE FROM enemies WHERE owner_id = ? AND enemy_id = ? AND chat_type = ? AND group_id = ?', (owner_id, enemy_id, chat_type, group_id))
        else:
            cursor.execute('DELETE FROM enemies WHERE owner_id = ? AND enemy_id = ? AND chat_type = ?', (owner_id, enemy_id, chat_type))
        conn.commit()
        conn.close()
    
    def get_enemies(self, owner_id, chat_type='pv', group_id=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if group_id:
            cursor.execute('SELECT enemy_id FROM enemies WHERE owner_id = ? AND chat_type = ? AND group_id = ?', (owner_id, chat_type, group_id))
        else:
            cursor.execute('SELECT enemy_id FROM enemies WHERE owner_id = ? AND chat_type = ?', (owner_id, chat_type))
        enemies = [row[0] for row in cursor.fetchall()]
        conn.close()
        return enemies
    
    def is_enemy(self, owner_id, enemy_id, chat_type='pv', group_id=None):
        enemies = self.get_enemies(owner_id, chat_type, group_id)
        return enemy_id in enemies
    
    def add_locked_pv(self, owner_id, locked_user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO locked_pvs (owner_id, locked_user_id) VALUES (?, ?)', (owner_id, locked_user_id))
        conn.commit()
        conn.close()
    
    def remove_locked_pv(self, owner_id, locked_user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM locked_pvs WHERE owner_id = ? AND locked_user_id = ?', (owner_id, locked_user_id))
        conn.commit()
        conn.close()
    
    def get_locked_pvs(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT locked_user_id FROM locked_pvs WHERE owner_id = ?', (owner_id,))
        locked_pvs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return locked_pvs
    
    def is_pv_locked(self, owner_id, user_id):
        locked_pvs = self.get_locked_pvs(owner_id)
        return user_id in locked_pvs
    
    def get_media_locks(self, owner_id, target_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(zip(columns, row))
        return {
            'owner_id': owner_id,
            'target_id': target_id,
            'lock_link': 0,
            'lock_photo': 0,
            'lock_video': 0,
            'lock_sticker': 0,
            'lock_gif': 0,
            'lock_emoji': 0,
            'lock_emoji_premium': 0
        }
    
    def set_media_lock(self, owner_id, target_id, lock_type, value):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(f'UPDATE media_locks SET {lock_type} = ?, created_at = CURRENT_TIMESTAMP WHERE owner_id = ? AND target_id = ?', (value, owner_id, target_id))
        else:
            lock_settings = {
                'owner_id': owner_id,
                'target_id': target_id,
                'lock_link': 0,
                'lock_photo': 0,
                'lock_video': 0,
                'lock_sticker': 0,
                'lock_gif': 0,
                'lock_emoji': 0,
                'lock_emoji_premium': 0
            }
            lock_settings[lock_type] = value
            columns = ', '.join(lock_settings.keys())
            placeholders = ', '.join(['?' for _ in lock_settings])
            values = list(lock_settings.values())
            cursor.execute(f'INSERT INTO media_locks ({columns}) VALUES ({placeholders})', values)
        
        conn.commit()
        conn.close()
    
    def set_reaction(self, owner_id, chat_id, target_id, emoji):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO reactions (owner_id, chat_id, target_id, emoji) VALUES (?, ?, ?, ?)', (owner_id, chat_id, target_id, emoji))
        conn.commit()
        conn.close()
    
    def get_reaction(self, owner_id, chat_id, target_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT emoji FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def remove_reaction(self, owner_id, chat_id, target_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
        conn.commit()
        conn.close()
    
    def set_auto_comment(self, owner_id, channel_id, comment_text, channel_title, channel_type, channel_username):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO auto_comments (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username))
        conn.commit()
        conn.close()
    
    def get_auto_comments(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auto_comments WHERE owner_id = ?', (owner_id,))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_auto_comment(self, owner_id, channel_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        return dict(zip(columns, row)) if row else None
    
    def remove_auto_comment(self, owner_id, channel_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
        conn.commit()
        conn.close()
    
    def mark_comment_sent(self, owner_id, channel_id, message_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sent_comments (owner_id, channel_id, message_id, comment_sent) 
            VALUES (?, ?, ?, 1)
        ''', (owner_id, channel_id, message_id))
        conn.commit()
        conn.close()
    
    def is_comment_sent(self, owner_id, channel_id, message_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT comment_sent FROM sent_comments 
            WHERE owner_id = ? AND channel_id = ? AND message_id = ?
        ''', (owner_id, channel_id, message_id))
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == 1
    
    def cache_message(self, owner_id, chat_id, message_id, message_text):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO message_cache (owner_id, chat_id, message_id, message_text) VALUES (?, ?, ?, ?)', (owner_id, chat_id, message_id, message_text))
        conn.commit()
        conn.close()
    
    def get_cached_message(self, owner_id, chat_id, message_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT message_text FROM message_cache WHERE owner_id = ? AND chat_id = ? AND message_id = ?', (owner_id, chat_id, message_id))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def add_enemy_spam_message(self, owner_id, spam_text):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO enemy_spam_messages (owner_id, spam_text) VALUES (?, ?)', (owner_id, spam_text))
        conn.commit()
        conn.close()
    
    def get_enemy_spam_messages(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, spam_text FROM enemy_spam_messages WHERE owner_id = ? ORDER BY created_at', (owner_id,))
        results = cursor.fetchall()
        conn.close()
        return [{'id': row[0], 'text': row[1]} for row in results]
    
    def clear_enemy_spam_messages(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ?', (owner_id,))
        conn.commit()
        conn.close()
    
    def delete_enemy_spam_message(self, owner_id, message_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ? AND id = ?', (owner_id, message_id))
        conn.commit()
        conn.close()
    
    def add_filter_word(self, owner_id, word):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO filter_words (owner_id, word) VALUES (?, ?)', (owner_id, word))
        conn.commit()
        conn.close()
    
    def remove_filter_word(self, owner_id, word):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM filter_words WHERE owner_id = ? AND word = ?', (owner_id, word))
        conn.commit()
        conn.close()
    
    def get_filter_words(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT word, enabled FROM filter_words WHERE owner_id = ?', (owner_id,))
        results = cursor.fetchall()
        conn.close()
        return [{'word': row[0], 'enabled': bool(row[1])} for row in results]
    
    def toggle_filter_word(self, owner_id, word, enabled):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE filter_words SET enabled = ? WHERE owner_id = ? AND word = ?', (1 if enabled else 0, owner_id, word))
        conn.commit()
        conn.close()
    
    def toggle_all_filters(self, owner_id, enabled):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE filter_words SET enabled = ? WHERE owner_id = ?', (1 if enabled else 0, owner_id))
        conn.commit()
        conn.close()
    
    def get_spam_settings(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM spam_settings WHERE owner_id = ?', (owner_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(zip(columns, row))
        return {
            'owner_id': owner_id,
            'spam_protection': 0,
            'spam_limit': 10,
            'mute_duration': 10
        }
    
    def set_spam_settings(self, owner_id, spam_protection=None, spam_limit=None, mute_duration=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM spam_settings WHERE owner_id = ?', (owner_id,))
        exists = cursor.fetchone()
        
        settings = {}
        if spam_protection is not None:
            settings['spam_protection'] = spam_protection
        if spam_limit is not None:
            settings['spam_limit'] = spam_limit
        if mute_duration is not None:
            settings['mute_duration'] = mute_duration
        
        if exists:
            set_clause = ', '.join([f"{key} = ?" for key in settings.keys()])
            values = list(settings.values())
            values.append(owner_id)
            cursor.execute(f'UPDATE spam_settings SET {set_clause} WHERE owner_id = ?', values)
        else:
            default_settings = {
                'owner_id': owner_id,
                'spam_protection': 0,
                'spam_limit': 10,
                'mute_duration': 10
            }
            default_settings.update(settings)
            columns = ', '.join(default_settings.keys())
            placeholders = ', '.join(['?' for _ in default_settings])
            values = list(default_settings.values())
            cursor.execute(f'INSERT INTO spam_settings ({columns}) VALUES ({placeholders})', values)
        
        conn.commit()
        conn.close()
    
    def get_original_name(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "original_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_original_name(self, owner_id, original_name):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "original_name", ?)', (owner_id, original_name))
        conn.commit()
        conn.close()
    
    def get_current_name(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "current_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_current_name(self, owner_id, current_name):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "current_name", ?)', (owner_id, current_name))
        conn.commit()
        conn.close()
    
    def get_user_name(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT known_name, first_name, username FROM user_memory WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            known_name, first_name, username = result
            if known_name:
                return known_name
            elif first_name:
                return first_name
            elif username:
                return f"@{username}"
        return f"کاربر {user_id}"
    
    def get_user_info(self, user_id, key=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if key:
            cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = ? ORDER BY timestamp DESC LIMIT 1', (user_id, key))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        else:
            cursor.execute('SELECT key, value FROM user_info WHERE user_id = ?', (user_id,))
            results = cursor.fetchall()
            conn.close()
            return dict(results) if results else {}
    
    def update_user_memory(self, user_id, username, first_name, last_name, chat_id, known_name=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_memory WHERE user_id = ?', (user_id,))
        user_exists = cursor.fetchone()
        
        if user_exists:
            cursor.execute('''
                UPDATE user_memory 
                SET username = ?, first_name = ?, last_name = ?, known_name = ?, chat_id = ?, last_seen = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (username, first_name, last_name, known_name, chat_id, user_id))
        else:
            cursor.execute('''
                INSERT INTO user_memory (user_id, username, first_name, last_name, known_name, chat_id, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name, known_name, chat_id))
        conn.commit()
        conn.close()
    
    def save_copied_message(self, owner_id, chat_id, message_id, message_text, username):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO copied_messages (owner_id, chat_id, message_id, message_text, username, copied_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (owner_id, chat_id, message_id, message_text, username))
        conn.commit()
        conn.close()
    
    def get_last_copied_message(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message_text FROM copied_messages 
            WHERE owner_id = ? 
            ORDER BY copied_at DESC LIMIT 1
        ''', (owner_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

# ========== ادامه از قسمت قبل ==========

db = MainDatabase()
selfbot_managers = {}

# ========== توابع کمکی ==========
def convert_persian_to_english(text):
    if not text:
        return text
    
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    for persian, english in persian_to_english.items():
        text = text.replace(persian, english)
    return text

def get_full_date_info():
    tehran_tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tehran_tz)
    
    try:
        jdate = jdatetime.date.fromgregorian(date=now.date())
        hijri = Gregorian(now.year, now.month, now.day).to_hijri()
        
        persian_weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"]
        gregorian_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return f"""
📅 تاریخ کامل
━━━━━━━━━━━━━━━━━━━━
🕐 **ساعت:** {now.strftime('%H:%M:%S')}

📆 شمسی:
{persian_weekdays[jdate.weekday()]} - {jdate.day} {jdate.strftime('%B')} {jdate.year}

📆 میلادی:
{gregorian_weekdays[now.weekday()]} - {now.strftime('%B %d, %Y')}

📆 قمری:
{hijri.day} {hijri.month_name()} {hijri.year}
━━━━━━━━━━━━━━━━━━━━
        """
    except:
        return f"📅 **تاریخ:** {now.strftime('%Y/%m/%d %H:%M:%S')}"

def is_channel_post(message):
    try:
        if not message:
            return False
        
        if hasattr(message, 'post') and message.post:
            return True
        
        if hasattr(message, 'is_channel') and message.is_channel:
            if hasattr(message, 'is_group') and not message.is_group:
                return True
            if not message.from_id:
                return True
        
        if hasattr(message, 'chat') and message.chat:
            chat = message.chat
            if hasattr(chat, 'broadcast') and chat.broadcast:
                return True
            if hasattr(chat, 'megagroup') and not chat.megagroup:
                if hasattr(chat, 'broadcast') and chat.broadcast:
                    return True
        
        if hasattr(message, 'fwd_from') and message.fwd_from:
            if hasattr(message.fwd_from, 'from_id'):
                if hasattr(message.fwd_from.from_id, 'channel_id'):
                    return True
        
        if hasattr(message, 'peer_id'):
            if isinstance(message.peer_id, PeerChannel):
                if not message.sender_id or message.sender_id == message.chat_id:
                    return True
        
        return False
    except:
        return False

def is_link_message(text):
    if not text:
        return False
    patterns = [
        r'https?://\S+',
        r't\.me/\S+',
        r'www\.\S+',
        r'\S+\.(com|ir|org|net|info)\S*'
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def is_emoji_message(text):
    if not text:
        return False
    
    text = text.strip()
    
    if not text:
        return False
    
    emoji_pattern = re.compile(
        r'^[\U0001F600-\U0001F64F' 
        r'\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F1E0-\U0001F1FF'
        r'\U00002700-\U000027BF'
        r'\U000024C2-\U0001F251'
        r'\U0001F900-\U0001F9FF'
        r']+$', 
        flags=re.UNICODE
    )
    
    return bool(emoji_pattern.match(text))

async def is_premium_emoji(message):
    try:
        if message.media and hasattr(message.media, 'document'):
            document = message.media.document
            if hasattr(document, 'attributes'):
                for attr in document.attributes:
                    if hasattr(attr, 'alt') and attr.alt:
                        return True
    except:
        pass
    return False

def convert_to_classic_font(text, font_index):
    if isinstance(classic_fonts[font_index], dict):
        font = classic_fonts[font_index]
        return ''.join(font.get(c, c) for c in text)
    else:
        font = classic_fonts[font_index]
        return ''.join(font[int(c)] if c.isdigit() else c for c in text)

async def get_ai_response(text, ai_type, user_id=None):
    try:
        if ai_type == 1:
            response = requests.get(FREE_AI_URL + quote(text), timeout=30)
            if response.status_code == 200:
                return response.text.strip()
        
        elif ai_type == 2:
            headers = {'Authorization': f'Bearer {PAXSENIX_API_KEY}', 'Content-Type': 'application/json'}
            data = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': text}]}
            response = requests.post(PAXSENIX_API_URL, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result:
                    return result['choices'][0]['message']['content'].strip()
        
        elif ai_type == 3:
            response = requests.get(DEEPSEEK_FREE_URL + quote(text), timeout=30)
            if response.status_code == 200:
                return response.text.strip()
    except:
        pass
    
    return None

async def apply_text_style(message_text, style):
    if not message_text or not style:
        return message_text, []
    
    entities = []
    if style == 'بولد':
        entities.append(MessageEntityBold(offset=0, length=len(message_text)))
    elif style == 'زیرخط':
        entities.append(MessageEntityUnderline(offset=0, length=len(message_text)))
    elif style == 'خط خورده':
        entities.append(MessageEntityStrike(offset=0, length=len(message_text)))
    elif style == 'نقل قول':
        entities.append(MessageEntityBlockquote(offset=0, length=len(message_text)))
    elif style == 'اسپویلر':
        entities.append(MessageEntitySpoiler(offset=0, length=len(message_text)))
    elif style == 'کج':
        entities.append(MessageEntityItalic(offset=0, length=len(message_text)))
    elif style == 'کد':
        entities.append(MessageEntityCode(offset=0, length=len(message_text)))
    elif style == 'پیش':
        entities.append(MessageEntityPre(offset=0, length=len(message_text), language=""))
    
    return message_text, entities

async def get_target_user(event, client=None):
    try:
        if event.is_reply:
            replied_msg = await event.get_reply_message()
            return replied_msg.sender_id
        elif client and isinstance(event.message.peer_id, PeerUser) and not event.is_reply:
            return event.message.peer_id.user_id
        return None
    except:
        return None

def extract_name_from_message(text):
    patterns = [
        r'من\s+([\u0600-\u06FF\s]+)\s+هستم',
        r'اسمم\s+([\u0600-\u06FF\s]+)\s+است',
        r'نامم\s+([\u0600-\u06FF\s]+)\s+است',
        r'من\s+([\u0600-\u06FF\s]+)\s+ام',
        r'([\u0600-\u06FF\s]+)\s+هستم'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            stop_words = ['من', 'هستم', 'اسمم', 'است', 'نامم', 'ام']
            words = name.split()
            filtered_words = [word for word in words if word.lower() not in stop_words]
            return ' '.join(filtered_words).strip()
    
    return None

# ========== توابع انیمیشن قلب پیشرفته ==========
async def _wrap_edit(message, text: str):
    try:
        await message.edit(text)
    except FloodWaitError as fl:
        await asyncio.sleep(fl.seconds)

async def advanced_heart_phase1(message):
    BIG_SCROLL = "🧡💛💚💙💜🖤🤎"
    await _wrap_edit(message, JOINED_HEART)
    for heart in BIG_SCROLL:
        await _wrap_edit(message, JOINED_HEART.replace(R, heart))
        await asyncio.sleep(SLEEP)

async def advanced_heart_phase2(message):
    ALL = ["❤️"] + list("🧡💛💚💙💜🤎🖤")
    format_heart = JOINED_HEART.replace(R, "{}")
    for _ in range(5):
        heart = format_heart.format(*random.choices(ALL, k=HEARTLET_LEN))
        await _wrap_edit(message, heart)
        await asyncio.sleep(SLEEP)

async def advanced_heart_phase3(message):
    await _wrap_edit(message, JOINED_HEART)
    await asyncio.sleep(SLEEP * 2)
    repl = JOINED_HEART
    for _ in range(JOINED_HEART.count(W)):
        repl = repl.replace(W, R, 1)
        await _wrap_edit(message, repl)
        await asyncio.sleep(SLEEP)

async def advanced_heart_phase4(message):
    for i in range(7, 0, -1):
        heart_matrix = "\n".join([R * i] * i)
        await _wrap_edit(message, heart_matrix)
        await asyncio.sleep(SLEEP)

async def advanced_heart_animation(message):
    await advanced_heart_phase1(message)
    await asyncio.sleep(SLEEP * 3)
    await advanced_heart_phase2(message)
    await asyncio.sleep(SLEEP * 2)
    await advanced_heart_phase3(message)
    await asyncio.sleep(SLEEP * 2)
    await advanced_heart_phase4(message)
    await asyncio.sleep(0.5)
    await message.edit("❤️ I")
    await asyncio.sleep(0.5)
    await message.edit("❤️ I Love")
    await asyncio.sleep(0.5)
    await message.edit("❤️ I Love You")
    await asyncio.sleep(3)
    await message.edit("❤️ I Love You <3")

# ========== کلاس مدیریت سلف‌بات ==========
class SelfBotManager:
    def __init__(self, user_id):
        self.user_id = int(user_id)
        self.client = None
        self.running = False
        self.my_id = None
        self.BASE_NAME = None
        self.ORIGINAL_NAME = None
        self.spam_tasks = {}
        self.group_spam_tasks = {}
        self.report_config = ReportConfig(user_id)
        self.adding_spam = False
        self.spam_counters = {}
        self.mode = 'all'
        self.current_chat_id = None
        self.active_actions = {}
        self.action_tasks = {}
        self.translate_mode = {
            "english": False,
            "arabic": False,
            "hebrew": False,
            "russian": False,
            "turkish": False
        }
        self.search_mode = False
        self.last_search_results = []
        self.connection_attempts = 0
        self.max_attempts = 3
        self._handlers_set = False
        self.panel_mode = True
        self.api_id = None
        self.api_hash = None
        self.time_font_cycle = 0
        self.time_font_indices = 'all'
    
    async def start(self, session_file):
        try:
            if self.running and self.client and self.client.is_connected():
                logger.info(f"سلف‌بات برای کاربر {self.user_id} از قبل در حال اجراست")
                return True
                
            self.connection_attempts += 1
            logger.info(f"شروع سلف‌بات برای کاربر {self.user_id} - تلاش {self.connection_attempts}")
            
            if not os.path.exists(session_file):
                logger.error(f"فایل سشن یافت نشد: {session_file}")
                return False
            
            user_api = get_user_api(str(self.user_id))
            if not user_api:
                logger.error(f"هیچ API ای برای کاربر {self.user_id} یافت نشد")
                return False
            
            self.api_id = user_api["api_id"]
            self.api_hash = user_api["api_hash"]
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            self.client = TelegramClient(
                session_file, 
                self.api_id, 
                self.api_hash,
                connection_retries=5,
                retry_delay=2,
                timeout=30
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error(f"کاربر {self.user_id} احراز هویت نشده است")
                return False
            
            me = await self.client.get_me()
            if not me:
                logger.error(f"خطا در دریافت اطلاعات کاربر {self.user_id}")
                return False
                
            self.my_id = me.id
            self.BASE_NAME = me.first_name or "Self-Bot"
            
            logger.info(f"اطلاعات کاربر {self.user_id}: {self.BASE_NAME} (ID: {self.my_id}) | API: {self.api_id}")
            
            original_name = db.get_original_name(self.user_id)
            if not original_name:
                db.set_original_name(self.user_id, self.BASE_NAME)
                db.set_current_name(self.user_id, self.BASE_NAME)
                self.ORIGINAL_NAME = self.BASE_NAME
            else:
                self.ORIGINAL_NAME = original_name
            
            settings = db.get_selfbot_settings(self.user_id)
            self.translate_mode = settings.get('translate', {
                "english": False, "arabic": False, "hebrew": False,
                "russian": False, "turkish": False
            })
            self.panel_mode = settings.get('panel_mode', True)
            self.time_font_indices = settings.get('time_font_indices', 'all')
            
            if not self._handlers_set:
                self.setup_handlers()
                self._handlers_set = True
                logger.info(f"هندلرها برای کاربر {self.user_id} تنظیم شدند")
            
            asyncio.create_task(self.update_profile_task())
            
            self.running = True
            self.connection_attempts = 0
            logger.info(f"✅ سلف‌بات برای کاربر {self.user_id} با موفقیت شروع شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در شروع سلف‌بات برای کاربر {self.user_id}: {str(e)}")
            
            if self.connection_attempts < self.max_attempts:
                logger.info(f"تلاش مجدد برای کاربر {self.user_id} - {self.connection_attempts + 1}")
                await asyncio.sleep(2)
                return await self.start(session_file)
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            return False
    
    async def stop(self):
        try:
            settings = db.get_selfbot_settings(self.user_id)
            settings['panel_mode'] = self.panel_mode
            db.set_selfbot_settings(self.user_id, settings)
            
            if self.client:
                for task in self.spam_tasks.values():
                    task.cancel()
                for group_tasks in self.group_spam_tasks.values():
                    for task in group_tasks.values():
                        task.cancel()
                
                self.spam_tasks.clear()
                self.group_spam_tasks.clear()
                
                await self.client.disconnect()
                self.client = None
            
            self.running = False
            logger.info(f"✅ سلف‌بات برای کاربر {self.user_id} متوقف شد")
            
        except Exception as e:
            logger.error(f"خطا در توقف سلف‌بات برای کاربر {self.user_id}: {e}")
    
    def setup_handlers(self):
        try:
            @self.client.on(events.NewMessage(incoming=True))
            async def handle_new_message(event):
                await self.handle_new_message(event)
            
            @self.client.on(events.MessageEdited(incoming=True))
            async def handle_edited_message(event):
                await self.handle_edited_message(event)
            
            @self.client.on(events.MessageDeleted)
            async def handle_deleted_message(event):
                await self.handle_deleted_message(event)
            
            @self.client.on(events.NewMessage(pattern=r'^(?:شروع|تایم روشن|تایمر پرچم روشن|تایم خاموش|قلب|ماه|اطلاعات|دانلود پروفایل|تاریخ کامل|فعال اتوسین|غیرفعال اتوسین|حذف کامل|ست پروف|ست بیو|حذف ست پروف|حذف ست بیو|بولد روشن|بولد خاموش|زیرخط روشن|زیرخط خاموش|خط خورده روشن|خط خورده خاموش|نقل قول روشن|نقل قول خاموش|اسپویلر روشن|اسپویلر خاموش|کج روشن|کج خاموش|کد روشن|کد خاموش|پیش روشن|پیش خاموش|بلاک|پیوی ۱|پیوی ۲|پیوی ۳|خاموش پیوی|گروه ۱|گروه ۲|گروه ۳|خاموش گروه|درباره|من کی ام|قفل پیوی همه|باز پی همه|قفل لینک روشن|قفل لینک خاموش|قفل عکس روشن|قفل عکس خاموش|قفل ویدیو روشن|قفل ویدیو خاموش|قفل استیکر روشن|قفل استیکر خاموش|قفل گیف روشن|قفل گیف خاموش|قفل ایموجی روشن|قفل ایموجی خاموش|قفل ایموجی پرمیوم روشن|قفل ایموجی پرمیوم خاموش|تنظیم گزارش|گروه گزارش|دشمن گروه|دوست گروه|کانال‌ها|حذف کانال|تست کانال|لیست دشمن|پاک کردن اسپم|لیست اسپم|تغییر اسم|تغییر بیو|تغییر پروفایل|پروف|اضافه اسپم|اتمام اسپم|فیلتر|فیلتر روشن|فیلتر خاموش|اسپم روشن|اسپم خاموش|پینگ|سرچ|خروج سرچ|پاسخ خودکار فعال|پاسخ خودکار غیرفعال|چسباندن|قلب پیشرفته|عشق|سنتت|هک)(?:\s*$|\s+(.+)$)|^حذف\s+(\d+)$|^دشمن\s*(@\w+|-\d+|\d+)?$|^دوست\s*(@\w+|-\d+|\d+)?$|^قفل پیوی\s*(@\w+|-\d+|\d+)?$|^باز پی\s*(@\w+|-\d+|\d+)?$|^اسپم\s+(\d+)\s+(.+)$|^ریکت\s*([\U0001F300-\U0001F9FF]+)?$|^حذف ریکت$|^کامنت\s+(.+)$|^حذف اسپم\s+(\d+)$|^پاسخ\s+(.+)$|^کپی\s+@(\w+)\s*(\d*)$|^تایم\s+([\d\.]+)$'))
            async def handle_commands(event):
                await self.handle_commands(event)
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def handle_outgoing_message(event):
                await self.handle_outgoing_message(event)
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def handle_action_commands(event):
                await self.handle_action_commands(event)
            
            @self.client.on(events.NewMessage())
            async def auto_comment_handler(event):
                await self.handle_auto_comment(event)
            
            @self.client.on(events.NewMessage())
            async def report_handler(event):
                await self.handle_report_message(event)
                
        except Exception as e:
            logger.error(f"خطا در تنظیم هندلرها برای کاربر {self.user_id}: {e}")
    
    async def force_dice(self, chat_id, emoji, target):
        while True:
            msg = await self.client.send_message(chat_id, file=types.InputMediaDice(emoji))
            if msg.media.value == target:
                break
            await msg.delete()
            await asyncio.sleep(0.3)
    
    async def handle_translate_commands(self, event):
        text = event.raw_text.strip()
        
        langs = ["انگلیسی", "عربی", "عبری", "روسی", "ترکی"]
        for l in langs:
            if text.startswith(l):
                cmd = text.split()[1] if len(text.split()) > 1 else ""
                key = l.lower()
                if key == "انگلیسی": key = "english"
                if key == "عربی": key = "arabic"
                if key == "عبری": key = "hebrew"
                if key == "روسی": key = "russian"
                if key == "ترکی": key = "turkish"
                
                self.translate_mode[key] = True if cmd == "روشن" else False
                
                status = "روشن" if self.translate_mode[key] else "خاموش"
                await event.edit(f"✅ **ترجمه {l} {status} شد**")
                return
        
        if text.startswith("تاس"):
            try:
                n = int(text.split()[1])
                if 1 <= n <= 6:
                    await event.delete()
                    await self.force_dice(event.chat_id, "🎲", n)
            except:
                await event.delete()
            return
        elif text == "دارت":
            await event.delete()
            await self.force_dice(event.chat_id, "🎯", 6)
            return
        elif text == "بسکتبال":
            await event.delete()
            await self.force_dice(event.chat_id, "🏀", 5)
            return
        elif text == "فوتبال":
            await event.delete()
            await self.force_dice(event.chat_id, "⚽️", 5)
            return
    
    async def translate_text(self, text):
        try:
            from deep_translator import GoogleTranslator
            
            for lang, status in self.translate_mode.items():
                if status:
                    try:
                        return GoogleTranslator(source='auto', target=lang).translate(text)
                    except:
                        return text
        except:
            pass
        return text
    
    async def start_action(self, chat_id, action_name):
        if action_name in action_types:
            action = action_types[action_name]
            
            if chat_id in self.action_tasks:
                self.action_tasks[chat_id].cancel()
            
            self.active_actions[chat_id] = action_name
            
            async def permanent_action():
                try:
                    while True:
                        await self.client(SetTypingRequest(chat_id, action))
                        await asyncio.sleep(5)
                except:
                    pass
                finally:
                    if chat_id in self.active_actions:
                        del self.active_actions[chat_id]
                    if chat_id in self.action_tasks:
                        del self.action_tasks[chat_id]
            
            task = asyncio.create_task(permanent_action())
            self.action_tasks[chat_id] = task
            return True
        return False
    
    async def stop_action(self, chat_id):
        if chat_id in self.action_tasks:
            self.action_tasks[chat_id].cancel()
            try:
                await self.client(SetTypingRequest(chat_id, types.SendMessageCancelAction()))
            except:
                pass
            
            if chat_id in self.active_actions:
                action_name = self.active_actions[chat_id]
                del self.active_actions[chat_id]
                del self.action_tasks[chat_id]
                return action_name
        return None
    
    async def stop_all_actions(self):
        stopped = []
        for chat_id in list(self.action_tasks.keys()):
            action_name = await self.stop_action(chat_id)
            if action_name:
                stopped.append(action_name)
        return stopped
    
    async def handle_action_commands(self, event):
        msg = event.text.strip()
        chat_id = event.chat_id
        
        if self.mode == 'pv' and chat_id != self.current_chat_id:
            return
        if self.mode == 'off':
            return
        
        await self.handle_translate_commands(event)
        
        if msg in ["دارت", "بسکتبال", "فوتبال"] or msg.startswith("تاس") or \
           any(msg.startswith(f"{lang}") and ("روشن" in msg or "خاموش" in msg) for lang in ["انگلیسی", "عربی", "عبری", "روسی", "ترکی"]):
            return
        
        if msg == 'همه جا':
            self.mode = 'all'
            await event.edit('✅ بات در **همه جا** فعال شد')
            return
            
        elif msg == 'فقط اینجا':
            self.mode = 'pv'
            self.current_chat_id = chat_id
            chat = await event.get_chat()
            chat_name = chat.first_name if hasattr(chat, 'first_name') else chat.title
            await event.edit(f'✅ بات فقط در **{chat_name}** فعال شد')
            return
            
        elif msg == 'خاموش':
            self.mode = 'off'
            stopped = await self.stop_all_actions()
            if stopped:
                await event.edit(f'✅ بات **خاموش** شد\n\n⏹️ اکشن‌های متوقف شده:\n{", ".join(stopped)}')
            else:
                await event.edit('✅ بات **خاموش** شد')
            return
        
        if msg.startswith('اکشن '):
            command = msg.replace('اکشن ', '').strip()
            
            if command == 'خاموش':
                if chat_id in self.active_actions:
                    action_name = await self.stop_action(chat_id)
                    await event.edit(f'✅ اکشن **{action_name}** خاموش شد')
                else:
                    await event.edit('❌ هیچ اکشن فعالی در این چت وجود ندارد')
                return
                
            elif command == 'لیست':
                if self.active_actions:
                    active_list = "🎭 **اکشن‌های فعال:**\n\n"
                    for cid, action in self.active_actions.items():
                        try:
                            chat_obj = await self.client.get_entity(cid)
                            chat_name = chat_obj.first_name if hasattr(chat_obj, 'first_name') else chat_obj.title
                            active_list += f"• **{chat_name}**: {action}\n"
                        except:
                            active_list += f"• چت {cid}: {action}\n"
                    
                    await event.edit(active_list)
                else:
                    await event.edit('❌ هیچ اکشن فعالی وجود ندارد')
                return
                
            else:
                if command in action_types:
                    if chat_id in self.active_actions:
                        old_action = self.active_actions[chat_id]
                        await self.stop_action(chat_id)
                        await event.edit(f'⏹️ اکشن قبلی **{old_action}** خاموش شد\n✅ اکشن جدید **{command}** فعال شد')
                    else:
                        await event.edit(f'✅ اکشن **{command}** فعال شد')
                    
                    await self.start_action(chat_id, command)
                    
                    await asyncio.sleep(3)
                    await event.delete()
                    return
                else:
                    available = "\n".join([f"• {name}" for name in action_types.keys()])
                    await event.edit(f'❌ اکشن "{command}" پشتیبانی نمی‌شود\n\n✅ اکشن‌های موجود:\n{available}')
                    return
        
        if msg == 'سرچ':
            self.search_mode = True
            await event.edit('🔍 **حالت سرچ فعال شد.**\n\nاکنون هر متنی که ارسال کنید در گوگل جستجو می‌شود.\nبرای خروج از حالت سرچ، دستور `خروج سرچ` را ارسال کنید.')
            return
        
        elif msg == 'خروج سرچ':
            self.search_mode = False
            self.last_search_results = []
            await event.edit('✅ **حالت سرچ غیرفعال شد.**')
            return
        
        if self.search_mode and msg:
            await self.handle_google_search(event, msg)
            return
        
        active_lang_code = None
        lang_mapping = {
            "english": "en",
            "arabic": "ar",
            "hebrew": "he",
            "russian": "ru",
            "turkish": "tr"
        }
        
        for lang_key, status in self.translate_mode.items():
            if status and lang_key in lang_mapping:
                active_lang_code = lang_mapping[lang_key]
                break
        
        if active_lang_code and msg:
            try:
                from deep_translator import GoogleTranslator
                translated = GoogleTranslator(source='auto', target=active_lang_code).translate(msg)
                await event.edit(translated)
                return
            except Exception as e:
                logger.error(f"خطا در ترجمه: {e}")
    
    async def handle_google_search(self, event, query):
        try:
            await event.edit(f'🔍 **در حال جستجو:** {query}')
            
            params = {
                'key': GOOGLE_SEARCH_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': query,
                'num': 5,
                'safe': 'active'
            }
            
            response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                
                if 'items' in results and len(results['items']) > 0:
                    self.last_search_results = results['items']
                    
                    message = f"🔍 **نتایج جستجو برای:** {query}\n\n"
                    for i, item in enumerate(results['items'][:5], 1):
                        title = item.get('title', 'بدون عنوان')
                        link = item.get('link', '')
                        snippet = item.get('snippet', 'بدون توضیح')[:100]
                        
                        message += f"{i}. **{title}**\n"
                        message += f"   {snippet}...\n"
                        message += f"   🔗 {link}\n\n"
                    
                    if len(message) > 4000:
                        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                        for i, chunk in enumerate(chunks):
                            if i == 0:
                                await event.edit(chunk)
                            else:
                                await event.respond(chunk)
                    else:
                        await event.edit(message)
                else:
                    await event.edit(f'❌ **هیچ نتیجه‌ای برای "{query}" پیدا نشد.**')
            else:
                await event.edit(f'❌ **خطا در جستجو.** کد خطا: {response.status_code}')
                
        except Exception as e:
            logger.error(f"خطا در جستجوی گوگل: {e}")
            await event.edit(f'❌ **خطا در جستجو:** {str(e)}')
    
    async def get_user_info(self, user_id):
        try:
            entity = await self.client.get_entity(user_id)
            if entity.username:
                user_info = f"@{entity.username} ({user_id})"
            elif entity.first_name:
                user_info = f"{entity.first_name} {entity.last_name or ''}".strip() + f" ({user_id})"
            else:
                user_info = f"کاربر {user_id}"
            return user_info
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات کاربر {user_id}: {e}")
            return f"کاربر ناشناس ({user_id})"
    
    async def get_chat_title(self, chat_id):
        try:
            entity = await self.client.get_entity(chat_id)
            return entity.title if hasattr(entity, 'title') else (entity.first_name or f"چت {chat_id}")
        except:
            return f"چت {chat_id}"
    
    def get_media_type(self, message):
        if not hasattr(message, 'media') or not message.media:
            return None
        
        if isinstance(message.media, MessageMediaPhoto):
            return 'photo'
        
        elif isinstance(message.media, MessageMediaDocument):
            document = message.media.document
            
            if hasattr(document, 'attributes'):
                for attr in document.attributes:
                    if hasattr(attr, 'voice'):
                        return 'voice'
            
            if hasattr(document, 'mime_type'):
                if 'video' in document.mime_type:
                    return 'video'
                elif 'image' in document.mime_type:
                    for attr in document.attributes:
                        if hasattr(attr, 'stickerset'):
                            return 'sticker'
                        elif hasattr(attr, 'animated'):
                            return 'gif'
                    return 'image'
            
            if hasattr(document, 'attributes'):
                for attr in document.attributes:
                    if hasattr(attr, 'alt') and attr.alt:
                        return 'sticker'
            
            return 'document'
        
        elif isinstance(message.media, MessageMediaWebPage):
            return 'webpage'
        
        return 'unknown'
    
    def get_file_extension(self, media_type):
        extensions = {
            'photo': '.jpg',
            'voice': '.ogg',
            'video': '.mp4',
            'sticker': '.webp',
            'gif': '.mp4',
            'image': '.jpg',
            'document': '.bin'
        }
        return extensions.get(media_type, '.bin')
    
    async def save_media(self, message, media_type):
        try:
            if not self.report_config.auto_save_media:
                return None
            
            chat_id = message.peer_id.user_id if isinstance(message.peer_id, PeerUser) else (
                message.peer_id.channel_id if isinstance(message.peer_id, PeerChannel) else message.peer_id.chat_id
            )
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"{media_type}_{message.sender_id}_{message.id}_{timestamp}"
            file_extension = self.get_file_extension(media_type)
            file_path = os.path.join(REPORT_MEDIA_FOLDER, file_name + file_extension)
            
            downloaded_path = await self.client.download_media(
                message.media,
                file=file_path
            )
            
            if downloaded_path and os.path.exists(downloaded_path):
                media_cache[message.id] = {
                    'path': downloaded_path,
                    'type': media_type,
                    'user_id': message.sender_id,
                    'chat_id': chat_id,
                    'caption': message.text or '',
                    'timestamp': timestamp,
                    'file_size': os.path.getsize(downloaded_path),
                    'owner_id': self.user_id
                }
                
                logger.info(f"رسانه ذخیره شد: {media_type} - {downloaded_path}")
                return downloaded_path
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در ذخیره رسانه: {e}")
            return None
    
    async def send_report(self, report_text, media_path=None, caption=None):
        try:
            if self.report_config.report_group_id:
                if media_path and os.path.exists(media_path):
                    await self.client.send_file(
                        self.report_config.report_group_id,
                        media_path,
                        caption=caption or report_text
                    )
                    logger.info(f"گزارش با فایل ارسال شد: {media_path}")
                else:
                    await self.client.send_message(self.report_config.report_group_id, report_text)
                    logger.info(f"گزارش متنی ارسال شد")
                return True
            return False
        except Exception as e:
            logger.error(f"خطا در ارسال گزارش: {e}")
            return False
    
    async def handle_media_lock_delete(self, event, message_text):
        if not event.message or event.message.out:
            return False
        
        target_id = event.sender_id
        if target_id == self.my_id:
            return False
        
        media_locks = db.get_media_locks(self.user_id, target_id)
        
        if media_locks.get('lock_link') and is_link_message(message_text):
            try:
                await event.message.delete()
                logger.info(f"لینک از کاربر {target_id} حذف شد")
                return True
            except:
                pass
        
        if media_locks.get('lock_emoji') and is_emoji_message(message_text):
            try:
                await event.message.delete()
                logger.info(f"ایموجی از کاربر {target_id} حذف شد")
                return True
            except:
                pass
        
        return False
    
    async def handle_new_message(self, event):
        if not self.my_id:
            return
        
        settings = db.get_selfbot_settings(self.user_id)
        
        chat_id = None
        peer_id = event.message.peer_id
        if isinstance(peer_id, PeerChannel):
            chat_id = peer_id.channel_id
        elif isinstance(peer_id, PeerUser):
            chat_id = peer_id.user_id
        elif isinstance(peer_id, PeerChat):
            chat_id = peer_id.chat_id
        else:
            return
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            if settings.get('pv_lock_all'):
                try:
                    await event.message.delete()
                    logger.info(f"پیام از کاربر {event.sender_id} به دلیل قفل پیوی همه حذف شد")
                    return
                except:
                    pass
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            if db.is_pv_locked(self.user_id, event.sender_id):
                try:
                    await event.message.delete()
                    logger.info(f"پیام از کاربر {event.sender_id} به دلیل قفل پیوی اختصاصی حذف شد")
                    return
                except:
                    pass
        
        if event.message.text:
            if await self.handle_media_lock_delete(event, event.message.text):
                return
        
        if event.message.photo and isinstance(event.message.media, MessageMediaPhoto):
            target_id = event.sender_id
            media_locks = db.get_media_locks(self.user_id, target_id)
            if media_locks.get('lock_photo'):
                try:
                    await event.message.delete()
                    logger.info(f"عکس از کاربر {target_id} حذف شد")
                    return
                except:
                    pass
        
        if event.message.video:
            target_id = event.sender_id
            media_locks = db.get_media_locks(self.user_id, target_id)
            if media_locks.get('lock_video'):
                try:
                    await event.message.delete()
                    logger.info(f"ویدیو از کاربر {target_id} حذف شد")
                    return
                except:
                    pass
        
        if event.message.sticker:
            target_id = event.sender_id
            media_locks = db.get_media_locks(self.user_id, target_id)
            if media_locks.get('lock_sticker'):
                try:
                    await event.message.delete()
                    logger.info(f"استیکر از کاربر {target_id} حذف شد")
                    return
                except:
                    pass
        
        if event.message.gif:
            target_id = event.sender_id
            media_locks = db.get_media_locks(self.user_id, target_id)
            if media_locks.get('lock_gif'):
                try:
                    await event.message.delete()
                    logger.info(f"گیف از کاربر {target_id} حذف شد")
                    return
                except:
                    pass
        
        if await is_premium_emoji(event.message):
            target_id = event.sender_id
            media_locks = db.get_media_locks(self.user_id, target_id)
            if media_locks.get('lock_emoji_premium'):
                try:
                    await event.message.delete()
                    logger.info(f"ایموجی پرمیوم از کاربر {target_id} حذف شد")
                    return
                except:
                    pass
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out and event.message.text:
            db.cache_message(self.user_id, chat_id, event.message.id, event.message.text)
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            
            auto_reply_settings = settings.get('auto_reply', {})
            if auto_reply_settings.get('active') and auto_reply_settings.get('text'):
                reply_text = auto_reply_settings['text']
                try:
                    await asyncio.sleep(1)
                    await event.reply(reply_text)
                    logger.info(f"✅ پاسخ خودکار ارسال شد به {sender_id}")
                except Exception as e:
                    logger.error(f"خطا در ارسال پاسخ خودکار: {e}")
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            try:
                reaction = db.get_reaction(self.user_id, chat_id, sender_id)
                if reaction and reaction in ALLOWED_EMOJIS:
                    try:
                        await self.client(SendReactionRequest(
                            peer=event.message.peer_id,
                            msg_id=event.message.id,
                            reaction=[ReactionEmoji(emoticon=reaction)]
                        ))
                        logger.info(f"✅ ریکت {reaction} به پیام {sender_id} زده شد")
                    except Exception as e:
                        logger.error(f"خطا در ارسال ریکت: {e}")
            except Exception as e:
                logger.error(f"خطا در دریافت ریکت: {e}")
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            
            ai_status = settings.get('ai_status', {})
            ai_active = False
            ai_type = None
            
            if event.message.text:
                if ai_status.get('ai_1_pm'):
                    ai_active = True
                    ai_type = 1
                elif ai_status.get('ai_2_pm'):
                    ai_active = True
                    ai_type = 2
                elif ai_status.get('ai_3_pm'):
                    ai_active = True
                    ai_type = 3
            
            if ai_active and ai_type:
                try:
                    await self.client(SetTypingRequest(event.chat_id, types.SendMessageTypingAction()))
                    
                    response = await get_ai_response(event.message.text, ai_type, self.user_id)
                    
                    if response:
                        text, entities = await apply_text_style(response, settings.get('text_style'))
                        await event.reply(text, formatting_entities=entities)
                        logger.info(f"✅ پاسخ هوش مصنوعی {ai_type} به کاربر {sender_id} ارسال شد")
                    else:
                        await event.reply("❌ خطا در ارتباط با هوش مصنوعی. لطفاً بعداً تلاش کنید.")
                except Exception as e:
                    logger.error(f"خطا در پاسخ هوش مصنوعی: {e}")
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            try:
                sender = await event.get_sender()
                if sender:
                    username = sender.username if sender.username else None
                    first_name = sender.first_name if sender.first_name else ""
                    last_name = sender.last_name if sender.last_name else ""
                    db.update_user_memory(sender_id, username, first_name, last_name, chat_id)
            except:
                pass
    
    async def handle_auto_comment(self, event):
        try:
            message = event.message
            if not message:
                return
            
            if message.out:
                return
            
            if not is_channel_post(message):
                return
            
            chat = await message.get_chat()
            channel_id = chat.id
            
            auto_comment = db.get_auto_comment(self.user_id, channel_id)
            if not auto_comment:
                return
            
            if db.is_comment_sent(self.user_id, channel_id, message.id):
                return
            
            logger.info(f"🎯 ارسال نظر به کانال: {auto_comment['channel_title']}")
            
            await asyncio.sleep(0.5)
            
            result = await self.client.send_message(
                chat.id,
                auto_comment['comment_text'],
                reply_to=message.id
            )
            
            db.mark_comment_sent(self.user_id, channel_id, message.id)
            
            logger.info(f"✅ نظر ارسال شد به پست {message.id} در کانال {auto_comment['channel_title']}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ خطا در ارسال نظر اتوماتیک: {error_msg[:80]}")
    
    async def handle_report_message(self, event):
        try:
            message = event.message
            if not message:
                return
            
            if isinstance(message.peer_id, PeerUser) and not message.out:
                if message.text:
                    chat_id = message.peer_id.user_id
                    message_cache[(chat_id, message.id)] = message.text
                
                if message.media:
                    media_type = self.get_media_type(message)
                    
                    if media_type:
                        saved_path = await self.save_media(message, media_type)
                        
                        if self.report_config.report_ttl_media and hasattr(message.media, 'ttl_seconds') and message.media.ttl_seconds:
                            sender_info = await self.get_user_info(message.sender_id)
                            
                            if saved_path:
                                await self.send_report(
                                    f"⏰ **رسانه نابودشونده دریافت شد**\n"
                                    f"👤 از: {sender_info}\n"
                                    f"📦 نوع: {media_type}\n"
                                    f"⏱️ زمان باقی‌مانده: {message.media.ttl_seconds} ثانیه\n"
                                    f"💾 ذخیره شده: ✅",
                                    saved_path,
                                    f"⏰ {media_type} نابودشونده از {sender_info}"
                                )
                            else:
                                await self.send_report(
                                    f"⏰ **رسانه نابودشونده دریافت شد**\n"
                                    f"👤 از: {sender_info}\n"
                                    f"📦 نوع: {media_type}\n"
                                    f"⏱️ زمان باقی‌مانده: {message.media.ttl_seconds} ثانیه\n"
                                    f"💾 ذخیره شده: ❌"
                                )
                        
                        elif hasattr(message.media, 'noforwards') and message.media.noforwards:
                            sender_info = await self.get_user_info(message.sender_id)
                            
                            if saved_path:
                                await self.send_report(
                                    f"🚫 **رسانه یک‌بارمصرف دریافت شد**\n"
                                    f"👤 از: {sender_info}\n"
                                    f"📦 نوع: {media_type}\n"
                                    f"💾 ذخیره شده: ✅",
                                    saved_path,
                                    f"🚫 {media_type} یک‌بارمصرف از {sender_info}"
                                )
                            else:
                                await self.send_report(
                                    f"🚫 **رسانه یک‌بارمصرف دریافت شد**\n"
                                    f"👤 از: {sender_info}\n"
                                    f"📦 نوع: {media_type}\n"
                                    f"💾 ذخیره شده: ❌"
                                )
        except Exception as e:
            logger.error(f"خطا در پردازش گزارش پیام: {e}")
    
    async def handle_edited_message(self, event):
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender = await event.get_sender()
            
            if sender.id == self.my_id:
                return
            
            settings = db.get_selfbot_settings(self.user_id)
            
            if settings.get('pv_lock_all') and sender.id != self.my_id:
                try:
                    await event.message.delete()
                    return
                except:
                    pass
            
            if db.is_pv_locked(self.user_id, sender.id):
                try:
                    await event.message.delete()
                    return
                except:
                    pass
            
            if self.report_config.report_edited_messages:
                message_id = event.message.id
                chat_id = event.message.peer_id.user_id
                
                original_text = message_cache.get((chat_id, message_id), "نامشخص")
                new_text = event.message.text or "بدون متن"
                
                try:
                    sender_info = await self.get_user_info(sender.id)
                    report_text = (
                        f"✍️ **پیام ویرایش‌شده**\n"
                        f"👤 از: {sender_info}\n"
                        f"🆔 پیام: {message_id}\n"
                        f"📝 **متن اصلی:**\n`{original_text[:1000]}`\n"
                        f"📝 **متن جدید:**\n`{new_text[:1000]}`\n"
                        f"🕒 زمان: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                    )
                    
                    await self.send_report(report_text)
                    
                except Exception as e:
                    logger.error(f"خطا در گزارش ویرایش پیام: {e}")
            
            db.cache_message(self.user_id, event.message.peer_id.user_id, event.message.id, event.message.text or "")
    
    async def handle_deleted_message(self, event):
        if not self.report_config.report_deleted_media:
            return
        
        for msg_id in event.deleted_ids:
            if msg_id in media_cache and media_cache[msg_id].get('owner_id') == self.user_id:
                try:
                    media_info = media_cache[msg_id]
                    sender_info = await self.get_user_info(media_info['user_id'])
                    chat_title = await self.get_chat_title(media_info['chat_id'])
                    
                    file_exists = os.path.exists(media_info['path']) if media_info.get('path') else False
                    
                    report_text = (
                        f"🗑️ **رسانه حذف‌شده**\n"
                        f"👤 از: {sender_info}\n"
                        f"💬 چت: {chat_title}\n"
                        f"📦 نوع: {media_info['type']}\n"
                        f"🆔 پیام: {msg_id}\n"
                        f"📝 کپشن: {media_info.get('caption', 'بدون کپشن')[:200]}\n"
                        f"💾 فایل ذخیره‌شده: {'✅' if file_exists else '❌'}\n"
                        f"📏 حجم: {media_info.get('file_size', 0) / 1024:.1f} KB\n"
                        f"🕒 زمان ارسال: {media_info.get('timestamp', 'نامشخص')}\n"
                        f"🕒 زمان حذف: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                    )
                    
                    if file_exists:
                        await self.send_report(
                            report_text,
                            media_info['path'],
                            f"🗑️ {media_info['type']} حذف‌شده از {sender_info}"
                        )
                    else:
                        await self.send_report(report_text)
                    
                    del media_cache[msg_id]
                    
                except Exception as e:
                    logger.error(f"خطا در گزارش حذف رسانه {msg_id}: {e}")
                    if msg_id in media_cache:
                        del media_cache[msg_id]
            
            for (chat_id, cached_msg_id), text in list(message_cache.items()):
                if cached_msg_id == msg_id:
                    try:
                        sender_info = await self.get_user_info(chat_id)
                        chat_title = await self.get_chat_title(chat_id)
                        
                        report_text = (
                            f"🗑️ **پیام متنی حذف‌شده**\n"
                            f"👤 از: {sender_info}\n"
                            f"💬 چت: {chat_title}\n"
                            f"🆔 پیام: {msg_id}\n"
                            f"📝 **متن پیام:**\n`{text[:1000] or 'بدون متن'}`\n"
                            f"🕒 زمان: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                        )
                        
                        await self.send_report(report_text)
                        
                        del message_cache[(chat_id, msg_id)]
                        
                    except Exception as e:
                        logger.error(f"خطا در گزارش حذف پیام: {e}")
                        if (chat_id, msg_id) in message_cache:
                            del message_cache[(chat_id, msg_id)]
    
    def format_status_info(self, settings):
        try:
            conn = sqlite3.connect('main_database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM user_memory')
            user_count = cursor.fetchone()[0]
            conn.close()
        except:
            user_count = 0
        
        pv_enemies = len(db.get_enemies(self.user_id, 'pv'))
        
        comment_channels = len(db.get_auto_comments(self.user_id))
        
        cached_media = len([m for m in media_cache.values() if m.get('owner_id') == self.user_id])
        
        spam_settings = db.get_spam_settings(self.user_id)
        
        filter_words = db.get_filter_words(self.user_id)
        active_filters = len([w for w in filter_words if w['enabled']])
        
        spam_messages = len(db.get_enemy_spam_messages(self.user_id))
        
        font_info = "همه فونت‌ها" if self.time_font_indices == 'all' else f"فونت‌های {self.time_font_indices}"
        
        return f"""
📊 **وضعیت فعلی:**

↪️ حالت اتوسین: {'✅ فعال' if settings.get('autosend_mode') else '❌ غیرفعال'}
↪️ استایل متن: {settings.get('text_style') or '❌ غیرفعال'}
↪️ قفل پیوی همگانی: {'✅ فعال' if settings.get('pv_lock_all') else '❌ غیرفعال'}
↪️ فونت‌های تایم: {font_info}
↪️ تعداد دشمنان پیوی: {pv_enemies}
↪️ تعداد پی‌وی‌های قفل‌شده: {len(db.get_locked_pvs(self.user_id))}
↪️ گروه گزارش: {self.report_config.report_group_id}
↪️ کانال‌های نظر‌دهی: {comment_channels}
↪️ کاربران ذخیره شده: {user_count}
↪️ رسانه‌های ذخیره‌شده: {cached_media}
↪️ حفاظت اسپم: {'✅ فعال' if spam_settings.get('spam_protection') else '❌ غیرفعال'}
↪️ کلمات فیلتر فعال: {active_filters}
↪️ پیام‌های اسپم ذخیره شده: {spam_messages}
"""
    
    async def handle_commands(self, event):
        if event.sender_id != self.my_id:
            return
        
        command_text = event.text.strip()
        chat_id = None
        
        if isinstance(event.message.peer_id, PeerUser):
            chat_id = event.message.peer_id.user_id
        elif isinstance(event.message.peer_id, PeerChannel):
            chat_id = event.message.peer_id.channel_id
        elif isinstance(event.message.peer_id, PeerChat):
            chat_id = event.message.peer_id.chat_id
        
        match = re.match(r'^تایم\s+([\d\.]+)$', command_text)
        if match:
            indices_str = match.group(1)
            indices = []
            for part in indices_str.split('.'):
                try:
                    idx = int(part)
                    if 0 <= idx < len(classic_fonts):
                        indices.append(idx)
                except:
                    pass
            
            if indices:
                self.time_font_indices = indices
                db.update_selfbot_setting(self.user_id, 'time_font_indices', ','.join(map(str, indices)))
                await event.edit(f"✅ فونت‌های تایم تنظیم شد: {indices}")
            else:
                await event.edit(f"❌ ایندکس نامعتبر. محدوده مجاز: 0 تا {len(classic_fonts)-1}")
            return
        
        if command_text.startswith('پاسخ '):
            reply_text = command_text[5:].strip()
            if reply_text:
                db.update_selfbot_setting(self.user_id, 'auto_reply_text', reply_text)
                await event.edit(f"✅ متن پاسخ خودکار تنظیم شد:\n\n{reply_text}")
            else:
                await event.edit("❌ لطفاً متن پاسخ را وارد کنید")
            return
        
        elif command_text == 'پاسخ خودکار فعال':
            db.update_selfbot_setting(self.user_id, 'auto_reply_active', 1)
            settings = db.get_selfbot_settings(self.user_id)
            text = settings.get('auto_reply_text', 'تنظیم نشده')
            await event.edit(f"✅ پاسخ خودکار فعال شد\n📝 متن فعلی: {text}")
            return
        
        elif command_text == 'پاسخ خودکار غیرفعال':
            db.update_selfbot_setting(self.user_id, 'auto_reply_active', 0)
            await event.edit("❌ پاسخ خودکار غیرفعال شد")
            return
        
        if command_text.startswith('کپی @'):
            parts = command_text.split()
            if len(parts) >= 2:
                target_username = parts[1].replace('@', '')
                message_index = 1
                
                if len(parts) >= 3:
                    try:
                        message_index = int(parts[2])
                    except:
                        message_index = 1
                
                try:
                    entity = await self.client.get_entity(target_username)
                    
                    messages = []
                    async for message in self.client.iter_messages(entity, limit=message_index):
                        messages.append(message)
                    
                    if messages and len(messages) >= message_index:
                        target_message = messages[message_index - 1]
                        
                        if target_message.text:
                            db.save_copied_message(
                                self.user_id, 
                                entity.id, 
                                target_message.id, 
                                target_message.text,
                                target_username
                            )
                            
                            preview = target_message.text[:100] + "..." if len(target_message.text) > 100 else target_message.text
                            await event.edit(f"✅ پیام شماره {message_index} از آخر کپی شد:\n\n{preview}")
                        else:
                            await event.edit("❌ این پیام متن نداره")
                    else:
                        await event.edit(f"❌ کاربر {message_index} پیام نداره")
                        
                except Exception as e:
                    await event.edit(f"❌ خطا: {str(e)}")
            else:
                await event.edit("❌ فرمت صحیح: کپی @username [شماره]")
            return
        
        elif command_text == 'چسباندن':
            try:
                last_message = db.get_last_copied_message(self.user_id)
                
                if last_message:
                    await event.respond(last_message)
                    await event.delete()
                else:
                    await event.edit("❌ پیام کپی شده‌ای وجود نداره")
            except Exception as e:
                await event.edit(f"❌ خطا: {str(e)}")
            return
        
        if command_text == 'قلب پیشرفته':
            await event.delete()
            try:
                msg = await self.client.send_message(event.chat_id, "❤️ شروع انیمیشن قلب پیشرفته...")
                await advanced_heart_animation(msg)
            except Exception as e:
                logger.error(f"خطا در انیمیشن قلب پیشرفته: {e}")
            return
        
        if command_text == 'عشق':
            await event.delete()
            try:
                msg = await event.respond("💝 شروع انیمیشن عشق...")
                await advanced_heart_animation(msg)
            except Exception as e:
                logger.error(f"خطا در انیمیشن عشق: {e}")
            return
        
        if command_text == 'سنتت':
            await event.delete()
            try:
                msg = await event.respond("🕯️ در حال اجرای سنتت...")
                for i in range(101):
                    bar_len = int(i / 100 * 20)
                    bar = "█" * bar_len + "░" * (20 - bar_len)
                    await msg.edit(f"🕯️ **سنتت در حال اجرا...**\n\n`{i}% [{bar}]`")
                    await asyncio.sleep(0.03)
                await asyncio.sleep(1)
                await msg.edit("✅ **سنتت با موفقیت انجام شد! 🥴**")
            except Exception as e:
                logger.error(f"خطا در سنتت: {e}")
            return
        
        if command_text == 'هک':
            await event.delete()
            try:
                msg = await event.respond("🔍 Looking for WhatsApp databases in targeted person...")
                await asyncio.sleep(2)
                await msg.edit("User online: True\nTelegram access: True\nRead Storage: True")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]\n`Looking for WhatsApp...`\nETA: 0m, 20s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 11.07%\n[██░░░░░░░░░░░░░░░░░░]\n`Looking for WhatsApp...`\nETA: 0m, 18s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 20.63%\n[███░░░░░░░░░░░░░░░░░]\n`Found folder C:/WhatsApp`\nETA: 0m, 16s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 34.42%\n[█████░░░░░░░░░░░░░░░]\n`Found folder C:/WhatsApp`\nETA: 0m, 14s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 42.17%\n[███████░░░░░░░░░░░░░]\n`Searching for databases`\nETA: 0m, 12s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 55.30%\n[█████████░░░░░░░░░░░]\n`Found msgstore.db.crypt12`\nETA: 0m, 10s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 64.86%\n[███████████░░░░░░░░░]\n`Found msgstore.db.crypt12`\nETA: 0m, 08s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 74.02%\n[█████████████░░░░░░░]\n`Trying to Decrypt...`\nETA: 0m, 06s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 86.21%\n[███████████████░░░░░]\n`Trying to Decrypt...`\nETA: 0m, 04s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 93.50%\n[█████████████████░░░]\n`Decryption successful!`\nETA: 0m, 02s")
                await asyncio.sleep(2)
                await msg.edit("Hacking... 100%\n[████████████████████]\n`Scanning file...`\nETA: 0m, 00s")
                await asyncio.sleep(2)
                await msg.edit("Hacking complete!\nUploading file...")
                await asyncio.sleep(2)
                await msg.edit("✅ **Targeted Account Hacked!**\n\nFile: `./DOWNLOADS/msgstore.db.crypt12`")
            except Exception as e:
                logger.error(f"خطا در هک: {e}")
            return
        
        if command_text == 'شروع':
            await event.delete()
            try:
                await event.respond("🌟 سلف‌بات شروع شد!")
            except:
                pass
        
        elif command_text == 'تایم روشن':
            db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
            await self.update_profile_name()
            await event.delete()
        
        elif command_text == "تایمر پرچم روشن":
            db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 1)
            await self.update_profile_name()
            await event.delete()
        
        elif command_text == "تایم خاموش":
            db.update_selfbot_setting(self.user_id, 'time_enabled', 0)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
            await self.restore_profile_name()
            await event.delete()
        
        elif command_text == 'پینگ':
            await self.handle_ping_command(event)
        
        elif command_text == 'لیست دشمن':
            await self.handle_list_enemies_command(event)
        
        elif command_text == 'لیست اسپم':
            await self.handle_list_spam_command(event)
        
        elif command_text == 'پاک کردن اسپم':
            await self.handle_clear_spam_command(event)
        
        elif re.match(r'^حذف اسپم\s+(\d+)$', command_text):
            await self.handle_delete_spam_command(event)
        
        elif command_text == 'اضافه اسپم':
            await self.handle_add_spam_command(event)
        
        elif command_text == 'اتمام اسپم':
            await self.handle_end_spam_command(event)
        
        elif re.match(r'^تغییر اسم\s+(.+)$', event.text):
            await self.handle_change_name_command(event)
        
        elif re.match(r'^تغییر بیو\s+(.+)$', event.text):
            await self.handle_change_bio_command(event)
        
        elif command_text in ['تغییر پروفایل', 'پروف']:
            await self.handle_change_profile_command(event)
        
        elif re.match(r'^فیلتر\s+(.+)$', command_text) and command_text != 'فیلتر روشن' and command_text != 'فیلتر خاموش':
            await self.handle_filter_command(event)
        
        elif command_text == 'فیلتر روشن':
            await self.handle_filter_toggle_command(event, True)
        
        elif command_text == 'فیلتر خاموش':
            await self.handle_filter_toggle_command(event, False)
        
        elif command_text == 'لیست فیلتر':
            await self.handle_list_filters_command(event)
        
        elif re.match(r'^حذف فیلتر\s+(.+)$', command_text):
            await self.handle_remove_filter_command(event)
        
        elif command_text == 'اسپم روشن':
            await self.handle_spam_protection_command(event, True)
        
        elif command_text == 'اسپم خاموش':
            await self.handle_spam_protection_command(event, False)
        
        elif re.match(r'^تنظیم اسپم\s+(\d+)\s+(\d+)$', command_text):
            await self.handle_set_spam_settings_command(event)
        
        elif command_text == 'وضعیت اسپم':
            await self.handle_spam_status_command(event)
        
        elif re.match(r'^کامنت\s+(.+)$', event.text):
            await self.handle_comment_command(event)
        
        elif command_text == 'کانال‌ها':
            await self.handle_channels_command(event)
        
        elif command_text == 'حذف کانال':
            await self.handle_delete_channel_command(event)
        
        elif command_text == 'تست کانال':
            await self.handle_test_channel_command(event)
        
        elif command_text == 'دشمن گروه':
            await self.handle_group_enemy_command(event, 'add')
        
        elif command_text == 'دوست گروه':
            await self.handle_group_enemy_command(event, 'remove')
        
        elif re.match(r'^دشمن\s*(@\w+|-\d+|\d+)?$', command_text):
            await self.handle_enemy_command(event, 'add')
        
        elif re.match(r'^دوست\s*(@\w+|-\d+|\d+)?$', command_text):
            await self.handle_enemy_command(event, 'remove')
        
        elif re.match(r'^قفل پیوی\s*(@\w+|-\d+|\d+)?$', command_text):
            await self.handle_lock_pv_command(event, 'lock')
        
        elif re.match(r'^باز پی\s*(@\w+|-\d+|\d+)?$', command_text):
            await self.handle_lock_pv_command(event, 'unlock')
        
        elif command_text == "قفل پیوی همه":
            await self.handle_lock_all_pv_command(event, True)
        
        elif command_text == "باز پی همه":
            await self.handle_lock_all_pv_command(event, False)
        
        elif command_text == "قلب":
            await self.handle_heart_animation(event)
        
        elif command_text == "ماه":
            await self.handle_moon_animation(event)
        
        elif command_text in ["بولد روشن", "بولد خاموش", "زیرخط روشن", "زیرخط خاموش", 
                            "خط خورده روشن", "خط خورده خاموش", "نقل قول روشن", 
                            "نقل قول خاموش", "اسپویلر روشن", "اسپویلر خاموش",
                            "کج روشن", "کج خاموش", "کد روشن", "کد خاموش",
                            "پیش روشن", "پیش خاموش"]:
            await self.handle_text_style_command(event)
        
        elif command_text == "اطلاعات":
            await self.handle_info_command(event)
        
        elif command_text == "دانلود پروفایل":
            await self.handle_download_profile_command(event)
        
        elif command_text == "ست پروف":
            await self.handle_set_profile_command(event, 'photo')
        
        elif command_text == "ست بیو":
            await self.handle_set_profile_command(event, 'bio')
        
        elif command_text == "حذف ست پروف":
            await self.handle_delete_profile_command(event, 'photo')
        
        elif command_text == "حذف ست بیو":
            await self.handle_delete_profile_command(event, 'bio')
        
        elif command_text == "تاریخ کامل":
            await self.handle_full_date_command(event)
        
        elif command_text == "فعال اتوسین":
            await self.handle_autosend_command(event, True)
        
        elif command_text == "غیرفعال اتوسین":
            await self.handle_autosend_command(event, False)
        
        elif re.match(r'^حذف\s+(\d+)$', command_text) or command_text == "حذف کامل":
            await self.handle_delete_command(event)
        
        elif re.match(r'^اسپم\s+(\d+)\s+(.+)$', command_text):
            await self.handle_spam_command(event)
        
        elif command_text == "بلاک":
            await self.handle_block_command(event)
        
        elif re.match(r'^ریکت\s*([\U0001F300-\U0001F9FF]+)?$', command_text):
            await self.handle_reaction_command(event, 'set')
        
        elif command_text == "حذف ریکت":
            await self.handle_reaction_command(event, 'remove')
        
        elif command_text in ['پیوی ۱', 'پیوی ۲', 'پیوی ۳', 'خاموش پیوی']:
            await self.handle_ai_command(event, 'pm')
        
        elif command_text in ['گروه ۱', 'گروه ۲', 'گروه ۳', 'خاموش گروه']:
            await self.handle_ai_command(event, 'group')
        
        elif command_text == 'درباره':
            await event.delete()
        
        elif command_text == 'من کی ام':
            await self.handle_whoami_command(event)
        
        elif command_text.startswith('قفل ') and command_text.endswith('روشن'):
            await self.handle_media_lock_command(event, True)
        
        elif command_text.startswith('قفل ') and command_text.endswith('خاموش'):
            await self.handle_media_lock_command(event, False)
        
        elif command_text == "تنظیم گزارش":
            await self.handle_report_group_command(event, 'set')
        
        elif command_text == "گروه گزارش":
            await self.handle_report_group_command(event, 'get')
        
        elif command_text == 'سرچ':
            await self.handle_search_command(event)
        
        elif command_text == 'خروج سرچ':
            await self.handle_exit_search_command(event)
    
    async def handle_ping_command(self, event):
        try:
            start_time = time.time()
            message = await event.respond("🔄 در حال محاسبه پینگ...")
            end_time = time.time()
            ping_time = (end_time - start_time) * 1000
            
            await message.edit(f"🏓 **پینگ:** `{ping_time:.2f} ms`\n🕒 **زمان:** {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"خطا در پینگ: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_list_enemies_command(self, event):
        try:
            enemies = db.get_enemies(self.user_id, 'pv')
            
            if enemies:
                message = "📋 **لیست دشمنان:**\n\n"
                for i, enemy_id in enumerate(enemies, 1):
                    try:
                        enemy = await self.client.get_entity(enemy_id)
                        enemy_name = enemy.first_name or f"کاربر {enemy_id}"
                        message += f"{i}. **{enemy_name}** (`{enemy_id}`)\n"
                    except:
                        message += f"{i}. کاربر `{enemy_id}`\n"
                
                await event.edit(message)
            else:
                await event.edit("📭 لیست دشمنان خالی است.")
        except Exception as e:
            logger.error(f"خطا در نمایش لیست دشمنان: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_list_spam_command(self, event):
        try:
            spam_messages = db.get_enemy_spam_messages(self.user_id)
            
            if spam_messages:
                message = "📜 **لیست پیام‌های اسپم:**\n\n"
                for i, spam_msg in enumerate(spam_messages, 1):
                    message += f"{i}. {spam_msg['text']}\n"
                
                message += f"\n📊 **تعداد کل:** {len(spam_messages)}\n"
                message += "🗑️ برای حذف یک پیام: `حذف اسپم [شماره]`\n"
                message += "🧹 برای پاک کردن همه: `پاک کردن اسپم`"
                
                if len(message) > 4000:
                    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await event.edit(chunk)
                        else:
                            await event.respond(chunk)
                else:
                    await event.edit(message)
            else:
                await event.edit("📭 لیست پیام‌های اسپم خالی است.")
        except Exception as e:
            logger.error(f"خطا در نمایش لیست اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_clear_spam_command(self, event):
        try:
            db.clear_enemy_spam_messages(self.user_id)
            await event.edit("✅ **لیست پیام‌های اسپم پاک شد.**")
        except Exception as e:
            logger.error(f"خطا در پاک کردن اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_delete_spam_command(self, event):
        try:
            match = re.match(r'^حذف اسپم\s+(\d+)$', event.text.lower())
            message_id = int(match.group(1))
            
            spam_messages = db.get_enemy_spam_messages(self.user_id)
            
            if 1 <= message_id <= len(spam_messages):
                spam_msg = spam_messages[message_id - 1]
                db.delete_enemy_spam_message(self.user_id, spam_msg['id'])
                await event.edit(f"✅ **پیام اسپم شماره {message_id} حذف شد.**")
            else:
                await event.edit(f"⚠️ **پیام شماره {message_id} وجود ندارد.**\nتعداد پیام‌ها: {len(spam_messages)}")
        except Exception as e:
            logger.error(f"خطا در حذف اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_add_spam_command(self, event):
        try:
            self.adding_spam = True
            await event.edit("📝 **حالت اضافه کردن پیام اسپم فعال شد.**\n\nهر متنی که ارسال کنید به لیست اسپم اضافه می‌شود.\nبرای پایان، دستور `اتمام اسپم` را ارسال کنید.")
        except Exception as e:
            logger.error(f"خطا در شروع اضافه کردن اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_end_spam_command(self, event):
        try:
            self.adding_spam = False
            await event.edit("✅ **حالت اضافه کردن پیام اسپم غیرفعال شد.**")
        except Exception as e:
            logger.error(f"خطا در پایان اضافه کردن اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_change_name_command(self, event):
        try:
            match = re.match(r'^تغییر اسم\s+(.+)$', event.text)
            new_name = match.group(1)
            
            current_name = db.get_current_name(self.user_id)
            if not current_name:
                db.set_current_name(self.user_id, self.BASE_NAME)
                current_name = self.BASE_NAME
            
            db.set_current_name(self.user_id, new_name)
            
            await self.client(UpdateProfileRequest(first_name=new_name))
            
            settings = db.get_selfbot_settings(self.user_id)
            if settings.get('time_enabled'):
                self.BASE_NAME = new_name
                await self.update_profile_name()
            else:
                self.BASE_NAME = new_name
            
            await event.edit(f"✅ نام پروفایل به **{new_name}** تغییر کرد.")
        except Exception as e:
            logger.error(f"خطا در تغییر نام: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_change_bio_command(self, event):
        try:
            match = re.match(r'^تغییر بیو\s+(.+)$', event.text)
            new_bio = match.group(1)
            
            await self.client(UpdateProfileRequest(about=new_bio))
            
            await event.edit(f"✅ بیوگرافی به **{new_bio}** تغییر کرد.")
        except Exception as e:
            logger.error(f"خطا در تغییر بیو: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_change_profile_command(self, event):
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                
                if isinstance(reply_message.media, MessageMediaPhoto):
                    photo_path = await self.client.download_media(
                        reply_message.media,
                        file=f"{MEDIA_FOLDER}/profile_{self.user_id}.jpg"
                    )
                    
                    if photo_path and os.path.exists(photo_path):
                        me = await self.client.get_me()
                        if me.photo:
                            photos = await self.client.get_profile_photos(me.id, limit=1)
                            if photos:
                                await self.client(DeletePhotosRequest(id=[photos[0]]))
                        
                        file = await self.client.upload_file(photo_path)
                        await self.client(UploadProfilePhotoRequest(file=file))
                        
                        os.remove(photo_path)
                        
                        await event.edit("✅ عکس پروفایل تغییر کرد.")
                    else:
                        await event.edit("⚠️ خطا در دانلود عکس.")
                else:
                    await event.edit("⚠️ لطفاً روی یک عکس ریپلای کنید.")
            else:
                await event.edit("⚠️ لطفاً روی عکس مورد نظر ریپلای کنید و سپس دستور را بزنید.")
        except Exception as e:
            logger.error(f"خطا در تغییر پروفایل: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_filter_command(self, event):
        try:
            match = re.match(r'^فیلتر\s+(.+)$', event.text)
            word = match.group(1)
            
            db.add_filter_word(self.user_id, word)
            
            await event.edit(f"✅ کلمه `{word}` به لیست فیلتر اضافه شد.\n\nپیام‌های حاوی این کلمه حذف خواهند شد.")
        except Exception as e:
            logger.error(f"خطا در افزودن فیلتر: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_filter_toggle_command(self, event, enable):
        try:
            db.toggle_all_filters(self.user_id, enable)
            
            if enable:
                await event.edit("✅ **همه فیلترها فعال شدند.**\n\nپیام‌های حاوی کلمات فیلتر شده حذف خواهند شد.")
            else:
                await event.edit("✅ **همه فیلترها غیرفعال شدند.**")
        except Exception as e:
            logger.error(f"خطا در تغییر وضعیت فیلترها: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_list_filters_command(self, event):
        try:
            filters = db.get_filter_words(self.user_id)
            
            if filters:
                message_text = "📜 **لیست کلمات فیلتر شده:**\n\n"
                for i, word_info in enumerate(filters, 1):
                    status = "✅ فعال" if word_info['enabled'] else "❌ غیرفعال"
                    message_text += f"{i}. `{word_info['word']}` - {status}\n"
                
                await event.edit(message_text)
            else:
                await event.edit("📭 لیست کلمات فیلتر خالی است.")
        except Exception as e:
            logger.error(f"خطا در نمایش لیست فیلترها: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_remove_filter_command(self, event):
        try:
            match = re.match(r'^حذف فیلتر\s+(.+)$', event.text)
            word = match.group(1)
            
            db.remove_filter_word(self.user_id, word)
            
            await event.edit(f"✅ کلمه `{word}` از لیست فیلتر حذف شد.")
        except Exception as e:
            logger.error(f"خطا در حذف فیلتر: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_spam_protection_command(self, event, enable):
        try:
            db.set_spam_settings(self.user_id, spam_protection=1 if enable else 0)
            
            if enable:
                await event.edit("✅ **حفاظت اسپم فعال شد.**\n\nکاربرانی که پیام‌های زیادی ارسال کنند محدود خواهند شد.")
            else:
                await event.edit("✅ **حفاظت اسپم غیرفعال شد.**")
        except Exception as e:
            logger.error(f"خطا در تغییر وضعیت حفاظت اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_set_spam_settings_command(self, event):
        try:
            match = re.match(r'^تنظیم اسپم\s+(\d+)\s+(\d+)$', event.text.lower())
            limit = int(match.group(1))
            duration = int(match.group(2))
            
            if limit < 1 or limit > 50:
                await event.edit("⚠️ محدودیت نامعتبر است. باید بین 1 تا 50 باشد.")
                return
            
            if duration < 1 or duration > 60:
                await event.edit("⚠️ زمان سکوت نامعتبر است. باید بین 1 تا 60 ثانیه باشد.")
                return
            
            db.set_spam_settings(self.user_id, spam_limit=limit, mute_duration=duration)
            
            await event.edit(f"✅ **تنظیمات حفاظت اسپم به‌روز شد:**\n\n📊 محدودیت: `{limit} پیام`\n⏱️ زمان سکوت: `{duration} ثانیه`")
        except Exception as e:
            logger.error(f"خطا در تنظیم اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_spam_status_command(self, event):
        try:
            settings = db.get_spam_settings(self.user_id)
            
            status_text = f"""
🛡️ **وضعیت حفاظت اسپم:**

🔒 حفاظت: {'✅ فعال' if settings.get('spam_protection') else '❌ غیرفعال'}
📊 محدودیت: {settings.get('spam_limit', 10)} پیام
⏱️ زمان سکوت: {settings.get('mute_duration', 10)} ثانیه

📝 **توضیح:**
اگر کاربری در مدت کوتاهی بیش از {settings.get('spam_limit', 10)} پیام ارسال کند،
برای {settings.get('mute_duration', 10)} ثانیه سکوت می‌شود.
"""
            
            await event.edit(status_text)
        except Exception as e:
            logger.error(f"خطا در نمایش وضعیت اسپم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_search_command(self, event):
        try:
            self.search_mode = True
            await event.edit('🔍 **حالت سرچ فعال شد.**\n\nاکنون هر متنی که ارسال کنید در گوگل جستجو می‌شود.\nبرای خروج از حالت سرچ، دستور `خروج سرچ` را ارسال کنید.')
        except Exception as e:
            logger.error(f"خطا در فعال کردن حالت سرچ: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_exit_search_command(self, event):
        try:
            self.search_mode = False
            self.last_search_results = []
            await event.edit('✅ **حالت سرچ غیرفعال شد.**')
        except Exception as e:
            logger.error(f"خطا در غیرفعال کردن حالت سرچ: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_comment_command(self, event):
        try:
            comment_text = event.text[7:].strip()
            
            chat = await event.get_chat()
            
            chat_type = "کانال" if hasattr(chat, 'broadcast') and chat.broadcast else "گروه"
            
            db.set_auto_comment(
                self.user_id,
                chat.id,
                comment_text,
                chat.title,
                chat_type,
                getattr(chat, 'username', None)
            )
            
            logger.info(f"✅ کامنت تنظیم شد در {chat_type}: {chat.title}")
            
            try:
                await event.edit(comment_text)
                logger.info("✏️ پیام ویرایش شد")
            except:
                pass
                
        except Exception as e:
            logger.error(f"❌ خطا در تنظیم: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_channels_command(self, event):
        try:
            auto_comments = db.get_auto_comments(self.user_id)
            
            if auto_comments:
                msg = "📊 **کانال‌های تنظیم شده:**\n\n"
                for comment in auto_comments:
                    msg += f"• {comment['channel_title']} ({comment['channel_type']})\n"
                    msg += f"  آیدی: {comment['channel_id']}\n"
                    msg += f"  متن: {comment['comment_text'][:30]}...\n\n"
            else:
                msg = "📭 هیچ کانالی تنظیم نشده"
            
            await event.edit(msg)
        except Exception as e:
            logger.error(f"خطا در نمایش کانال‌ها: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_delete_channel_command(self, event):
        try:
            chat = await event.get_chat()
            channel_id = chat.id
            
            auto_comment = db.get_auto_comment(self.user_id, channel_id)
            
            if auto_comment:
                db.remove_auto_comment(self.user_id, channel_id)
                await event.edit(f"✅ تنظیمات {auto_comment['channel_title']} حذف شد ⏸️")
            else:
                await event.edit("⚠️ این کانال تنظیم نشده است.")
        except Exception as e:
            logger.error(f"خطا در حذف کانال: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_test_channel_command(self, event):
        try:
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                chat = await reply_msg.get_chat()
                msg = reply_msg
            else:
                chat = await event.get_chat()
                msg = event.message
            
            info = f"🔍 **اطلاعات تست:**\n\n"
            info += f"چت: {chat.title}\n"
            info += f"نوع: {'کانال' if hasattr(chat, 'broadcast') and chat.broadcast else 'گروه'}\n"
            info += f"آیدی: {chat.id}\n"
            
            auto_comment = db.get_auto_comment(self.user_id, chat.id)
            info += f"تنظیم شده: {'✅' if auto_comment else '❌'}\n"
            
            if auto_comment:
                info += f"متن: {auto_comment['comment_text'][:50]}...\n"
            
            info += f"\n📨 **اطلاعات پیام:**\n"
            info += f"پست کانال: {is_channel_post(msg)}\n"
            
            await event.edit(info)
                
        except Exception as e:
            logger.error(f"⚠️ خطای تست: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_group_enemy_command(self, event, action):
        try:
            if isinstance(event.message.peer_id, (PeerChannel, PeerChat)):
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    target_id = reply_message.sender_id
                    
                    group_id = event.message.peer_id.channel_id if isinstance(event.message.peer_id, PeerChannel) else event.message.peer_id.chat_id
                    
                    if action == 'add':
                        db.add_enemy(self.user_id, target_id, 'group', group_id)
                        await event.edit(f"✅ کاربر به دشمنان گروه اضافه شد 🥷")
                        await self.spam_in_group(group_id, target_id)
                    else:
                        db.remove_enemy(self.user_id, target_id, 'group', group_id)
                        await event.edit(f"✅ کاربر از دشمنان گروه حذف شد 🧸")
                        
                        if group_id in self.group_spam_tasks and target_id in self.group_spam_tasks[group_id]:
                            self.group_spam_tasks[group_id][target_id].cancel()
                            del self.group_spam_tasks[group_id][target_id]
                    
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید.")
            else:
                await event.edit("⚠️ این دستور فقط در گروه‌ها کار می‌کند.")
        except Exception as e:
            logger.error(f"خطا در {action} دشمن گروه: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_enemy_command(self, event, action):
        try:
            target_id = await get_target_user(event, self.client)
            if target_id:
                if action == 'add':
                    db.add_enemy(self.user_id, target_id, 'pv')
                    await event.edit(f"✅ دشمن🥷")
                    await self.spam_enemy(target_id)
                else:
                    db.remove_enemy(self.user_id, target_id, 'pv')
                    await event.edit(f"✅ دوست 🧸")
                    
                    if target_id in self.spam_tasks:
                        self.spam_tasks[target_id].cancel()
                        del self.spam_tasks[target_id]
            else:
                await event.edit("⚠️ کاربر هدف مشخص نشد. روی پیامش ریپلای کنید یا از یوزرنیم/آیدی استفاده کنید.")
        except Exception as e:
            logger.error(f"خطا در {action} دشمن: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_lock_pv_command(self, event, action):
        try:
            target_id = await get_target_user(event, self.client)
            if target_id:
                if action == 'lock':
                    db.add_locked_pv(self.user_id, target_id)
                    await event.edit(f"✅ قفل شد✓")
                else:
                    db.remove_locked_pv(self.user_id, target_id)
                    await event.edit(f"✅ باز شد✓")
            else:
                await event.edit("⚠️ کاربر هدف مشخص نشد. روی پیامش ریپلای کنید یا از یوزرنیم/آیدی استفاده کنید.")
        except Exception as e:
            logger.error(f"خطا در {action} پیوی: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_lock_all_pv_command(self, event, lock):
        try:
            db.update_selfbot_setting(self.user_id, 'pv_lock_all', 1 if lock else 0)
            
            if lock:
                await event.edit("✅ قفل پیوی همگانی فعال شد 🔒\n\nاز این پس همه پیام‌های دریافتی در پی‌وی حذف خواهند شد.")
            else:
                await event.edit("✅ قفل پیوی همگانی غیرفعال شد 🔓\n\nپیام‌های دریافتی در پی‌وی دیگر حذف نمی‌شوند.")
        except Exception as e:
            logger.error(f"خطا در قفل پیوی همگانی: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_heart_animation(self, event):
        try:
            await event.delete()
            await self.heart_animation(event.chat_id)
        except Exception as e:
            logger.error(f"خطا در انیمیشن قلب: {e}")
    
    async def handle_moon_animation(self, event):
        try:
            await event.delete()
            await self.moon_animation(event.chat_id)
        except Exception as e:
            logger.error(f"خطا در انیمیشن ماه: {e}")
    
    async def handle_text_style_command(self, event):
        try:
            command_text = event.text.lower()
            style = command_text.split()[0]
            is_on = "روشن" in command_text
            
            if is_on:
                db.update_selfbot_setting(self.user_id, 'text_style', style)
                await event.edit(f"✅ استایل {style} فعال شد 📝")
            else:
                settings = db.get_selfbot_settings(self.user_id)
                if settings.get('text_style') == style:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.edit(f"✅ استایل {style} غیرفعال شد 📝")
                else:
                    await event.edit(f"⚠️ استایل {style} فعال نیست.")
        except Exception as e:
            logger.error(f"خطا در استایل متن: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_info_command(self, event):
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                user = await reply_message.get_sender()
            else:
                user = await self.client.get_me()
            
            username = f"@{user.username}" if user.username else "ندارد"
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "ندارد"
            
            try:
                full_user = await self.client(GetFullUserRequest(user.id))
                bio = full_user.full_user.about or "ندارد"
            except:
                bio = "ندارد"
            
            user_id = user.id
            
            try:
                photos = await self.client(GetUserPhotosRequest(user_id=user.id, offset=0, max_id=0, limit=1))
                photo_count = len(photos.photos) if photos.photos else 0
            except:
                photo_count = 0
            
            info_text = f"📋 **اطلاعات کاربر:**\n\n"
            info_text += f"👤 یوزرنیم: {username}\n"
            info_text += f"🆔 ID عددی: {user_id}\n"
            info_text += f"📛 نام: {name}\n"
            info_text += f"📝 بیو: {bio}\n"
            info_text += f"📸 تعداد عکس‌های پروفایل: {photo_count}"
            
            if user.photo:
                try:
                    photo = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user_id}.jpg")
                    if photo:
                        await self.client.send_file(event.chat_id, photo, caption=info_text)
                        if os.path.exists(photo):
                            os.remove(photo)
                    else:
                        await event.edit(info_text + "\n\n📸 عکس پروفایل: خطا در دانلود")
                except:
                    await event.edit(info_text + "\n\n📸 عکس پروفایل: خطا در دانلود")
            else:
                await event.edit(info_text + "\n\n📸 عکس پروفایل: ندارد")
            
            await event.delete()
            
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات: {str(e)}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_download_profile_command(self, event):
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                user = await reply_message.get_sender()
            else:
                user = await self.client.get_me()
            
            user_id = user.id
            user_name = user.first_name or user.username or "کاربر"
            
            if user.photo:
                try:
                    photo = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user_id}.jpg")
                    if photo and os.path.exists(photo):
                        await self.client.send_file(event.chat_id, photo, caption=f"📸 پروفایل {user_name}")
                        os.remove(photo)
                    else:
                        await event.edit(f"⚠️ خطا در دانلود عکس پروفایل {user_name}")
                except:
                    await event.edit(f"⚠️ خطا در دانلود عکس پروفایل {user_name}")
            else:
                await event.edit(f"⚠️ عکس پروفایلی برای {user_name} وجود ندارد")
            
            await event.delete()
            
        except Exception as e:
            logger.error(f"خطا در دانلود پروفایل: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_set_profile_command(self, event, type_):
        try:
            if event.is_reply:
                reply_message = await event.get_reply_message()
                user = await reply_message.get_sender()
                
                if type_ == 'photo':
                    if user.photo:
                        photo_path = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user.id}.jpg")
                        if photo_path and os.path.exists(photo_path):
                            try:
                                me = await self.client.get_me()
                                if me.photo:
                                    photos = await self.client.get_profile_photos(me.id, limit=1)
                                    if photos:
                                        await self.client(DeletePhotosRequest(id=[photos[0]]))
                                
                                file = await self.client.upload_file(photo_path)
                                await self.client(UploadProfilePhotoRequest(file=file))
                                await event.edit("✅ عکس پروفایل ست شد 📸")
                                os.remove(photo_path)
                            except FloodWaitError as e:
                                await event.edit(f"⚠️ خطا: لطفاً {e.seconds} ثانیه صبر کنید.")
                            except:
                                await event.edit("⚠️ خطا در ست پروفایل")
                        else:
                            await event.edit("⚠️ خطا در دانلود عکس پروفایل.")
                    else:
                        await event.edit("⚠️ این کاربر عکس پروفایل ندارد.")
                else:
                    try:
                        full_user = await self.client(GetFullUserRequest(user.id))
                        bio = full_user.full_user.about or ""
                        await self.client(UpdateProfileRequest(about=bio))
                        await event.edit("✅ بیوگرافی ست شد ✏️")
                    except:
                        await event.edit("⚠️ خطا در ست بیو")
            else:
                await event.edit("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")
            
            await event.delete()
            
        except Exception as e:
            logger.error(f"خطا در ست {type_}: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_delete_profile_command(self, event, type_):
        try:
            if type_ == 'photo':
                me = await self.client.get_me()
                if me.photo:
                    try:
                        photos = await self.client.get_profile_photos(me.id, limit=1)
                        if photos:
                            await self.client(DeletePhotosRequest(id=[photos[0]]))
                        await event.edit("✅ عکس پروفایل حذف شد 🗑️")
                    except FloodWaitError as e:
                        await event.edit(f"⚠️ خطا: لطفاً {e.seconds} ثانیه صبر کنید.")
                    except:
                        await event.edit("⚠️ خطا در حذف عکس پروفایل")
                else:
                    await event.edit("⚠️ عکس پروفایلی وجود ندارد.")
            else:
                try:
                    await self.client(UpdateProfileRequest(about=""))
                    await event.edit("✅ بیوگرافی به حالت خالی بازگشت 🗑️")
                except:
                    await event.edit("⚠️ خطا در حذف بیوگرافی")
            
            await event.delete()
            
        except Exception as e:
            logger.error(f"خطا در حذف {type_}: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_full_date_command(self, event):
        try:
            date_info = get_full_date_info()
            settings = db.get_selfbot_settings(self.user_id)
            text, entities = await apply_text_style(date_info, settings.get('text_style'))
            await self.client.send_message(event.chat_id, text, formatting_entities=entities)
            await event.delete()
        except Exception as e:
            logger.error(f"خطا در تاریخ کامل: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_autosend_command(self, event, enable):
        try:
            db.update_selfbot_setting(self.user_id, 'autosend_mode', 1 if enable else 0)
            
            if enable:
                await event.edit("✅ حالت اتوسین فعال شد 👀")
            else:
                await event.edit("✅ حالت اتوسین غیرفعال شد 👀")
        except Exception as e:
            logger.error(f"خطا در اتوسین: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_delete_command(self, event):
        try:
            command_text = event.text.lower()
            
            if re.match(r'^حذف\s+(\d+)$', command_text):
                match = re.match(r'^حذف\s+(\d+)$', command_text)
                num_messages = int(match.group(1))
                
                messages = []
                async for msg in self.client.iter_messages(event.chat_id, limit=num_messages):
                    if msg.sender_id == self.my_id:
                        messages.append(msg.id)
                
                if messages:
                    await self.client.delete_messages(event.chat_id, messages)
                    await event.edit(f"✅ {len(messages)} پیام من حذف شد 🗑️")
                else:
                    await event.edit("⚠️ هیچ پیامی از شما برای حذف یافت نشد.")
            else:
                messages = []
                async for msg in self.client.iter_messages(event.chat_id, limit=None):
                    if msg.sender_id == self.my_id:
                        messages.append(msg.id)
                
                if messages:
                    await self.client.delete_messages(event.chat_id, messages)
                    await event.edit(f"✅ {len(messages)} پیام من حذف شدند 🗑️")
                else:
                    await event.edit("⚠️ هیچ پیامی از شما برای حذف یافت نشد.")
        except Exception as e:
            logger.error(f"خطا در حذف پیام‌ها: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_spam_command(self, event):
        try:
            match = re.match(r'^اسپم\s+(\d+)\s+(.+)$', event.text.lower())
            num = int(match.group(1))
            message = match.group(2)
            
            if event.is_reply:
                reply_message = await event.get_reply_message()
                message = reply_message.text or message
            
            for _ in range(num):
                settings = db.get_selfbot_settings(self.user_id)
                text, entities = await apply_text_style(message, settings.get('text_style'))
                await self.client.send_message(event.chat_id, text, formatting_entities=entities)
                await asyncio.sleep(0.05)
            
            await event.edit(f"✅ {num} پیام اسپم ارسال شد 📩")
        except Exception as e:
            logger.error(f"خطا در اسپم پیام: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_block_command(self, event):
        try:
            if isinstance(event.message.peer_id, PeerUser):
                target_id = event.message.peer_id.user_id
                await self.client(BlockRequest(id=target_id))
                await event.edit("✅ کاربر بلاک شد 🔒")
            else:
                await event.edit("⚠️ این دستور فقط در پی‌وی کار می‌کند.")
        except Exception as e:
            logger.error(f"خطا در بلاک سریع: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_reaction_command(self, event, action):
        try:
            chat_id = None
            if isinstance(event.message.peer_id, PeerUser):
                chat_id = event.message.peer_id.user_id
            elif isinstance(event.message.peer_id, PeerChannel):
                chat_id = event.message.peer_id.channel_id
            elif isinstance(event.message.peer_id, PeerChat):
                chat_id = event.message.peer_id.chat_id
            
            target_id = await get_target_user(event, self.client)
            
            if action == 'set':
                match = re.match(r'^ریکت\s*([\U0001F300-\U0001F9FF]+)?$', event.text.lower())
                emoji = match.group(1) if match and match.group(1) else None
                
                if not emoji:
                    await event.edit("⚠️ لطفاً یک ایموجی معتبر وارد کنید.")
                    return
                
                if emoji in ALLOWED_EMOJIS:
                    db.set_reaction(self.user_id, chat_id, target_id, emoji)
                    
                    await event.edit(f"✅ ریکت خودکار {emoji} برای کاربر {target_id} تنظیم شد.\n\nاز این به بعد به هر پیام این کاربر ریکت {emoji} زده می‌شود.")
                else:
                    await event.edit(f"⚠️ ایموجی {emoji} مجاز نیست.")
            
            else:
                if target_id:
                    db.remove_reaction(self.user_id, chat_id, target_id)
                    await event.edit(f"✅ ریکت خودکار برای کاربر {target_id} غیرفعال شد.")
                else:
                    await event.edit("⚠️ کاربر هدف مشخص نشد.")
        
        except Exception as e:
            logger.error(f"خطا در ریکشن: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_ai_command(self, event, ai_type):
        try:
            command_text = event.text.lower()
            settings = db.get_selfbot_settings(self.user_id)
            ai_status = settings.get('ai_status', {})
            
            if ai_type == 'pm':
                if command_text == 'پیوی ۱':
                    ai_status['ai_1_pm'] = True
                    ai_status['ai_2_pm'] = False
                    ai_status['ai_3_pm'] = False
                    message = '✅ **هوش ۱ در پی‌وی روشن شد**\n❌ هوش ۲ خاموش شد\n❌ هوش ۳ خاموش شد\n\nهوش ۱: ChatGPT رایگان'
                elif command_text == 'پیوی ۲':
                    ai_status['ai_1_pm'] = False
                    ai_status['ai_2_pm'] = True
                    ai_status['ai_3_pm'] = False
                    message = '❌ **هوش ۱ در پی‌وی خاموش شد**\n✅ هوش ۲ روشن شد\n❌ هوش ۳ خاموش شد\n\nهوش ۲: Paxsenix API'
                elif command_text == 'پیوی ۳':
                    ai_status['ai_1_pm'] = False
                    ai_status['ai_2_pm'] = False
                    ai_status['ai_3_pm'] = True
                    message = '❌ **هوش ۱ در پی‌وی خاموش شد**\n❌ هوش ۲ خاموش شد\n✅ هوش ۳ روشن شد\n\nهوش ۳: DeepSeek رایگان'
                else:
                    ai_status['ai_1_pm'] = False
                    ai_status['ai_2_pm'] = False
                    ai_status['ai_3_pm'] = False
                    message = '✅ **همه هوش‌های مصنوعی در پی‌وی خاموش شدند**'
            else:
                if command_text == 'گروه ۱':
                    ai_status['ai_1_group'] = True
                    ai_status['ai_2_group'] = False
                    ai_status['ai_3_group'] = False
                    message = '✅ **هوش ۱ در گروه روشن شد**\n❌ هوش ۲ خاموش شد\n❌ هوش ۳ خاموش شد\n\nهوش ۱: ChatGPT رایگان'
                elif command_text == 'گروه ۲':
                    ai_status['ai_1_group'] = False
                    ai_status['ai_2_group'] = True
                    ai_status['ai_3_group'] = False
                    message = '❌ **هوش ۱ در گروه خاموش شد**\n✅ هوش ۲ روشن شد\n❌ هوش ۳ خاموش شد\n\nهوش ۲: Paxsenix API'
                elif command_text == 'گروه ۳':
                    ai_status['ai_1_group'] = False
                    ai_status['ai_2_group'] = False
                    ai_status['ai_3_group'] = True
                    message = '❌ **هوش ۱ در گروه خاموش شد**\n❌ هوش ۲ خاموش شد\n✅ هوش ۳ روشن شد\n\nهوش ۳: DeepSeek رایگان'
                else:
                    ai_status['ai_1_group'] = False
                    ai_status['ai_2_group'] = False
                    ai_status['ai_3_group'] = False
                    message = '✅ **همه هوش‌های مصنوعی در گروه خاموش شدند**'
            
            db.update_ai_status(self.user_id, ai_status)
            await event.edit(message)
        
        except Exception as e:
            logger.error(f"خطا در دستور هوش مصنوعی: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_whoami_command(self, event):
        try:
            if isinstance(event.message.peer_id, PeerUser):
                user_id = event.sender_id
                user_name = db.get_user_name(user_id)
                user_info = db.get_user_info(user_id)
                
                info_text = f"👤 **اطلاعات شما:**\n"
                info_text += f"• نام: {user_name}\n"
                info_text += f"• آی‌دی: {user_id}\n"
                
                if user_info:
                    info_text += f"\n📝 **اطلاعات ذخیره شده:**\n"
                    for key, value in user_info.items():
                        info_text += f"• {key}: {value}\n"
                else:
                    info_text += f"\nℹ️ هیچ اطلاعات اضافی ذخیره نشده است.\n"
                
                await event.edit(info_text)
        except Exception as e:
            logger.error(f"خطا در نمایش اطلاعات کاربر: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_media_lock_command(self, event, enable):
        try:
            command_text = event.text.lower()
            
            lock_type = None
            if 'لینک' in command_text:
                lock_type = 'lock_link'
            elif 'عکس' in command_text:
                lock_type = 'lock_photo'
            elif 'ویدیو' in command_text:
                lock_type = 'lock_video'
            elif 'استیکر' in command_text:
                lock_type = 'lock_sticker'
            elif 'گیف' in command_text:
                lock_type = 'lock_gif'
            elif 'ایموجی' in command_text and 'پرمیوم' not in command_text:
                lock_type = 'lock_emoji'
            elif 'ایموجی پرمیوم' in command_text:
                lock_type = 'lock_emoji_premium'
            
            if lock_type:
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    target_id = reply_message.sender_id
                    db.set_media_lock(self.user_id, target_id, lock_type, 1 if enable else 0)
                    lock_names = {
                        'lock_link': 'لینک',
                        'lock_photo': 'عکس',
                        'lock_video': 'ویدیو',
                        'lock_sticker': 'استیکر',
                        'lock_gif': 'گیف',
                        'lock_emoji': 'ایموجی معمولی',
                        'lock_emoji_premium': 'ایموجی پرمیوم'
                    }
                    status = "فعال" if enable else "غیرفعال"
                    await event.edit(f"✅ قفل {lock_names[lock_type]} برای کاربر {target_id} {status} شد")
                else:
                    db.set_media_lock(self.user_id, 0, lock_type, 1 if enable else 0)
                    lock_names = {
                        'lock_link': 'لینک',
                        'lock_photo': 'عکس',
                        'lock_video': 'ویدیو',
                        'lock_sticker': 'استیکر',
                        'lock_gif': 'گیف',
                        'lock_emoji': 'ایموجی معمولی',
                        'lock_emoji_premium': 'ایموجی پرمیوم'
                    }
                    status = "فعال" if enable else "غیرفعال"
                    await event.edit(f"✅ قفل {lock_names[lock_type]} برای **همه کاربران** {status} شد")
            else:
                await event.edit("⚠️ نوع قفل نامعتبر است.")
        
        except Exception as e:
            logger.error(f"خطا در قفل رسانه: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_report_group_command(self, event, action):
        try:
            if action == 'set':
                if isinstance(event.message.peer_id, (PeerChannel, PeerChat)):
                    chat_id = event.message.peer_id.channel_id if isinstance(event.message.peer_id, PeerChannel) else event.message.peer_id.chat_id
                    self.report_config.set_report_group(chat_id)
                    await event.edit(f"✅ گروه گزارش تنظیم شد 📍\n\nآیدی گروه: `{chat_id}`")
                else:
                    await event.edit("⚠️ این دستور فقط در گروه‌ها کار می‌کند.")
            else:
                await event.edit(f"📍 **گروه گزارش فعلی:**\nآیدی: `{self.report_config.report_group_id}`")
        
        except Exception as e:
            logger.error(f"خطا در گروه گزارش: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_outgoing_message(self, event):
        message_text = event.text or ""
        
        if self.adding_spam and message_text and not message_text.startswith(('لیست', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'درباره', 'من کی ام', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'فیلتر', 'فیلتر روشن', 'فیلتر خاموش', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ', 'پاسخ', 'پاسخ خودکار فعال', 'پاسخ خودکار غیرفعال', 'کپی', 'چسباندن', 'قلب پیشرفته', 'عشق', 'سنتت', 'هک')):
            db.add_enemy_spam_message(self.user_id, message_text)
            try:
                await event.delete()
            except:
                pass
            return
        
        if event.text:
            settings = db.get_selfbot_settings(self.user_id)
            text_style = settings.get('text_style')
            
            if text_style and not message_text.startswith(('/','لیست','شروع','تایم','قلب','ماه','اطلاعات','دانلود','تاریخ','فعال','غیرفعال','حذف','ست','بولد','زیرخط','خط خورده','نقل قول','اسپویلر','کج','کد','پیش','اسپم','بلاک','ریکت','پیوی','گروه','درباره','من کی ام','قفل','باز','تنظیم','گروه گزارش','دشمن','دوست','کانال','کامنت','تست','لیست دشمن','لیست اسپم','پاک کردن اسپم','حذف اسپم','اضافه اسپم','اتمام اسپم','تغییر اسم','تغییر بیو','تغییر پروفایل','پروف','فیلتر','فیلتر روشن','فیلتر خاموش','اسپم روشن','اسپم خاموش','پینگ','سرچ','خروج سرچ','پاسخ','پاسخ خودکار فعال','پاسخ خودکار غیرفعال','کپی','چسباندن','قلب پیشرفته','عشق','سنتت','هک')):
                try:
                    text, entities = await apply_text_style(message_text, text_style)
                    if entities:
                        await event.message.edit(text, formatting_entities=entities)
                except:
                    pass
        
        if self.search_mode and message_text and not message_text.startswith(('لیست', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'درباره', 'من کی ام', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'فیلتر', 'فیلتر روشن', 'فیلتر خاموش', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ', 'پاسخ', 'پاسخ خودکار فعال', 'پاسخ خودکار غیرفعال', 'کپی', 'چسباندن', 'قلب پیشرفته', 'عشق', 'سنتت', 'هک')):
            await self.handle_google_search(event, message_text)
            return
        
        if event.text:
            translated_text = await self.translate_text(event.text)
            if translated_text != event.text:
                try:
                    await event.edit(translated_text)
                except:
                    pass
    
    async def spam_enemy(self, enemy_id):
        if enemy_id in self.spam_tasks:
            return
        
        async def spam_task():
            while db.is_enemy(self.user_id, enemy_id, 'pv'):
                spam_messages = db.get_enemy_spam_messages(self.user_id)
                
                if spam_messages:
                    for spam_message in spam_messages:
                        try:
                            settings = db.get_selfbot_settings(self.user_id)
                            text, entities = await apply_text_style(spam_message['text'], settings.get('text_style'))
                            await self.client.send_message(enemy_id, text, formatting_entities=entities)
                        except:
                            pass
                        await asyncio.sleep(1)
                else:
                    for spam_message in SPAM_MESSAGES:
                        try:
                            settings = db.get_selfbot_settings(self.user_id)
                            text, entities = await apply_text_style(spam_message, settings.get('text_style'))
                            await self.client.send_message(enemy_id, text, formatting_entities=entities)
                        except:
                            pass
                        await asyncio.sleep(1)
        
        self.spam_tasks[enemy_id] = asyncio.create_task(spam_task())
    
    async def spam_in_group(self, group_id, user_id):
        if group_id not in self.group_spam_tasks:
            self.group_spam_tasks[group_id] = {}
        
        if user_id in self.group_spam_tasks[group_id]:
            return
        
        async def spam_group_task():
            while db.is_enemy(self.user_id, user_id, 'group', group_id):
                try:
                    entity = await self.client.get_entity(group_id)
                    async for message in self.client.iter_messages(entity, limit=100):
                        if message.sender_id == user_id and message.text:
                            spam_messages = db.get_enemy_spam_messages(self.user_id)
                            
                            if spam_messages:
                                spam_msg = spam_messages[0]['text']
                            else:
                                spam_msg = SPAM_MESSAGES[0]
                                
                            try:
                                await message.reply(spam_msg)
                                break
                            except:
                                pass
                    await asyncio.sleep(1)
                except:
                    await asyncio.sleep(1)
        
        self.group_spam_tasks[group_id][user_id] = asyncio.create_task(spam_group_task())
    
    async def update_profile_name(self):
        settings = db.get_selfbot_settings(self.user_id)
        
        if settings.get('time_enabled'):
            now = datetime.now()
            current_minute = now.minute
            
            if self.time_font_indices == 'all':
                font_index = current_minute % len(classic_fonts)
                font = classic_fonts[font_index]
            elif isinstance(self.time_font_indices, list) and self.time_font_indices:
                if hasattr(self, 'time_font_cycle'):
                    self.time_font_cycle = (self.time_font_cycle + 1) % len(self.time_font_indices)
                else:
                    self.time_font_cycle = 0
                font_index = self.time_font_indices[self.time_font_cycle]
                if font_index < len(classic_fonts):
                    font = classic_fonts[font_index]
                else:
                    font = classic_fonts[0]
            else:
                font = classic_fonts[0]
            
            time_now = now.strftime("%H:%M")
            time_now_classic = convert_to_classic_font(time_now, font_index if isinstance(font_index, int) else 0)
            
            try:
                current_name = db.get_current_name(self.user_id)
                if not current_name:
                    current_name = self.BASE_NAME
                
                if settings.get('flag_enabled'):
                    flag_index = current_minute % len(flags)
                    flag = flags[flag_index]
                    new_name = f"『 {flag} 』{current_name} {time_now_classic}"
                else:
                    new_name = f"{current_name} | {time_now_classic}"
                
                await self.client(UpdateProfileRequest(first_name=new_name))
            except:
                pass
    
    async def restore_profile_name(self):
        try:
            current_name = db.get_current_name(self.user_id)
            if current_name:
                await self.client(UpdateProfileRequest(first_name=current_name))
            else:
                original_name = db.get_original_name(self.user_id)
                if original_name:
                    await self.client(UpdateProfileRequest(first_name=original_name))
                    db.set_current_name(self.user_id, original_name)
                    self.BASE_NAME = original_name
        except:
            pass
    
    async def update_profile_task(self):
        while self.running:
            await self.update_profile_name()
            await asyncio.sleep(60)
    
    async def heart_animation(self, chat_id):
        try:
            message = await self.client.send_message(chat_id, HEARTS[0])
            for i in range(1, len(HEARTS) * 99999):
                await asyncio.sleep(4)
                await self.client.edit_message(chat_id, message, HEARTS[i % len(HEARTS)])
            
            settings = db.get_selfbot_settings(self.user_id)
            if chat_id != abs(self.report_config.report_group_id):
                await self.client.delete_messages(chat_id, message)
        except:
            pass
    
    async def moon_animation(self, chat_id):
        try:
            message = await self.client.send_message(chat_id, MOONS[0])
            for i in range(1, len(MOONS) * 1):
                await asyncio.sleep(3)
                await self.client.edit_message(chat_id, message, MOONS[i % len(MOONS)])
            
            settings = db.get_selfbot_settings(self.user_id)
            if chat_id != abs(self.report_config.report_group_id):
                await self.client.delete_messages(chat_id, message)
        except:
            pass

# ========== توابع کیبورد ==========
def get_main_panel_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🕐 زمان و پروفایل", callback_data=f"time_menu_{user_id}"),
            InlineKeyboardButton("❤️ انیمیشن", callback_data=f"animation_menu_{user_id}"),
            InlineKeyboardButton("👥 مدیریت کاربران", callback_data=f"user_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("🔒 قفل رسانه", callback_data=f"lock_menu_{user_id}"),
            InlineKeyboardButton("💬 کامنت", callback_data=f"comment_menu_{user_id}"),
            InlineKeyboardButton("📋 عمومی", callback_data=f"general_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("🎮 اکشن", callback_data=f"action_menu_{user_id}"),
            InlineKeyboardButton("🎲 بازی‌ها", callback_data=f"games_menu_{user_id}"),
            InlineKeyboardButton("🌐 ترجمه", callback_data=f"translate_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("🔍 گوگل", callback_data=f"google_menu_{user_id}"),
            InlineKeyboardButton("ℹ️ اطلاعاتی", callback_data=f"info_menu_{user_id}"),
            InlineKeyboardButton("📸 پروفایل", callback_data=f"profile_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("✍️ استایل متن", callback_data=f"style_menu_{user_id}"),
            InlineKeyboardButton("📨 مدیریت پیام", callback_data=f"message_menu_{user_id}"),
            InlineKeyboardButton("😊 ریکشن", callback_data=f"reaction_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("📩 اسپم", callback_data=f"spam_menu_{user_id}"),
            InlineKeyboardButton("✏️ تغییر پروفایل", callback_data=f"change_menu_{user_id}"),
            InlineKeyboardButton("🥷 مدیریت دشمنان", callback_data=f"enemy_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("🚫 فیلتر کلمات", callback_data=f"filter_menu_{user_id}"),
            InlineKeyboardButton("🛡️ حفاظت اسپم", callback_data=f"protection_menu_{user_id}"),
            InlineKeyboardButton("🤖 هوش مصنوعی", callback_data=f"ai_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("📊 گزارش", callback_data=f"report_menu_{user_id}"),
            InlineKeyboardButton("🤖 پاسخ خودکار", callback_data=f"autoreply_menu_{user_id}"),
            InlineKeyboardButton("📋 کپی/چسباندن", callback_data=f"copypaste_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("❌ بستن پنل", callback_data=f"close_panel")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_time_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🕐 تایم روشن", callback_data=f"exec_time_on_{user_id}"),
            InlineKeyboardButton("🏳️ تایمر پرچم", callback_data=f"exec_time_flag_{user_id}")
        ],
        [
            InlineKeyboardButton("🚫 تایم خاموش", callback_data=f"exec_time_off_{user_id}"),
            InlineKeyboardButton("📅 تاریخ کامل", callback_data=f"exec_full_date_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_animation_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("❤️ قلب", callback_data=f"exec_heart_{user_id}"),
            InlineKeyboardButton("🌙 ماه", callback_data=f"exec_moon_{user_id}")
        ],
        [
            InlineKeyboardButton("💖 قلب پیشرفته", callback_data=f"exec_advanced_heart_{user_id}"),
            InlineKeyboardButton("💝 عشق", callback_data=f"exec_love_{user_id}")
        ],
        [
            InlineKeyboardButton("🕯️ سنتت", callback_data=f"exec_santet_{user_id}"),
            InlineKeyboardButton("💻 هک", callback_data=f"exec_hack_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🥷 دشمن", callback_data=f"exec_enemy_{user_id}"),
            InlineKeyboardButton("🧸 دوست", callback_data=f"exec_friend_{user_id}"),
            InlineKeyboardButton("🥷 دشمن گروه", callback_data=f"exec_enemy_group_{user_id}")
        ],
        [
            InlineKeyboardButton("🧸 دوست گروه", callback_data=f"exec_friend_group_{user_id}"),
            InlineKeyboardButton("🔒 قفل پیوی", callback_data=f"exec_lock_pv_{user_id}"),
            InlineKeyboardButton("🔓 باز پی", callback_data=f"exec_unlock_pv_{user_id}")
        ],
        [
            InlineKeyboardButton("🔒 قفل پیوی همه", callback_data=f"exec_lock_all_{user_id}"),
            InlineKeyboardButton("🔓 باز پی همه", callback_data=f"exec_unlock_all_{user_id}"),
            InlineKeyboardButton("⛔ بلاک", callback_data=f"exec_block_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_lock_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🔗 قفل لینک", callback_data=f"exec_lock_link_{user_id}"),
            InlineKeyboardButton("📸 قفل عکس", callback_data=f"exec_lock_photo_{user_id}"),
            InlineKeyboardButton("🎥 قفل ویدیو", callback_data=f"exec_lock_video_{user_id}")
        ],
        [
            InlineKeyboardButton("🎨 قفل استیکر", callback_data=f"exec_lock_sticker_{user_id}"),
            InlineKeyboardButton("🎞️ قفل گیف", callback_data=f"exec_lock_gif_{user_id}"),
            InlineKeyboardButton("😀 قفل ایموجی", callback_data=f"exec_lock_emoji_{user_id}")
        ],
        [
            InlineKeyboardButton("💎 قفل ایموجی پرمیوم", callback_data=f"exec_lock_emoji_premium_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_comment_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("💬 کامنت", callback_data=f"exec_comment_{user_id}"),
            InlineKeyboardButton("📊 کانال‌ها", callback_data=f"exec_channels_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ حذف کانال", callback_data=f"exec_delete_channel_{user_id}"),
            InlineKeyboardButton("🔍 تست کانال", callback_data=f"exec_test_channel_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_general_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📊 وضعیت ۱", callback_data=f"exec_status_1_{user_id}"),
            InlineKeyboardButton("📊 وضعیت ۲", callback_data=f"exec_status_2_{user_id}"),
            InlineKeyboardButton("ℹ️ درباره", callback_data=f"exec_about_{user_id}")
        ],
        [
            InlineKeyboardButton("⏱️ پینگ", callback_data=f"exec_ping_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_action_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🎮 اکشن [نام]", callback_data=f"exec_action_{user_id}"),
            InlineKeyboardButton("⏹️ اکشن خاموش", callback_data=f"exec_action_off_{user_id}")
        ],
        [
            InlineKeyboardButton("📋 اکشن لیست", callback_data=f"exec_action_list_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_games_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🎲 تاس ۱", callback_data=f"exec_dice_1_{user_id}"),
            InlineKeyboardButton("🎲 تاس ۲", callback_data=f"exec_dice_2_{user_id}"),
            InlineKeyboardButton("🎲 تاس ۳", callback_data=f"exec_dice_3_{user_id}")
        ],
        [
            InlineKeyboardButton("🎲 تاس ۴", callback_data=f"exec_dice_4_{user_id}"),
            InlineKeyboardButton("🎲 تاس ۵", callback_data=f"exec_dice_5_{user_id}"),
            InlineKeyboardButton("🎲 تاس ۶", callback_data=f"exec_dice_6_{user_id}")
        ],
        [
            InlineKeyboardButton("🎯 دارت", callback_data=f"exec_dart_{user_id}"),
            InlineKeyboardButton("🏀 بسکتبال", callback_data=f"exec_basketball_{user_id}"),
            InlineKeyboardButton("⚽️ فوتبال", callback_data=f"exec_football_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_translate_menu_keyboard(user_id):
    translate_mode = {}
    if str(user_id) in selfbot_managers:
        translate_mode = selfbot_managers[str(user_id)].translate_mode
    
    keyboard = [
        [
            InlineKeyboardButton(f"🇬🇧 انگلیسی {'✅' if translate_mode.get('english') else '❌'}", callback_data=f"exec_translate_en_{user_id}"),
            InlineKeyboardButton(f"🇸🇦 عربی {'✅' if translate_mode.get('arabic') else '❌'}", callback_data=f"exec_translate_ar_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🇮🇱 عبری {'✅' if translate_mode.get('hebrew') else '❌'}", callback_data=f"exec_translate_he_{user_id}"),
            InlineKeyboardButton(f"🇷🇺 روسی {'✅' if translate_mode.get('russian') else '❌'}", callback_data=f"exec_translate_ru_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🇹🇷 ترکی {'✅' if translate_mode.get('turkish') else '❌'}", callback_data=f"exec_translate_tr_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_google_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🔍 سرچ", callback_data=f"exec_search_on_{user_id}"),
            InlineKeyboardButton("❌ خروج جستجو", callback_data=f"exec_search_off_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_info_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📋 اطلاعات", callback_data=f"exec_info_{user_id}"),
            InlineKeyboardButton("⬇️ دانلود پروفایل", callback_data=f"exec_download_profile_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_profile_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📸 ست پروف", callback_data=f"exec_set_profile_{user_id}"),
            InlineKeyboardButton("✏️ ست بیو", callback_data=f"exec_set_bio_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ حذف ست پروف", callback_data=f"exec_delete_profile_{user_id}"),
            InlineKeyboardButton("🗑️ حذف ست بیو", callback_data=f"exec_delete_bio_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_style_menu_keyboard(user_id):
    settings = db.get_selfbot_settings(user_id)
    current = settings.get('text_style', 'هیچ')
    
    keyboard = [
        [
            InlineKeyboardButton(f"بولد {'✅' if current == 'بولد' else '❌'}", callback_data=f"exec_bold_{user_id}"),
            InlineKeyboardButton(f"زیرخط {'✅' if current == 'زیرخط' else '❌'}", callback_data=f"exec_underline_{user_id}"),
            InlineKeyboardButton(f"خط خورده {'✅' if current == 'خط خورده' else '❌'}", callback_data=f"exec_strike_{user_id}")
        ],
        [
            InlineKeyboardButton(f"نقل قول {'✅' if current == 'نقل قول' else '❌'}", callback_data=f"exec_quote_{user_id}"),
            InlineKeyboardButton(f"اسپویلر {'✅' if current == 'اسپویلر' else '❌'}", callback_data=f"exec_spoiler_{user_id}"),
            InlineKeyboardButton(f"کج {'✅' if current == 'کج' else '❌'}", callback_data=f"exec_italic_{user_id}")
        ],
        [
            InlineKeyboardButton(f"کد {'✅' if current == 'کد' else '❌'}", callback_data=f"exec_code_{user_id}"),
            InlineKeyboardButton(f"پیش {'✅' if current == 'پیش' else '❌'}", callback_data=f"exec_pre_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_message_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🧹 حذف کامل", callback_data=f"exec_delete_all_{user_id}"),
            InlineKeyboardButton("🧹 حذف کامل ۵۰", callback_data=f"exec_delete_50_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ حذف ۱۰", callback_data=f"exec_delete_10_{user_id}"),
            InlineKeyboardButton("👁️ فعال اتوسین", callback_data=f"exec_autosend_on_{user_id}")
        ],
        [
            InlineKeyboardButton("🙈 غیرفعال اتوسین", callback_data=f"exec_autosend_off_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reaction_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("👍 ریکت", callback_data=f"exec_reaction_{user_id}"),
            InlineKeyboardButton("❌ حذف ریکت", callback_data=f"exec_reaction_off_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_spam_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📩 اسپم", callback_data=f"exec_spam_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_change_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("✏️ تغییر اسم", callback_data=f"exec_change_name_{user_id}"),
            InlineKeyboardButton("✏️ تغییر بیو", callback_data=f"exec_change_bio_{user_id}")
        ],
        [
            InlineKeyboardButton("📸 تغییر پروفایل", callback_data=f"exec_change_profile_{user_id}"),
            InlineKeyboardButton("📸 پروف", callback_data=f"exec_change_profile_alt_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_enemy_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📋 لیست دشمن", callback_data=f"exec_enemy_list_{user_id}"),
            InlineKeyboardButton("📝 اضافه اسپم", callback_data=f"exec_add_spam_{user_id}")
        ],
        [
            InlineKeyboardButton("✅ اتمام اسپم", callback_data=f"exec_end_spam_{user_id}"),
            InlineKeyboardButton("📜 لیست اسپم", callback_data=f"exec_spam_list_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ پاک کردن اسپم", callback_data=f"exec_clear_spam_{user_id}"),
            InlineKeyboardButton("🗑️ حذف اسپم", callback_data=f"exec_delete_spam_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_filter_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🚫 فیلتر [کلمه]", callback_data=f"exec_filter_word_{user_id}"),
            InlineKeyboardButton("✅ فیلتر روشن", callback_data=f"exec_filter_on_{user_id}")
        ],
        [
            InlineKeyboardButton("❌ فیلتر خاموش", callback_data=f"exec_filter_off_{user_id}"),
            InlineKeyboardButton("📜 لیست فیلتر", callback_data=f"exec_filter_list_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ حذف فیلتر", callback_data=f"exec_filter_remove_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_protection_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🛡️ اسپم روشن", callback_data=f"exec_spam_protection_on_{user_id}"),
            InlineKeyboardButton("🛡️ اسپم خاموش", callback_data=f"exec_spam_protection_off_{user_id}")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیم اسپم", callback_data=f"exec_spam_settings_{user_id}"),
            InlineKeyboardButton("📊 وضعیت اسپم", callback_data=f"exec_spam_status_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ai_menu_keyboard(user_id):
    settings = db.get_selfbot_settings(user_id)
    ai = settings['ai_status']
    
    keyboard = [
        [
            InlineKeyboardButton(f"🟢 پیوی ۱ {'✅' if ai['ai_1_pm'] else '❌'}", callback_data=f"exec_ai_pm_1_{user_id}"),
            InlineKeyboardButton(f"🔵 پیوی ۲ {'✅' if ai['ai_2_pm'] else '❌'}", callback_data=f"exec_ai_pm_2_{user_id}"),
            InlineKeyboardButton(f"🟣 پیوی ۳ {'✅' if ai['ai_3_pm'] else '❌'}", callback_data=f"exec_ai_pm_3_{user_id}")
        ],
        [
            InlineKeyboardButton("⚫ خاموش پیوی", callback_data=f"exec_ai_pm_off_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🟢 گروه ۱ {'✅' if ai['ai_1_group'] else '❌'}", callback_data=f"exec_ai_group_1_{user_id}"),
            InlineKeyboardButton(f"🔵 گروه ۲ {'✅' if ai['ai_2_group'] else '❌'}", callback_data=f"exec_ai_group_2_{user_id}"),
            InlineKeyboardButton(f"🟣 گروه ۳ {'✅' if ai['ai_3_group'] else '❌'}", callback_data=f"exec_ai_group_3_{user_id}")
        ],
        [
            InlineKeyboardButton("⚫ خاموش گروه", callback_data=f"exec_ai_group_off_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_report_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📍 تنظیم گزارش", callback_data=f"exec_set_report_{user_id}"),
            InlineKeyboardButton("ℹ️ گروه گزارش", callback_data=f"exec_show_report_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_autoreply_menu_keyboard(user_id):
    settings = db.get_selfbot_settings(user_id)
    auto_reply = settings.get('auto_reply', {})
    status = '✅ فعال' if auto_reply.get('active') else '❌ غیرفعال'
    text = auto_reply.get('text', 'تنظیم نشده')[:30]
    
    keyboard = [
        [
            InlineKeyboardButton("📝 تنظیم پاسخ", callback_data=f"exec_set_reply_{user_id}"),
            InlineKeyboardButton("✅ فعال کردن", callback_data=f"exec_reply_on_{user_id}")
        ],
        [
            InlineKeyboardButton("❌ غیرفعال کردن", callback_data=f"exec_reply_off_{user_id}"),
            InlineKeyboardButton("📋 نمایش متن", callback_data=f"exec_show_reply_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_copypaste_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📋 کپی پیام", callback_data=f"exec_copy_{user_id}"),
            InlineKeyboardButton("📎 چسباندن", callback_data=f"exec_paste_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== دیکشنری سلف‌بات‌ها ==========
selfbot_managers = {}

# ========== توابع پنل اینلاین ==========
async def inline_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    if not query:
        return
    
    user_id = query.from_user.id
    
    user_data = db.get_user(str(user_id))
    if not user_data or not user_data.get('self_active'):
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⛔ دسترسی محدود",
                description="شما عضو سرویس نیستید",
                input_message_content=InputTextMessageContent("⛔ **شما به این پنل دسترسی ندارید**\n\nبرای عضویت در سرویس، دستور /start را بزنید.")
            )
        ]
        await query.answer(results, cache_time=1, is_personal=True)
        return
    
    if not query.query:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🌟 پنل اصلی",
                description="مدیریت تمام قابلیت‌های سلف‌بات",
                input_message_content=InputTextMessageContent("🌟 **پنل سلف‌بات باز شد**\n\n⚠️ **توجه:** این پنل فقط مخصوص شماست.\nدیگران با کلیک روی دکمه‌ها محدودیت می‌خورند."),
                reply_markup=get_main_panel_keyboard(user_id)
            ),
        ]
        
        if user_id == ADMIN_ID:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="👑 پنل ادمین",
                    description="مدیریت کاربران و سلف‌بات‌ها",
                    input_message_content=InputTextMessageContent("👑 **پنل ادمین**"),
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"admin_requests"),
                            InlineKeyboardButton("🔐 منتظر ورود", callback_data=f"admin_login")
                        ],
                        [
                            InlineKeyboardButton("✅ کاربران فعال", callback_data=f"admin_active"),
                            InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data=f"admin_selfbots")
                        ],
                        [
                            InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats")
                        ],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
                    ])
                )
            )
    else:
        search = query.query.lower()
        results = []
        
        all_commands = [
            ("🕐 زمان و پروفایل", "time", "مدیریت زمان و پروفایل"),
            ("❤️ انیمیشن", "animation", "انیمیشن قلب و ماه و سنتت"),
            ("👥 مدیریت کاربران", "user", "مدیریت دشمن/دوست/بلاک"),
            ("🔒 قفل رسانه", "lock", "قفل لینک/عکس/ویدیو/استیکر"),
            ("💬 کامنت", "comment", "کامنت خودکار در کانال"),
            ("📋 عمومی", "general", "وضعیت/درباره/پینگ"),
            ("🎮 اکشن", "action", "اکشن‌های تایپ و ..."),
            ("🎲 بازی‌ها", "games", "تاس/دارت/بسکتبال/فوتبال"),
            ("🌐 ترجمه", "translate", "ترجمه به زبان‌های مختلف"),
            ("🔍 گوگل", "google", "جستجوی گوگل"),
            ("ℹ️ اطلاعاتی", "info", "اطلاعات کاربر و دانلود پروفایل"),
            ("📸 پروفایل", "profile", "کپی پروفایل و بیو"),
            ("✍️ استایل متن", "style", "بولد/زیرخط/خط خورده/..."),
            ("📨 مدیریت پیام", "message", "حذف پیام و اتوسین"),
            ("😊 ریکشن", "reaction", "ریکت خودکار"),
            ("📩 اسپم", "spam", "ارسال اسپم"),
            ("✏️ تغییر پروفایل", "change", "تغییر نام/بیو/پروفایل"),
            ("🥷 مدیریت دشمنان", "enemy", "لیست دشمن/اضافه اسپم"),
            ("🚫 فیلتر کلمات", "filter", "فیلتر کلمات"),
            ("🛡️ حفاظت اسپم", "protection", "محافظت در برابر اسپم"),
            ("🤖 هوش مصنوعی", "ai", "مدیریت هوش مصنوعی"),
            ("📊 گزارش", "report", "تنظیم گروه گزارش"),
            ("🤖 پاسخ خودکار", "autoreply", "پاسخ خودکار به پیام‌ها"),
            ("📋 کپی/چسباندن", "copypaste", "کپی و چسباندن پیام")
        ]
        
        for title, cmd, desc in all_commands:
            if search in title.lower() or search in desc.lower() or search in cmd.lower():
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title=title,
                        description=desc,
                        input_message_content=InputTextMessageContent(f"✅ **دستور {title} ارسال شد**"),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(f"ℹ️ توضیحات", callback_data=f"desc_{cmd}"),
                            InlineKeyboardButton(f"▶️ باز کردن", callback_data=f"menu_{cmd}")
                        ]])
                    )
                )
    
    await query.answer(results, cache_time=1, is_personal=True)

# هندلرهای عضویت
async def membership_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await query.edit_message_text("❌ خطا در دریافت اطلاعات")
        return
    
    if user_data.get('self_active'):
        await query.edit_message_text("✅ شما قبلاً عضو شده‌اید!")
        return
    
    if user_data.get('rejected'):
        await query.edit_message_text("❌ درخواست شما قبلاً رد شده است")
        return
    
    if user_data.get('request_sent'):
        await query.edit_message_text("⏳ درخواست شما در انتظار تأیید است")
        return
    
    db.update_user(user_id_str, request_sent=1, request_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    admin_text = f"""
📋 **درخواست عضویت جدید**
━━━━━━━━━━━━━━━━━━━━
👤 نام: {user_data['full_name']}
🆔 آیدی: {user_id_str}
👤 یوزرنیم: @{user_data['username'] if user_data['username'] else 'ندارد'}
📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
برای تأیید یا رد روی دکمه‌ها کلیک کنید.
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id_str}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id_str}")
        ]
    ])
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        reply_markup=keyboard
    )
    
    await query.edit_message_text(
        "✅ **درخواست عضویت شما با موفقیت ثبت شد!**\n\n"
        "⏳ لطفاً منتظر تأیید ادمین باشید.\n"
        "به محض تأیید، به شما اطلاع داده خواهد شد."
    )

async def membership_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await query.edit_message_text("👤 شما هنوز ثبت‌نام نکرده‌اید")
    elif user_data.get('self_active'):
        exp = user_data.get('expiration_date', 'نامشخص')
        await query.edit_message_text(f"✅ **شما عضو فعال هستید**\n\n📅 تاریخ انقضا: {exp}")
    elif user_data.get('admin_approved'):
        await query.edit_message_text("⏳ **در مرحله ورود اطلاعات**\n\nلطفاً شماره تلفن خود را وارد کنید.")
    elif user_data.get('request_sent'):
        await query.edit_message_text("⏳ **درخواست شما در انتظار تأیید است**")
    elif user_data.get('rejected'):
        await query.edit_message_text("❌ **درخواست شما رد شده است**")
    else:
        await query.edit_message_text("👤 **وضعیت عضویت شما مشخص نیست**\n\nلطفاً روی دکمه عضویت کلیک کنید.")

# هندلرهای پنل ادمین
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text("پنل واسه تو نیست دست نزن ")
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"admin_requests"),
            InlineKeyboardButton("🔐 منتظر ورود", callback_data=f"admin_login")
        ],
        [
            InlineKeyboardButton("✅ کاربران فعال", callback_data=f"admin_active"),
            InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data=f"admin_selfbots")
        ],
        [
            InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پنل اصلی", callback_data=f"back_main")]
    ])
    
    await query.edit_message_text(
        "👑 **پنل مدیریت**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=keyboard
    )

async def admin_requests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    pending = db.get_pending_requests()
    if pending:
        text = "📋 **درخواست‌های عضویت:**\n\n"
        keyboard = []
        for req in pending[:10]:
            text += f"👤 {req['full_name']}\n🆔 `{req['user_id']}`\n📅 {req.get('request_date', 'نامشخص')}\n\n"
            keyboard.append([
                InlineKeyboardButton(f"✅ تأیید {req['user_id']}", callback_data=f"approve_{req['user_id']}"),
                InlineKeyboardButton(f"❌ رد {req['user_id']}", callback_data=f"reject_{req['user_id']}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("📋 **درخواست‌های عضویت**\n\nهیچ درخواستی در انتظار نیست.")

async def admin_login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    pending = db.get_pending_login()
    if pending:
        text = "🔐 **کاربران در مرحله ورود:**\n\n"
        for user in pending[:10]:
            text += f"👤 {user['full_name']}\n🆔 `{user['user_id']}`\n📞 {user.get('phone', 'نامشخص')}\nمرحله: {user.get('step', 'نامشخص')}\n\n"
        await query.edit_message_text(text)
    else:
        await query.edit_message_text("🔐 **منتظر ورود**\n\nهیچ کاربری در مرحله ورود نیست.")

async def admin_active_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    active = db.get_active_users()
    if active:
        text = "✅ **کاربران فعال:**\n\n"
        for user in active[:10]:
            text += f"👤 {user['full_name']}\n🆔 `{user['user_id']}`\n📞 {user.get('phone', 'نامشخص')}\n📅 انقضا: {user.get('expiration_date', 'نامشخص')}\n"
            text += f"🤖 سلف‌بات: {'✅' if user['user_id'] in selfbot_managers else '❌'}\n\n"
        await query.edit_message_text(text)
    else:
        await query.edit_message_text("✅ **کاربران فعال**\n\nهیچ کاربر فعالی وجود ندارد.")

async def admin_selfbots_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    if selfbot_managers:
        text = "🤖 **سلف‌بات‌های فعال:**\n\n"
        keyboard = []
        for uid, manager in list(selfbot_managers.items())[:10]:
            user_data = db.get_user(uid)
            name = user_data['full_name'] if user_data else f"کاربر {uid}"
            text += f"👤 {name}\n🆔 `{uid}`\n\n"
            keyboard.append([
                InlineKeyboardButton(f"🛑 توقف {uid}", callback_data=f"stop_selfbot_{uid}"),
                InlineKeyboardButton(f"🔄 ریستارت {uid}", callback_data=f"restart_selfbot_{uid}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("🤖 **سلف‌بات‌های فعال**\n\nهیچ سلف‌باتی در حال اجرا نیست.")

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    total_users = len(db.get_active_users()) + len(db.get_pending_requests()) + len(db.get_pending_login())
    active_users = len(db.get_active_users())
    pending_requests = len(db.get_pending_requests())
    pending_login = len(db.get_pending_login())
    active_selfbots = len(selfbot_managers)
    
    stats = f"""
📊 **آمار کلی سیستم**
━━━━━━━━━━━━━━━━━━━━
👥 **کل کاربران:** {total_users}
✅ **کاربران فعال:** {active_users}
📋 **درخواست‌های عضویت:** {pending_requests}
🔐 **منتظر ورود:** {pending_login}
🤖 **سلف‌بات‌های فعال:** {active_selfbots}

🕐 **آخرین به‌روزرسانی:** {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
    """
    await query.edit_message_text(stats)

# ========== هندلرهای تأیید و رد ==========
async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[1]
    
    user_data = db.get_user(target_id)
    if not user_data:
        await query.answer("❌ کاربر یافت نشد!", show_alert=True)
        return
    
    db.update_user(target_id, admin_approved=1, activation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text="🎉 **درخواست عضویت شما تأیید شد!**\n\nلطفاً شماره تلفن خود را وارد کنید:\nمثال: +989123456789"
        )
        db.update_user(target_id, step='get_phone')
    except:
        pass
    
    await query.edit_message_text(f"✅ کاربر {target_id} تأیید شد")
    await query.message.delete()

async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[1]
    
    user_data = db.get_user(target_id)
    if not user_data:
        await query.answer("❌ کاربر یافت نشد!", show_alert=True)
        return
    
    db.update_user(target_id, rejected=1, request_sent=0)
    
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text="⚠ **درخواست عضویت شما رد شد.**\n\nمی‌توانید دوباره درخواست دهید."
        )
    except:
        pass
    
    await query.edit_message_text(f"❌ کاربر {target_id} رد شد")
    await query.message.delete()

# ========== هندلرهای سلف‌بات ==========
async def stop_selfbot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[2]
    
    if target_id in selfbot_managers:
        await selfbot_managers[target_id].stop()
        del selfbot_managers[target_id]
        await query.answer(f"✅ سلف‌بات کاربر {target_id} متوقف شد", show_alert=True)
    else:
        await query.answer("❌ سلف‌بات فعال نیست!", show_alert=True)

async def restart_selfbot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[2]
    
    user_data = db.get_user(target_id)
    if not user_data or not user_data.get('self_active'):
        await query.answer("❌ کاربر فعال نیست!", show_alert=True)
        return
    
    session_file = user_data.get('session_file')
    if not session_file or not os.path.exists(session_file):
        await query.answer("❌ فایل سشن یافت نشد!", show_alert=True)
        return
    
    if target_id in selfbot_managers:
        await selfbot_managers[target_id].stop()
        del selfbot_managers[target_id]
    
    manager = SelfBotManager(target_id)
    if await manager.start(session_file):
        selfbot_managers[target_id] = manager
        await query.answer(f"✅ سلف‌بات کاربر {target_id} راه‌اندازی مجدد شد", show_alert=True)
    else:
        await query.answer("❌ خطا در راه‌اندازی مجدد!", show_alert=True)

# ========== هندلرهای اجرای دستورات از پنل ==========
async def exec_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    if not data.startswith('exec_'):
        return
    
    await query.answer()
    
    parts = data.split('_')
    if len(parts) >= 2:
        owner_id = None
        for part in reversed(parts):
            if part.isdigit():
                owner_id = part
                break
        
        if owner_id and str(owner_id) != user_id_str:
            await query.answer("⛔ این پنل مال شما نیست!", show_alert=True)
            return
    
    if user_id_str not in selfbot_managers:
        await query.edit_message_text("❌ سلف‌بات شما فعال نیست! لطفاً ابتدا سلف‌بات را روشن کنید.")
        return
    
    manager = selfbot_managers[user_id_str]
    cmd = data.replace(f'exec_', '').replace(f'_{user_id}', '')
    
    msg = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"⏳ در حال اجرای دستور..."
    )
    
    if cmd == 'advanced_heart':
        await msg.edit_text("❤️ شروع انیمیشن قلب پیشرفته...")
        try:
            heart_msg = await manager.client.send_message(query.message.chat_id, "❤️ شروع...")
            await advanced_heart_animation(heart_msg)
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
    
    elif cmd == 'love':
        await msg.edit_text("💝 شروع انیمیشن عشق...")
        try:
            love_msg = await manager.client.send_message(query.message.chat_id, "💝 شروع...")
            await advanced_heart_animation(love_msg)
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
    
    elif cmd == 'santet':
        await msg.edit_text("🕯️ در حال اجرای سنتت...")
        try:
            santet_msg = await manager.client.send_message(query.message.chat_id, "🕯️ شروع...")
            for i in range(101):
                bar_len = int(i / 100 * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                await santet_msg.edit(f"🕯️ **سنتت در حال اجرا...**\n\n`{i}% [{bar}]`")
                await asyncio.sleep(0.03)
            await asyncio.sleep(1)
            await santet_msg.edit("✅ **سنتت با موفقیت انجام شد! 🥴**")
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
    
    elif cmd == 'hack':
        await msg.edit_text("💻 در حال اجرای هک...")
        try:
            hack_msg = await manager.client.send_message(query.message.chat_id, "💻 شروع...")
            await asyncio.sleep(2)
            await hack_msg.edit("User online: True\nTelegram access: True\nRead Storage: True")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]\n`Looking for WhatsApp...`\nETA: 0m, 20s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 11.07%\n[██░░░░░░░░░░░░░░░░░░]\n`Looking for WhatsApp...`\nETA: 0m, 18s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 20.63%\n[███░░░░░░░░░░░░░░░░░]\n`Found folder C:/WhatsApp`\nETA: 0m, 16s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 34.42%\n[█████░░░░░░░░░░░░░░░]\n`Found folder C:/WhatsApp`\nETA: 0m, 14s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 42.17%\n[███████░░░░░░░░░░░░░]\n`Searching for databases`\nETA: 0m, 12s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 55.30%\n[█████████░░░░░░░░░░░]\n`Found msgstore.db.crypt12`\nETA: 0m, 10s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 64.86%\n[███████████░░░░░░░░░]\n`Found msgstore.db.crypt12`\nETA: 0m, 08s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 74.02%\n[█████████████░░░░░░░]\n`Trying to Decrypt...`\nETA: 0m, 06s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 86.21%\n[███████████████░░░░░]\n`Trying to Decrypt...`\nETA: 0m, 04s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 93.50%\n[█████████████████░░░]\n`Decryption successful!`\nETA: 0m, 02s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 100%\n[████████████████████]\n`Scanning file...`\nETA: 0m, 00s")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking complete!\nUploading file...")
            await asyncio.sleep(2)
            await hack_msg.edit("✅ **Targeted Account Hacked!**\n\nFile: `./DOWNLOADS/msgstore.db.crypt12`")
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
    
    elif cmd == 'set_reply':
        await msg.edit_text("📝 برای تنظیم پاسخ خودکار، دستور زیر را ارسال کنید:\n\n`پاسخ [متن دلخواه]`")
    
    elif cmd == 'reply_on':
        db.update_selfbot_setting(user_id, 'auto_reply_active', 1)
        settings = db.get_selfbot_settings(user_id)
        text = settings.get('auto_reply_text', 'تنظیم نشده')
        await msg.edit_text(f"✅ پاسخ خودکار فعال شد\n📝 متن فعلی: {text}")
    
    elif cmd == 'reply_off':
        db.update_selfbot_setting(user_id, 'auto_reply_active', 0)
        await msg.edit_text("❌ پاسخ خودکار غیرفعال شد")
    
    elif cmd == 'show_reply':
        settings = db.get_selfbot_settings(user_id)
        auto_reply = settings.get('auto_reply', {})
        status = '✅ فعال' if auto_reply.get('active') else '❌ غیرفعال'
        text = auto_reply.get('text', 'تنظیم نشده')
        await msg.edit_text(f"🤖 **وضعیت پاسخ خودکار:**\n\n📊 وضعیت: {status}\n📝 متن پاسخ: {text}")
    
    elif cmd == 'copy':
        await msg.edit_text("📋 برای کپی کردن پیام از یک کاربر، دستور زیر را ارسال کنید:\n\n`کپی @username [شماره]`\n\nمثال: `کپی @ali 3`")
    
    elif cmd == 'paste':
        last_message = db.get_last_copied_message(user_id)
        if last_message:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=last_message
            )
            await msg.edit_text("📎 پیام چسبانده شد")
        else:
            await msg.edit_text("❌ پیام کپی شده‌ای وجود نداره")
    
    elif cmd == 'status_1':
        active_langs = []
        for lang, enabled in manager.translate_mode.items():
            if enabled:
                active_langs.append(lang)
        langs = ", ".join(active_langs) if active_langs else "هیچ"
        
        text = f"""
📊 **وضعیت ۱ - کلی:**
━━━━━━━━━━━━━━━━━━━━
📍 **مکان:** {'همه جا' if manager.mode == 'all' else 'فقط اینجا' if manager.mode == 'pv' else 'خاموش'}
🌐 **ترجمه فعال:** {langs}
🎲 **بازی تاس:** ✅ فعال
🔍 **حالت سرچ:** {'✅ فعال' if manager.search_mode else '❌ غیرفعال'}
💾 **حافظه:** فعال
🕐 **زمان:** {datetime.now().strftime("%H:%M:%S")}
━━━━━━━━━━━━━━━━━━━━
✅ **سلف بات فعال**
        """
        await msg.edit_text(text)
    
    elif cmd == 'status_2':
        settings = db.get_selfbot_settings(user_id)
        
        active_ai_pm = "هیچ هوش فعالی در پی‌وی وجود ندارد"
        if settings['ai_status']['ai_1_pm']:
            active_ai_pm = "هوش ۱ (ChatGPT رایگان)"
        elif settings['ai_status']['ai_2_pm']:
            active_ai_pm = "هوش ۲ (Paxsenix API)"
        elif settings['ai_status']['ai_3_pm']:
            active_ai_pm = "هوش ۳ (DeepSeek رایگان)"
        
        active_ai_group = "هیچ هوش فعالی در گروه وجود ندارد"
        if settings['ai_status']['ai_1_group']:
            active_ai_group = "هوش ۱ (ChatGPT رایگان)"
        elif settings['ai_status']['ai_2_group']:
            active_ai_group = "هوش ۲ (Paxsenix API)"
        elif settings['ai_status']['ai_3_group']:
            active_ai_group = "هوش ۳ (DeepSeek رایگان)"
        
        pv_enemies = len(db.get_enemies(user_id, 'pv'))
        
        cached_media = len([m for m in media_cache.values() if m.get('owner_id') == user_id])
        
        spam_settings = db.get_spam_settings(user_id)
        
        filter_words = db.get_filter_words(user_id)
        active_filters = len([w for w in filter_words if w['enabled']])
        
        spam_messages = len(db.get_enemy_spam_messages(user_id))
        
        auto_reply = settings.get('auto_reply', {})
        auto_reply_status = '✅ فعال' if auto_reply.get('active') else '❌ غیرفعال'
        
        font_info = "همه فونت‌ها" if manager.time_font_indices == 'all' else f"فونت‌های {manager.time_font_indices}"
        
        status_msg = f"""
📊 **وضعیت ۲ - کامل:**
━━━━━━━━━━━━━━━━━━━━
🤖 **هوش مصنوعی:**
• پی‌وی: {active_ai_pm}
• گروه: {active_ai_group}

🤖 **پاسخ خودکار:**
• وضعیت: {auto_reply_status}
• متن: {auto_reply.get('text', 'تنظیم نشده')[:30]}

🔒 **تنظیمات قفل:**
• قفل پیوی همگانی: {'✅ فعال' if settings.get('pv_lock_all') else '❌ غیرفعال'}
• دشمنان پیوی: {pv_enemies}
• پی‌وی‌های قفل‌شده: {len(db.get_locked_pvs(user_id))}

📊 **گزارش‌گیری:**
• گروه گزارش: {manager.report_config.report_group_id}
• رسانه‌های ذخیره‌شده: {cached_media}
• ذخیره خودکار: {'✅ فعال' if manager.report_config.auto_save_media else '❌ غیرفعال'}

🛡️ **حفاظت‌ها:**
• حفاظت اسپم: {'✅ فعال' if spam_settings.get('spam_protection') else '❌ غیرفعال'}
• کلمات فیلتر فعال: {active_filters}
• پیام‌های اسپم ذخیره شده: {spam_messages}

🎨 **فونت تایم:** {font_info}

📅 **آخرین به‌روزرسانی:** {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
✅ **Self-Bot v{BOT_VERSION}**
        """
        await msg.edit_text(status_msg)
    
    elif cmd == 'about':
        await msg.edit_text(f"ℹ️ درباره بات\n\n🤖 نسخه: v{BOT_VERSION}\n👨‍💻 سازنده: {BOT_CREATOR}")
    
    elif cmd == 'ping':
        start = time.time()
        await msg.edit_text("🏓 پینگ: ...")
        end = time.time()
        ping = round((end - start) * 1000, 2)
        await msg.edit_text(f"🏓 پینگ: {ping} ms")
    
    elif cmd.startswith('time_on'):
        db.update_selfbot_setting(user_id, 'time_enabled', 1)
        db.update_selfbot_setting(user_id, 'flag_enabled', 0)
        await manager.update_profile_name()
        await msg.edit_text("✅ تایم روشن شد")
    
    elif cmd.startswith('time_flag'):
        db.update_selfbot_setting(user_id, 'time_enabled', 1)
        db.update_selfbot_setting(user_id, 'flag_enabled', 1)
        await manager.update_profile_name()
        await msg.edit_text("✅ تایمر پرچم روشن شد")
    
    elif cmd.startswith('time_off'):
        db.update_selfbot_setting(user_id, 'time_enabled', 0)
        db.update_selfbot_setting(user_id, 'flag_enabled', 0)
        await manager.restore_profile_name()
        await msg.edit_text("✅ تایم خاموش شد")
    
    elif cmd.startswith('full_date'):
        await msg.edit_text(get_full_date_info())
    
    elif cmd.startswith('heart'):
        asyncio.create_task(manager.heart_animation(query.message.chat_id))
        await msg.edit_text("❤️ انیمیشن قلب شروع شد")
    
    elif cmd.startswith('moon'):
        asyncio.create_task(manager.moon_animation(query.message.chat_id))
        await msg.edit_text("🌙 انیمیشن ماه شروع شد")
    
    else:
        await msg.edit_text(f"✅ دستور {cmd} اجرا شد")

# ========== هندلر اصلی دکمه‌ها ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    if '_' in data and not data.startswith(('admin_', 'approve_', 'reject_', 'stop_selfbot_', 'restart_selfbot_')):
        parts = data.split('_')
        for part in parts:
            if part.isdigit() and len(part) >= 5:
                if part != user_id_str:
                    await query.answer("⛔ این پنل مال شما نیست!", show_alert=True)
                    return
                break
    
    if data == "close_panel":
        await query.delete_message()
        return
    
    if data == "back_main":
        await query.edit_message_text(
            "🌟 **پنل مدیریت سلف‌بات**\n\n⚠️ **توجه:** این پنل فقط مخصوص شماست.\nدیگران با کلیک روی دکمه‌ها محدودیت می‌خورند.",
            reply_markup=get_main_panel_keyboard(user_id)
        )
        return
    
    if data == "admin_panel":
        await admin_panel_handler(update, context)
        return
    
    if data == "admin_requests":
        await admin_requests_handler(update, context)
        return
    
    if data == "admin_login":
        await admin_login_handler(update, context)
        return
    
    if data == "admin_active":
        await admin_active_handler(update, context)
        return
    
    if data == "admin_selfbots":
        await admin_selfbots_handler(update, context)
        return
    
    if data == "admin_stats":
        await admin_stats_handler(update, context)
        return
    
    if data.startswith("approve_"):
        await approve_handler(update, context)
        return
    
    if data.startswith("reject_"):
        await reject_handler(update, context)
        return
    
    if data.startswith("stop_selfbot_"):
        await stop_selfbot_handler(update, context)
        return
    
    if data.startswith("restart_selfbot_"):
        await restart_selfbot_handler(update, context)
        return
    
    if data.startswith("membership_request_"):
        await membership_request_handler(update, context)
        return
    
    if data.startswith("membership_status_"):
        await membership_status_handler(update, context)
        return
    
    if data.startswith("admin_panel_"):
        await admin_panel_handler(update, context)
        return
    
    if data.startswith("exec_"):
        await exec_command_handler(update, context)
        return
    
    parts = data.split('_')
    if len(parts) > 1:
        action = parts[0]
        
        menu_keyboards = {
            "time": ("🕐 **دستورات زمان و پروفایل**\n\n• تایم روشن\n• تایمر پرچم روشن\n• تایم خاموش\n• تایم [اعداد] (تنظیم فونت دلخواه)\n• تاریخ کامل", get_time_menu_keyboard),
            "animation": ("❤️ **انیمیشن‌ها**\n\n• قلب\n• ماه\n• قلب پیشرفته\n• عشق\n• سنتت\n• هک", get_animation_menu_keyboard),
            "user": ("👥 **مدیریت کاربران**\n\n• دشمن (ریپلای)\n• دوست (ریپلای)\n• دشمن گروه (ریپلای)\n• دوست گروه (ریپلای)\n• قفل پیوی (ریپلای)\n• باز پی (ریپلای)\n• قفل پیوی همه\n• باز پی همه\n• بلاک", get_user_menu_keyboard),
            "lock": ("🔒 **قفل رسانه**\n\n⚠️ بدون نیاز به ریپلای:\n• قفل لینک روشن/خاموش\n• قفل عکس روشن/خاموش\n• قفل ویدیو روشن/خاموش\n• قفل استیکر روشن/خاموش\n• قفل گیف روشن/خاموش\n• قفل ایموجی روشن/خاموش\n• قفل ایموجی پرمیوم روشن/خاموش\n\n💡 با ریپلای روی پیام کاربر، قفل فقط برای آن کاربر فعال می‌شود.", get_lock_menu_keyboard),
            "comment": ("💬 **کامنت خودکار**\n\n• کامنت [متن]\n• کانال‌ها\n• حذف کانال\n• تست کانال", get_comment_menu_keyboard),
            "general": ("📋 **دستورات عمومی**\n\n• وضعیت ۱\n• وضعیت ۲\n• درباره\n• پینگ", get_general_menu_keyboard),
            "action": ("🎮 **اکشن‌ها**\n\n• اکشن [نام]\n• اکشن خاموش\n• اکشن لیست\n\nلیست اکشن‌ها:\n• تایپ\n• ویس\n• ویدیو\n• عکس\n• فیلم\n• فایل\n• بازی\n• استیکر\n• موقعیت\n• تماس\n• صحبت\n• لغو", get_action_menu_keyboard),
            "games": ("🎲 **بازی‌های تاس (چیت)**\n\n• تاس [1-6]\n• دارت\n• بسکتبال\n• فوتبال", get_games_menu_keyboard),
            "translate": ("🌐 **ترجمه خودکار**\n\n• انگلیسی روشن/خاموش\n• عربی روشن/خاموش\n• عبری روشن/خاموش\n• روسی روشن/خاموش\n• ترکی روشن/خاموش", get_translate_menu_keyboard),
            "google": ("🔍 **جستجوی گوگل**\n\n• سرچ [موضوع]\n• خروج جستجو", get_google_menu_keyboard),
            "info": ("ℹ️ **دستورات اطلاعاتی**\n\n• اطلاعات (ریپلای)\n• دانلود پروفایل (ریپلای)", get_info_menu_keyboard),
            "profile": ("📸 **مدیریت پروفایل**\n\n• ست پروف (ریپلای)\n• ست بیو (ریپلای)\n• حذف ست پروف\n• حذف ست بیو", get_profile_menu_keyboard),
            "style": ("✍️ **استایل متن**\n\n• بولد روشن/خاموش\n• زیرخط روشن/خاموش\n• خط خورده روشن/خاموش\n• نقل قول روشن/خاموش\n• اسپویلر روشن/خاموش\n• کج روشن/خاموش\n• کد روشن/خاموش\n• پیش روشن/خاموش", get_style_menu_keyboard),
            "message": ("📨 **مدیریت پیام**\n\n• حذف کامل\n• حذف کامل ۵۰\n• حذف ۱۰\n• فعال اتوسین\n• غیرفعال اتوسین", get_message_menu_keyboard),
            "reaction": ("😊 **ریکشن خودکار**\n\n• ریکت [ایموجی] (ریپلای)\n• حذف ریکت (ریپلای)", get_reaction_menu_keyboard),
            "spam": ("📩 **ارسال اسپم**\n\n• اسپم [تعداد] [متن]", get_spam_menu_keyboard),
            "change": ("✏️ **تغییر پروفایل**\n\n• تغییر اسم [نام]\n• تغییر بیو [متن]\n• تغییر پروفایل (ریپلای)\n• پروف (ریپلای)", get_change_menu_keyboard),
            "enemy": ("🥷 **مدیریت دشمنان**\n\n• لیست دشمن\n• اضافه اسپم\n• اتمام اسپم\n• لیست اسپم\n• پاک کردن اسپم\n• حذف اسپم [شماره]", get_enemy_menu_keyboard),
            "filter": ("🚫 **فیلتر کلمات**\n\n• فیلتر [کلمه]\n• فیلتر روشن\n• فیلتر خاموش\n• لیست فیلتر\n• حذف فیلتر [کلمه]", get_filter_menu_keyboard),
            "protection": ("🛡️ **حفاظت اسپم**\n\n• اسپم روشن\n• اسپم خاموش\n• تنظیم اسپم [تعداد] [زمان]\n• وضعیت اسپم", get_protection_menu_keyboard),
            "ai": ("🤖 **هوش مصنوعی**\n\n⚠️ توجه: هوش مصنوعی فقط به پیام‌هایی که خودتان دریافت می‌کنید پاسخ می‌دهد و روی سلف‌بات دیگران تأثیری ندارد.\n\n• پیوی ۱/۲/۳\n• خاموش پیوی\n• گروه ۱/۲/۳\n• خاموش گروه", get_ai_menu_keyboard),
            "report": ("📊 **گزارش**\n\n• تنظیم گزارش\n• گروه گزارش", get_report_menu_keyboard),
            "autoreply": ("🤖 **پاسخ خودکار**\n\n• تنظیم پاسخ [متن]\n• پاسخ خودکار فعال\n• پاسخ خودکار غیرفعال", get_autoreply_menu_keyboard),
            "copypaste": ("📋 **کپی و چسباندن**\n\n• کپی @آیدی_کاربر [شماره]\n• چسباندن", get_copypaste_menu_keyboard)
        }
        
        if action in menu_keyboards and parts[1] == "menu":
            text, keyboard_func = menu_keyboards[action]
            await query.edit_message_text(
                text,
                reply_markup=keyboard_func(user_id)
            )
            return

# ========== هندلرهای دستورات ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    user = update.effective_user
    user_id = str(user.id)
    
    full_name = user.full_name or "کاربر"
    username = user.username or ""
    db.add_user(user_id, full_name, username)
    
    user_data = db.get_user(user_id)
    if user_data and user_data.get('self_active'):
        text = f"""
👋 **سلام {full_name} عزیز!**

✅ حساب شما از قبل فعال است.
برای استفاده از سلف‌بات، از دستورات زیر استفاده کنید:
• /panel - باز کردن پنل مدیریت
• @{BOT_USERNAME} - استفاده از پنل اینلاین

⚠️ **توجه:** پنل فقط برای شماست و دیگران نمی‌توانند از دکمه‌های آن استفاده کنند.
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel")])
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    text = f"""
👋 **سلام {full_name} عزیز!**

🌟 به ربات سلف‌بات خوش آمدید.

📌 **برای استفاده از ربات، ابتدا باید عضو شوید:**
1️⃣ روی دکمه "عضویت" کلیک کنید
2️⃣ شماره تلفن خود را وارد کنید
3️⃣ کد تأیید را وارد کنید
4️⃣ سلف‌بات شما فعال می‌شود

✅ پس از فعال شدن، می‌توانید از دستورات زیر استفاده کنید:
• /panel - باز کردن پنل مدیریت
• @{BOT_USERNAME} - استفاده از پنل اینلاین

⚠️ **توجه:** پنل فقط برای شماست و دیگران نمی‌توانند از دکمه‌های آن استفاده کنند.
    """
    
    keyboard = [
        [InlineKeyboardButton("📝 عضویت", callback_data=f"membership_request_{user_id}")],
        [InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    user_id = update.effective_user.id
    
    user_data = db.get_user(str(user_id))
    if not user_data or not user_data.get('self_active'):
        await update.message.reply_text("⛔ شما عضو سرویس نیستید")
        return
    
    try:
        await update.message.delete()
    except:
        pass
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 باز کردن پنل اینلاین", switch_inline_query_current_chat="")]
    ])
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🌟 **پنل مدیریت سلف‌بات**\n\nبرای باز کردن پنل، روی دکمه زیر کلیک کنید:\n\n⚠️ **توجه:** این پنل فقط مخصوص شماست و دیگران نمی‌توانند از آن استفاده کنند.",
        reply_markup=keyboard
    )

async def membership_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await update.message.reply_text("👤 شما هنوز ثبت‌نام نکرده‌اید")
    elif user_data.get('self_active'):
        await update.message.reply_text("✅ شما عضو فعال هستید")
    elif user_data.get('admin_approved'):
        await update.message.reply_text("⏳ در مرحله ورود اطلاعات")
    elif user_data.get('request_sent'):
        await update.message.reply_text("⏳ درخواست شما در انتظار تأیید است")
    elif user_data.get('rejected'):
        await update.message.reply_text("❌ درخواست شما رد شده است")
    else:
        await update.message.reply_text("👤 وضعیت عضویت شما مشخص نیست")

# ========== هندلر پیام‌ها (عضویت) ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = update.message.text

    text = convert_persian_to_english(text)
    
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await start(update, context)
        return
    
    if user_data.get('rejected'):
        await update.message.reply_text(
            "✖ درخواست شما رد شده است.\n\n"
            "🔁 می‌توانید دوباره درخواست عضویت دهید."
        )
        return

    if user_data.get('self_active'):
        if user_id_str not in selfbot_managers:
            session_file = user_data.get('session_file')
            if session_file and os.path.exists(session_file):
                manager = SelfBotManager(user_id_str)
                if await manager.start(session_file):
                    selfbot_managers[user_id_str] = manager
                    await update.message.reply_text("🚀 سلف‌بات شما با موفقیت فعال شد!")
                else:
                    await update.message.reply_text("⚠️ خطا در شروع سلف‌بات. لطفاً با ادمین تماس بگیرید.")
        else:
            await update.message.reply_text("✅ اکانت شما فعال است و سلف‌بات در حال اجراست!")
        
        return

    step = user_data.get('step')
    
    if step == 'get_phone':
        if not user_data.get('admin_approved'):
            await update.message.reply_text("⏳ هنوز درخواست شما توسط ادمین تأیید نشده است.")
            return
        
        db.update_user(user_id_str, phone=text, step='get_code')
        
        await update.message.reply_text(
            f"✅ شماره {text} ذخیره شد.\n\n"
            "⏳ در حال ارسال کد تأیید..."
        )
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            
            if os.path.exists(session_path):
                os.remove(session_path)
            
            user_api = get_user_api(user_id_str)
            if not user_api:
                await update.message.reply_text("❌ خطا در دریافت API. لطفاً بعداً تلاش کنید.")
                return
            
            API_ID = user_api["api_id"]
            API_HASH = user_api["api_hash"]
            
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            sent_code = await client.send_code_request(text)
            phone_code_hash = sent_code.phone_code_hash
            
            db.update_user(user_id_str, phone_code_hash=phone_code_hash)
            
            await update.message.reply_text(
                "✅ **کد تأیید ارسال شد!**\n\n"
                "📩 کد ۵ رقمی را از تلگرام دریافت کرده و وارد کنید:\n"
                "(مثال: ۱۲۳۴۵)"
            )
            
            await client.disconnect()
            
        except TelethonFloodWaitError as e:
            await update.message.reply_text(
                f"⏳ لطفاً {e.seconds} ثانیه صبر کنید و دوباره تلاش کنید."
            )
            db.update_user(user_id_str, step='get_phone')
        except Exception as e:
            logger.error(f"خطا در ارسال کد: {e}")
            await update.message.reply_text(
                f"✖ خطا در ارسال کد: {str(e)}\n\n"
                "لطفاً شماره را دوباره بررسی کرده و وارد کنید:"
            )
            db.update_user(user_id_str, step='get_phone')
    
    elif step == 'get_code':
        db.update_user(user_id_str, code=text)
        
        await update.message.reply_text(
            "⏳ در حال تأیید کد..."
        )
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            
            user_api = get_user_api(user_id_str)
            if not user_api:
                await update.message.reply_text("❌ خطا در دریافت API. لطفاً بعداً تلاش کنید.")
                return
            
            API_ID = user_api["api_id"]
            API_HASH = user_api["api_hash"]
            
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            user_data = db.get_user(user_id_str)
            
            code_for_telegram = text
            persian_digits = '۰۱۲۳۴۵۶۷۸۹'
            english_digits = '0123456789'
            trans_table = str.maketrans(persian_digits, english_digits)
            code_for_telegram = code_for_telegram.translate(trans_table)
            
            await client.sign_in(
                phone=user_data['phone'],
                code=code_for_telegram,
                phone_code_hash=user_data['phone_code_hash']
            )
            
            expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            db.update_user(user_id_str,
                          self_active=1,
                          session_file=session_path,
                          expiration_date=expiration_date,
                          step=None)
            
            await update.message.reply_text(
                f"🎉 **عضویت شما کامل شد!**\n\n"
                f"✅ اکانت شما با موفقیت فعال شد.\n\n"
                f"⏳ مدت اشتراک: ۳۰ روز\n"
                f"📅 انقضا: {expiration_date}\n\n"
                f"💫 موفق باشید!"
            )
            
            await client.disconnect()
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_path):
                selfbot_managers[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات شما به طور خودکار فعال شد!")
            
            admin_message = (
                "✅ **کاربر با موفقیت وارد شد!**\n\n"
                f"👤 نام: {user_data['full_name']}\n"
                f"🆔 آیدی: {user_id_str}\n"
                f"📞 شماره: {user_data['phone']}\n"
                f"💾 سشن: ✓ ایجاد شد\n"
                f"⏳ انقضا: {expiration_date}\n"
                f"🔑 API: {user_data.get('api_id', 'نامشخص')}"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_message
                )
            except Exception as e:
                logger.error(f"خطا در ارسال به ادمین: {e}")
            
        except SessionPasswordNeededError:
            db.update_user(user_id_str, step='get_password')
            await update.message.reply_text(
                "🔐 **اکانت شما رمز دو مرحله‌ای دارد.**\n\n"
                "لطفاً رمز دو مرحله‌ای (2FA) خود را وارد کنید:"
            )
            
        except Exception as e:
            logger.error(f"خطا در تأیید کد: {e}")
            await update.message.reply_text(
                f"✖ کد نامعتبر یا منقضی شده است.\n\n"
                "لطفاً دوباره شماره تلفن را وارد کنید:"
            )
            db.update_user(user_id_str, step='get_phone', phone=None, code=None, phone_code_hash=None)
    
    elif step == 'get_password':
        db.update_user(user_id_str, password=text)
        
        await update.message.reply_text(
            "⏳ در حال تأیید رمز..."
        )
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            
            user_api = get_user_api(user_id_str)
            if not user_api:
                await update.message.reply_text("❌ خطا در دریافت API. لطفاً بعداً تلاش کنید.")
                return
            
            API_ID = user_api["api_id"]
            API_HASH = user_api["api_hash"]
            
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            user_data = db.get_user(user_id_str)
            
            await client.sign_in(password=text)
            
            expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            db.update_user(user_id_str,
                          self_active=1,
                          session_file=session_path,
                          expiration_date=expiration_date,
                          step=None)
            
            await update.message.reply_text(
                f"🎉 **عضویت شما کامل شد!**\n\n"
                f"✅ اکانت شما با موفقیت فعال شد.\n\n"
                f"⏳ مدت اشتراک: ۳۰ روز\n"
                f"📅 انقضا: {expiration_date}\n\n"
                f"💫 موفق باشید!"
            )
            
            await client.disconnect()
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_path):
                selfbot_managers[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات شما به طور خودکار فعال شد!")
            
            admin_message = (
                "✅ **کاربر با موفقیت وارد شد!**\n\n"
                f"👤 نام: {user_data['full_name']}\n"
                f"🆔 آیدی: {user_id_str}\n"
                f"📞 شماره: {user_data['phone']}\n"
                f"🔐 رمز دو مرحله‌ای: ✓\n"
                f"💾 سشن: ✓ ایجاد شد\n"
                f"⏳ انقضا: {expiration_date}\n"
                f"🔑 API: {user_data.get('api_id', 'نامشخص')}"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_message
                )
            except Exception as e:
                logger.error(f"خطا در ارسال به ادمین: {e}")
            
        except Exception as e:
            logger.error(f"خطا در تأیید رمز: {e}")
            await update.message.reply_text(
                f"✖ رمز دو مرحله‌ای نامعتبر است.\n\n"
                "لطفاً دوباره شماره تلفن را وارد کنید:"
            )
            db.update_user(user_id_str, step='get_phone', phone=None, code=None, phone_code_hash=None, password=None)
    
    else:
        await update.message.reply_text(
            "لطفاً برای شروع فرآیند عضویت، روی دکمه 'عضویت در سرویس' کلیک کنید."
        )

# ========== تابع بررسی فایل‌های سشن ==========
async def check_session_files():
    print("\n" + "=" * 60)
    print("🔍 بررسی فایل‌های سشن...")
    
    if not os.path.exists(SESSIONS_FOLDER):
        os.makedirs(SESSIONS_FOLDER)
        print(f"📁 پوشه سشن‌ها ایجاد شد: {SESSIONS_FOLDER}")
    
    session_files = [f for f in os.listdir(SESSIONS_FOLDER) if f.endswith('.session')]
    print(f"📊 تعداد فایل‌های سشن: {len(session_files)}")
    
    for session_file in session_files[:5]:
        file_path = os.path.join(SESSIONS_FOLDER, session_file)
        size = os.path.getsize(file_path)
        modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  • {session_file} - {size} bytes - {modified}")
    
    if len(session_files) > 5:
        print(f"  ... و {len(session_files) - 5} فایل دیگر")
    
    print("=" * 60 + "\n")

# ========== راه‌اندازی اصلی ==========
async def main():
    print("=" * 60)
    print("🤖 سیستم جامع عضویت و سلف‌بات")
    print(f"👑 ادمین: {ADMIN_ID}")
    print(f"📁 پوشه سشن‌ها: {SESSIONS_FOLDER}")
    print("=" * 60)
    
    await check_session_files()
    
    request = HTTPXRequest(
        connection_pool_size=10,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    app = Application.builder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel_command))
    app.add_handler(CommandHandler("membership", membership_command))
    
    app.add_handler(InlineQueryHandler(inline_panel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    
    print("✅ ربات شروع شد و آماده دریافت درخواست‌ها است")
    print("=" * 60)
    
    active_users = db.get_active_users()
    success_count = 0
    fail_count = 0
    
    print(f"🔄 در حال راه‌اندازی {len(active_users)} سلف‌بات...")
    
    for user in active_users:
        user_id_str = user['user_id']
        session_file = user.get('session_file')
        
        if session_file and os.path.exists(session_file):
            print(f"  • راه‌اندازی سلف‌بات برای کاربر {user_id_str}...", end=" ")
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_file):
                selfbot_managers[user_id_str] = manager
                print("✅ موفق")
                success_count += 1
            else:
                print("❌ ناموفق")
                fail_count += 1
        else:
            print(f"  • کاربر {user_id_str}: فایل سشن یافت نشد ❌")
            fail_count += 1
    
    print(f"✅ {success_count} سلف‌بات با موفقیت فعال شدند")
    if fail_count > 0:
        print(f"⚠️ {fail_count} سلف‌بات فعال نشدند")
    print("=" * 60)
    
    # شروع سرویس‌های نگهدارنده
    asyncio.create_task(self_ping())
    asyncio.create_task(backup_session_files())
    
    while True:
        await asyncio.sleep(3600)

# ========== نقطه شروع برنامه برای Render ==========
if __name__ == '__main__':
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 ربات متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای fatal: {e}")
