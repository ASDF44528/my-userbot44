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
import threading
from datetime import datetime, timedelta
from urllib.parse import quote
import pytz
import jdatetime
from hijridate import Gregorian
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler
from telegram.request import HTTPXRequest
from telethon import TelegramClient, events, types
from telethon.tl.types import PeerUser, PeerChannel, PeerChat, MessageMediaPhoto, MessageMediaDocument, ReactionEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityStrike, MessageEntityBlockquote, MessageEntitySpoiler, MessageEntityItalic, MessageEntityCode, MessageEntityPre, InputPeerChat, InputPeerChannel, InputPeerUser, KeyboardButtonSwitchInline, MessageMediaWebPage
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest, SetTypingRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest, GetUserPhotosRequest
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.users import GetFullUserRequest

# ========== تنظیمات وب سرور برای Render (پورت 10000) ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": "Gap_5_bot",
        "version": "4.5.0"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@flask_app.route('/ping')
def ping():
    return jsonify({"status": "alive", "message": "Bot is awake"}), 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 وب سرور روی پورت {port} در حال اجراست")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== تنظیم زمان ایران برای کل سیستم ==========
os.environ['TZ'] = 'Asia/Tehran'
try:
    time.tzset()
except:
    pass

# ========== تنظیمات گوگل سرچ ==========
GOOGLE_SEARCH_API_KEY = "AIzaSyCMYOU0NpU5xfu7GrffyywVUugd1yD2uDU"
GOOGLE_CSE_ID = "3185e48756dfd482f"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# ========== تنظیمات هوش مصنوعی ==========
GEMINI_KEY = "AIzaSyBhlSytH4Zfe-ww1D8HsrgJfCf5TRY1SLc"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
PAXSENIX_API_KEY = "sk-paxsenix-Xo_BAFNGgWVZ_ymWd02Rk1JHbyoDSEzfPhiolJ3F12cY6XZG"
PAXSENIX_API_URL = "https://api.paxsenix.org/v1/chat/completions"
DEEPSEEK_FREE_URL = "https://deepseek.api-sina-free.workers.dev/?text="

# ========== تنظیمات لاگ ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    conn = sqlite3.connect('main_database.db', timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL;')
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

BOT_TOKEN = "8304449635:AAHTqMEke8e1z1ZeMdgkFJGD9gV8EWtmfVk"
ADMIN_ID = 6443963679
BOT_USERNAME = "Gap_5_bot"
MUSIC_BOT = "Gap_4_bot"

SESSIONS_FOLDER = 'user_sessions'
if not os.path.exists(SESSIONS_FOLDER):
    os.makedirs(SESSIONS_FOLDER)

GROUP_ID = -1002817019483

MEDIA_FOLDER = 'media_storage'
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

REPORT_CONFIG_FILE = "report_config.json"
REPORT_MEDIA_FOLDER = 'reported_media'
if not os.path.exists(REPORT_MEDIA_FOLDER):
    os.makedirs(REPORT_MEDIA_FOLDER)

ALLOWED_EMOJIS = [
    "🤯", "🐳", "😍", "💩", "👏", "🍌", "🤓", "😢", "🙉", "🤩",
    "🤝", "👀", "🌚", "🗿", "🤡", "😐", "👨‍💻", "😭", "🙈", "❤",
    "🙏", "😴", "💋", "🥰", "🤪", "✍️", "🥱", "👻", "🤣", "🌭",
    "😨", "🍓", "🔥", "🖕", "🤗", "🤔", "🤬", "😁", "🎄", "🫡",
    "⚡", "🥴", "😈", "🏆", "😇", "🎃", "☃️", "🤮", "👍", "👎",
    "😱", "😖", "🕊", "💯", "💔", "🤨", "❤️‍🔥", "💘", "😘", "💊",
    "🆒", "🤷‍♂", "🤷‍♀", "🎅"
]

classic_fonts = [
    "⊘𝟷ϩӠ4ƼϬ7𝟾९",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "<b>0123456789</b>",
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    "⓿①❷③❹⑤❻⑦❽⑨",
    "₀₁₂₃₄₅₆₇₈₉",
    "⁰¹²³⁴⁵⁶⁷⁸⁹",
    "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    "₀¹²³⁴⁵⁶₇₈₉",
    "<b>0123456789</b>",
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
    "<b>0123456789</b>",
    "🟪🟧🟩🟦🟫⬛🟥🟨",
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    "𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫",
    "０１２３４５６７８９",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡",
    "<b>0123456789</b>",
    "🟪🟧🟩🟦🟫⬛🟥🟨",
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', ':': ':'},
    {'0': '<b>0</b>', '1': '<b>1</b>', '2': '<b>2</b>', '3': '<b>3</b>', '4': '<b>4</b>', '5': '<b>5</b>', '6': '<b>6</b>', '7': '<b>7</b>', '8': '<b>8</b>', '9': '<b>9</b>', ':': ':'},
    {'0': '🟪', '1': '🟧', '2': '🟩', '3': '🟦', '4': '🟫', '5': '⬛', '6': '🟥', '7': '🟨', '8': '⬜', '9': '🟪', ':': ':'},
    {'0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨', ':': ':'},
    {'0': '🄋', '1': '➊', '2': '➋', '3': '➌', '4': '➍', '5': '➎', '6': '➏', '7': '➐', '8': '➑', '9': '➒', ':': ':'},
    {'0': '⓿', '1': '❶', '2': '❷', '3': '❸', '4': '❹', '5': '❺', '6': '❻', '7': '❼', '8': '❽', '9': '❾', ':': ':'},
    {'0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜', '5': '𝟝', '6': '𝟞', '7': '𝟟', '8': '𝟠', '9': '𝟡', ':': ':'},
    {'0': '⒒', '1': '⑴', '2': '⑵', '3': '⑶', '4': '⑷', '5': '⑸', '6': '⑹', '7': '⑺', '8': '⑻', '9': '⑼', ':': ':'},
    {'0': '０', '1': '１', '2': '２', '3': '３', '4': '４', '5': '５', '6': '６', '7': '７', '8': '８', '9': '９', ':': '：'},
    {'0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵', ':': ':'},
    {'0': '〇', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九', ':': ':'}
]

flags = [
    "🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇼", "🇦🇼", "🇦🇹", "🇦🇿", "🇧🇸", "🇧🇭",
    "🇧🇩", "🇧🇧", "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇴", "🇧🇦", "🇧🇼",
    "🇧🇷", "🇮🇴", "🇻🇬", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦",
    "🇨🇻", "🇰🇾", "🇨🇫", "🇹🇩", "🇨🇱", "🇨🇴", "🇰🇲", "🇨🇬", "🇨🇩", "🇨🇽",
    "🇨🇨", "🇨🇴", "🇰🇲", "🇨🇬", "🇨🇩", "🇨🇰", "🇨🇰", "🕋"
]

SPAM_MESSAGES = [
    "مادربزرگت کسده، کسشو تو قبرم اجاره داده",
    "پدربزرگت کونی، هنوزم تو گور کونشو به شیاطین می‌سپره",
    "کس ننت چنان بازه، کل شهر توش چادر زدن",
    "بابات کسکش، تو خیابون کونشو به موتورسوارا نشون می‌ده",
    "خواهرت فاحشه، تو کلوپ شبانه کسشو به حراج گذاشته",
    "برادرت کیرکش، تو کوچه کونشو به گربه‌ها می‌ده",
    "بچه‌هات جنده‌ان، تو پارک کسشونو به نیمکت‌ها می‌مالن",
    "عمه‌ت کس‌کش، کسشو تو حموم عمومی به همه نشون می‌ده",
    "خاله‌ت کونی, کیر هر غریبه‌ای رو تو کوچه می‌گیره",
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
    "مادرتو زدم به سیخ"
]

DEFAULT_LOCK_SETTINGS = {
    'link': False,
    'photo': False,
    'video': False,
    'sticker': False,
    'gif': False,
    'voice': False,
    'file': False,
    'music': False,
    'video_note': False,
    'contact': False,
    'location': False,
    'emoji': False,
    'text': False
}

BOT_VERSION = "4.5.0"
BOT_CREATOR = "Self-Bot AI Assistant"

HEARTS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤍"]
MOONS = ["🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]

media_cache = {}
message_cache = {}
user_inline_messages = {}

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

R = "❤️"
W = "🤍"
SLEEP = 0.1

def create_heart_matrix(size):
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

# ========== دیتابیس اصلی با حالت WAL و Timeout ==========
class MainDatabase:
    def __init__(self, db_name='main_database.db'):
        self.db_name = db_name
        self.init_database()
        
    def get_conn(self):
        conn = sqlite3.connect(self.db_name, timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL;')
        return conn
    
    def init_database(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
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
                    lock_voice BOOLEAN DEFAULT 0,
                    lock_file BOOLEAN DEFAULT 0,
                    lock_music BOOLEAN DEFAULT 0,
                    lock_video_note BOOLEAN DEFAULT 0,
                    lock_contact BOOLEAN DEFAULT 0,
                    lock_location BOOLEAN DEFAULT 0,
                    lock_emoji BOOLEAN DEFAULT 0,
                    lock_text BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, target_id)
                )
            ''')
            
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
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    message_text TEXT,
                    message_type TEXT DEFAULT 'text',
                    media_file TEXT,
                    sent_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    panel_mode BOOLEAN DEFAULT 1,
                    time_font_indices TEXT,
                    filter_enabled BOOLEAN DEFAULT 0,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, enemy_id, chat_type)
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
            conn.commit()
        logger.info("✓ دیتابیس اصلی ایجاد شد")
    
    def add_user(self, user_id, full_name, username):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, full_name, username, updated_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, full_name, username))
            conn.commit()
    
    def get_user(self, user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
    
    def update_user(self, user_id, **kwargs):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)
            cursor.execute(f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', values)
            conn.commit()
    
    def get_pending_requests(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE request_sent = 1 AND admin_approved = 0 AND rejected = 0 AND step IS NULL
                ORDER BY request_date DESC
            ''')
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def get_pending_login(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE admin_approved = 1 AND self_active = 0 AND step IS NOT NULL
                ORDER BY activation_date DESC
            ''')
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def get_active_users(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                WHERE self_active = 1 AND admin_approved = 1
                ORDER BY activation_date DESC
            ''')
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def get_all_users(self):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, full_name, username, phone, self_active, created_at 
                FROM users ORDER BY created_at DESC
            ''')
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def get_selfbot_settings(self, user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM selfbot_settings WHERE user_id = ?', (user_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
        
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
                'panel_mode': 1,
                'time_font_indices': 'all',
                'filter_enabled': 0,
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
                }
            }
            self.set_selfbot_settings(user_id, default_settings)
            return default_settings
    
    def set_selfbot_settings(self, user_id, settings):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            settings_to_save = settings.copy()
            settings_to_save.pop('ai_status', None)
            settings_to_save.pop('translate', None)
            
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
    
    def update_selfbot_setting(self, user_id, key, value):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE selfbot_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (value, user_id))
            conn.commit()
    
    def update_ai_status(self, user_id, ai_status):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            for key, value in ai_status.items():
                if key in ['ai_1_pm', 'ai_2_pm', 'ai_3_pm', 'ai_1_group', 'ai_2_group', 'ai_3_group']:
                    cursor.execute(f'UPDATE selfbot_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (1 if value else 0, user_id))
            conn.commit()
    
    def add_enemy(self, owner_id, enemy_id, chat_type='pv'):
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO enemies (owner_id, enemy_id, chat_type)
                    VALUES (?, ?, ?)
                ''', (owner_id, enemy_id, chat_type))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding enemy: {e}")
            return False
    
    def remove_enemy(self, owner_id, enemy_id, chat_type='pv'):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM enemies WHERE owner_id = ? AND enemy_id = ? AND chat_type = ?', (owner_id, enemy_id, chat_type))
            conn.commit()
    
    def get_enemies(self, owner_id, chat_type='pv'):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT enemy_id FROM enemies WHERE owner_id = ? AND chat_type = ?', (owner_id, chat_type))
            return [row[0] for row in cursor.fetchall()]
    
    def is_enemy(self, owner_id, enemy_id, chat_type='pv'):
        enemies = self.get_enemies(owner_id, chat_type)
        return enemy_id in enemies
    
    def add_locked_pv(self, owner_id, locked_user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO locked_pvs (owner_id, locked_user_id) VALUES (?, ?)', (owner_id, locked_user_id))
            conn.commit()
    
    def remove_locked_pv(self, owner_id, locked_user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM locked_pvs WHERE owner_id = ? AND locked_user_id = ?', (owner_id, locked_user_id))
            conn.commit()
    
    def get_locked_pvs(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT locked_user_id FROM locked_pvs WHERE owner_id = ?', (owner_id,))
            return [row[0] for row in cursor.fetchall()]
    
    def is_pv_locked(self, owner_id, user_id):
        locked_pvs = self.get_locked_pvs(owner_id)
        return user_id in locked_pvs
    
    def get_media_locks(self, owner_id, target_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
        
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
            'lock_voice': 0,
            'lock_file': 0,
            'lock_music': 0,
            'lock_video_note': 0,
            'lock_contact': 0,
            'lock_location': 0,
            'lock_emoji': 0,
            'lock_text': 0
        }
    
    def set_media_lock(self, owner_id, target_id, lock_type, value):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
            exists = cursor.fetchone()
            
            if exists:
                cursor.execute(f'UPDATE media_locks SET {lock_type} = ?, created_at = CURRENT_TIMESTAMP WHERE owner_id = ? AND target_id = ?', (1 if value else 0, owner_id, target_id))
            else:
                lock_settings = {
                    'owner_id': owner_id,
                    'target_id': target_id,
                    'lock_link': 0,
                    'lock_photo': 0,
                    'lock_video': 0,
                    'lock_sticker': 0,
                    'lock_gif': 0,
                    'lock_voice': 0,
                    'lock_file': 0,
                    'lock_music': 0,
                    'lock_video_note': 0,
                    'lock_contact': 0,
                    'lock_location': 0,
                    'lock_emoji': 0,
                    'lock_text': 0
                }
                lock_settings[lock_type] = 1 if value else 0
                columns = ', '.join(lock_settings.keys())
                placeholders = ', '.join(['?' for _ in lock_settings])
                values = list(lock_settings.values())
                cursor.execute(f'INSERT INTO media_locks ({columns}) VALUES ({placeholders})', values)
            conn.commit()
    
    def set_reaction(self, owner_id, chat_id, target_id, emoji):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO reactions (owner_id, chat_id, target_id, emoji) VALUES (?, ?, ?, ?)', (owner_id, chat_id, target_id, emoji))
            conn.commit()
    
    def get_reaction(self, owner_id, chat_id, target_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT emoji FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def remove_reaction(self, owner_id, chat_id, target_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
            conn.commit()
    
    def set_auto_comment(self, owner_id, channel_id, comment_text, channel_title, channel_type, channel_username):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO auto_comments (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username))
            conn.commit()
    
    def get_auto_comments(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_comments WHERE owner_id = ?', (owner_id,))
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def get_auto_comment(self, owner_id, channel_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
    
    def remove_auto_comment(self, owner_id, channel_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
            conn.commit()
    
    def mark_comment_sent(self, owner_id, channel_id, message_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sent_comments (owner_id, channel_id, message_id, comment_sent) 
                VALUES (?, ?, ?, 1)
            ''', (owner_id, channel_id, message_id))
            conn.commit()
    
    def is_comment_sent(self, owner_id, channel_id, message_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT comment_sent FROM sent_comments 
                WHERE owner_id = ? AND channel_id = ? AND message_id = ?
            ''', (owner_id, channel_id, message_id))
            result = cursor.fetchone()
            return result and result[0] == 1
    
    def cache_message(self, owner_id, chat_id, message_id, message_text):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO message_cache (owner_id, chat_id, message_id, message_text) VALUES (?, ?, ?, ?)', (owner_id, chat_id, message_id, message_text))
            conn.commit()
    
    def get_cached_message(self, owner_id, chat_id, message_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT message_text FROM message_cache WHERE owner_id = ? AND chat_id = ? AND message_id = ?', (owner_id, chat_id, message_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def add_enemy_spam_message(self, owner_id, spam_text):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO enemy_spam_messages (owner_id, spam_text) VALUES (?, ?)', (owner_id, spam_text))
            conn.commit()
    
    def get_enemy_spam_messages(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, spam_text FROM enemy_spam_messages WHERE owner_id = ? ORDER BY created_at', (owner_id,))
            results = cursor.fetchall()
            return [{'id': row[0], 'text': row[1]} for row in results]
    
    def clear_enemy_spam_messages(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ?', (owner_id,))
            conn.commit()
    
    def delete_enemy_spam_message(self, owner_id, message_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ? AND id = ?', (owner_id, message_id))
            conn.commit()
    
    def add_filter_word(self, owner_id, word):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO filter_words (owner_id, word) VALUES (?, ?)', (owner_id, word))
            conn.commit()
    
    def remove_filter_word(self, owner_id, word):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM filter_words WHERE owner_id = ? AND word = ?', (owner_id, word))
            conn.commit()
    
    def get_filter_words(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word, enabled FROM filter_words WHERE owner_id = ?', (owner_id,))
            results = cursor.fetchall()
            return [{'word': row[0], 'enabled': bool(row[1])} for row in results]
    
    def toggle_filter_word(self, owner_id, word, enabled):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE filter_words SET enabled = ? WHERE owner_id = ? AND word = ?', (1 if enabled else 0, owner_id, word))
            conn.commit()
    
    def toggle_all_filters(self, owner_id, enabled):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE filter_words SET enabled = ? WHERE owner_id = ?', (1 if enabled else 0, owner_id))
            conn.commit()
    
    def get_filter_enabled(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT filter_enabled FROM selfbot_settings WHERE user_id = ?', (owner_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def set_filter_enabled(self, owner_id, enabled):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE selfbot_settings SET filter_enabled = ? WHERE user_id = ?', (1 if enabled else 0, owner_id))
            except:
                try:
                    cursor.execute('ALTER TABLE selfbot_settings ADD COLUMN filter_enabled BOOLEAN DEFAULT 0')
                    cursor.execute('UPDATE selfbot_settings SET filter_enabled = ? WHERE user_id = ?', (1 if enabled else 0, owner_id))
                except:
                    pass
            conn.commit()
    
    def get_spam_settings(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM spam_settings WHERE owner_id = ?', (owner_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return {
                'owner_id': owner_id,
                'spam_protection': 0,
                'spam_limit': 10,
                'mute_duration': 10
            }
    
    def set_spam_settings(self, owner_id, spam_protection=None, spam_limit=None, mute_duration=None):
        with self.get_conn() as conn:
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
    
    def get_original_name(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "original_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set_original_name(self, owner_id, original_name):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "original_name", ?)', (owner_id, original_name))
            conn.commit()
    
    def get_current_name(self, owner_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "current_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set_current_name(self, owner_id, current_name):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "current_name", ?)', (owner_id, current_name))
            conn.commit()
    
    def get_user_name(self, user_id):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT known_name, first_name, username FROM user_memory WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
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
        with self.get_conn() as conn:
            cursor = conn.cursor()
            if key:
                cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = ? ORDER BY timestamp DESC LIMIT 1', (user_id, key))
                result = cursor.fetchone()
                return result[0] if result else None
            else:
                cursor.execute('SELECT key, value FROM user_info WHERE user_id = ?', (user_id,))
                results = cursor.fetchall()
                return dict(results) if results else {}
    
    def update_user_memory(self, user_id, username, first_name, last_name, chat_id, known_name=None):
        with self.get_conn() as conn:
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
    
    def add_broadcast(self, admin_id, message_text, message_type='text', media_file=None):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO broadcasts (admin_id, message_text, message_type, media_file)
                VALUES (?, ?, ?, ?)
            ''', (admin_id, message_text, message_type, media_file))
            broadcast_id = cursor.lastrowid
            conn.commit()
            return broadcast_id
    
    def update_broadcast_stats(self, broadcast_id, sent_count, failed_count):
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE broadcasts SET sent_count = ?, failed_count = ?
                WHERE id = ?
            ''', (sent_count, failed_count, broadcast_id))
            conn.commit()

db = MainDatabase()
selfbot_managers = {}

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
🕐 ساعت: {now.strftime('%H:%M:%S')}

📆 شمسی:
{persian_weekdays[jdate.weekday()]} - {jdate.day} {jdate.strftime('%B')} {jdate.year}

📆 میلادی:
{gregorian_weekdays[now.weekday()]} - {now.strftime('%B %d, %Y')}

📆 قمری:
{hijri.day} {hijri.month_name()} {hijri.year}
━━━━━━━━━━━━━━━━━━━━
        """
    except:
        return f"📅 تاریخ: {now.strftime('%Y/%m/%d %H:%M:%S')}"

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
            url = f"{GEMINI_URL}?key={GEMINI_KEY}"
            payload = {"contents": [{"parts": [{"text": text}]}]}
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
        
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

# ========== کلاس مدیر سلف‌بات با هوش مصنوعی و ترجمه لحظه‌ای ==========
class SelfBotManager:
    def __init__(self, user_id):
        self.user_id = int(user_id)
        self.client = None
        self.running = False
        self.my_id = None
        self.BASE_NAME = None
        self.ORIGINAL_NAME = None
        self.spam_tasks = {}
        self.report_config = ReportConfig(user_id)
        self.adding_spam = False
        self.spam_counters = {}
        self.mode = 'all'
        self.current_chat_id = None
        self.last_active_pv_id = None      
        self.last_active_chat_id = None    
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
        self.max_attempts = 10
        self._handlers_set = False
        self.panel_mode = True
        self.api_id = None
        self.api_hash = None
        self.time_font_cycle = 0
        self.time_font_indices = 'all'
        self.reconnect_task = None
        self.last_ping = 0
    
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
                connection_retries=15,
                retry_delay=5,
                timeout=90,
                flood_sleep_threshold=120,
                device_model="SelfBot",
                system_version="4.5.0",
                app_version="4.5.0"
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
            asyncio.create_task(self.keep_alive_task())
            
            self.running = True
            self.connection_attempts = 0
            logger.info(f"✅ سلف‌بات برای کاربر {self.user_id} با موفقیت شروع شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در شروع سلف‌بات برای کاربر {self.user_id}: {str(e)}")
            
            if self.connection_attempts < self.max_attempts:
                wait_time = 3 * self.connection_attempts
                logger.info(f"تلاش مجدد در {wait_time} ثانیه برای کاربر {self.user_id}")
                await asyncio.sleep(wait_time)
                return await self.start(session_file)
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            return False
    
    async def keep_alive_task(self):
        while self.running:
            try:
                await asyncio.sleep(60)
                if not self.running:
                    break
                
                if self.client:
                    is_connected = False
                    try:
                        if self.client.is_connected():
                            await self.client.get_me()
                            self.last_ping = time.time()
                            is_connected = True
                    except Exception as e:
                        logger.warning(f"پینگ ناموفق برای کاربر {self.user_id}: {e}")
                    
                    if not is_connected:
                        logger.warning(f"اتصال کاربر {self.user_id} قطع شده، تلاش برای reconnect...")
                        await self.reconnect()
                else:
                    await self.reconnect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"خطا در keep_alive_task برای کاربر {self.user_id}: {e}")
                await asyncio.sleep(15)
    
    async def reconnect(self):
        try:
            logger.info(f"شروع reconnect برای کاربر {self.user_id}")
            old_mode = self.mode
            old_chat_id = self.current_chat_id
            
            user_data = db.get_user(str(self.user_id))
            if not user_data or not user_data.get('session_file'):
                logger.error(f"فایل سشن برای کاربر {self.user_id} یافت نشد")
                return False
            
            session_file = user_data['session_file']
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            self.running = False
            self._handlers_set = False
            await asyncio.sleep(2)
            
            if await self.start(session_file):
                self.mode = old_mode
                self.current_chat_id = old_chat_id
                logger.info(f"✅ reconnect برای کاربر {self.user_id} موفقیت‌آمیز بود")
                return True
            else:
                logger.error(f"❌ reconnect برای کاربر {self.user_id} ناموفق بود")
                return False
        except Exception as e:
            logger.error(f"خطا در reconnect برای کاربر {self.user_id}: {e}")
            return False
    
    async def stop(self):
        try:
            settings = db.get_selfbot_settings(self.user_id)
            settings['panel_mode'] = self.panel_mode
            db.set_selfbot_settings(self.user_id, settings)
            
            if self.client:
                for task in self.spam_tasks.values():
                    task.cancel()
                self.spam_tasks.clear()
                
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            self.running = False
            logger.info(f"✅ سلف‌بات برای کاربر {self.user_id} متوقف شد")
        except Exception as e:
            logger.error(f"خطا در توقف سلف‌بات برای کاربر {self.user_id}: {e}")
    
    def setup_handlers(self):
        try:
            @self.client.on(events.NewMessage(incoming=True))
            async def _on_new_message(event):
                await self.handle_new_message(event)
            
            @self.client.on(events.MessageEdited(incoming=True))
            async def _on_message_edited(event):
                await self.handle_edited_message(event)
            
            @self.client.on(events.MessageDeleted)
            async def _on_message_deleted(event):
                await self.handle_deleted_message(event)
            
            @self.client.on(events.NewMessage(pattern=r'^(?:شروع|تایم روشن|تایمر پرچم روشن|تایم خاموش|قلب|ماه|اطلاعات|دانلود پروفایل|تاریخ کامل|فعال اتوسین|غیرفعال اتوسین|حذف کامل|ست پروف|ست بیو|حذف ست پروف|حذف ست بیو|بولد روشن|بولد خاموش|زیرخط روشن|زیرخط خاموش|خط خورده روشن|خط خورده خاموش|نقل قول روشن|نقل قول خاموش|اسپویلر روشن|اسپویلر خاموش|کج روشن|کج خاموش|کد روشن|کد خاموش|پیش روشن|پیش خاموش|بلاک|پیوی ۱|پیوی ۲|پیوی ۳|خاموش پیوی|گروه ۱|گروه ۲|گروه ۳|خاموش گروه|درباره|من کی ام|قفل پیوی همه|باز پی همه|قفل لینک روشن|قفل لینک خاموش|قفل عکس روشن|قفل عکس خاموش|قفل ویدیو روشن|قفل ویدیو خاموش|قفل استیکر روشن|قفل استیکر خاموش|قفل گیف روشن|قفل گیف خاموش|قفل ویس روشن|قفل ویس خاموش|قفل فایل روشن|قفل فایل خاموش|قفل موزیک روشن|قفل موزیک خاموش|قفل ویدیو نوت روشن|قفل ویدیو نوت خاموش|قفل کانتکت روشن|قفل کانتکت خاموش|قفل لوکیشن روشن|قفل لوکیشن خاموش|قفل ایموجی روشن|قفل ایموجی خاموش|قفل متن روشن|قفل متن خاموش|تنظیم گزارش|گروه گزارش|کانال‌ها|حذف کانال|تست کانال|لیست دشمن|پاک کردن اسپم|لیست اسپم|تغییر اسم|تغییر بیو|تغییر پروفایل|پروف|اضافه اسپم|اتمام اسپم|فیلتر روشن|فیلتر خاموش|لیست فیلتر|اسپم روشن|اسپم خاموش|پینگ|سرچ|خروج سرچ|وضعیت|قلب پیشرفته|عشق|سنتت|هک|حذف ریکت)(?:\s*$|\s+(.+)$)|^حذف\s+(\d+)$|^دشمن\s*(@\w+|-\d+|\d+)?$|^دوست\s*(@\w+|-\d+|\d+)?$|^قفل پیوی\s*(@\w+|-\d+|\d+)?$|^باز پی\s*(@\w+|-\d+|\d+)?$|^اسپم\s+(\d+)\s+(.+)$|^ریکت\s*([\U0001F300-\U0001F9FF]+)?$|^کامنت\s+(.+)$|^حذف اسپم\s+(\d+)$|^تایم\s+([\d\.]+)$|^\.فیلتر\s+(.+)$|^حذف فیلتر\s+(.+)$|^\.پنل$|^پنل$|^/panel$|^\.اهنگ\s+(.+)$|^تنظیم اسپم\s+(\d+)\s+(\d+)$'))
            async def _on_commands(event):
                await self.handle_commands(event)
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def _on_outgoing_message(event):
                await self.handle_outgoing_message(event)
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def _on_action_commands(event):
                await self.handle_action_commands(event)
            
            @self.client.on(events.NewMessage())
            async def _on_auto_comment(event):
                await self.handle_auto_comment(event)
            
            @self.client.on(events.NewMessage())
            async def _on_report_message(event):
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
                await event.edit(f"✅ ترجمه {l} {status} شد")
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
            await event.edit('✅ بات در همه جا فعال شد')
            return
        elif msg == 'فقط اینجا':
            self.mode = 'pv'
            self.current_chat_id = chat_id
            chat = await event.get_chat()
            chat_name = chat.first_name if hasattr(chat, 'first_name') else chat.title
            await event.edit(f'✅ بات فقط در {chat_name} فعال شد')
            return
        elif msg == 'خاموش':
            self.mode = 'off'
            stopped = await self.stop_all_actions()
            if stopped:
                await event.edit(f'✅ بات خاموش شد\n\n⏹️ اکشن‌های متوقف شده:\n{", ".join(stopped)}')
            else:
                await event.edit('✅ بات خاموش شد')
            return
        
        if msg.startswith('اکشن '):
            command = msg.replace('اکشن ', '').strip()
            if command == 'خاموش':
                if chat_id in self.active_actions:
                    action_name = await self.stop_action(chat_id)
                    await event.edit(f'✅ اکشن {action_name} خاموش شد')
                else:
                    await event.edit('❌ هیچ اکشن فعالی در این چت وجود ندارد')
                return
            elif command == 'لیست':
                if self.active_actions:
                    active_list = "🎭 اکشن‌های فعال:\n\n"
                    for cid, action in self.active_actions.items():
                        try:
                            chat_obj = await self.client.get_entity(cid)
                            chat_name = chat_obj.first_name if hasattr(chat_obj, 'first_name') else chat_obj.title
                            active_list += f"• {chat_name}: {action}\n"
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
                        await event.edit(f'⏹️ اکشن قبلی {old_action} خاموش شد\n✅ اکشن جدید {command} فعال شد')
                    else:
                        await event.edit(f'✅ اکشن {command} فعال شد')
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
            await event.edit('🔍 حالت سرچ فعال شد.\n\nاکنون هر متنی که ارسال کنید در گوگل جستجو می‌شود.')
            return
        elif msg == 'خروج سرچ':
            self.search_mode = False
            self.last_search_results = []
            await event.edit('✅ حالت سرچ غیرفعال شد.')
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
            await event.edit(f'🔍 در حال جستجو: {query}')
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
                    message = f"🔍 نتایج جستجو برای: {query}\n\n"
                    for i, item in enumerate(results['items'][:5], 1):
                        title = item.get('title', 'بدون عنوان')
                        link = item.get('link', '')
                        snippet = item.get('snippet', 'بدون توضیح')[:100]
                        message += f"{i}. {title}\n"
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
                    await event.edit(f'❌ هیچ نتیجه‌ای برای "{query}" پیدا نشد.')
            else:
                await event.edit(f'❌ خطا در جستجو. کد خطا: {response.status_code}')
        except Exception as e:
            logger.error(f"خطا در جستجوی گوگل: {e}")
            await event.edit(f'❌ خطا در جستجو: {str(e)}')
    
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
                    for attr in document.attributes:
                        if hasattr(attr, 'voice'):
                            return 'video_note'
                    return 'video'
                elif 'image' in document.mime_type:
                    for attr in document.attributes:
                        if hasattr(attr, 'stickerset'):
                            return 'sticker'
                        elif hasattr(attr, 'animated'):
                            return 'gif'
                    return 'image'
                elif 'audio' in document.mime_type:
                    return 'music'
            if hasattr(document, 'attributes'):
                for attr in document.attributes:
                    if hasattr(attr, 'alt') and attr.alt:
                        return 'sticker'
            return 'file'
        elif isinstance(message.media, MessageMediaWebPage):
            return 'webpage'
        elif hasattr(message.media, 'contact'):
            return 'contact'
        elif hasattr(message.media, 'geo'):
            return 'location'
        return 'unknown'
    
    def get_file_extension(self, media_type):
        extensions = {
            'photo': '.jpg',
            'voice': '.ogg',
            'video': '.mp4',
            'video_note': '.mp4',
            'sticker': '.webp',
            'gif': '.mp4',
            'image': '.jpg',
            'file': '.bin',
            'music': '.mp3'
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
            
            downloaded_path = await self.client.download_media(message.media, file=file_path)
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
    
    async def handle_media_lock_delete(self, event):
        if not event.message or event.message.out:
            return False
        
        target_id = event.sender_id
        if target_id == self.my_id:
            return False
            
        media_locks = db.get_media_locks(self.user_id, target_id)
        if not any(media_locks.values()):
            media_locks = db.get_media_locks(self.user_id, 0)
            
        message = event.message
        message_text = message.text or ""
        
        if media_locks.get('lock_link') and is_link_message(message_text):
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_text') and message_text:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_emoji') and is_emoji_message(message_text):
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_photo') and message.photo:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_video') and message.video:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_sticker') and message.sticker:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_gif') and message.gif:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_voice') and message.voice:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_file') and message.document and not message.sticker and not message.gif:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_music') and message.audio:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_video_note') and message.video_note:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_contact') and message.contact:
            try:
                await message.delete()
                return True
            except:
                pass
        if media_locks.get('lock_location') and message.geo:
            try:
                await message.delete()
                return True
            except:
                pass
        return False
    
    async def handle_new_message(self, event):
        if not self.my_id:
            return
            
        self.last_active_chat_id = event.chat_id
        if event.is_private:
            self.last_active_pv_id = event.chat_id
            
        settings = db.get_selfbot_settings(self.user_id)
        chat_id = event.chat_id
        
        if event.is_private and not event.message.out:
            if settings.get('pv_lock_all') or db.is_pv_locked(self.user_id, event.sender_id):
                try:
                    await event.message.delete()
                    return
                except:
                    pass
                    
        if await self.handle_media_lock_delete(event):
            return
            
        if event.is_private and not event.message.out and event.message.text:
            db.cache_message(self.user_id, chat_id, event.message.id, event.message.text)
            
        if not event.message.out and event.message.text:
            if db.get_filter_enabled(self.user_id):
                filter_words = db.get_filter_words(self.user_id)
                for word_info in filter_words:
                    if word_info['enabled'] and word_info['word'].lower() in event.message.text.lower():
                        try:
                            await event.message.delete()
                            return
                        except:
                            pass
                            
        if event.is_private and not event.message.out:
            sender_id = event.sender_id
            try:
                reaction = db.get_reaction(self.user_id, chat_id, sender_id)
                if reaction and reaction in ALLOWED_EMOJIS:
                    await self.client(SendReactionRequest(
                        peer=event.message.peer_id,
                        msg_id=event.message.id,
                        reaction=[ReactionEmoji(emoticon=reaction)]
                    ))
            except Exception as e:
                logger.error(f"خطا در ارسال ریکت خودکار: {e}")
                
        if event.is_private and not event.message.out:
            sender_id = event.sender_id
            ai_status = settings.get('ai_status', {})
            ai_active, ai_type = False, None
            
            if event.message.text:
                if ai_status.get('ai_1_pm'):
                    ai_active, ai_type = True, 1
                elif ai_status.get('ai_2_pm'):
                    ai_active, ai_type = True, 2
                elif ai_status.get('ai_3_pm'):
                    ai_active, ai_type = True, 3
                    
            if ai_active and ai_type:
                try:
                    await self.client(SetTypingRequest(event.chat_id, types.SendMessageTypingAction()))
                    response = await get_ai_response(event.message.text, ai_type, self.user_id)
                    if response:
                        text, entities = await apply_text_style(response, settings.get('text_style'))
                        await event.reply(text, formatting_entities=entities)
                except Exception as e:
                    logger.error(f"خطا در هوش مصنوعی: {e}")
                    
        spam_settings = db.get_spam_settings(self.user_id)
        if spam_settings.get('spam_protection') and not event.message.out:
            sender_id = event.sender_id
            chat_key = f"{chat_id}_{sender_id}"
            if chat_key not in self.spam_counters:
                self.spam_counters[chat_key] = []
            now = time.time()
            self.spam_counters[chat_key].append(now)
            mute_duration = spam_settings.get('mute_duration', 10)
            self.spam_counters[chat_key] = [t for t in self.spam_counters[chat_key] if now - t <= mute_duration]
            spam_limit = spam_settings.get('spam_limit', 10)
            if len(self.spam_counters[chat_key]) > spam_limit:
                try:
                    await event.message.delete()
                except:
                    pass
                    
        if event.is_private and not event.message.out:
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
            if not message or message.out or not is_channel_post(message):
                return
            chat = await message.get_chat()
            channel_id = chat.id
            auto_comment = db.get_auto_comment(self.user_id, channel_id)
            if not auto_comment:
                return
            if db.is_comment_sent(self.user_id, channel_id, message.id):
                return
            
            await asyncio.sleep(0.3)
            await self.client.send_message(chat.id, auto_comment['comment_text'], reply_to=message.id)
            db.mark_comment_sent(self.user_id, channel_id, message.id)
        except Exception as e:
            logger.error(f"خطا در کامنت خودکار: {e}")
    
    async def handle_report_message(self, event):
        try:
            message = event.message
            if not message or not event.is_private or message.out:
                return
            if message.text:
                chat_id = message.peer_id.user_id
                message_cache[(chat_id, message.id)] = message.text
            if message.media:
                media_type = self.get_media_type(message)
                if media_type:
                    saved_path = await self.save_media(message, media_type)
                    if self.report_config.report_ttl_media and hasattr(message.media, 'ttl_seconds') and message.media.ttl_seconds:
                        sender_info = await self.get_user_info(message.sender_id)
                        await self.send_report(
                            f"⏰ رسانه نابودشونده\n👤 از: {sender_info}\n📦 نوع: {media_type}\n💾 ذخیره: {'✅' if saved_path else '❌'}",
                            saved_path,
                            f"⏰ {media_type} نابودشونده"
                        )
                    elif hasattr(message.media, 'noforwards') and message.media.noforwards:
                        sender_info = await self.get_user_info(message.sender_id)
                        await self.send_report(
                            f"🚫 رسانه یک‌بارمصرف\n👤 از: {sender_info}\n📦 نوع: {media_type}\n💾 ذخیره: {'✅' if saved_path else '❌'}",
                            saved_path,
                            f"🚫 {media_type} یک‌بارمصرف"
                        )
        except Exception as e:
            logger.error(f"خطا در گزارش پیام: {e}")
    
    async def handle_edited_message(self, event):
        if event.is_private and not event.message.out:
            sender = await event.get_sender()
            if sender.id == self.my_id:
                return
            settings = db.get_selfbot_settings(self.user_id)
            if settings.get('pv_lock_all') or db.is_pv_locked(self.user_id, sender.id):
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
                    await self.send_report(
                        f"✍️ پیام ویرایش‌شده\n👤 از: {sender_info}\n📝 متن اصلی:\n{original_text}\n📝 جدید:\n{new_text}"
                    )
                except Exception as e:
                    logger.error(f"خطا در گزارش ویرایش: {e}")
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
                    
                    report_text = f"🗑️ رسانه حذف‌شده\n👤 از: {sender_info}\n💬 چت: {chat_title}\n📦 نوع: {media_info['type']}\n📝 کپشن: {media_info.get('caption', '')}"
                    if file_exists:
                        await self.send_report(report_text, media_info['path'])
                    else:
                        await self.send_report(report_text)
                    del media_cache[msg_id]
                except Exception as e:
                    logger.error(f"خطا در گزارش حذف رسانه: {e}")
            
            for (chat_id, cached_msg_id), text in list(message_cache.items()):
                if cached_msg_id == msg_id:
                    try:
                        sender_info = await self.get_user_info(chat_id)
                        await self.send_report(f"🗑️ پیام متنی حذف‌شده\n👤 از: {sender_info}\n📝 متن:\n{text}")
                        del message_cache[(chat_id, msg_id)]
                    except Exception as e:
                        logger.error(f"خطا در گزارش حذف متن: {e}")
    
    def format_status_info(self, settings):
        try:
            conn = sqlite3.connect('main_database.db', timeout=30.0)
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
        
        ai_status = settings.get('ai_status', {})
        active_ai_pm = "هیچکدام"
        if ai_status.get('ai_1_pm'): active_ai_pm = "هوش ۱"
        elif ai_status.get('ai_2_pm'): active_ai_pm = "هوش ۲"
        elif ai_status.get('ai_3_pm'): active_ai_pm = "هوش ۳"
        
        active_ai_group = "هیچکدام"
        if ai_status.get('ai_1_group'): active_ai_group = "هوش ۱"
        elif ai_status.get('ai_2_group'): active_ai_group = "هوش ۲"
        elif ai_status.get('ai_3_group'): active_ai_group = "هوش ۳"
        
        filter_status = "فعال" if db.get_filter_enabled(self.user_id) else "غیرفعال"
        text_style = settings.get('text_style') or "هیچکدام"
        
        return f"""
📊 وضعیت کامل سلف‌بات
━━━━━━━━━━━━━━━━━━━━
📍 حالت: {'همه جا' if self.mode == 'all' else 'فقط اینجا' if self.mode == 'pv' else 'خاموش'}
🕐 تایم روی پروفایل: {'فعال' if settings.get('time_enabled') else 'غیرفعال'}
🏳️ پرچم در تایم: {'فعال' if settings.get('flag_enabled') else 'غیرفعال'}
🎨 فونت تایم: {font_info}

🤖 هوش مصنوعی:
• پی‌وی: {active_ai_pm}
• گروه: {active_ai_group}

✍️ استایل متن: {text_style}
🔒 قفل همگانی پی‌وی: {'فعال' if settings.get('pv_lock_all') else 'غیرفعال'}
🚫 فیلتر کلمات: {filter_status}

📊 آمار:
• دشمنان پیوی: {pv_enemies}
• پی‌وی‌های قفل‌شده: {len(db.get_locked_pvs(self.user_id))}
• کانال‌های نظر‌دهی: {comment_channels}
• رسانه‌های ذخیره‌شده: {cached_media}
• کلمات فیلتر فعال: {active_filters}
• پیام‌های اسپم ذخیره شده: {spam_messages}
• کاربران ذخیره شده: {user_count}

🛡️ حفاظت اسپم:
• وضعیت: {'فعال' if spam_settings.get('spam_protection') else 'غیرفعال'}
• محدودیت: {spam_settings.get('spam_limit', 10)} پیام در {spam_settings.get('mute_duration', 10)} ثانیه
━━━━━━━━━━━━━━━━━━━━
        """
    
    async def handle_commands(self, event):
        if event.sender_id != self.my_id:
            return
        command_text = event.text.strip()
        chat_id = event.chat_id
        
        if command_text in ['.پنل', 'پنل', '/panel']:
            try:
                bot_username = BOT_USERNAME.replace('@', '')
                results = await self.client.inline_query(bot_username, '')
                if results and len(results) > 0:
                    await results[0].click(chat_id)
                    await event.delete()
                else:
                    await event.edit("❌ پنل یافت نشد. ربات را چک کنید.")
            except Exception as e:
                await event.edit(f"❌ خطا در باز کردن پنل: {str(e)[:100]}")
            return
        
        if command_text.startswith('.اهنگ '):
            song_name = command_text[6:].strip()
            if not song_name:
                await event.edit("❌ نام آهنگ را وارد کنید.")
                return
            await event.edit(f"🎵 در حال جستجوی: {song_name}...")
            try:
                bot_username = MUSIC_BOT.replace('@', '')
                results = await self.client.inline_query(bot_username, song_name)
                if results and len(results) > 0:
                    await results[0].click(chat_id)
                    await event.delete()
                else:
                    await event.edit(f"❌ آهنگی یافت نشد.")
            except Exception as e:
                await event.edit(f"❌ خطا: {str(e)[:100]}")
            return
        
        if command_text.startswith('تایم ') and not command_text.startswith('تایم روشن') and not command_text.startswith('تایم خاموش'):
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
                    await event.edit(f"❌ محدوده مجاز: 0 تا {len(classic_fonts)-1}")
                return
        
        if command_text.startswith('.فیلتر '):
            word = command_text[8:].strip()
            if word:
                db.add_filter_word(self.user_id, word)
                await event.edit(f"✅ کلمه {word} فیلتر شد.")
            return
        if command_text.startswith('حذف فیلتر '):
            word = command_text[11:].strip()
            if word:
                db.remove_filter_word(self.user_id, word)
                await event.edit(f"✅ کلمه {word} آزاد شد.")
            return
        if command_text == 'لیست فیلتر':
            filters = db.get_filter_words(self.user_id)
            if filters:
                msg = "📜 کلمات فیلتر:\n\n" + "\n".join([f"- {w['word']}" for w in filters])
                await event.edit(msg)
            else:
                await event.edit("📭 لیست فیلتر خالی است.")
            return
        if command_text == 'فیلتر روشن':
            db.set_filter_enabled(self.user_id, True)
            await event.edit("✅ فیلتر فعال شد.")
            return
        if command_text == 'فیلتر خاموش':
            db.set_filter_enabled(self.user_id, False)
            await event.edit("✅ فیلتر خاموش شد.")
            return
            
        if command_text == 'وضعیت':
            settings = db.get_selfbot_settings(self.user_id)
            await event.edit(self.format_status_info(settings))
            return
        if command_text == 'پینگ':
            start = time.time()
            await event.edit("🏓 پینگ: ...")
            ping = round((time.time() - start) * 1000, 2)
            await event.edit(f"🏓 پینگ: {ping} ms")
            return
        if command_text == 'شروع':
            await event.delete()
            await event.respond("🌟 سلف‌بات با موفقیت شروع شد.")
    
    async def handle_outgoing_message(self, event):
        message_text = event.text or ""
        self.last_active_chat_id = event.chat_id
        if event.is_private:
            self.last_active_pv_id = event.chat_id
            
        if self.adding_spam and message_text and not message_text.startswith('.'):
            db.add_enemy_spam_message(self.user_id, message_text)
            try:
                await event.delete()
            except:
                pass
            return
            
        if event.text:
            settings = db.get_selfbot_settings(self.user_id)
            text_style = settings.get('text_style')
            if text_style and not message_text.startswith('.'):
                try:
                    text, entities = await apply_text_style(message_text, text_style)
                    if entities:
                        await event.message.edit(text, formatting_entities=entities)
                except:
                    pass
                    
        if self.search_mode and message_text and not message_text.startswith('.'):
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
    
    async def update_profile_name(self):
        settings = db.get_selfbot_settings(self.user_id)
        if settings.get('time_enabled'):
            now = datetime.now()
            current_minute = now.minute
            
            if self.time_font_indices == 'all':
                font_index = current_minute % len(classic_fonts)
            elif isinstance(self.time_font_indices, list) and self.time_font_indices:
                if hasattr(self, 'time_font_cycle'):
                    self.time_font_cycle = (self.time_font_cycle + 1) % len(self.time_font_indices)
                else:
                    self.time_font_cycle = 0
                font_index = self.time_font_indices[self.time_font_cycle]
            else:
                font_index = 0
                
            time_now = now.strftime("%H:%M")
            time_now_classic = convert_to_classic_font(time_now, font_index)
            
            try:
                current_name = db.get_current_name(self.user_id) or self.BASE_NAME
                if settings.get('flag_enabled'):
                    flag = flags[current_minute % len(flags)]
                    new_name = f"『 {flag} 』{current_name} {time_now_classic}"
                else:
                    new_name = f"{current_name} | {time_now_classic}"
                await self.client(UpdateProfileRequest(first_name=new_name))
            except:
                pass
    
    async def restore_profile_name(self):
        try:
            current_name = db.get_current_name(self.user_id) or db.get_original_name(self.user_id) or self.BASE_NAME
            await self.client(UpdateProfileRequest(first_name=current_name))
        except Exception as e:
            logger.error(f"خطا در بازگرداندن نام: {e}")
    
    async def update_profile_task(self):
        while self.running:
            await self.update_profile_name()
            await asyncio.sleep(60)
            
    async def heart_animation(self, chat_id):
        try:
            message = await self.client.send_message(chat_id, HEARTS[0])
            for i in range(1, len(HEARTS) * 3):
                await asyncio.sleep(4)
                await self.client.edit_message(chat_id, message, HEARTS[i % len(HEARTS)])
            await self.client.delete_messages(chat_id, message)
        except:
            pass
            
    async def moon_animation(self, chat_id):
        try:
            message = await self.client.send_message(chat_id, MOONS[0])
            for i in range(1, len(MOONS) * 3):
                await asyncio.sleep(3)
                await self.client.edit_message(chat_id, message, MOONS[i % len(MOONS)])
            await self.client.delete_messages(chat_id, message)
        except:
            pass

# ========== توابع کیبوردهای پنل اصلی و زیرمنوها ==========
def get_main_panel_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("⚈ زمان و پروفایل", callback_data=f"time_menu_{user_id}"),
            InlineKeyboardButton("⚉ انیمیشن", callback_data=f"animation_menu_{user_id}"),
            InlineKeyboardButton("⚇ مدیریت کاربران", callback_data=f"user_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("☗ قفل رسانه", callback_data=f"lock_menu_{user_id}"),
            InlineKeyboardButton("☖ کامنت", callback_data=f"comment_menu_{user_id}"),
            InlineKeyboardButton("⊖ عمومی", callback_data=f"general_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("✈ اکشن", callback_data=f"action_menu_{user_id}"),
            InlineKeyboardButton("⚗ بازی‌ها", callback_data=f"games_menu_{user_id}"),
            InlineKeyboardButton("⚜ ترجمه", callback_data=f"translate_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("⚕ گوگل", callback_data=f"google_menu_{user_id}"),
            InlineKeyboardButton("☦ اطلاعاتی", callback_data=f"info_menu_{user_id}"),
            InlineKeyboardButton("☥ پروفایل", callback_data=f"profile_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("☹ استایل متن", callback_data=f"style_menu_{user_id}"),
            InlineKeyboardButton("☻ مدیریت پیام", callback_data=f"message_menu_{user_id}"),
            InlineKeyboardButton("❍ ریکشن", callback_data=f"reaction_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("✿ اسپم", callback_data=f"spam_menu_{user_id}"),
            InlineKeyboardButton("✼ تغییر پروفایل", callback_data=f"change_menu_{user_id}"),
            InlineKeyboardButton("☯ مدیریت دشمنان", callback_data=f"enemy_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("⚈ فیلتر کلمات", callback_data=f"filter_menu_{user_id}"),
            InlineKeyboardButton("⚉ حفاظت اسپم", callback_data=f"protection_menu_{user_id}"),
            InlineKeyboardButton("⚇ هوش مصنوعی", callback_data=f"ai_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("☗ گزارش", callback_data=f"report_menu_{user_id}"),
            InlineKeyboardButton("☖ پیام همگانی", callback_data=f"broadcast_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("❌ بستن پنل", callback_data=f"close_panel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_broadcast_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("📝 پیام همگانی", callback_data=f"exec_broadcast_{user_id}"),
            InlineKeyboardButton("📊 آمار کاربران", callback_data=f"exec_user_stats_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_time_menu_keyboard(user_id):
    settings = db.get_selfbot_settings(user_id)
    time_enabled = bool(settings.get('time_enabled', 0))
    flag_enabled = bool(settings.get('flag_enabled', 0))
    
    keyboard = [
        [
            InlineKeyboardButton(f"🕐 تایم روشن {'✓' if (time_enabled and not flag_enabled) else '✗'}", callback_data=f"exec_time_on_{user_id}"),
            InlineKeyboardButton(f"🏳️ تایمر پرچم {'✓' if (time_enabled and flag_enabled) else '✗'}", callback_data=f"exec_time_flag_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🚫 تایم خاموش {'✓' if not time_enabled else '✗'}", callback_data=f"exec_time_off_{user_id}"),
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
    manager = selfbot_managers.get(str(user_id))
    target_text = ""
    if manager and manager.last_active_pv_id:
        target_text = f" (پیوی {manager.last_active_pv_id})"
        
    keyboard = [
        [
            InlineKeyboardButton(f"🥷 دشمن{target_text}", callback_data=f"exec_user_enemy_{user_id}"),
            InlineKeyboardButton(f"🧸 دوست{target_text}", callback_data=f"exec_user_friend_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🔒 قفل پیوی{target_text}", callback_data=f"exec_user_lockpv_{user_id}"),
            InlineKeyboardButton(f"🔓 باز پیوی{target_text}", callback_data=f"exec_user_unlockpv_{user_id}")
        ],
        [
            InlineKeyboardButton("🔒 قفل پیوی همه", callback_data=f"exec_user_lockall_{user_id}"),
            InlineKeyboardButton("🔓 باز پیوی همه", callback_data=f"exec_user_unlockall_{user_id}"),
            InlineKeyboardButton(f"⛔ بلاک{target_text}", callback_data=f"exec_user_block_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_lock_menu_keyboard(user_id):
    manager = selfbot_managers.get(str(user_id))
    target_id = manager.last_active_pv_id if (manager and manager.last_active_pv_id) else 0
    locks = db.get_media_locks(user_id, target_id)
    
    keyboard = [
        [
            InlineKeyboardButton(f"🔗 لینک {'✓' if locks.get('lock_link') else '✗'}", callback_data=f"exec_toggle_lock_link_{user_id}"),
            InlineKeyboardButton(f"📸 عکس {'✓' if locks.get('lock_photo') else '✗'}", callback_data=f"exec_toggle_lock_photo_{user_id}"),
            InlineKeyboardButton(f"🎥 ویدیو {'✓' if locks.get('lock_video') else '✗'}", callback_data=f"exec_toggle_lock_video_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🎨 استیکر {'✓' if locks.get('lock_sticker') else '✗'}", callback_data=f"exec_toggle_lock_sticker_{user_id}"),
            InlineKeyboardButton(f"🎞️ گیف {'✓' if locks.get('lock_gif') else '✗'}", callback_data=f"exec_toggle_lock_gif_{user_id}"),
            InlineKeyboardButton(f"🎤 ویس {'✓' if locks.get('lock_voice') else '✗'}", callback_data=f"exec_toggle_lock_voice_{user_id}")
        ],
        [
            InlineKeyboardButton(f"📁 فایل {'✓' if locks.get('lock_file') else '✗'}", callback_data=f"exec_toggle_lock_file_{user_id}"),
            InlineKeyboardButton(f"🎵 موزیک {'✓' if locks.get('lock_music') else '✗'}", callback_data=f"exec_toggle_lock_music_{user_id}"),
            InlineKeyboardButton(f"📹 ویدیو نوت {'✓' if locks.get('lock_video_note') else '✗'}", callback_data=f"exec_toggle_lock_video_note_{user_id}")
        ],
        [
            InlineKeyboardButton(f"📞 کانتکت {'✓' if locks.get('lock_contact') else '✗'}", callback_data=f"exec_toggle_lock_contact_{user_id}"),
            InlineKeyboardButton(f"📍 لوکیشن {'✓' if locks.get('lock_location') else '✗'}", callback_data=f"exec_toggle_lock_location_{user_id}"),
            InlineKeyboardButton(f"😀 ایموجی {'✓' if locks.get('lock_emoji') else '✗'}", callback_data=f"exec_toggle_lock_emoji_{user_id}")
        ],
        [
            InlineKeyboardButton(f"📝 متن {'✓' if locks.get('lock_text') else '✗'}", callback_data=f"exec_toggle_lock_text_{user_id}")
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
            InlineKeyboardButton("📊 وضعیت", callback_data=f"exec_status_{user_id}"),
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
    else:
        settings = db.get_selfbot_settings(user_id)
        translate_mode = settings.get('translate', {})
        
    keyboard = [
        [
            InlineKeyboardButton(f"🇬🇧 انگلیسی {'✓' if translate_mode.get('english') else '✗'}", callback_data=f"exec_translate_en_{user_id}"),
            InlineKeyboardButton(f"🇸🇦 عربی {'✓' if translate_mode.get('arabic') else '✗'}", callback_data=f"exec_translate_ar_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🇮🇱 عبری {'✓' if translate_mode.get('hebrew') else '✗'}", callback_data=f"exec_translate_he_{user_id}"),
            InlineKeyboardButton(f"🇷🇺 روسی {'✓' if translate_mode.get('russian') else '✗'}", callback_data=f"exec_translate_ru_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🇹🇷 ترکی {'✓' if translate_mode.get('turkish') else '✗'}", callback_data=f"exec_translate_tr_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_google_menu_keyboard(user_id):
    keyboard = [
        [
            InlineKeyboardButton("🔍 سرچ", callback_data=f"exec_search_on_{user_id}"),
            InlineKeyboardButton("❌ خروج جستجو", callback_data=f"exec_search_off_{user_id}"),
            InlineKeyboardButton("🎵 اهنگ", callback_data=f"exec_music_{user_id}")
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
    current = settings.get('text_style')
    
    keyboard = [
        [
            InlineKeyboardButton(f"بولد {'✓' if current == 'بولد' else '✗'}", callback_data=f"exec_style_bold_{user_id}"),
            InlineKeyboardButton(f"زیرخط {'✓' if current == 'زیرخط' else '✗'}", callback_data=f"exec_style_underline_{user_id}"),
            InlineKeyboardButton(f"خط خورده {'✓' if current == 'خط خورده' else '✗'}", callback_data=f"exec_style_strike_{user_id}")
        ],
        [
            InlineKeyboardButton(f"نقل قول {'✓' if current == 'نقل قول' else '✗'}", callback_data=f"exec_style_quote_{user_id}"),
            InlineKeyboardButton(f"اسپویلر {'✓' if current == 'اسپویلر' else '✗'}", callback_data=f"exec_style_spoiler_{user_id}"),
            InlineKeyboardButton(f"کج {'✓' if current == 'کج' else '✗'}", callback_data=f"exec_style_italic_{user_id}")
        ],
        [
            InlineKeyboardButton(f"کد {'✓' if current == 'کد' else '✗'}", callback_data=f"exec_style_code_{user_id}"),
            InlineKeyboardButton(f"پیش {'✓' if current == 'پیش' else '✗'}", callback_data=f"exec_style_pre_{user_id}")
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
            InlineKeyboardButton("🚫 .فیلتر [کلمه]", callback_data=f"exec_filter_word_{user_id}"),
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
    ai = settings.get('ai_status', {})
    
    keyboard = [
        [
            InlineKeyboardButton(f"🟢 پیوی ۱ {'✓' if ai.get('ai_1_pm') else '✗'}", callback_data=f"exec_ai_toggle_ai_1_pm_{user_id}"),
            InlineKeyboardButton(f"🔵 پیوی ۲ {'✓' if ai.get('ai_2_pm') else '✗'}", callback_data=f"exec_ai_toggle_ai_2_pm_{user_id}"),
            InlineKeyboardButton(f"🟣 پیوی ۳ {'✓' if ai.get('ai_3_pm') else '✗'}", callback_data=f"exec_ai_toggle_ai_3_pm_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🟢 گروه ۱ {'✓' if ai.get('ai_1_group') else '✗'}", callback_data=f"exec_ai_toggle_ai_1_group_{user_id}"),
            InlineKeyboardButton(f"🔵 گروه ۲ {'✓' if ai.get('ai_2_group') else '✗'}", callback_data=f"exec_ai_toggle_ai_2_group_{user_id}"),
            InlineKeyboardButton(f"🟣 گروه ۳ {'✓' if ai.get('ai_3_group') else '✗'}", callback_data=f"exec_ai_toggle_ai_3_group_{user_id}")
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
                input_message_content=InputTextMessageContent("⛔ شما به این پنل دسترسی ندارید\n\nبرای عضویت: /start")
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
                input_message_content=InputTextMessageContent("🌟 پنل سلف‌بات باز شد\n\n⚠️ توجه: این پنل فقط مخصوص شماست"),
                reply_markup=get_main_panel_keyboard(user_id)
            ),
        ]
        
        if user_id == ADMIN_ID:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="👑 پنل ادمین",
                    description="مدیریت کاربران و سلف‌بات‌ها و ارسال پیام همگانی",
                    input_message_content=InputTextMessageContent("👑 پنل ادمین"),
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
                            InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats"),
                            InlineKeyboardButton("📢 پیام همگانی", callback_data=f"admin_broadcast")
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
            ("🔒 قفل رسانه", "lock", "قفل لینک/عکس/ویدیو/استیکر/ویس/فایل/موزیک/ویدیو نوت/کانتکت/لوکیشن/ایموجی/متن"),
            ("💬 کامنت", "comment", "کامنت خودکار در کانال"),
            ("📋 عمومی", "general", "وضعیت/درباره/پینگ"),
            ("🎮 اکشن", "action", "اکشن‌های تایپ و ..."),
            ("🎲 بازی‌ها", "games", "تاس/دارت/بسکتبال/فوتبال"),
            ("🌐 ترجمه", "translate", "ترجمه به زبان‌های مختلف"),
            ("🔍 گوگل", "google", "جستجوی گوگل/اهنگ"),
            ("ℹ️ اطلاعاتی", "info", "اطلاعات کاربر و دانلود پروفایل"),
            ("📸 پروفایل", "profile", "کپی پروفایل و بیو"),
            ("✍️ استایل متن", "style", "بولد/زیرخط/خط خورده/نقل قول/اسپویلر/کج/کد/پیش"),
            ("📨 مدیریت پیام", "message", "حذف پیام و اتوسین"),
            ("😊 ریکشن", "reaction", "ریکت خودکار"),
            ("📩 اسپم", "spam", "ارسال اسپم"),
            ("✏️ تغییر پروفایل", "change", "تغییر نام/بیو/پروفایل"),
            ("🥷 مدیریت دشمنان", "enemy", "لیست دشمن/اضافه اسپم"),
            ("🚫 فیلتر کلمات", "filter", "فیلتر کلمات"),
            ("🛡️ حفاظت اسپم", "protection", "محافظت در برابر اسپم"),
            ("🤖 هوش مصنوعی", "ai", "مدیریت هوش مصنوعی"),
            ("📊 گزارش", "report", "تنظیم گروه گزارش"),
            ("📢 پیام همگانی", "broadcast", "ارسال پیام به همه کاربران")
        ]
        
        for title, cmd, desc in all_commands:
            if search in title.lower() or search in desc.lower() or search in cmd.lower():
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title=title,
                        description=desc,
                        input_message_content=InputTextMessageContent(f"✅ دستور {title} ارسال شد"),
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(f"ℹ️ توضیحات", callback_data=f"desc_{cmd}"),
                            InlineKeyboardButton(f"▶️ باز کردن", callback_data=f"menu_{cmd}")
                        ]])
                    )
                )
    await query.answer(results, cache_time=1, is_personal=True)

async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    await query.edit_message_text(
        "📢 ارسال پیام همگانی\n\n"
        "لطفاً پیام خود را ارسال کنید.\n\n"
        "⚠️ توجه: این پیام برای همه کاربران فعال ارسال خواهد شد.\n\n"
        "برای لغو: /cancel"
    )
    context.user_data['broadcast_mode'] = True

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if not context.user_data.get('broadcast_mode'):
        return
    if update.message.text == '/cancel':
        context.user_data['broadcast_mode'] = False
        await update.message.reply_text("✅ ارسال پیام همگانی لغو شد")
        return
    
    message_text = update.message.text
    await update.message.reply_text("⏳ در حال ارسال پیام همگانی...")
    
    all_users = db.get_all_users()
    active_users = [u for u in all_users if u.get('self_active')]
    sent_count, failed_count = 0, 0
    broadcast_id = db.add_broadcast(user_id, message_text, 'text')
    
    for user in active_users:
        try:
            await context.bot.send_message(
                chat_id=int(user['user_id']),
                text=f"📢 **پیام همگانی**\n━━━━━━━━━━━━━━━━━━━━\n\n{message_text}\n\n━━━━━━━━━━━━━━━━━━━━\n🕐 {datetime.now().strftime('%Y/%m/%d %H:%M')}",
                parse_mode='Markdown'
            )
            sent_count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"خطا در ارسال به {user['user_id']}: {e}")
            failed_count += 1
            
    db.update_broadcast_stats(broadcast_id, sent_count, failed_count)
    result_text = f"""
✅ ارسال پیام همگانی کامل شد!

📊 آمار ارسال:
• کل کاربران فعال: {len(active_users)}
• ارسال موفق: {sent_count}
• ارسال ناموفق: {failed_count}

📝 متن پیام:
{message_text[:200]}

🕐 زمان: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
    """
    await update.message.reply_text(result_text)
    context.user_data['broadcast_mode'] = False

async def membership_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    user_id_str = str(user_id)
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await query.edit_message_text("❌ خطا")
        return
    if user_data.get('self_active'):
        await query.edit_message_text("✅ شما قبلاً عضو شده‌اید")
        return
    if user_data.get('rejected'):
        await query.edit_message_text("❌ درخواست شما رد شده است")
        return
    if user_data.get('request_sent'):
        await query.edit_message_text("⏳ درخواست شما در انتظار تأیید است")
        return
        
    db.update_user(user_id_str, request_sent=1, request_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    admin_text = f"""
📋 درخواست عضویت جدید
━━━━━━━━━━━━━━━━━━━━
👤 نام: {user_data['full_name']}
🆔 آیدی: {user_id_str}
👤 یوزرنیم: @{user_data['username'] if user_data['username'] else 'ندارد'}
📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id_str}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id_str}")
        ]
    ])
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=keyboard)
    await query.edit_message_text("✅ درخواست عضویت شما ثبت شد!\n\n⏳ منتظر تأیید ادمین باشید")

async def membership_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    user_id_str = str(user_id)
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await query.edit_message_text("👤 شما ثبت‌نام نکرده‌اید")
    elif user_data.get('self_active'):
        exp = user_data.get('expiration_date', 'نامشخص')
        await query.edit_message_text(f"✅ شما عضو فعال هستید\n\n📅 انقضا: {exp}")
    elif user_data.get('admin_approved'):
        await query.edit_message_text("⏳ در مرحله ورود اطلاعات\n\nشماره تلفن خود را وارد کنید")
    elif user_data.get('request_sent'):
        await query.edit_message_text("⏳ درخواست شما در انتظار تأیید است")
    elif user_data.get('rejected'):
        await query.edit_message_text("❌ درخواست شما رد شده است")
    else:
        await query.edit_message_text("👤 وضعیت نامشخص")

async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text("⛔ دسترسی غیرمجاز")
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
            InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats"),
            InlineKeyboardButton("📢 پیام همگانی", callback_data=f"admin_broadcast")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])
    await query.edit_message_text("👑 پنل مدیریت\n\nلطفاً انتخاب کنید:", reply_markup=keyboard)

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
        text = "📋 درخواست‌های عضویت:\n\n"
        keyboard = []
        for req in pending[:10]:
            text += f"👤 {req['full_name']}\n🆔 {req['user_id']}\n📅 {req.get('request_date', 'نامشخص')}\n\n"
            keyboard.append([
                InlineKeyboardButton(f"✅ تأیید {req['user_id']}", callback_data=f"approve_{req['user_id']}"),
                InlineKeyboardButton(f"❌ رد {req['user_id']}", callback_data=f"reject_{req['user_id']}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("📋 هیچ درخواستی در انتظار نیست")

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
        text = "🔐 کاربران در مرحله ورود:\n\n"
        for user in pending[:10]:
            text += f"👤 {user['full_name']}\n🆔 {user['user_id']}\n📞 {user.get('phone', 'نامشخص')}\nمرحله: {user.get('step', 'نامشخص')}\n\n"
        await query.edit_message_text(text)
    else:
        await query.edit_message_text("🔐 هیچ کاربری در مرحله ورود نیست")

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
        text = "✅ کاربران فعال:\n\n"
        for user in active[:10]:
            text += f"👤 {user['full_name']}\n🆔 {user['user_id']}\n📞 {user.get('phone', 'نامشخص')}\n📅 انقضا: {user.get('expiration_date', 'نامشخص')}\n"
            text += f"🤖 سلف‌بات: {'✅' if user['user_id'] in selfbot_managers else '❌'}\n\n"
        await query.edit_message_text(text)
    else:
        await query.edit_message_text("✅ هیچ کاربر فعالی وجود ندارد")

async def admin_selfbots_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        return
    
    if selfbot_managers:
        text = "🤖 سلف‌بات‌های فعال:\n\n"
        keyboard = []
        for uid, manager in list(selfbot_managers.items())[:10]:
            user_data = db.get_user(uid)
            name = user_data['full_name'] if user_data else f"کاربر {uid}"
            text += f"👤 {name}\n🆔 {uid}\n\n"
            keyboard.append([
                InlineKeyboardButton(f"🛑 توقف {uid}", callback_data=f"stop_selfbot_{uid}"),
                InlineKeyboardButton(f"🔄 ریستارت {uid}", callback_data=f"restart_selfbot_{uid}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("🤖 هیچ سلف‌باتی در حال اجرا نیست")

async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        return
    
    total_users = len(db.get_all_users())
    active_users = len(db.get_active_users())
    pending_requests = len(db.get_pending_requests())
    pending_login = len(db.get_pending_login())
    active_selfbots = len(selfbot_managers)
    
    stats = f"""
📊 آمار کلی
━━━━━━━━━━━━━━━━━━━━
👥 کل کاربران: {total_users}
✅ کاربران فعال: {active_users}
📋 درخواست‌ها: {pending_requests}
🔐 منتظر ورود: {pending_login}
🤖 سلف‌بات فعال: {active_selfbots}

🕐 آخرین به‌روزرسانی: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
    """
    await query.edit_message_text(stats)

async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    target_id = query.data.split('_')[1]
    user_data = db.get_user(target_id)
    if not user_data:
        await query.answer("❌ کاربر یافت نشد", show_alert=True)
        return
    
    db.update_user(target_id, admin_approved=1, activation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text="🎉 درخواست عضویت شما تأیید شد!\n\nلطفاً شماره تلفن خود را وارد کنید:\nمثال: +989123456789"
        )
        db.update_user(target_id, step='get_phone')
    except:
        pass
    await query.edit_message_text(f"✅ کاربر {target_id} تأیید شد")

async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    target_id = query.data.split('_')[1]
    user_data = db.get_user(target_id)
    if not user_data:
        await query.answer("❌ کاربر یافت نشد", show_alert=True)
        return
    
    db.update_user(target_id, rejected=1, request_sent=0)
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text="⚠ درخواست عضویت شما رد شد.\n\nمی‌توانید دوباره درخواست دهید"
        )
    except:
        pass
    await query.edit_message_text(f"❌ کاربر {target_id} رد شد")

async def stop_selfbot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    target_id = query.data.split('_')[2]
    if target_id in selfbot_managers:
        await selfbot_managers[target_id].stop()
        del selfbot_managers[target_id]
        await query.answer(f"✅ سلف‌بات کاربر {target_id} متوقف شد", show_alert=True)
    else:
        await query.answer("❌ سلف‌بات فعال نیست", show_alert=True)

async def restart_selfbot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    target_id = query.data.split('_')[2]
    user_data = db.get_user(target_id)
    if not user_data or not user_data.get('self_active'):
        await query.answer("❌ کاربر فعال نیست", show_alert=True)
        return
    
    session_file = user_data.get('session_file')
    if not session_file or not os.path.exists(session_file):
        await query.answer("❌ فایل سشن یافت نشد", show_alert=True)
        return
    
    if target_id in selfbot_managers:
        await selfbot_managers[target_id].stop()
        del selfbot_managers[target_id]
    
    manager = SelfBotManager(target_id)
    if await manager.start(session_file):
        selfbot_managers[target_id] = manager
        await query.answer(f"✅ سلف‌بات کاربر {target_id} راه‌اندازی مجدد شد", show_alert=True)
    else:
        await query.answer("❌ خطا در راه‌اندازی مجدد", show_alert=True)

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
            await query.answer("⛔ این پنل مال شما نیست", show_alert=True)
            return
            
    if user_id_str not in selfbot_managers:
        await query.edit_message_text("❌ سلف‌بات شما فعال نیست")
        return
    
    manager = selfbot_managers[user_id_str]
    cmd = data.replace(f'exec_', '').replace(f'_{user_id}', '')
    
    # ---------- بخش ۱: تاگل‌ها و ادیت مستقیم کیبورد (بروزرسانی تیک‌ها و دکمه‌ها) ----------
    if cmd.startswith('translate_'):
        lang_key = cmd.replace('translate_', '')
        lang_map = {
            "en": "english", "ar": "arabic", "he": "hebrew", "ru": "russian", "tr": "turkish"
        }
        if lang_key in lang_map:
            db_key = lang_map[lang_key]
            current_status = manager.translate_mode.get(db_key, False)
            new_status = not current_status
            manager.translate_mode[db_key] = new_status
            db.update_selfbot_setting(user_id, f"translate_{db_key}", 1 if new_status else 0)
            await query.edit_message_reply_markup(reply_markup=get_translate_menu_keyboard(user_id))
        return

    elif cmd.startswith('time_'):
        action = cmd.replace('time_', '')
        if action == 'on':
            db.update_selfbot_setting(user_id, 'time_enabled', 1)
            db.update_selfbot_setting(user_id, 'flag_enabled', 0)
            await manager.update_profile_name()
        elif action == 'flag':
            db.update_selfbot_setting(user_id, 'time_enabled', 1)
            db.update_selfbot_setting(user_id, 'flag_enabled', 1)
            await manager.update_profile_name()
        elif action == 'off':
            db.update_selfbot_setting(user_id, 'time_enabled', 0)
            db.update_selfbot_setting(user_id, 'flag_enabled', 0)
            await manager.restore_profile_name()
        await query.edit_message_reply_markup(reply_markup=get_time_menu_keyboard(user_id))
        return

    elif cmd.startswith('toggle_lock_'):
        lock_key = cmd.replace('toggle_lock_', '')
        target_id = manager.last_active_pv_id if manager.last_active_pv_id else 0
        locks = db.get_media_locks(user_id, target_id)
        current_status = locks.get(f'lock_{lock_key}', 0)
        new_status = not current_status
        db.set_media_lock(user_id, target_id, f'lock_{lock_key}', 1 if new_status else 0)
        await query.edit_message_reply_markup(reply_markup=get_lock_menu_keyboard(user_id))
        return

    elif cmd.startswith('style_'):
        style_key = cmd.replace('style_', '')
        style_map = {
            "bold": "بولد", "underline": "زیرخط", "strike": "خط خورده",
            "quote": "نقل قول", "spoiler": "اسپویلر", "italic": "کج",
            "code": "کد", "pre": "پیش"
        }
        if style_key in style_map:
            mapped_style = style_map[style_key]
            settings = db.get_selfbot_settings(user_id)
            current = settings.get('text_style')
            if current == mapped_style:
                db.update_selfbot_setting(user_id, 'text_style', None)
            else:
                db.update_selfbot_setting(user_id, 'text_style', mapped_style)
            await query.edit_message_reply_markup(reply_markup=get_style_menu_keyboard(user_id))
        return

    elif cmd.startswith('ai_toggle_'):
        ai_key = cmd.replace('ai_toggle_', '')
        settings = db.get_selfbot_settings(user_id)
        ai_status = settings.get('ai_status', {})
        current_status = ai_status.get(ai_key, False)
        new_status = not current_status
        if new_status:
            if 'pm' in ai_key:
                for k in ['ai_1_pm', 'ai_2_pm', 'ai_3_pm']:
                    ai_status[k] = False
            elif 'group' in ai_key:
                for k in ['ai_1_group', 'ai_2_group', 'ai_3_group']:
                    ai_status[k] = False
        ai_status[ai_key] = new_status
        db.update_ai_status(user_id, ai_status)
        await query.edit_message_reply_markup(reply_markup=get_ai_menu_keyboard(user_id))
        return

    elif cmd.startswith('user_'):
        action = cmd.replace('user_', '')
        target_id = manager.last_active_pv_id
        if not target_id and action not in ['lockall', 'unlockall']:
            await query.edit_message_text("⚠️ شما در پیوی هیچ کاربری نیستید یا آخرین پیوی فعال ثبت نشده است.")
            return
        
        if action == 'enemy':
            db.add_enemy(user_id, target_id, 'pv')
            await manager.spam_enemy(target_id)
            await query.edit_message_text(f"✅ کاربر {target_id} به عنوان دشمن تعریف شد و اسپم آغاز گردید.")
        elif action == 'friend':
            db.remove_enemy(user_id, target_id, 'pv')
            if target_id in manager.spam_tasks:
                manager.spam_tasks[target_id].cancel()
                del manager.spam_tasks[target_id]
            await query.edit_message_text(f"✅ کاربر {target_id} از لیست دشمنان خارج شد.")
        elif action == 'lockpv':
            db.add_locked_pv(user_id, target_id)
            await query.edit_message_text(f"✅ پیوی کاربر {target_id} با موفقیت قفل شد.")
        elif action == 'unlockpv':
            db.remove_locked_pv(user_id, target_id)
            await query.edit_message_text(f"✅ قفل پیوی کاربر {target_id} باز شد.")
        elif action == 'lockall':
            db.update_selfbot_setting(user_id, 'pv_lock_all', 1)
            await query.edit_message_text("✅ قفل همگانی پیوی فعال شد.")
        elif action == 'unlockall':
            db.update_selfbot_setting(user_id, 'pv_lock_all', 0)
            await query.edit_message_text("✅ قفل همگانی پیوی غیرفعال شد.")
        elif action == 'block':
            try:
                await manager.client(BlockRequest(id=target_id))
                await query.edit_message_text(f"✅ کاربر {target_id} مسدود گردید.")
            except Exception as e:
                await query.edit_message_text(f"❌ خطا در مسدودسازی: {e}")
        return

    # ---------- بخش ۲: هدایت انیمیشن‌ها به چت فعال ----------
    elif cmd in ['heart', 'moon', 'advanced_heart', 'love', 'santet', 'hack']:
        target_chat = manager.last_active_chat_id if manager.last_active_chat_id else query.message.chat_id
        if cmd == 'heart':
            asyncio.create_task(manager.heart_animation(target_chat))
            await query.edit_message_text("❤️ انیمیشن قلب آغاز گردید.")
        elif cmd == 'moon':
            asyncio.create_task(manager.moon_animation(target_chat))
            await query.edit_message_text("🌙 انیمیشن ماه آغاز گردید.")
        elif cmd == 'advanced_heart':
            try:
                heart_msg = await manager.client.send_message(target_chat, "❤️")
                asyncio.create_task(advanced_heart_animation(heart_msg))
                await query.edit_message_text("💖 انیمیشن قلب پیشرفته آغاز گردید.")
            except Exception as e:
                await query.edit_message_text(f"❌ خطا: {e}")
        elif cmd == 'love':
            try:
                love_msg = await manager.client.send_message(target_chat, "💝")
                asyncio.create_task(advanced_heart_animation(love_msg))
                await query.edit_message_text("💝 انیمیشن عشق آغاز گردید.")
            except Exception as e:
                await query.edit_message_text(f"❌ خطا: {e}")
        elif cmd == 'santet':
            try:
                santet_msg = await manager.client.send_message(target_chat, "🕯️")
                async def run_santet():
                    for i in range(101):
                        bar_len = int(i / 100 * 20)
                        bar = "█" * bar_len + "░" * (20 - bar_len)
                        await santet_msg.edit(f"🕯️ {i}% [{bar}]")
                        await asyncio.sleep(0.03)
                    await asyncio.sleep(1)
                    await santet_msg.edit("✅ انجام شد 🥴")
                asyncio.create_task(run_santet())
                await query.edit_message_text("🕯️ فرآیند سنتت آغاز گردید.")
            except Exception as e:
                await query.edit_message_text(f"❌ خطا: {e}")
        elif cmd == 'hack':
            try:
                hack_msg = await manager.client.send_message(target_chat, "💻")
                async def run_hack():
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("User online: True\nTelegram access: True\nRead Storage: True")
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]")
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("Hacking... 25%\n[█████░░░░░░░░░░░░░░░]")
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("Hacking... 50%\n[██████████░░░░░░░░░░]")
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("Hacking... 75%\n[███████████████░░░░░]")
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("Hacking... 100%\n[████████████████████]")
                    await asyncio.sleep(1.5)
                    await hack_msg.edit("✅ هک کامل شد")
                asyncio.create_task(run_hack())
                await query.edit_message_text("💻 فرآیند شبیه‌ساز هک آغاز گردید.")
            except Exception as e:
                await query.edit_message_text(f"❌ خطا: {e}")
        return

    # ---------- بخش ۳: سایر دستورات عمومی پنل ----------
    msg = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"⏳ در حال اجرا..."
    )
    
    if cmd == 'status':
        settings = db.get_selfbot_settings(user_id)
        await msg.edit_text(manager.format_status_info(settings))
    elif cmd == 'about':
        await msg.edit_text(f"ℹ️ درباره بات\n\n🤖 نسخه: v{BOT_VERSION}\n👨‍💻 سازنده: {BOT_CREATOR}")
    elif cmd == 'ping':
        start = time.time()
        await msg.edit_text("🏓 پینگ: ...")
        ping = round((time.time() - start) * 1000, 2)
        await msg.edit_text(f"🏓 پینگ: {ping} ms")
    elif cmd == 'music':
        await msg.edit_text("🎵 دستور اهنگ\n\nبرای جستجو و پخش آهنگ از فرمت زیر استفاده کنید:\n\n`.اهنگ [نام آهنگ]`\n\nمثال: `.اهنگ مهدیار احمدی`")
    elif cmd == 'broadcast':
        await msg.edit_text("📢 ارسال پیام همگانی\n\nلطفاً پیام خود را به صورت مستقیم برای ربات ارسال کنید.")
    elif cmd == 'user_stats':
        all_users = db.get_all_users()
        active_users = db.get_active_users()
        stats = f"""
📊 آمار کاربران:
━━━━━━━━━━━━━━━━━━━━
👥 کل کاربران ثبت‌نام: {len(all_users)}
✅ کاربران فعال: {len(active_users)}
📋 در انتظار تأیید: {len(db.get_pending_requests())}
🔐 در مرحله ورود: {len(db.get_pending_login())}
🤖 سلف‌بات فعال: {len(selfbot_managers)}
━━━━━━━━━━━━━━━━━━━━
        """
        await msg.edit_text(stats)
    elif cmd.startswith('full_date'):
        await msg.edit_text(get_full_date_info())
    elif cmd.startswith('enemy_list'):
        enemies = db.get_enemies(user_id, 'pv')
        if enemies:
            message = "📋 لیست دشمنان:\n\n"
            for i, enemy_id in enumerate(enemies, 1):
                try:
                    enemy = await manager.client.get_entity(enemy_id)
                    enemy_name = enemy.first_name or f"کاربر {enemy_id}"
                    message += f"{i}. {enemy_name} ({enemy_id})\n"
                except:
                    message += f"{i}. کاربر {enemy_id}\n"
            await msg.edit_text(message)
        else:
            await msg.edit_text("📭 لیست دشمنان خالی است")
    elif cmd.startswith('add_spam'):
        manager.adding_spam = True
        await msg.edit_text("📝 حالت اضافه کردن اسپم فعال شد\nبرای پایان: اتمام اسپم")
    elif cmd.startswith('end_spam'):
        manager.adding_spam = False
        await msg.edit_text("✅ حالت اضافه کردن اسپم غیرفعال شد")
    elif cmd.startswith('spam_list'):
        spam_messages = db.get_enemy_spam_messages(user_id)
        if spam_messages:
            message = "📜 لیست پیام‌های اسپم:\n\n"
            for i, spam_msg in enumerate(spam_messages, 1):
                message += f"{i}. {spam_msg['text']}\n"
            message += f"\n📊 تعداد: {len(spam_messages)}"
            await msg.edit_text(message)
        else:
            await msg.edit_text("📭 لیست پیام‌های اسپم خالی است")
    elif cmd.startswith('clear_spam'):
        db.clear_enemy_spam_messages(user_id)
        await msg.edit_text("✅ لیست اسپم پاک شد")
    elif cmd.startswith('delete_spam'):
        await msg.edit_text("🗑️ حذف اسپم [شماره]")
    elif cmd.startswith('filter_word'):
        await msg.edit_text("🚫 .فیلتر [کلمه]")
    elif cmd.startswith('filter_on'):
        db.set_filter_enabled(user_id, True)
        await msg.edit_text("✅ فیلتر کلمات فعال شد")
    elif cmd.startswith('filter_off'):
        db.set_filter_enabled(user_id, False)
        await msg.edit_text("✅ فیلتر کلمات غیرفعال شد")
    elif cmd.startswith('filter_list'):
        filters = db.get_filter_words(user_id)
        if filters:
            message_text = "📜 لیست کلمات فیلتر شده:\n\n"
            for i, word_info in enumerate(filters, 1):
                status = "فعال" if word_info['enabled'] else "غیرفعال"
                message_text += f"{i}. {word_info['word']} - {status}\n"
            await msg.edit_text(message_text)
        else:
            await msg.edit_text("📭 لیست کلمات فیلتر خالی است")
    elif cmd.startswith('filter_remove'):
        await msg.edit_text("🗑️ حذف فیلتر [کلمه]")
    elif cmd.startswith('spam_protection_on'):
        db.set_spam_settings(user_id, spam_protection=1)
        await msg.edit_text("✅ حفاظت اسپم فعال شد")
    elif cmd.startswith('spam_protection_off'):
        db.set_spam_settings(user_id, spam_protection=0)
        await msg.edit_text("✅ حفاظت اسپم غیرفعال شد")
    elif cmd.startswith('spam_settings'):
        await msg.edit_text("⚙️ تنظیم اسپم [تعداد] [زمان]\nمثال: تنظیم اسپم 5 10")
    elif cmd.startswith('spam_status'):
        settings = db.get_spam_settings(user_id)
        status_text = f"""
🛡️ حفاظت اسپم:
🔒 وضعیت: {'فعال' if settings.get('spam_protection') else 'غیرفعال'}
📊 محدودیت: {settings.get('spam_limit', 10)} پیام
⏱️ زمان: {settings.get('mute_duration', 10)} ثانیه
"""
        await msg.edit_text(status_text)
    elif cmd.startswith('set_report'):
        await msg.edit_text("📍 برای تنظیم گروه گزارش: تنظیم گزارش")
    elif cmd.startswith('show_report'):
        report_config = manager.report_config
        await msg.edit_text(f"📍 گروه گزارش:\nآیدی: {report_config.report_group_id}")
    else:
        await msg.edit_text(f"✅ دستور {cmd} اجرا شد")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    if '_' in data and not data.startswith(('admin_', 'approve_', 'reject_', 'stop_selfbot_', 'restart_selfbot_', 'desc_', 'menu_')):
        parts = data.split('_')
        for part in parts:
            if part.isdigit() and len(part) >= 5:
                if part != user_id_str:
                    await query.answer("⛔ این پنل مال شما نیست", show_alert=True)
                    return
                break
                
    if data == "close_panel":
        try:
            if query.message:
                await query.message.delete()
            else:
                await query.edit_message_text("❌ پنل مدیریت بسته شد.")
        except Exception as e:
            logger.error(f"Error closing panel: {e}")
        return
    
    if data == "back_main":
        await query.edit_message_text(
            "🌟 پنل مدیریت سلف‌بات\n\n⚠️ توجه: این پنل فقط مخصوص شماست\n\n✅ سلف‌بات به صورت ۲۴ ساعته فعال می‌ماند",
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
    if data == "admin_broadcast":
        await admin_broadcast_handler(update, context)
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
    if data.startswith("exec_"):
        await exec_command_handler(update, context)
        return
    
    parts = data.split('_')
    if len(parts) > 1:
        action = parts[0]
        menu_keyboards = {
            "time": ("🕐 زمان و پروفایل\n\nتغییر وضعیت یا تنظیمات:", get_time_menu_keyboard),
            "animation": ("❤️ انیمیشن\n\nانتخاب یکی از سناریوهای نمایشی:", get_animation_menu_keyboard),
            "user": ("👥 مدیریت کاربران\n\nمسدودسازی یا کنترل پی‌وی‌های خاص:", get_user_menu_keyboard),
            "lock": ("🔒 قفل رسانه\n\nمحدودسازی ارسال رسانه‌ها در پی‌وی کاربر فعال:", get_lock_menu_keyboard),
            "comment": ("💬 کامنت\n\nتنظیم کامنت خودکار در کانال‌ها:", get_comment_menu_keyboard),
            "general": ("📋 عمومی\n\nمشاهده پینگ یا جزئیات فنی:", get_general_menu_keyboard),
            "action": ("🎮 اکشن\n\nتنظیم افکت در حال نوشتن یا ویس گرفتن:", get_action_menu_keyboard),
            "games": ("🎲 بازی‌ها\n\nارسال بازی با تاس‌های داینامیک:", get_games_menu_keyboard),
            "translate": ("🌐 ترجمه\n\nترجمه خودکار متن‌ها به زبان‌های مختلف:", get_translate_menu_keyboard),
            "google": ("🔍 گوگل و اهنگ\n\nجستجوی نتایج یا دانلود آهنگ:", get_google_menu_keyboard),
            "info": ("ℹ️ اطلاعاتی\n\nدریافت اطلاعات آماری کاربر یا دانلود عکس پروفایل:", get_info_menu_keyboard),
            "profile": ("📸 پروفایل\n\nتنظیم بیو یا کپی کردن پروفایل‌ها:", get_profile_menu_keyboard),
            "style": ("✍️ استایل متن\n\nتغییر ساختار نوشتاری پیام‌ها:", get_style_menu_keyboard),
            "message": ("📨 مدیریت پیام\n\nحذف چت‌ها و پیام‌ها یا اتوسین:", get_message_menu_keyboard),
            "reaction": ("😊 ریکشن\n\nثبت ری‌اکشن به چت‌های دریافتی:", get_reaction_menu_keyboard),
            "spam": ("📩 اسپم\n\nارسال هرزنامه یا پیام مکرر:", get_spam_menu_keyboard),
            "change": ("✏️ تغییر پروفایل\n\nتغییر مستقیم مشخصات اکانت شما:", get_change_menu_keyboard),
            "enemy": ("🥷 مدیریت دشمنان\n\nپیکربندی حملات اسپم مکرر علیه دشمن:", get_enemy_menu_keyboard),
            "filter": ("🚫 فیلتر کلمات\n\nحذف خودکار کلمات خاص در چت‌ها:", get_filter_menu_keyboard),
            "protection": ("🛡️ حفاظت اسپم\n\nمسدودسازی مزاحمین هرزنامه‌نویس:", get_protection_menu_keyboard),
            "ai": ("🤖 هوش مصنوعی\n\nمدیریت و اتصال پاسخگوی خودکار هوشمند:", get_ai_menu_keyboard),
            "report": ("📊 گزارش\n\nتنظیم لاگ یا ارسال گزارش چت به گروه:", get_report_menu_keyboard),
            "broadcast": ("📢 پیام همگانی\n\nارسال پیام انبوه توسط ادمین اصلی سیستم:", get_broadcast_menu_keyboard)
        }
        
        if action in menu_keyboards and parts[1] == "menu":
            text, keyboard_func = menu_keyboards[action]
            await query.edit_message_text(text, reply_markup=keyboard_func(user_id))
            return

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
👋 سلام {full_name} عزیز!

✅ حساب شما فعال است.
• /panel - پنل مدیریت
• @{BOT_USERNAME} - پنل اینلاین
• .پنل - پنل در همین چت
• .اهنگ [نام آهنگ] - پخش آهنگ

⚠️ پنل فقط مخصوص شماست
        """
        keyboard = [[InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]]
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel")])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    text = f"""
👋 سلام {full_name} عزیز!

🌟 به ربات سلف‌بات خوش آمدید.

📌 برای استفاده:
1️⃣ روی دکمه عضویت کلیک کنید
2️⃣ شماره تلفن خود را وارد کنید
3️⃣ کد تأیید را وارد کنید

✅ پس از فعال شدن:
• /panel - پنل مدیریت
• @{BOT_USERNAME} - پنل اینلاین
• .پنل - پنل در همین چت
• .اهنگ [نام آهنگ] - پخش آهنگ
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
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🌟 باز کردن پنل اینلاین", switch_inline_query_current_chat="")]])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🌟 پنل مدیریت سلف‌بات\n\nبرای باز کردن پنل، روی دکمه کلیک کنید:\n\n⚠️ توجه: این پنل فقط مخصوص شماست",
        reply_markup=keyboard
    )

async def membership_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    user_data = db.get_user(user_id_str)
    
    if not user_data:
        await update.message.reply_text("👤 شما ثبت‌نام نکرده‌اید")
    elif user_data.get('self_active'):
        await update.message.reply_text("✅ شما عضو فعال هستید")
    elif user_data.get('admin_approved'):
        await update.message.reply_text("⏳ در مرحله ورود اطلاعات")
    elif user_data.get('request_sent'):
        await update.message.reply_text("⏳ درخواست شما در انتظار تأیید است")
    elif user_data.get('rejected'):
        await update.message.reply_text("❌ درخواست شما رد شده است")
    else:
        await update.message.reply_text("👤 وضعیت عضویت نامشخص")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = convert_persian_to_english(update.message.text)
    
    if context.user_data.get('broadcast_mode') and user_id == ADMIN_ID:
        await handle_broadcast_message(update, context)
        return
    
    user_data = db.get_user(user_id_str)
    if not user_data:
        await start(update, context)
        return
    if user_data.get('rejected'):
        await update.message.reply_text("✖ درخواست شما رد شده است")
        return
        
    if user_data.get('self_active'):
        if user_id_str not in selfbot_managers:
            session_file = user_data.get('session_file')
            if session_file and os.path.exists(session_file):
                manager = SelfBotManager(user_id_str)
                if await manager.start(session_file):
                    selfbot_managers[user_id_str] = manager
                    await update.message.reply_text("🚀 سلف‌بات فعال شد")
                else:
                    await update.message.reply_text("⚠️ خطا در شروع سلف‌بات")
        else:
            await update.message.reply_text("✅ سلف‌بات در حال اجراست")
        return

    step = user_data.get('step')
    if step == 'get_phone':
        if not user_data.get('admin_approved'):
            await update.message.reply_text("⏳ درخواست شما تأیید نشده است")
            return
            
        db.update_user(user_id_str, phone=text, step='get_code')
        await update.message.reply_text(f"✅ شماره {text} ذخیره شد\n⏳ در حال ارسال کد...")
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            if os.path.exists(session_path):
                os.remove(session_path)
            
            user_api = get_user_api(user_id_str)
            if not user_api:
                await update.message.reply_text("❌ خطا در دریافت API")
                return
            
            client = TelegramClient(session_path, user_api["api_id"], user_api["api_hash"])
            await client.connect()
            sent_code = await client.send_code_request(text)
            db.update_user(user_id_str, phone_code_hash=sent_code.phone_code_hash)
            await update.message.reply_text("✅ کد تأیید ارسال شد!\n\n📩 کد ۵ رقمی را وارد کنید:")
            await client.disconnect()
        except TelethonFloodWaitError as e:
            await update.message.reply_text(f"⏳ {e.seconds} ثانیه صبر کنید")
            db.update_user(user_id_str, step='get_phone')
        except Exception as e:
            logger.error(f"خطا: {e}")
            await update.message.reply_text(f"✖ خطا: {str(e)[:100]}\nدوباره شماره را وارد کنید")
            db.update_user(user_id_str, step='get_phone')
            
    elif step == 'get_code':
        db.update_user(user_id_str, code=text)
        await update.message.reply_text("⏳ در حال تأیید کد...")
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            user_api = get_user_api(user_id_str)
            if not user_api:
                await update.message.reply_text("❌ خطا در دریافت API")
                return
            
            client = TelegramClient(session_path, user_api["api_id"], user_api["api_hash"])
            await client.connect()
            user_data = db.get_user(user_id_str)
            
            code_for_telegram = text
            trans_table = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            code_for_telegram = code_for_telegram.translate(trans_table)
            
            await client.sign_in(
                phone=user_data['phone'],
                code=code_for_telegram,
                phone_code_hash=user_data['phone_code_hash']
            )
            
            expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            db.update_user(user_id_str, self_active=1, session_file=session_path, expiration_date=expiration_date, step=None)
            await update.message.reply_text(f"🎉 عضویت کامل شد!\n\n✅ اکانت فعال شد\n📅 انقضا: {expiration_date}")
            await client.disconnect()
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_path):
                selfbot_managers[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات فعال شد")
            
            admin_message = f"✅ کاربر {user_data['full_name']} وارد شد\n🆔 {user_id_str}\n📞 {user_data['phone']}\n🔑 API: {user_data.get('api_id', 'نامشخص')}"
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
            except:
                pass
        except SessionPasswordNeededError:
            db.update_user(user_id_str, step='get_password')
            await update.message.reply_text("🔐 رمز دو مرحله‌ای را وارد کنید:")
        except Exception as e:
            logger.error(f"خطا: {e}")
            await update.message.reply_text(f"✖ کد نامعتبر است\nدوباره شماره را وارد کنید")
            db.update_user(user_id_str, step='get_phone', phone=None, code=None, phone_code_hash=None)
            
    elif step == 'get_password':
        db.update_user(user_id_str, password=text)
        await update.message.reply_text("⏳ در حال تأیید رمز...")
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            user_api = get_user_api(user_id_str)
            if not user_api:
                await update.message.reply_text("❌ خطا در دریافت API")
                return
            
            client = TelegramClient(session_path, user_api["api_id"], user_api["api_hash"])
            await client.connect()
            user_data = db.get_user(user_id_str)
            
            await client.sign_in(password=text)
            expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            db.update_user(user_id_str, self_active=1, session_file=session_path, expiration_date=expiration_date, step=None)
            await update.message.reply_text(f"🎉 عضویت کامل شد!\n\n✅ اکانت فعال شد\n📅 انقضا: {expiration_date}")
            await client.disconnect()
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_path):
                selfbot_managers[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات فعال شد")
            
            admin_message = f"✅ کاربر {user_data['full_name']} وارد شد\n🆔 {user_id_str}\n📞 {user_data['phone']}\n🔐 رمز: ✓\n🔑 API: {user_data.get('api_id', 'نامشخص')}"
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
            except:
                pass
        except Exception as e:
            logger.error(f"خطا: {e}")
            await update.message.reply_text(f"✖ رمز نامعتبر است\nدوباره شماره را وارد کنید")
            db.update_user(user_id_str, step='get_phone', phone=None, code=None, phone_code_hash=None, password=None)
    else:
        await update.message.reply_text("لطفاً روی دکمه عضویت کلیک کنید")

async def check_session_files():
    print("\n" + "=" * 60)
    print("🔍 بررسی فایل‌های سشن...")
    if not os.path.exists(SESSIONS_FOLDER):
        os.makedirs(SESSIONS_FOLDER)
    session_files = [f for f in os.listdir(SESSIONS_FOLDER) if f.endswith('.session')]
    print(f"📊 تعداد فایل‌های سشن: {len(session_files)}")
    print("=" * 60 + "\n")

async def main():
    print("=" * 60)
    print("🤖 سیستم جامع عضویت و سلف‌بات")
    print(f"👑 ادمین: {ADMIN_ID}")
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
    print("✅ ربات شروع شد")
    print("=" * 60)
    
    active_users = db.get_active_users()
    success_count, fail_count = 0, 0
    print(f"🔄 راه‌اندازی {len(active_users)} سلف‌بات...")
    
    for user in active_users:
        user_id_str = user['user_id']
        session_file = user.get('session_file')
        if session_file and os.path.exists(session_file):
            print(f"  • کاربر {user_id_str}...", end=" ")
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
            
    print(f"✅ {success_count} سلف‌بات فعال شدند")
    if fail_count > 0:
        print(f"⚠️ {fail_count} سلف‌بات فعال نشدند")
    print("=" * 60)
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("در حال توقف...")
    finally:
        for manager in selfbot_managers.values():
            await manager.stop()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 ربات متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای fatal: {e}")
