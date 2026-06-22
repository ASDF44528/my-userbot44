# bot.py - نسخه کامل 5.0.0

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
from telethon.tl.types import PeerUser, PeerChannel, PeerChat, MessageMediaPhoto, MessageMediaDocument, ReactionEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityStrike, MessageEntityBlockquote, MessageEntitySpoiler, MessageEntityItalic, MessageEntityCode, MessageEntityPre
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest, SetTypingRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest, GetUserPhotosRequest
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import MessageDeleteForbiddenError, FloodWaitError, SessionPasswordNeededError, FloodWaitError as TelethonFloodWaitError

# ========== تنظیمات وب سرور ==========
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({"status": "running", "bot": "Gap_5_bot", "version": "5.0.0"})

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@flask_app.route('/ping')
def ping():
    return jsonify({"status": "alive", "message": "Bot is awake"}), 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"🚀 وب سرور روی پورت {port} در حال اجراست")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== تنظیمات ==========
os.environ['TZ'] = 'Asia/Tehran'
try:
    time.tzset()
except:
    pass

GOOGLE_SEARCH_API_KEY = "AIzaSyCMYOU0NpU5xfu7GrffyywVUugd1yD2uDU"
GOOGLE_CSE_ID = "3185e48756dfd482f"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

GEMINI_KEY = "AIzaSyBhlSytH4Zfe-ww1D8HsrgJfCf5TRY1SLc"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
PAXSENIX_API_KEY = "sk-paxsenix-Xo_BAFNGgWVZ_ymWd02Rk1JHbyoDSEzfPhiolJ3F12cY6XZG"
PAXSENIX_API_URL = "https://api.paxsenix.org/v1/chat/completions"
DEEPSEEK_FREE_URL = "https://deepseek.api-sina-free.workers.dev/?text="

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== API های ثابت ==========
API_CONFIGS = [
    {"api_id": 22409632, "api_hash": "b74c1ee200ad9ced6315859e9bd4125a"},
    {"api_id": 28297221, "api_hash": "8d682eb5c41a9762ef73f9ebe06c4eff"},
    {"api_id": 28039994, "api_hash": "00877cdcd706564a4de6abf7f7d64349"},
    {"api_id": 29031463, "api_hash": "64f122a7094dbab7e32b911eae6589e9"},
    {"api_id": 12832882, "api_hash": "1953c708cb3c47ecba74dc618b209e22"},
    {"api_id": 26645489, "api_hash": "6a212d0a400c97264600b3f932de5c2f"},
]

def get_user_api(user_id):
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

# ========== ایموجی‌های جدید برای دکمه‌ها ==========
BTN_ICONS = ["⚈", "⚉", "⚇", "☗", "☖", "⊖", "⚜", "⚕", "☻", "❍", "✿", "✼", "✷", "✬", "✮", "థ", "❂", "✰", "✧", "✠", "⚚", "☤", "❢", "⌬", "❖", "⟁", "ⱉ"]
CHECK = "✓"
CROSS = "✗"
CLOSE = "✕"

# ========== فونت‌های کلاسیک ==========
classic_fonts = [
    "⊘𝟷ϩӠ4ƼϬ7𝟾९", "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    "⓿①❷③❹⑤❻⑦❽⑨", "₀₁₂₃₄₅₆₇₈₉", "⁰¹²³⁴⁵⁶⁷⁸⁹", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿",
    "₀¹²³⁴⁵⁶₇₈₉", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡", "０１２３４５６７８９",
    "₀₁₂₃₄₅₆₇₈₉", "⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789", "⓪①②③④⑤⑥⑦⑧⑨",
    "⓿❶❷❸❹❺❻❼❽❾", "🄀🄁🄂🄃🄄🄅🄆🄇🄈🄉", "🄞🄟🄠🄡🄢🄣🄤🄥🄦🄧🄨",
    "０１２３４５６７８９", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    "𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫", "０１２３４５６７８９", "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', ':': ':'},
    {'0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗', ':': ':'},
]

ALLOWED_EMOJIS = ["🤯", "🐳", "😍", "💩", "👏", "🍌", "🤓", "😢", "🙉", "🤩", "🤝", "👀", "🌚", "🗿", "🤡", "😐", "👨‍💻", "😭", "🙈", "❤", "🙏", "😴", "💋", "🥰", "🤪", "✍️", "🥱", "👻", "🤣", "🌭", "😨", "🍓", "🔥", "🖕", "🤗", "🤔", "🤬", "😁", "🎄", "🫡", "⚡", "🥴", "😈", "🏆", "😇", "🎃", "☃️", "🤮", "👍", "👎", "😱", "😖", "🕊", "💯", "💔", "🤨", "❤️‍🔥", "💘", "😘", "💊", "🆒", "🤷‍♂", "🤷‍♀", "🎅"]

flags = ["🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇼", "🇦🇼", "🇦🇹", "🇦🇿", "🇧🇸", "🇧🇭", "🇧🇩", "🇧🇧", "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇴", "🇧🇦", "🇧🇼", "🇧🇷", "🇮🇴", "🇻🇬", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦", "🇨🇻", "🇰🇾", "🇨🇫", "🇹🇩", "🇨🇱", "🇨🇴", "🇰🇲", "🇨🇬", "🇨🇩", "🇨🇽", "🇨🇨", "🇨🇴", "🇰🇲", "🇨🇬", "🇨🇩", "🇨🇰", "🇨🇰", "🕋"]

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
]

DEFAULT_LOCK_SETTINGS = {
    'link': False, 'photo': False, 'video': False, 'sticker': False,
    'gif': False, 'voice': False, 'file': False, 'music': False,
    'video_note': False, 'contact': False, 'location': False,
    'emoji': False, 'text': False
}

BOT_VERSION = "5.0.0"
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
            if (i == 0 and (j == 0 or j == size-1)) or (i == 1 and (j == 0 or j == 1 or j == size-2 or j == size-1)) or (i == 2 and (j == 0 or j == 1 or j == 2 or j == size-3 or j == size-2 or j == size-1)) or (i >= 3 and i < size-1 and (j >= i-2 and j <= size-(i-2)-1)) or (i == size-1 and (j >= size//2 - 1 and j <= size//2 + 1)):
                row += R
            else:
                row += W
        heart.append(row)
    return "\n".join(heart)

JOINED_HEART = create_heart_matrix(7)
HEARTLET_LEN = JOINED_HEART.count(R)

# ========== کلاس دیتابیس ==========
class MainDatabase:
    def __init__(self, db_name='main_database.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
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
        conn.close()
        logger.info("✓ دیتابیس اصلی ایجاد شد")
    
    def add_user(self, user_id, full_name, username):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (user_id, full_name, username, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)', (user_id, full_name, username))
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
        cursor.execute('SELECT * FROM users WHERE request_sent = 1 AND admin_approved = 0 AND rejected = 0 AND step IS NULL ORDER BY request_date DESC')
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_pending_login(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE admin_approved = 1 AND self_active = 0 AND step IS NOT NULL ORDER BY activation_date DESC')
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_active_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE self_active = 1 AND admin_approved = 1 ORDER BY activation_date DESC')
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def get_all_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, full_name, username, phone, self_active, created_at FROM users ORDER BY created_at DESC')
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
                'ai_status': {'ai_1_pm': False, 'ai_2_pm': False, 'ai_3_pm': False, 'ai_1_group': False, 'ai_2_group': False, 'ai_3_group': False},
                'translate': {'english': False, 'arabic': False, 'hebrew': False, 'russian': False, 'turkish': False}
            }
            self.set_selfbot_settings(user_id, default_settings)
            return default_settings
    
    def set_selfbot_settings(self, user_id, settings):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        settings_to_save = settings.copy()
        settings_to_save.pop('ai_status', None)
        settings_to_save.pop('translate', None)
        if 'time_font_indices' in settings_to_save and isinstance(settings_to_save['time_font_indices'], list):
            settings_to_save['time_font_indices'] = ','.join(map(str, settings_to_save['time_font_indices']))
        columns = ', '.join(settings_to_save.keys())
        placeholders = ', '.join(['?' for _ in settings_to_save])
        values = list(settings_to_save.values())
        cursor.execute(f'INSERT OR REPLACE INTO selfbot_settings ({columns}, updated_at) VALUES ({placeholders}, CURRENT_TIMESTAMP)', values)
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
    
    def add_enemy(self, owner_id, enemy_id, chat_type='pv'):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR IGNORE INTO enemies (owner_id, enemy_id, chat_type) VALUES (?, ?, ?)', (owner_id, enemy_id, chat_type))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    
    def remove_enemy(self, owner_id, enemy_id, chat_type='pv'):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM enemies WHERE owner_id = ? AND enemy_id = ? AND chat_type = ?', (owner_id, enemy_id, chat_type))
        conn.commit()
        conn.close()
    
    def get_enemies(self, owner_id, chat_type='pv'):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT enemy_id FROM enemies WHERE owner_id = ? AND chat_type = ?', (owner_id, chat_type))
        enemies = [row[0] for row in cursor.fetchall()]
        conn.close()
        return enemies
    
    def is_enemy(self, owner_id, enemy_id, chat_type='pv'):
        return enemy_id in self.get_enemies(owner_id, chat_type)
    
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
        return [row[0] for row in cursor.fetchall()]
    
    def is_pv_locked(self, owner_id, user_id):
        return user_id in self.get_locked_pvs(owner_id)
    
    def get_media_locks(self, owner_id, target_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(zip(columns, row))
        return {'owner_id': owner_id, 'target_id': target_id, 'lock_link': 0, 'lock_photo': 0, 'lock_video': 0, 'lock_sticker': 0, 'lock_gif': 0, 'lock_voice': 0, 'lock_file': 0, 'lock_music': 0, 'lock_video_note': 0, 'lock_contact': 0, 'lock_location': 0, 'lock_emoji': 0, 'lock_text': 0}
    
    def set_media_lock(self, owner_id, target_id, lock_type, value):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
        exists = cursor.fetchone()
        if exists:
            cursor.execute(f'UPDATE media_locks SET {lock_type} = ?, created_at = CURRENT_TIMESTAMP WHERE owner_id = ? AND target_id = ?', (1 if value else 0, owner_id, target_id))
        else:
            lock_settings = {'owner_id': owner_id, 'target_id': target_id, 'lock_link': 0, 'lock_photo': 0, 'lock_video': 0, 'lock_sticker': 0, 'lock_gif': 0, 'lock_voice': 0, 'lock_file': 0, 'lock_music': 0, 'lock_video_note': 0, 'lock_contact': 0, 'lock_location': 0, 'lock_emoji': 0, 'lock_text': 0}
            lock_settings[lock_type] = 1 if value else 0
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
        cursor.execute('INSERT OR REPLACE INTO auto_comments (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username) VALUES (?, ?, ?, ?, ?, ?)', (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username))
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
        cursor.execute('INSERT OR REPLACE INTO sent_comments (owner_id, channel_id, message_id, comment_sent) VALUES (?, ?, ?, 1)', (owner_id, channel_id, message_id))
        conn.commit()
        conn.close()
    
    def is_comment_sent(self, owner_id, channel_id, message_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT comment_sent FROM sent_comments WHERE owner_id = ? AND channel_id = ? AND message_id = ?', (owner_id, channel_id, message_id))
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
    
    def get_filter_enabled(self, owner_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT filter_enabled FROM selfbot_settings WHERE user_id = ?', (owner_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def set_filter_enabled(self, owner_id, enabled):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE selfbot_settings SET filter_enabled = ? WHERE user_id = ?', (1 if enabled else 0, owner_id))
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
        return {'owner_id': owner_id, 'spam_protection': 0, 'spam_limit': 10, 'mute_duration': 10}
    
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
            default_settings = {'owner_id': owner_id, 'spam_protection': 0, 'spam_limit': 10, 'mute_duration': 10}
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
    
    def update_user_memory(self, user_id, username, first_name, last_name, chat_id, known_name=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_memory WHERE user_id = ?', (user_id,))
        user_exists = cursor.fetchone()
        if user_exists:
            cursor.execute('UPDATE user_memory SET username = ?, first_name = ?, last_name = ?, known_name = ?, chat_id = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?', (username, first_name, last_name, known_name, chat_id, user_id))
        else:
            cursor.execute('INSERT INTO user_memory (user_id, username, first_name, last_name, known_name, chat_id, last_seen) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)', (user_id, username, first_name, last_name, known_name, chat_id))
        conn.commit()
        conn.close()
    
    def add_broadcast(self, admin_id, message_text, message_type='text', media_file=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO broadcasts (admin_id, message_text, message_type, media_file) VALUES (?, ?, ?, ?)', (admin_id, message_text, message_type, media_file))
        broadcast_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return broadcast_id
    
    def update_broadcast_stats(self, broadcast_id, sent_count, failed_count):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE broadcasts SET sent_count = ?, failed_count = ? WHERE id = ?', (sent_count, failed_count, broadcast_id))
        conn.commit()
        conn.close()

db = MainDatabase()
selfbot_managers = {}

# ========== توابع کمکی ==========
def convert_persian_to_english(text):
    if not text:
        return text
    persian_to_english = {'۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9', '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'}
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
        return f"📅 تاریخ کامل\n━━━━━━━━━━━━━━━━━━━━\n🕐 ساعت: {now.strftime('%H:%M:%S')}\n\n📆 شمسی:\n{persian_weekdays[jdate.weekday()]} - {jdate.day} {jdate.strftime('%B')} {jdate.year}\n\n📆 میلادی:\n{gregorian_weekdays[now.weekday()]} - {now.strftime('%B %d, %Y')}\n\n📆 قمری:\n{hijri.day} {hijri.month_name()} {hijri.year}\n━━━━━━━━━━━━━━━━━━━━"
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
    patterns = [r'https?://\S+', r't\.me/\S+', r'www\.\S+', r'\S+\.(com|ir|org|net|info)\S*']
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
    emoji_pattern = re.compile(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U000024C2-\U0001F251\U0001F900-\U0001F9FF]+$', flags=re.UNICODE)
    return bool(emoji_pattern.match(text))

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

async def advanced_heart_phase1(message):
    BIG_SCROLL = "🧡💛💚💙💜🖤🤎"
    for heart in BIG_SCROLL:
        try:
            await message.edit(JOINED_HEART.replace(R, heart))
        except:
            pass
        await asyncio.sleep(SLEEP)

async def advanced_heart_phase2(message):
    ALL = ["❤️"] + list("🧡💛💚💙💜🤎🖤")
    format_heart = JOINED_HEART.replace(R, "{}")
    for _ in range(5):
        heart = format_heart.format(*random.choices(ALL, k=HEARTLET_LEN))
        try:
            await message.edit(heart)
        except:
            pass
        await asyncio.sleep(SLEEP)

async def advanced_heart_phase3(message):
    await asyncio.sleep(SLEEP * 2)
    repl = JOINED_HEART
    for _ in range(JOINED_HEART.count(W)):
        repl = repl.replace(W, R, 1)
        try:
            await message.edit(repl)
        except:
            pass
        await asyncio.sleep(SLEEP)

async def advanced_heart_phase4(message):
    for i in range(7, 0, -1):
        heart_matrix = "\n".join([R * i] * i)
        try:
            await message.edit(heart_matrix)
        except:
            pass
        await asyncio.sleep(SLEEP)

async def advanced_heart_animation(message):
    try:
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
    except:
        pass

# ========== کلاس ReportConfig ==========
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
        except Exception as e:
            logger.error(f"خطا در بارگذاری تنظیمات: {e}")
    
    def save_config(self):
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
            data[str(self.user_id)] = {'report_group_id': self.report_group_id, 'auto_save_media': self.auto_save_media, 'report_deleted_media': self.report_deleted_media, 'report_edited_messages': self.report_edited_messages, 'report_ttl_media': self.report_ttl_media}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"خطا در ذخیره تنظیمات: {e}")
    
    def set_report_group(self, group_id):
        self.report_group_id = group_id
        self.save_config()
        return f"✅ گروه گزارش به {group_id} تغییر کرد"

# ========== کلاس SelfBotManager ==========
class SelfBotManager:
    def __init__(self, user_id):
        self.user_id = int(user_id)
        self.client = None
        self.running = False
        self.my_id = None
        self.BASE_NAME = None
        self.ORIGINAL_NAME = None
        self.spam_tasks = {}
        self.adding_spam = False
        self.spam_counters = {}
        self.mode = 'all'
        self.current_chat_id = None
        self.active_actions = {}
        self.action_tasks = {}
        self.translate_mode = {"english": False, "arabic": False, "hebrew": False, "russian": False, "turkish": False}
        self.search_mode = False
        self.last_search_results = []
        self.connection_attempts = 0
        self.max_attempts = 5
        self._handlers_set = False
        self.panel_mode = True
        self.api_id = None
        self.api_hash = None
        self.time_font_cycle = 0
        self.time_font_indices = 'all'
        self.reconnect_task = None
        self.last_ping = 0
        self.report_config = ReportConfig(user_id)
    
    async def start(self, session_file):
        try:
            if self.running and self.client and self.client.is_connected():
                logger.info(f"سلف‌بات کاربر {self.user_id} در حال اجراست")
                return True
            
            self.connection_attempts += 1
            logger.info(f"شروع سلف‌بات کاربر {self.user_id} - تلاش {self.connection_attempts}")
            
            if not os.path.exists(session_file):
                logger.error(f"فایل سشن یافت نشد: {session_file}")
                return False
            
            user_api = get_user_api(str(self.user_id))
            if not user_api:
                logger.error(f"API یافت نشد: {self.user_id}")
                return False
            
            self.api_id = user_api["api_id"]
            self.api_hash = user_api["api_hash"]
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            self.client = TelegramClient(session_file, self.api_id, self.api_hash, connection_retries=10, retry_delay=3, timeout=60, flood_sleep_threshold=60)
            
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
            
            logger.info(f"کاربر {self.user_id}: {self.BASE_NAME} (ID: {self.my_id}) | API: {self.api_id}")
            
            original_name = db.get_original_name(self.user_id)
            if not original_name:
                db.set_original_name(self.user_id, self.BASE_NAME)
                db.set_current_name(self.user_id, self.BASE_NAME)
                self.ORIGINAL_NAME = self.BASE_NAME
            else:
                self.ORIGINAL_NAME = original_name
            
            settings = db.get_selfbot_settings(self.user_id)
            self.translate_mode = settings.get('translate', {"english": False, "arabic": False, "hebrew": False, "russian": False, "turkish": False})
            self.panel_mode = settings.get('panel_mode', True)
            self.time_font_indices = settings.get('time_font_indices', 'all')
            
            if not self._handlers_set:
                self.setup_handlers()
                self._handlers_set = True
                logger.info(f"هندلرها تنظیم شدند برای کاربر {self.user_id}")
            
            asyncio.create_task(self.update_profile_task())
            asyncio.create_task(self.keep_alive_task())
            
            self.running = True
            self.connection_attempts = 0
            logger.info(f"✅ سلف‌بات کاربر {self.user_id} با موفقیت شروع شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در شروع سلف‌بات کاربر {self.user_id}: {str(e)}")
            if self.connection_attempts < self.max_attempts:
                wait_time = 5 * self.connection_attempts
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
                await asyncio.sleep(300)
                if self.client and self.client.is_connected():
                    try:
                        await self.client.get_me()
                        self.last_ping = time.time()
                        logger.debug(f"Keepalive موفق برای کاربر {self.user_id}")
                    except Exception as e:
                        logger.warning(f"خطا در keepalive: {e}")
                        await self.reconnect()
                else:
                    logger.warning(f"اتصال قطع شده، تلاش برای reconnect کاربر {self.user_id}")
                    await self.reconnect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"خطا در keep_alive_task: {e}")
                await asyncio.sleep(60)
    
    async def reconnect(self):
        try:
            logger.info(f"شروع reconnect برای کاربر {self.user_id}")
            user_data = db.get_user(str(self.user_id))
            if not user_data or not user_data.get('session_file'):
                logger.error(f"فایل سشن یافت نشد برای کاربر {self.user_id}")
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
                logger.info(f"✅ reconnect موفق برای کاربر {self.user_id}")
                return True
            else:
                logger.error(f"❌ reconnect ناموفق برای کاربر {self.user_id}")
                return False
        except Exception as e:
            logger.error(f"خطا در reconnect: {e}")
            return False
    
    async def stop(self):
        try:
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
            logger.info(f"✅ سلف‌بات کاربر {self.user_id} متوقف شد")
        except Exception as e:
            logger.error(f"خطا در توقف سلف‌بات: {e}")
    
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
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def handle_outgoing_message(event):
                await self.handle_outgoing_message(event)
            
            @self.client.on(events.NewMessage())
            async def auto_comment_handler(event):
                await self.handle_auto_comment(event)
            
            @self.client.on(events.NewMessage())
            async def report_handler(event):
                await self.handle_report_message(event)
                
        except Exception as e:
            logger.error(f"خطا در تنظیم هندلرها: {e}")
    
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
            if settings.get('pv_lock_all') or db.is_pv_locked(self.user_id, event.sender_id):
                try:
                    await event.message.delete()
                    logger.info(f"پیام از {event.sender_id} به دلیل قفل پیوی حذف شد")
                    return
                except:
                    pass
        
        if await self.handle_media_lock_delete(event):
            return
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out and event.message.text:
            db.cache_message(self.user_id, chat_id, event.message.id, event.message.text)
        
        if not event.message.out and event.message.text and db.get_filter_enabled(self.user_id):
            filter_words = db.get_filter_words(self.user_id)
            for word_info in filter_words:
                if word_info['enabled'] and word_info['word'].lower() in event.message.text.lower():
                    try:
                        await event.message.delete()
                        logger.info(f"پیام حاوی {word_info['word']} حذف شد")
                        return
                    except:
                        pass
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            try:
                reaction = db.get_reaction(self.user_id, chat_id, sender_id)
                if reaction and reaction in ALLOWED_EMOJIS:
                    try:
                        await self.client(SendReactionRequest(peer=event.message.peer_id, msg_id=event.message.id, reaction=[ReactionEmoji(emoticon=reaction)]))
                        logger.info(f"ریکت {reaction} به پیام {sender_id} زده شد")
                    except Exception as e:
                        logger.error(f"خطا در ارسال ریکت: {e}")
            except Exception as e:
                logger.error(f"خطا در دریافت ریکت: {e}")
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out and event.message.text:
            ai_status = settings.get('ai_status', {})
            ai_active = False
            ai_type = None
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
                        logger.info(f"پاسخ هوش {ai_type} به {sender_id} ارسال شد")
                    else:
                        await event.reply("❌ خطا در ارتباط با هوش مصنوعی")
                except Exception as e:
                    logger.error(f"خطا در پاسخ هوش مصنوعی: {e}")
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            spam_settings = db.get_spam_settings(self.user_id)
            if spam_settings.get('spam_protection'):
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
                        logger.info(f"اسپم از {sender_id} حذف شد")
                    except:
                        pass
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            try:
                sender = await event.get_sender()
                if sender:
                    db.update_user_memory(sender.id, sender.username, sender.first_name, sender.last_name, chat_id)
            except:
                pass
    
    async def handle_media_lock_delete(self, event):
        if not event.message or event.message.out:
            return False
        target_id = event.sender_id
        if target_id == self.my_id:
            return False
        media_locks = db.get_media_locks(self.user_id, target_id)
        message = event.message
        message_text = message.text or ""
        lock_map = {
            'lock_link': (is_link_message(message_text), "لینک"),
            'lock_text': (bool(message_text), "متن"),
            'lock_emoji': (is_emoji_message(message_text), "ایموجی"),
            'lock_photo': (message.photo, "عکس"),
            'lock_video': (message.video, "ویدیو"),
            'lock_sticker': (message.sticker, "استیکر"),
            'lock_gif': (message.gif, "گیف"),
            'lock_voice': (message.voice, "ویس"),
            'lock_file': (message.document and not message.sticker and not message.gif, "فایل"),
            'lock_music': (message.audio, "موزیک"),
            'lock_video_note': (message.video_note, "ویدیو نوت"),
            'lock_contact': (message.contact, "کانتکت"),
            'lock_location': (message.geo, "لوکیشن")
        }
        for lock_key, (condition, lock_name) in lock_map.items():
            if media_locks.get(lock_key) and condition:
                try:
                    await message.delete()
                    logger.info(f"{lock_name} از کاربر {target_id} حذف شد")
                    return True
                except:
                    pass
        return False
    
    async def handle_edited_message(self, event):
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
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
            db.cache_message(self.user_id, event.message.peer_id.user_id, event.message.id, event.message.text or "")
    
    async def handle_deleted_message(self, event):
        pass
    
    async def handle_auto_comment(self, event):
        try:
            message = event.message
            if not message or message.out or not is_channel_post(message):
                return
            chat = await message.get_chat()
            channel_id = chat.id
            auto_comment = db.get_auto_comment(self.user_id, channel_id)
            if not auto_comment or db.is_comment_sent(self.user_id, channel_id, message.id):
                return
            logger.info(f"ارسال نظر به کانال: {auto_comment['channel_title']}")
            await asyncio.sleep(0.3)
            await self.client.send_message(chat.id, auto_comment['comment_text'], reply_to=message.id)
            db.mark_comment_sent(self.user_id, channel_id, message.id)
            logger.info(f"نظر ارسال شد به پست {message.id}")
        except Exception as e:
            logger.error(f"خطا در ارسال نظر اتوماتیک: {e}")
    
    async def handle_report_message(self, event):
        pass
    
    async def handle_outgoing_message(self, event):
        message_text = event.text or ""
        
        # ====== پردازش دستورات متنی ======
        if message_text:
            # دستورات زمان
            if message_text == "تایم روشن":
                db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
                db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
                await self.update_profile_name()
                await event.delete()
                return
            
            if message_text == "تایمر پرچم روشن":
                db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
                db.update_selfbot_setting(self.user_id, 'flag_enabled', 1)
                await self.update_profile_name()
                await event.delete()
                return
            
            if message_text == "تایم خاموش":
                db.update_selfbot_setting(self.user_id, 'time_enabled', 0)
                db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
                await self.restore_profile_name()
                await event.delete()
                return
            
            if message_text == "تاریخ کامل":
                await event.edit(get_full_date_info())
                return
            
            # دستورات انیمیشن
            if message_text == "قلب":
                await event.delete()
                asyncio.create_task(self.heart_animation(event.chat_id))
                return
            
            if message_text == "ماه":
                await event.delete()
                asyncio.create_task(self.moon_animation(event.chat_id))
                return
            
            if message_text == "قلب پیشرفته":
                await event.delete()
                try:
                    msg = await self.client.send_message(event.chat_id, "❤️")
                    await advanced_heart_animation(msg)
                except Exception as e:
                    logger.error(f"خطا: {e}")
                return
            
            if message_text == "عشق":
                await event.delete()
                try:
                    msg = await self.client.send_message(event.chat_id, "💝")
                    await advanced_heart_animation(msg)
                except Exception as e:
                    logger.error(f"خطا: {e}")
                return
            
            if message_text == "سنتت":
                await event.delete()
                try:
                    msg = await self.client.send_message(event.chat_id, "🕯️")
                    for i in range(101):
                        bar_len = int(i / 100 * 20)
                        bar = "█" * bar_len + "░" * (20 - bar_len)
                        await msg.edit(f"🕯️ {i}% [{bar}]")
                        await asyncio.sleep(0.03)
                    await asyncio.sleep(1)
                    await msg.edit("✅ انجام شد 🥴")
                except Exception as e:
                    logger.error(f"خطا: {e}")
                return
            
            if message_text == "هک":
                await event.delete()
                try:
                    msg = await self.client.send_message(event.chat_id, "💻")
                    await asyncio.sleep(2)
                    await msg.edit("User online: True\nTelegram access: True\nRead Storage: True")
                    await asyncio.sleep(2)
                    await msg.edit("Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]")
                    await asyncio.sleep(2)
                    await msg.edit("Hacking... 25%\n[█████░░░░░░░░░░░░░░░]")
                    await asyncio.sleep(2)
                    await msg.edit("Hacking... 50%\n[██████████░░░░░░░░░░]")
                    await asyncio.sleep(2)
                    await msg.edit("Hacking... 75%\n[███████████████░░░░░]")
                    await asyncio.sleep(2)
                    await msg.edit("Hacking... 100%\n[████████████████████]")
                    await asyncio.sleep(2)
                    await msg.edit("✅ هک کامل شد")
                except Exception as e:
                    logger.error(f"خطا: {e}")
                return
            
            # دستورات استایل
            if message_text in ["بولد روشن", "بولد خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'بولد')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["زیرخط روشن", "زیرخط خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'زیرخط')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["خط خورده روشن", "خط خورده خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'خط خورده')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["نقل قول روشن", "نقل قول خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'نقل قول')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["اسپویلر روشن", "اسپویلر خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'اسپویلر')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["کج روشن", "کج خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'کج')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["کد روشن", "کد خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'کد')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            if message_text in ["پیش روشن", "پیش خاموش"]:
                if "روشن" in message_text:
                    db.update_selfbot_setting(self.user_id, 'text_style', 'پیش')
                    await event.delete()
                else:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.delete()
                return
            
            # دستورات مدیریت کاربران
            if message_text == "قفل پیوی همه":
                db.update_selfbot_setting(self.user_id, 'pv_lock_all', 1)
                await event.delete()
                return
            
            if message_text == "باز پی همه":
                db.update_selfbot_setting(self.user_id, 'pv_lock_all', 0)
                await event.delete()
                return
            
            if message_text == "بلاک":
                if isinstance(event.message.peer_id, PeerUser):
                    target_id = event.message.peer_id.user_id
                    try:
                        await self.client(BlockRequest(id=target_id))
                        await event.edit("✅ کاربر بلاک شد")
                    except:
                        await event.edit("❌ خطا در بلاک")
                else:
                    await event.edit("⚠️ فقط در پی‌وی")
                return
            
            # دستورات ترجمه
            if message_text.startswith("انگلیسی "):
                key = "english"
                status = "روشن" in message_text
                self.translate_mode[key] = status
                await event.delete()
                return
            
            if message_text.startswith("عربی "):
                key = "arabic"
                status = "روشن" in message_text
                self.translate_mode[key] = status
                await event.delete()
                return
            
            if message_text.startswith("عبری "):
                key = "hebrew"
                status = "روشن" in message_text
                self.translate_mode[key] = status
                await event.delete()
                return
            
            if message_text.startswith("روسی "):
                key = "russian"
                status = "روشن" in message_text
                self.translate_mode[key] = status
                await event.delete()
                return
            
            if message_text.startswith("ترکی "):
                key = "turkish"
                status = "روشن" in message_text
                self.translate_mode[key] = status
                await event.delete()
                return
            
            # دستورات اسپم
            if message_text.startswith("اسپم "):
                parts = message_text.split()
                if len(parts) >= 3:
                    try:
                        num = int(parts[1])
                        text = " ".join(parts[2:])
                        for _ in range(num):
                            settings = db.get_selfbot_settings(self.user_id)
                            text_msg, entities = await apply_text_style(text, settings.get('text_style'))
                            await self.client.send_message(event.chat_id, text_msg, formatting_entities=entities)
                            await asyncio.sleep(0.05)
                        await event.delete()
                    except:
                        pass
                return
            
            # دستورات دشمن/دوست
            if message_text.startswith("دشمن "):
                target = await get_target_user(event, self.client)
                if target:
                    db.add_enemy(self.user_id, target, 'pv')
                    asyncio.create_task(self.spam_enemy(target))
                    await event.delete()
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            if message_text.startswith("دوست "):
                target = await get_target_user(event, self.client)
                if target:
                    db.remove_enemy(self.user_id, target, 'pv')
                    if target in self.spam_tasks:
                        self.spam_tasks[target].cancel()
                        del self.spam_tasks[target]
                    await event.delete()
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            # دستورات قفل پیوی
            if message_text.startswith("قفل پیوی "):
                target = await get_target_user(event, self.client)
                if target:
                    db.add_locked_pv(self.user_id, target)
                    await event.delete()
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            if message_text.startswith("باز پی "):
                target = await get_target_user(event, self.client)
                if target:
                    db.remove_locked_pv(self.user_id, target)
                    await event.delete()
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            # دستورات قفل رسانه
            if message_text.startswith("قفل "):
                parts = message_text.split()
                if len(parts) >= 2:
                    lock_type = parts[1]
                    if lock_type in ["لینک", "عکس", "ویدیو", "استیکر", "گیف", "ویس", "فایل", "موزیک", "ویدیو نوت", "کانتکت", "لوکیشن", "ایموجی", "متن"]:
                        target = await get_target_user(event, self.client)
                        target_id = target if target else 0
                        lock_map = {
                            "لینک": "link", "عکس": "photo", "ویدیو": "video",
                            "استیکر": "sticker", "گیف": "gif", "ویس": "voice",
                            "فایل": "file", "موزیک": "music", "ویدیو نوت": "video_note",
                            "کانتکت": "contact", "لوکیشن": "location", "ایموجی": "emoji",
                            "متن": "text"
                        }
                        lock_key = f"lock_{lock_map[lock_type]}"
                        current = db.get_media_locks(self.user_id, target_id)
                        new_value = not current.get(lock_key, 0)
                        db.set_media_lock(self.user_id, target_id, lock_key, new_value)
                        await event.delete()
                    else:
                        await event.edit("⚠️ نوع قفل نامعتبر")
                return
            
            # دستورات هوش مصنوعی
            if message_text in ["پیوی ۱", "پیوی ۲", "پیوی ۳", "خاموش پیوی"]:
                settings = db.get_selfbot_settings(self.user_id)
                ai_status = settings.get('ai_status', {})
                if message_text == "پیوی ۱":
                    ai_status['ai_1_pm'] = True
                    ai_status['ai_2_pm'] = False
                    ai_status['ai_3_pm'] = False
                elif message_text == "پیوی ۲":
                    ai_status['ai_1_pm'] = False
                    ai_status['ai_2_pm'] = True
                    ai_status['ai_3_pm'] = False
                elif message_text == "پیوی ۳":
                    ai_status['ai_1_pm'] = False
                    ai_status['ai_2_pm'] = False
                    ai_status['ai_3_pm'] = True
                else:
                    ai_status['ai_1_pm'] = False
                    ai_status['ai_2_pm'] = False
                    ai_status['ai_3_pm'] = False
                db.update_ai_status(self.user_id, ai_status)
                await event.delete()
                return
            
            if message_text in ["گروه ۱", "گروه ۲", "گروه ۳", "خاموش گروه"]:
                settings = db.get_selfbot_settings(self.user_id)
                ai_status = settings.get('ai_status', {})
                if message_text == "گروه ۱":
                    ai_status['ai_1_group'] = True
                    ai_status['ai_2_group'] = False
                    ai_status['ai_3_group'] = False
                elif message_text == "گروه ۲":
                    ai_status['ai_1_group'] = False
                    ai_status['ai_2_group'] = True
                    ai_status['ai_3_group'] = False
                elif message_text == "گروه ۳":
                    ai_status['ai_1_group'] = False
                    ai_status['ai_2_group'] = False
                    ai_status['ai_3_group'] = True
                else:
                    ai_status['ai_1_group'] = False
                    ai_status['ai_2_group'] = False
                    ai_status['ai_3_group'] = False
                db.update_ai_status(self.user_id, ai_status)
                await event.delete()
                return
            
            # دستورات تغییر نام و بیو
            if message_text.startswith("تغییر اسم "):
                new_name = message_text[10:].strip()
                if new_name:
                    db.set_current_name(self.user_id, new_name)
                    await self.client(UpdateProfileRequest(first_name=new_name))
                    self.BASE_NAME = new_name
                    await event.delete()
                return
            
            if message_text.startswith("تغییر بیو "):
                new_bio = message_text[10:].strip()
                if new_bio:
                    await self.client(UpdateProfileRequest(about=new_bio))
                    await event.delete()
                return
            
            # دستورات فیلتر
            if message_text.startswith(".فیلتر "):
                word = message_text[8:].strip()
                if word:
                    db.add_filter_word(self.user_id, word)
                    await event.delete()
                return
            
            if message_text.startswith("حذف فیلتر "):
                word = message_text[11:].strip()
                if word:
                    db.remove_filter_word(self.user_id, word)
                    await event.delete()
                return
            
            if message_text == "فیلتر روشن":
                db.set_filter_enabled(self.user_id, True)
                await event.delete()
                return
            
            if message_text == "فیلتر خاموش":
                db.set_filter_enabled(self.user_id, False)
                await event.delete()
                return
            
            if message_text == "لیست فیلتر":
                filters = db.get_filter_words(self.user_id)
                if filters:
                    text = "📜 لیست کلمات فیلتر شده:\n\n"
                    for i, word_info in enumerate(filters, 1):
                        status = "فعال" if word_info['enabled'] else "غیرفعال"
                        text += f"{i}. {word_info['word']} - {status}\n"
                    await event.edit(text)
                else:
                    await event.edit("📭 لیست کلمات فیلتر خالی است")
                return
            
            # دستورات اضافه اسپم
            if message_text == "اضافه اسپم":
                self.adding_spam = True
                await event.edit("📝 حالت اضافه کردن اسپم فعال شد\nبرای پایان: اتمام اسپم")
                return
            
            if message_text == "اتمام اسپم":
                self.adding_spam = False
                await event.edit("✅ حالت اضافه کردن اسپم غیرفعال شد")
                return
            
            if message_text == "لیست اسپم":
                spam_messages = db.get_enemy_spam_messages(self.user_id)
                if spam_messages:
                    text = "📜 لیست پیام‌های اسپم:\n\n"
                    for i, spam_msg in enumerate(spam_messages, 1):
                        text += f"{i}. {spam_msg['text']}\n"
                    await event.edit(text)
                else:
                    await event.edit("📭 لیست پیام‌های اسپم خالی است")
                return
            
            if message_text == "پاک کردن اسپم":
                db.clear_enemy_spam_messages(self.user_id)
                await event.edit("✅ لیست پیام‌های اسپم پاک شد")
                return
            
            if message_text.startswith("حذف اسپم "):
                try:
                    num = int(message_text[10:].strip())
                    spam_messages = db.get_enemy_spam_messages(self.user_id)
                    if 1 <= num <= len(spam_messages):
                        spam_msg = spam_messages[num - 1]
                        db.delete_enemy_spam_message(self.user_id, spam_msg['id'])
                        await event.edit(f"✅ پیام شماره {num} حذف شد")
                    else:
                        await event.edit(f"⚠️ پیام شماره {num} وجود ندارد")
                except:
                    pass
                return
            
            # دستورات حذف
            if message_text.startswith("حذف "):
                try:
                    num = int(message_text[5:].strip())
                    messages = []
                    async for msg in self.client.iter_messages(event.chat_id, limit=num):
                        if msg.sender_id == self.my_id:
                            messages.append(msg.id)
                    if messages:
                        await self.client.delete_messages(event.chat_id, messages)
                        await event.edit(f"✅ {len(messages)} پیام حذف شد")
                    else:
                        await event.edit("⚠️ هیچ پیامی یافت نشد")
                except:
                    pass
                return
            
            if message_text == "حذف کامل":
                messages = []
                async for msg in self.client.iter_messages(event.chat_id, limit=None):
                    if msg.sender_id == self.my_id:
                        messages.append(msg.id)
                if messages:
                    await self.client.delete_messages(event.chat_id, messages)
                    await event.edit(f"✅ {len(messages)} پیام حذف شدند")
                else:
                    await event.edit("⚠️ هیچ پیامی یافت نشد")
                return
            
            # دستورات اتوسین
            if message_text == "فعال اتوسین":
                db.update_selfbot_setting(self.user_id, 'autosend_mode', 1)
                await event.delete()
                return
            
            if message_text == "غیرفعال اتوسین":
                db.update_selfbot_setting(self.user_id, 'autosend_mode', 0)
                await event.delete()
                return
            
            # دستورات پینگ و وضعیت
            if message_text == "پینگ":
                start = time.time()
                await event.edit("🏓 پینگ: ...")
                end = time.time()
                ping = round((end - start) * 1000, 2)
                await event.edit(f"🏓 پینگ: {ping} ms")
                return
            
            if message_text == "وضعیت":
                settings = db.get_selfbot_settings(self.user_id)
                await event.edit(self.format_status_info(settings))
                return
            
            if message_text == "درباره":
                await event.edit(f"ℹ️ درباره بات\n\n🤖 نسخه: v{BOT_VERSION}\n👨‍💻 سازنده: {BOT_CREATOR}")
                return
            
            if message_text == "من کی ام":
                if isinstance(event.message.peer_id, PeerUser):
                    user_id_display = event.sender_id
                    user_name = db.get_user_name(user_id_display)
                    await event.edit(f"👤 شما: {user_name}\n🆔 آی‌دی: {user_id_display}")
                return
            
            # دستورات سرچ
            if message_text == "سرچ":
                self.search_mode = True
                await event.edit("🔍 حالت سرچ فعال شد")
                return
            
            if message_text == "خروج سرچ":
                self.search_mode = False
                self.last_search_results = []
                await event.edit("✅ حالت سرچ غیرفعال شد")
                return
            
            # دستورات تنظیم گروه گزارش
            if message_text == "تنظیم گزارش":
                if isinstance(event.message.peer_id, (PeerChannel, PeerChat)):
                    chat_id_target = event.message.peer_id.channel_id if isinstance(event.message.peer_id, PeerChannel) else event.message.peer_id.chat_id
                    self.report_config.set_report_group(chat_id_target)
                    await event.edit(f"✅ گروه گزارش تنظیم شد\nآیدی: {chat_id_target}")
                else:
                    await event.edit("⚠️ این دستور فقط در گروه کار می‌کند")
                return
            
            if message_text == "گروه گزارش":
                await event.edit(f"📍 گروه گزارش فعلی:\nآیدی: {self.report_config.report_group_id}")
                return
            
            # دستورات کامنت
            if message_text.startswith("کامنت "):
                comment_text = message_text[7:].strip()
                chat = await event.get_chat()
                chat_type = "کانال" if hasattr(chat, 'broadcast') and chat.broadcast else "گروه"
                db.set_auto_comment(self.user_id, chat.id, comment_text, chat.title, chat_type, getattr(chat, 'username', None))
                await event.delete()
                return
            
            if message_text == "کانال‌ها":
                auto_comments = db.get_auto_comments(self.user_id)
                if auto_comments:
                    msg = "📊 کانال‌های تنظیم شده:\n\n"
                    for comment in auto_comments:
                        msg += f"• {comment['channel_title']} ({comment['channel_type']})\n"
                        msg += f"  آیدی: {comment['channel_id']}\n"
                        msg += f"  متن: {comment['comment_text'][:30]}...\n\n"
                    await event.edit(msg)
                else:
                    await event.edit("📭 هیچ کانالی تنظیم نشده")
                return
            
            if message_text == "حذف کانال":
                chat = await event.get_chat()
                channel_id = chat.id
                auto_comment = db.get_auto_comment(self.user_id, channel_id)
                if auto_comment:
                    db.remove_auto_comment(self.user_id, channel_id)
                    await event.edit(f"✅ تنظیمات {auto_comment['channel_title']} حذف شد")
                else:
                    await event.edit("⚠️ این کانال تنظیم نشده است")
                return
            
            if message_text == "تست کانال":
                chat = await event.get_chat()
                info = f"🔍 اطلاعات تست:\n\nچت: {chat.title}\nنوع: {'کانال' if hasattr(chat, 'broadcast') and chat.broadcast else 'گروه'}\nآیدی: {chat.id}"
                auto_comment = db.get_auto_comment(self.user_id, chat.id)
                info += f"\nتنظیم شده: {'✅' if auto_comment else '❌'}"
                if auto_comment:
                    info += f"\nمتن: {auto_comment['comment_text'][:50]}..."
                await event.edit(info)
                return
            
            # دستورات تغییر پروفایل
            if message_text == "تغییر پروفایل" or message_text == "پروف":
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    if isinstance(reply_message.media, MessageMediaPhoto):
                        photo_path = await self.client.download_media(reply_message.media, file=f"{MEDIA_FOLDER}/profile_{self.user_id}.jpg")
                        if photo_path and os.path.exists(photo_path):
                            me = await self.client.get_me()
                            if me.photo:
                                photos = await self.client.get_profile_photos(me.id, limit=1)
                                if photos:
                                    await self.client(DeletePhotosRequest(id=[photos[0]]))
                            file = await self.client.upload_file(photo_path)
                            await self.client(UploadProfilePhotoRequest(file=file))
                            os.remove(photo_path)
                            await event.edit("✅ عکس پروفایل تغییر کرد")
                        else:
                            await event.edit("⚠️ خطا در دانلود عکس")
                    else:
                        await event.edit("⚠️ روی یک عکس ریپلای کنید")
                else:
                    await event.edit("⚠️ روی عکس مورد نظر ریپلای کنید")
                return
            
            # دستورات ست پروف و بیو
            if message_text == "ست پروف":
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    user = await reply_message.get_sender()
                    if user.photo:
                        photo_path = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user.id}.jpg")
                        if photo_path and os.path.exists(photo_path):
                            me = await self.client.get_me()
                            if me.photo:
                                photos = await self.client.get_profile_photos(me.id, limit=1)
                                if photos:
                                    await self.client(DeletePhotosRequest(id=[photos[0]]))
                            file = await self.client.upload_file(photo_path)
                            await self.client(UploadProfilePhotoRequest(file=file))
                            os.remove(photo_path)
                            await event.edit("✅ عکس پروفایل ست شد")
                        else:
                            await event.edit("⚠️ خطا در دانلود")
                    else:
                        await event.edit("⚠️ این کاربر عکس پروفایل ندارد")
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            if message_text == "ست بیو":
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    user = await reply_message.get_sender()
                    try:
                        full_user = await self.client(GetFullUserRequest(user.id))
                        bio = full_user.full_user.about or ""
                        await self.client(UpdateProfileRequest(about=bio))
                        await event.edit("✅ بیو ست شد")
                    except:
                        await event.edit("⚠️ خطا")
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            if message_text == "حذف ست پروف":
                me = await self.client.get_me()
                if me.photo:
                    try:
                        photos = await self.client.get_profile_photos(me.id, limit=1)
                        if photos:
                            await self.client(DeletePhotosRequest(id=[photos[0]]))
                        await event.edit("✅ عکس پروفایل حذف شد")
                    except:
                        await event.edit("⚠️ خطا")
                else:
                    await event.edit("⚠️ عکس پروفایلی وجود ندارد")
                return
            
            if message_text == "حذف ست بیو":
                try:
                    await self.client(UpdateProfileRequest(about=""))
                    await event.edit("✅ بیو خالی شد")
                except:
                    await event.edit("⚠️ خطا")
                return
            
            # دستورات اطلاعات
            if message_text == "اطلاعات":
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
                info_text = f"📋 اطلاعات کاربر:\n\n👤 یوزرنیم: {username}\n🆔 ID: {user.id}\n📛 نام: {name}\n📝 بیو: {bio}"
                if user.photo:
                    try:
                        photo = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user.id}.jpg")
                        if photo:
                            await self.client.send_file(event.chat_id, photo, caption=info_text)
                            os.remove(photo)
                        else:
                            await event.edit(info_text)
                    except:
                        await event.edit(info_text)
                else:
                    await event.edit(info_text + "\n\n📸 عکس پروفایل ندارد")
                return
            
            if message_text == "دانلود پروفایل":
                if event.is_reply:
                    reply_message = await event.get_reply_message()
                    user = await reply_message.get_sender()
                else:
                    user = await self.client.get_me()
                if user.photo:
                    try:
                        photo = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user.id}.jpg")
                        if photo and os.path.exists(photo):
                            await self.client.send_file(event.chat_id, photo, caption=f"📸 پروفایل {user.first_name or ''}")
                            os.remove(photo)
                        else:
                            await event.edit("⚠️ خطا در دانلود")
                    except:
                        await event.edit("⚠️ خطا در دانلود")
                else:
                    await event.edit("⚠️ عکس پروفایلی وجود ندارد")
                return
            
            # دستورات ریکت
            if message_text.startswith("ریکت "):
                parts = message_text.split()
                if len(parts) >= 2:
                    emoji = parts[1]
                    if emoji in ALLOWED_EMOJIS:
                        target = await get_target_user(event, self.client)
                        if target:
                            chat_id_target = None
                            if isinstance(event.message.peer_id, PeerUser):
                                chat_id_target = event.message.peer_id.user_id
                            elif isinstance(event.message.peer_id, PeerChannel):
                                chat_id_target = event.message.peer_id.channel_id
                            elif isinstance(event.message.peer_id, PeerChat):
                                chat_id_target = event.message.peer_id.chat_id
                            db.set_reaction(self.user_id, chat_id_target, target, emoji)
                            await event.delete()
                        else:
                            await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                    else:
                        await event.edit("⚠️ ایموجی مجاز نیست")
                return
            
            if message_text == "حذف ریکت":
                target = await get_target_user(event, self.client)
                if target:
                    chat_id_target = None
                    if isinstance(event.message.peer_id, PeerUser):
                        chat_id_target = event.message.peer_id.user_id
                    elif isinstance(event.message.peer_id, PeerChannel):
                        chat_id_target = event.message.peer_id.channel_id
                    elif isinstance(event.message.peer_id, PeerChat):
                        chat_id_target = event.message.peer_id.chat_id
                    db.remove_reaction(self.user_id, chat_id_target, target)
                    await event.delete()
                else:
                    await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
                return
            
            # دستورات تنظیم اسپم
            if message_text.startswith("تنظیم اسپم "):
                parts = message_text.split()
                if len(parts) >= 3:
                    try:
                        limit = int(parts[1])
                        duration = int(parts[2])
                        db.set_spam_settings(self.user_id, spam_limit=limit, mute_duration=duration)
                        await event.delete()
                    except:
                        pass
                return
            
            if message_text == "اسپم روشن":
                db.set_spam_settings(self.user_id, spam_protection=1)
                await event.delete()
                return
            
            if message_text == "اسپم خاموش":
                db.set_spam_settings(self.user_id, spam_protection=0)
                await event.delete()
                return
            
            if message_text == "لیست دشمن":
                enemies = db.get_enemies(self.user_id, 'pv')
                if enemies:
                    text = "📋 لیست دشمنان:\n\n"
                    for i, enemy_id in enumerate(enemies, 1):
                        try:
                            enemy = await self.client.get_entity(enemy_id)
                            enemy_name = enemy.first_name or f"کاربر {enemy_id}"
                            text += f"{i}. {enemy_name} ({enemy_id})\n"
                        except:
                            text += f"{i}. کاربر {enemy_id}\n"
                    await event.edit(text)
                else:
                    await event.edit("📭 لیست دشمنان خالی است")
                return
            
            # دستورات اکشن
            if message_text.startswith("اکشن "):
                command = message_text[6:].strip()
                if command == "خاموش":
                    if event.chat_id in self.active_actions:
                        action_name = await self.stop_action(event.chat_id)
                        await event.edit(f'✅ اکشن {action_name} خاموش شد')
                    else:
                        await event.edit('❌ هیچ اکشن فعالی وجود ندارد')
                    return
                elif command == "لیست":
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
                        if event.chat_id in self.active_actions:
                            await self.stop_action(event.chat_id)
                        await self.start_action(event.chat_id, command)
                        await event.delete()
                    else:
                        available = "\n".join([f"• {name}" for name in action_types.keys()])
                        await event.edit(f'❌ اکشن "{command}" پشتیبانی نمی‌شود\n\n✅ اکشن‌های موجود:\n{available}')
                return
            
            # دستورات .پنل
            if message_text in [".پنل", "پنل", "/panel"]:
                bot_username = BOT_USERNAME.replace('@', '')
                results = await self.client.inline_query(bot_username, '')
                if results and len(results) > 0:
                    await results[0].click(event.chat_id)
                    await event.delete()
                else:
                    await event.edit("❌ پنل یافت نشد")
                return
            
            # دستورات .اهنگ
            if message_text.startswith(".اهنگ "):
                song_name = message_text[7:].strip()
                if song_name:
                    await event.edit(f"🎵 در حال جستجوی آهنگ: {song_name}...")
                    try:
                        bot_username = MUSIC_BOT.replace('@', '')
                        results = await self.client.inline_query(bot_username, song_name)
                        if results and len(results) > 0:
                            await results[0].click(event.chat_id)
                            await event.delete()
                        else:
                            await event.edit(f"❌ آهنگی با نام '{song_name}' پیدا نشد")
                    except:
                        await event.edit("❌ خطا در ارسال آهنگ")
                else:
                    await event.edit("❌ لطفاً نام آهنگ را وارد کنید")
                return
            
            # ترجمه خودکار
            if self.translate_mode and message_text:
                active_lang_code = None
                lang_mapping = {"english": "en", "arabic": "ar", "hebrew": "he", "russian": "ru", "turkish": "tr"}
                for lang_key, status in self.translate_mode.items():
                    if status and lang_key in lang_mapping:
                        active_lang_code = lang_mapping[lang_key]
                        break
                if active_lang_code and message_text and not message_text.startswith(('لیست', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'درباره', 'من کی ام', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ', 'قلب پیشرفته', 'عشق', 'سنتت', 'هک', 'وضعیت', '.پنل', 'پنل', '/panel', '.اهنگ', 'تنظیم اسپم')):
                    try:
                        from deep_translator import GoogleTranslator
                        translated = GoogleTranslator(source='auto', target=active_lang_code).translate(message_text)
                        if translated != message_text:
                            await event.edit(translated)
                    except:
                        pass
                return
            
            # حالت اضافه کردن اسپم
            if self.adding_spam and message_text and not message_text.startswith(('لیست', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'درباره', 'من کی ام', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ', 'قلب پیشرفته', 'عشق', 'سنتت', 'هک', 'وضعیت', '.پنل', 'پنل', '/panel', '.اهنگ', 'تنظیم اسپم')):
                db.add_enemy_spam_message(self.user_id, message_text)
                try:
                    await event.delete()
                except:
                    pass
                return
            
            # جستجوی گوگل
            if self.search_mode and message_text and not message_text.startswith(('لیست', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'درباره', 'من کی ام', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ', 'قلب پیشرفته', 'عشق', 'سنتت', 'هک', 'وضعیت', '.پنل', 'پنل', '/panel', '.اهنگ', 'تنظیم اسپم')):
                await self.handle_google_search(event, message_text)
                return
            
            # استایل متن
            if event.text:
                settings = db.get_selfbot_settings(self.user_id)
                text_style = settings.get('text_style')
                if text_style and not message_text.startswith(('لیست', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'درباره', 'من کی ام', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ', 'قلب پیشرفته', 'عشق', 'سنتت', 'هک', 'وضعیت', '.پنل', 'پنل', '/panel', '.اهنگ', 'تنظیم اسپم')):
                    try:
                        text, entities = await apply_text_style(message_text, text_style)
                        if entities:
                            await event.message.edit(text, formatting_entities=entities)
                    except:
                        pass
    
    async def handle_google_search(self, event, query):
        try:
            await event.edit(f'🔍 در حال جستجو: {query}')
            params = {'key': GOOGLE_SEARCH_API_KEY, 'cx': GOOGLE_CSE_ID, 'q': query, 'num': 5, 'safe': 'active'}
            response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
            if response.status_code == 200:
                results = response.json()
                if 'items' in results and len(results['items']) > 0:
                    self.last_search_results = results['items']
                    message = f"🔍 نتایج جستجو برای: {query}\n\n"
                    for i, item in enumerate(results['items'][:5], 1):
                        message += f"{i}. {item.get('title', 'بدون عنوان')}\n   {item.get('snippet', 'بدون توضیح')[:100]}...\n   🔗 {item.get('link', '')}\n\n"
                    await event.edit(message[:4000])
                else:
                    await event.edit(f'❌ هیچ نتیجه‌ای برای "{query}" پیدا نشد.')
            else:
                await event.edit(f'❌ خطا در جستجو. کد خطا: {response.status_code}')
        except Exception as e:
            await event.edit(f'❌ خطا در جستجو: {str(e)}')
    
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
    
    async def update_profile_name(self):
        settings = db.get_selfbot_settings(self.user_id)
        if settings.get('time_enabled'):
            now = datetime.now()
            current_minute = now.minute
            
            if self.time_font_indices == 'all':
                font_index = current_minute % len(classic_fonts)
            elif isinstance(self.time_font_indices, list) and self.time_font_indices:
                self.time_font_cycle = (self.time_font_cycle + 1) % len(self.time_font_indices)
                font_index = self.time_font_indices[self.time_font_cycle]
                if font_index >= len(classic_fonts):
                    font_index = 0
            else:
                font_index = 0
            
            time_now = now.strftime("%H:%M")
            time_now_classic = convert_to_classic_font(time_now, font_index)
            
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
    
    async def heart_animation(self, chat_id):
        try:
            message = await self.client.send_message(chat_id, HEARTS[0])
            for i in range(1, len(HEARTS) * 99999):
                await asyncio.sleep(4)
                await self.client.edit_message(chat_id, message, HEARTS[i % len(HEARTS)])
            await self.client.delete_messages(chat_id, message)
        except:
            pass
    
    async def moon_animation(self, chat_id):
        try:
            message = await self.client.send_message(chat_id, MOONS[0])
            for i in range(1, len(MOONS) * 1):
                await asyncio.sleep(3)
                await self.client.edit_message(chat_id, message, MOONS[i % len(MOONS)])
            await self.client.delete_messages(chat_id, message)
        except:
            pass
    
    async def format_status_info(self, settings):
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
        
        ai_status = settings.get('ai_status', {})
        active_ai_pm = "هیچ هوش فعالی در پی‌وی وجود ندارد"
        if ai_status.get('ai_1_pm'):
            active_ai_pm = "هوش ۱ (Gemini)"
        elif ai_status.get('ai_2_pm'):
            active_ai_pm = "هوش ۲ (Paxsenix API)"
        elif ai_status.get('ai_3_pm'):
            active_ai_pm = "هوش ۳ (DeepSeek)"
        
        active_ai_group = "هیچ هوش فعالی در گروه وجود ندارد"
        if ai_status.get('ai_1_group'):
            active_ai_group = "هوش ۱ (Gemini)"
        elif ai_status.get('ai_2_group'):
            active_ai_group = "هوش ۲ (Paxsenix API)"
        elif ai_status.get('ai_3_group'):
            active_ai_group = "هوش ۳ (DeepSeek)"
        
        filter_status = "فعال" if db.get_filter_enabled(self.user_id) else "غیرفعال"
        text_style = settings.get('text_style') or "هیچکدام"
        
        return f"""
وضعیت کامل سلف‌بات
━━━━━━━━━━━━━━━━━━━━
📍 حالت: {'همه جا' if self.mode == 'all' else 'فقط اینجا' if self.mode == 'pv' else 'خاموش'}
🔍 حالت سرچ: {'فعال' if self.search_mode else 'غیرفعال'}
🕐 تایم روی پروفایل: {'فعال' if settings.get('time_enabled') else 'غیرفعال'}
🏳️ پرچم در تایم: {'فعال' if settings.get('flag_enabled') else 'غیرفعال'}
🎨 فونت تایم: {font_info}

🤖 هوش مصنوعی:
• پی‌وی: {active_ai_pm}
• گروه: {active_ai_group}

✍️ استایل متن: {text_style}

🔒 قفل پیوی همگانی: {'فعال' if settings.get('pv_lock_all') else 'غیرفعال'}
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

📊 گروه گزارش: {self.report_config.report_group_id}
💾 ذخیره خودکار رسانه: {'فعال' if self.report_config.auto_save_media else 'غیرفعال'}
━━━━━━━━━━━━━━━━━━━━
✅ Self-Bot v{BOT_VERSION}
        """

# ========== کیبوردهای پنل ==========
def get_user_status_icon(status):
    return CHECK if status else CROSS

def get_main_panel_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{BTN_ICONS[0]} زمان و پروفایل", callback_data=f"time_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[1]} انیمیشن", callback_data=f"animation_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[2]} مدیریت کاربران", callback_data=f"user_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[3]} قفل رسانه", callback_data=f"lock_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[4]} کامنت", callback_data=f"comment_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[5]} عمومی", callback_data=f"general_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[6]} اکشن", callback_data=f"action_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[7]} بازی‌ها", callback_data=f"games_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[8]} ترجمه", callback_data=f"translate_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[9]} گوگل", callback_data=f"google_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[10]} اطلاعاتی", callback_data=f"info_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[11]} پروفایل", callback_data=f"profile_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[12]} استایل متن", callback_data=f"style_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[13]} مدیریت پیام", callback_data=f"message_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[14]} ریکشن", callback_data=f"reaction_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[15]} اسپم", callback_data=f"spam_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[16]} تغییر پروفایل", callback_data=f"change_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[17]} مدیریت دشمنان", callback_data=f"enemy_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[18]} فیلتر کلمات", callback_data=f"filter_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[19]} حفاظت اسپم", callback_data=f"protection_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[20]} هوش مصنوعی", callback_data=f"ai_menu_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[21]} گزارش", callback_data=f"report_menu_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[22]} پیام همگانی", callback_data=f"broadcast_menu_{user_id}"),
         InlineKeyboardButton(f"{CLOSE} بستن پنل", callback_data=f"close_panel_{user_id}")]
    ])

def get_time_menu_keyboard(user_id, settings):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🕐 تایم روشن {get_user_status_icon(settings.get('time_enabled', 0))}", callback_data=f"exec_time_on_{user_id}"),
         InlineKeyboardButton(f"🏳️ تایمر پرچم {get_user_status_icon(settings.get('flag_enabled', 0))}", callback_data=f"exec_time_flag_{user_id}")],
        [InlineKeyboardButton("🚫 تایم خاموش", callback_data=f"exec_time_off_{user_id}"),
         InlineKeyboardButton("📅 تاریخ کامل", callback_data=f"exec_full_date_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_user_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{BTN_ICONS[2]} دشمن", callback_data=f"exec_enemy_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[3]} دوست", callback_data=f"exec_friend_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[4]} قفل پیوی", callback_data=f"exec_lock_pv_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[5]} باز پی", callback_data=f"exec_unlock_pv_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[6]} قفل پیوی همه", callback_data=f"exec_lock_all_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[7]} باز پی همه", callback_data=f"exec_unlock_all_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[8]} بلاک", callback_data=f"exec_block_{user_id}"),
         InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_lock_menu_keyboard(user_id, target_id=None):
    if target_id:
        locks = db.get_media_locks(user_id, target_id)
    else:
        locks = db.get_media_locks(user_id, 0)
    target_str = f"_{target_id or 0}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔗 لینک {get_user_status_icon(locks.get('lock_link', 0))}", callback_data=f"exec_lock_link_{user_id}{target_str}"),
         InlineKeyboardButton(f"📸 عکس {get_user_status_icon(locks.get('lock_photo', 0))}", callback_data=f"exec_lock_photo_{user_id}{target_str}")],
        [InlineKeyboardButton(f"🎥 ویدیو {get_user_status_icon(locks.get('lock_video', 0))}", callback_data=f"exec_lock_video_{user_id}{target_str}"),
         InlineKeyboardButton(f"🎨 استیکر {get_user_status_icon(locks.get('lock_sticker', 0))}", callback_data=f"exec_lock_sticker_{user_id}{target_str}")],
        [InlineKeyboardButton(f"🎞️ گیف {get_user_status_icon(locks.get('lock_gif', 0))}", callback_data=f"exec_lock_gif_{user_id}{target_str}"),
         InlineKeyboardButton(f"🎤 ویس {get_user_status_icon(locks.get('lock_voice', 0))}", callback_data=f"exec_lock_voice_{user_id}{target_str}")],
        [InlineKeyboardButton(f"📁 فایل {get_user_status_icon(locks.get('lock_file', 0))}", callback_data=f"exec_lock_file_{user_id}{target_str}"),
         InlineKeyboardButton(f"🎵 موزیک {get_user_status_icon(locks.get('lock_music', 0))}", callback_data=f"exec_lock_music_{user_id}{target_str}")],
        [InlineKeyboardButton(f"📹 ویدیو نوت {get_user_status_icon(locks.get('lock_video_note', 0))}", callback_data=f"exec_lock_video_note_{user_id}{target_str}"),
         InlineKeyboardButton(f"📞 کانتکت {get_user_status_icon(locks.get('lock_contact', 0))}", callback_data=f"exec_lock_contact_{user_id}{target_str}")],
        [InlineKeyboardButton(f"📍 لوکیشن {get_user_status_icon(locks.get('lock_location', 0))}", callback_data=f"exec_lock_location_{user_id}{target_str}"),
         InlineKeyboardButton(f"😀 ایموجی {get_user_status_icon(locks.get('lock_emoji', 0))}", callback_data=f"exec_lock_emoji_{user_id}{target_str}")],
        [InlineKeyboardButton(f"📝 متن {get_user_status_icon(locks.get('lock_text', 0))}", callback_data=f"exec_lock_text_{user_id}{target_str}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_style_menu_keyboard(user_id, current_style):
    styles = ['بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش']
    keyboard = []
    row = []
    for i, style in enumerate(styles):
        row.append(InlineKeyboardButton(f"{style} {get_user_status_icon(current_style == style)}", callback_data=f"exec_style_{style}_{user_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")])
    return InlineKeyboardMarkup(keyboard)

def get_ai_menu_keyboard(user_id, settings):
    ai = settings.get('ai_status', {})
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🟢 پیوی ۱ {get_user_status_icon(ai.get('ai_1_pm', 0))}", callback_data=f"exec_ai_pm_1_{user_id}"),
         InlineKeyboardButton(f"🔵 پیوی ۲ {get_user_status_icon(ai.get('ai_2_pm', 0))}", callback_data=f"exec_ai_pm_2_{user_id}"),
         InlineKeyboardButton(f"🟣 پیوی ۳ {get_user_status_icon(ai.get('ai_3_pm', 0))}", callback_data=f"exec_ai_pm_3_{user_id}")],
        [InlineKeyboardButton("⚫ خاموش پیوی", callback_data=f"exec_ai_pm_off_{user_id}")],
        [InlineKeyboardButton(f"🟢 گروه ۱ {get_user_status_icon(ai.get('ai_1_group', 0))}", callback_data=f"exec_ai_group_1_{user_id}"),
         InlineKeyboardButton(f"🔵 گروه ۲ {get_user_status_icon(ai.get('ai_2_group', 0))}", callback_data=f"exec_ai_group_2_{user_id}"),
         InlineKeyboardButton(f"🟣 گروه ۳ {get_user_status_icon(ai.get('ai_3_group', 0))}", callback_data=f"exec_ai_group_3_{user_id}")],
        [InlineKeyboardButton("⚫ خاموش گروه", callback_data=f"exec_ai_group_off_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_translate_menu_keyboard(user_id, translate_mode):
    langs = [('english', '🇬🇧 انگلیسی'), ('arabic', '🇸🇦 عربی'), ('hebrew', '🇮🇱 عبری'), ('russian', '🇷🇺 روسی'), ('turkish', '🇹🇷 ترکی')]
    keyboard = []
    row = []
    for key, label in langs:
        row.append(InlineKeyboardButton(f"{label} {get_user_status_icon(translate_mode.get(key, 0))}", callback_data=f"exec_translate_{key}_{user_id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")])
    return InlineKeyboardMarkup(keyboard)

def get_animation_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{BTN_ICONS[0]} قلب", callback_data=f"exec_heart_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[1]} ماه", callback_data=f"exec_moon_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[2]} قلب پیشرفته", callback_data=f"exec_advanced_heart_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[3]} عشق", callback_data=f"exec_love_{user_id}")],
        [InlineKeyboardButton(f"{BTN_ICONS[4]} سنتت", callback_data=f"exec_santet_{user_id}"),
         InlineKeyboardButton(f"{BTN_ICONS[5]} هک", callback_data=f"exec_hack_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_comment_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 کامنت", callback_data=f"exec_comment_{user_id}"),
         InlineKeyboardButton("📊 کانال‌ها", callback_data=f"exec_channels_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف کانال", callback_data=f"exec_delete_channel_{user_id}"),
         InlineKeyboardButton("🔍 تست کانال", callback_data=f"exec_test_channel_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_general_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 وضعیت", callback_data=f"exec_status_{user_id}"),
         InlineKeyboardButton("ℹ️ درباره", callback_data=f"exec_about_{user_id}")],
        [InlineKeyboardButton("⏱️ پینگ", callback_data=f"exec_ping_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_action_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 اکشن [نام]", callback_data=f"exec_action_{user_id}"),
         InlineKeyboardButton("⏹️ اکشن خاموش", callback_data=f"exec_action_off_{user_id}")],
        [InlineKeyboardButton("📋 اکشن لیست", callback_data=f"exec_action_list_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_games_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 تاس ۱", callback_data=f"exec_dice_1_{user_id}"),
         InlineKeyboardButton("🎲 تاس ۲", callback_data=f"exec_dice_2_{user_id}"),
         InlineKeyboardButton("🎲 تاس ۳", callback_data=f"exec_dice_3_{user_id}")],
        [InlineKeyboardButton("🎲 تاس ۴", callback_data=f"exec_dice_4_{user_id}"),
         InlineKeyboardButton("🎲 تاس ۵", callback_data=f"exec_dice_5_{user_id}"),
         InlineKeyboardButton("🎲 تاس ۶", callback_data=f"exec_dice_6_{user_id}")],
        [InlineKeyboardButton("🎯 دارت", callback_data=f"exec_dart_{user_id}"),
         InlineKeyboardButton("🏀 بسکتبال", callback_data=f"exec_basketball_{user_id}"),
         InlineKeyboardButton("⚽️ فوتبال", callback_data=f"exec_football_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_google_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 سرچ", callback_data=f"exec_search_on_{user_id}"),
         InlineKeyboardButton("❌ خروج جستجو", callback_data=f"exec_search_off_{user_id}")],
        [InlineKeyboardButton("🎵 اهنگ", callback_data=f"exec_music_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_info_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 اطلاعات", callback_data=f"exec_info_{user_id}"),
         InlineKeyboardButton("⬇️ دانلود پروفایل", callback_data=f"exec_download_profile_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_profile_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 ست پروف", callback_data=f"exec_set_profile_{user_id}"),
         InlineKeyboardButton("✏️ ست بیو", callback_data=f"exec_set_bio_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف ست پروف", callback_data=f"exec_delete_profile_{user_id}"),
         InlineKeyboardButton("🗑️ حذف ست بیو", callback_data=f"exec_delete_bio_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_message_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧹 حذف کامل", callback_data=f"exec_delete_all_{user_id}"),
         InlineKeyboardButton("🧹 حذف کامل ۵۰", callback_data=f"exec_delete_50_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف ۱۰", callback_data=f"exec_delete_10_{user_id}"),
         InlineKeyboardButton("👁️ فعال اتوسین", callback_data=f"exec_autosend_on_{user_id}")],
        [InlineKeyboardButton("🙈 غیرفعال اتوسین", callback_data=f"exec_autosend_off_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_reaction_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 ریکت", callback_data=f"exec_reaction_{user_id}"),
         InlineKeyboardButton("❌ حذف ریکت", callback_data=f"exec_reaction_off_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_spam_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📩 اسپم", callback_data=f"exec_spam_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_change_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ تغییر اسم", callback_data=f"exec_change_name_{user_id}"),
         InlineKeyboardButton("✏️ تغییر بیو", callback_data=f"exec_change_bio_{user_id}")],
        [InlineKeyboardButton("📸 تغییر پروفایل", callback_data=f"exec_change_profile_{user_id}"),
         InlineKeyboardButton("📸 پروف", callback_data=f"exec_change_profile_alt_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_enemy_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 لیست دشمن", callback_data=f"exec_enemy_list_{user_id}"),
         InlineKeyboardButton("📝 اضافه اسپم", callback_data=f"exec_add_spam_{user_id}")],
        [InlineKeyboardButton("✅ اتمام اسپم", callback_data=f"exec_end_spam_{user_id}"),
         InlineKeyboardButton("📜 لیست اسپم", callback_data=f"exec_spam_list_{user_id}")],
        [InlineKeyboardButton("🗑️ پاک کردن اسپم", callback_data=f"exec_clear_spam_{user_id}"),
         InlineKeyboardButton("🗑️ حذف اسپم", callback_data=f"exec_delete_spam_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_filter_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 .فیلتر [کلمه]", callback_data=f"exec_filter_word_{user_id}"),
         InlineKeyboardButton("✅ فیلتر روشن", callback_data=f"exec_filter_on_{user_id}")],
        [InlineKeyboardButton("❌ فیلتر خاموش", callback_data=f"exec_filter_off_{user_id}"),
         InlineKeyboardButton("📜 لیست فیلتر", callback_data=f"exec_filter_list_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف فیلتر", callback_data=f"exec_filter_remove_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_protection_menu_keyboard(user_id):
    spam_settings = db.get_spam_settings(user_id)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🛡️ اسپم روشن {get_user_status_icon(spam_settings.get('spam_protection', 0))}", callback_data=f"exec_spam_protection_on_{user_id}"),
         InlineKeyboardButton("🛡️ اسپم خاموش", callback_data=f"exec_spam_protection_off_{user_id}")],
        [InlineKeyboardButton("⚙️ تنظیم اسپم", callback_data=f"exec_spam_settings_{user_id}"),
         InlineKeyboardButton("📊 وضعیت اسپم", callback_data=f"exec_spam_status_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_report_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📍 تنظیم گزارش", callback_data=f"exec_set_report_{user_id}"),
         InlineKeyboardButton("ℹ️ گروه گزارش", callback_data=f"exec_show_report_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

def get_broadcast_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 پیام همگانی", callback_data=f"exec_broadcast_{user_id}"),
         InlineKeyboardButton("📊 آمار کاربران", callback_data=f"exec_user_stats_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]
    ])

# ========== هندلرهای ربات تلگرام ==========
async def inline_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    if not query:
        return
    user_id = query.from_user.id
    user_data = db.get_user(str(user_id))
    if not user_data or not user_data.get('self_active'):
        results = [InlineQueryResultArticle(id=str(uuid.uuid4()), title="⛔ دسترسی محدود", description="شما عضو سرویس نیستید", input_message_content=InputTextMessageContent("⛔ شما به این پنل دسترسی ندارید\n\nبرای عضویت: /start"))]
        await query.answer(results, cache_time=1, is_personal=True)
        return
    
    if not query.query:
        results = [InlineQueryResultArticle(id=str(uuid.uuid4()), title="🌟 پنل اصلی", description="مدیریت تمام قابلیت‌های سلف‌بات", input_message_content=InputTextMessageContent("🌟 پنل سلف‌بات باز شد\n\n⚠️ توجه: این پنل فقط مخصوص شماست"), reply_markup=get_main_panel_keyboard(user_id))]
        if user_id == ADMIN_ID:
            results.append(InlineQueryResultArticle(id=str(uuid.uuid4()), title="👑 پنل ادمین", description="مدیریت کاربران و سلف‌بات‌ها و ارسال پیام همگانی", input_message_content=InputTextMessageContent("👑 پنل ادمین"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"admin_requests"), InlineKeyboardButton("🔐 منتظر ورود", callback_data=f"admin_login")], [InlineKeyboardButton("✅ کاربران فعال", callback_data=f"admin_active"), InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data=f"admin_selfbots")], [InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats"), InlineKeyboardButton("📢 پیام همگانی", callback_data=f"admin_broadcast")], [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]])))
        await query.answer(results, cache_time=1, is_personal=True)

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
                    await query.answer("⛔ این پنل مال شما نیست", show_alert=True)
                    return
                break
    
    if data == "back_main":
        await query.edit_message_text("🌟 پنل مدیریت سلف‌بات\n\n⚠️ توجه: این پنل فقط مخصوص شماست\n\n✅ سلف‌بات به صورت ۲۴ ساعته فعال می‌ماند", reply_markup=get_main_panel_keyboard(user_id))
        return
    
    if data.startswith("close_panel_"):
        try:
            await query.message.delete()
            await query.answer("✅ پنل بسته شد")
        except:
            await query.answer("❌ خطا در بستن پنل")
        return
    
    if data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"admin_requests"), InlineKeyboardButton("🔐 منتظر ورود", callback_data=f"admin_login")], [InlineKeyboardButton("✅ کاربران فعال", callback_data=f"admin_active"), InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data=f"admin_selfbots")], [InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats"), InlineKeyboardButton("📢 پیام همگانی", callback_data=f"admin_broadcast")], [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_main")]])
        await query.edit_message_text("👑 پنل مدیریت\n\nلطفاً انتخاب کنید:", reply_markup=keyboard)
        return
    
    if data == "admin_requests":
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        pending = db.get_pending_requests()
        if pending:
            text = "📋 درخواست‌های عضویت:\n\n"
            keyboard = []
            for req in pending[:10]:
                text += f"👤 {req['full_name']}\n🆔 {req['user_id']}\n📅 {req.get('request_date', 'نامشخص')}\n\n"
                keyboard.append([InlineKeyboardButton(f"✅ تأیید {req['user_id']}", callback_data=f"approve_{req['user_id']}"), InlineKeyboardButton(f"❌ رد {req['user_id']}", callback_data=f"reject_{req['user_id']}")])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_panel")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("📋 هیچ درخواستی در انتظار نیست")
        return
    
    if data.startswith("approve_") or data.startswith("reject_"):
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        target_id = data.split('_')[1]
        user_data = db.get_user(target_id)
        if not user_data:
            await query.answer("❌ کاربر یافت نشد", show_alert=True)
            return
        if data.startswith("approve_"):
            db.update_user(target_id, admin_approved=1, activation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            try:
                await context.bot.send_message(chat_id=int(target_id), text="🎉 درخواست عضویت شما تأیید شد!\n\nلطفاً شماره تلفن خود را وارد کنید:\nمثال: +989123456789")
                db.update_user(target_id, step='get_phone')
            except:
                pass
            await query.edit_message_text(f"✅ کاربر {target_id} تأیید شد")
        else:
            db.update_user(target_id, rejected=1, request_sent=0)
            try:
                await context.bot.send_message(chat_id=int(target_id), text="⚠ درخواست عضویت شما رد شد.\n\nمی‌توانید دوباره درخواست دهید")
            except:
                pass
            await query.edit_message_text(f"❌ کاربر {target_id} رد شد")
        await query.message.delete()
        return
    
    if data.startswith("stop_selfbot_"):
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        target_id = data.split('_')[2]
        if target_id in selfbot_managers:
            await selfbot_managers[target_id].stop()
            del selfbot_managers[target_id]
            await query.answer(f"✅ سلف‌بات کاربر {target_id} متوقف شد", show_alert=True)
        else:
            await query.answer("❌ سلف‌بات فعال نیست", show_alert=True)
        return
    
    if data.startswith("restart_selfbot_"):
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        target_id = data.split('_')[2]
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
        return
    
    if data == "admin_active":
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        active = db.get_active_users()
        if active:
            text = "✅ کاربران فعال:\n\n"
            for user in active[:10]:
                text += f"👤 {user['full_name']}\n🆔 {user['user_id']}\n📞 {user.get('phone', 'نامشخص')}\n📅 انقضا: {user.get('expiration_date', 'نامشخص')}\n🤖 سلف‌بات: {'✅' if user['user_id'] in selfbot_managers else '❌'}\n\n"
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("✅ هیچ کاربر فعالی وجود ندارد")
        return
    
    if data == "admin_selfbots":
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        if selfbot_managers:
            text = "🤖 سلف‌بات‌های فعال:\n\n"
            keyboard = []
            for uid, manager in list(selfbot_managers.items())[:10]:
                user_data = db.get_user(uid)
                name = user_data['full_name'] if user_data else f"کاربر {uid}"
                text += f"👤 {name}\n🆔 {uid}\n\n"
                keyboard.append([InlineKeyboardButton(f"🛑 توقف {uid}", callback_data=f"stop_selfbot_{uid}"), InlineKeyboardButton(f"🔄 ریستارت {uid}", callback_data=f"restart_selfbot_{uid}")])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_panel")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("🤖 هیچ سلف‌باتی در حال اجرا نیست")
        return
    
    if data == "admin_stats":
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        total_users = len(db.get_all_users())
        active_users = len(db.get_active_users())
        pending_requests = len(db.get_pending_requests())
        pending_login = len(db.get_pending_login())
        active_selfbots = len(selfbot_managers)
        stats = f"📊 آمار کلی\n━━━━━━━━━━━━━━━━━━━━\n👥 کل کاربران: {total_users}\n✅ کاربران فعال: {active_users}\n📋 درخواست‌ها: {pending_requests}\n🔐 منتظر ورود: {pending_login}\n🤖 سلف‌بات فعال: {active_selfbots}\n\n🕐 آخرین به‌روزرسانی: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}\n━━━━━━━━━━━━━━━━━━━━"
        await query.edit_message_text(stats)
        return
    
    if data == "admin_broadcast":
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
        await query.edit_message_text("📢 ارسال پیام همگانی\n\nلطفاً پیام خود را ارسال کنید.\n\n⚠️ توجه: این پیام برای همه کاربران فعال ارسال خواهد شد.\n\nبرای لغو: /cancel")
        context.user_data['broadcast_mode'] = True
        return
    
    if data.startswith("exec_"):
        await exec_command_handler(update, context)
        return
    
    parts = data.split('_')
    if len(parts) > 1:
        action = parts[0]
        menu_configs = {
            "time": ("🕐 دستورات زمان و پروفایل\n\n• تایم روشن\n• تایمر پرچم روشن\n• تایم خاموش\n• تایم [اعداد]\n• تاریخ کامل", lambda uid: get_time_menu_keyboard(uid, db.get_selfbot_settings(uid))),
            "animation": ("❤️ انیمیشن‌ها\n\n• قلب\n• ماه\n• قلب پیشرفته\n• عشق\n• سنتت\n• هک", get_animation_menu_keyboard),
            "user": ("👥 مدیریت کاربران\n\n• دشمن (ریپلای)\n• دوست (ریپلای)\n• قفل پیوی (ریپلای)\n• باز پی (ریپلای)\n• قفل پیوی همه\n• باز پی همه\n• بلاک", get_user_menu_keyboard),
            "lock": ("🔒 قفل رسانه (با ریپلای برای کاربر خاص)\n\n• قفل لینک\n• قفل عکس\n• قفل ویدیو\n• قفل استیکر\n• قفل گیف\n• قفل ویس\n• قفل فایل\n• قفل موزیک\n• قفل ویدیو نوت\n• قفل کانتکت\n• قفل لوکیشن\n• قفل ایموجی\n• قفل متن", lambda uid: get_lock_menu_keyboard(uid, None)),
            "comment": ("💬 کامنت خودکار\n\n• کامنت [متن]\n• کانال‌ها\n• حذف کانال\n• تست کانال", get_comment_menu_keyboard),
            "general": ("📋 دستورات عمومی\n\n• وضعیت\n• درباره\n• پینگ", get_general_menu_keyboard),
            "action": ("🎮 اکشن‌ها\n\n• اکشن [نام]\n• اکشن خاموش\n• اکشن لیست\n\nلیست اکشن‌ها:\n• تایپ\n• ویس\n• ویدیو\n• عکس\n• فیلم\n• فایل\n• بازی\n• استیکر\n• موقعیت\n• تماس\n• صحبت\n• لغو", get_action_menu_keyboard),
            "games": ("🎲 بازی‌ها\n\n• تاس [1-6]\n• دارت\n• بسکتبال\n• فوتبال", get_games_menu_keyboard),
            "translate": ("🌐 ترجمه خودکار\n\n• انگلیسی روشن/خاموش\n• عربی روشن/خاموش\n• عبری روشن/خاموش\n• روسی روشن/خاموش\n• ترکی روشن/خاموش", lambda uid: get_translate_menu_keyboard(uid, selfbot_managers.get(str(uid), SelfBotManager(uid)).translate_mode if str(uid) in selfbot_managers else {"english": False, "arabic": False, "hebrew": False, "russian": False, "turkish": False})),
            "google": ("🔍 گوگل و اهنگ\n\n• سرچ [موضوع]\n• خروج جستجو\n• .اهنگ [نام آهنگ]", get_google_menu_keyboard),
            "info": ("ℹ️ دستورات اطلاعاتی\n\n• اطلاعات (ریپلای)\n• دانلود پروفایل (ریپلای)", get_info_menu_keyboard),
            "profile": ("📸 مدیریت پروفایل\n\n• ست پروف (ریپلای)\n• ست بیو (ریپلای)\n• حذف ست پروف\n• حذف ست بیو", get_profile_menu_keyboard),
            "style": ("✍️ استایل متن\n\n• بولد\n• زیرخط\n• خط خورده\n• نقل قول\n• اسپویلر\n• کج\n• کد\n• پیش", lambda uid: get_style_menu_keyboard(uid, db.get_selfbot_settings(uid).get('text_style', 'هیچ'))),
            "message": ("📨 مدیریت پیام\n\n• حذف کامل\n• حذف کامل ۵۰\n• حذف ۱۰\n• فعال اتوسین\n• غیرفعال اتوسین", get_message_menu_keyboard),
            "reaction": ("😊 ریکشن خودکار\n\n• ریکت [ایموجی] (ریپلای)\n• حذف ریکت (ریپلای)", get_reaction_menu_keyboard),
            "spam": ("📩 ارسال اسپم\n\n• اسپم [تعداد] [متن]", get_spam_menu_keyboard),
            "change": ("✏️ تغییر پروفایل\n\n• تغییر اسم [نام]\n• تغییر بیو [متن]\n• تغییر پروفایل (ریپلای)\n• پروف (ریپلای)", get_change_menu_keyboard),
            "enemy": ("🥷 مدیریت دشمنان\n\n• لیست دشمن\n• اضافه اسپم\n• اتمام اسپم\n• لیست اسپم\n• پاک کردن اسپم\n• حذف اسپم [شماره]", get_enemy_menu_keyboard),
            "filter": ("🚫 فیلتر کلمات\n\n• .فیلتر [کلمه]\n• فیلتر روشن\n• فیلتر خاموش\n• لیست فیلتر\n• حذف فیلتر [کلمه]", get_filter_menu_keyboard),
            "protection": ("🛡️ حفاظت اسپم\n\n• اسپم روشن\n• اسپم خاموش\n• تنظیم اسپم [تعداد] [زمان]\n• وضعیت اسپم", get_protection_menu_keyboard),
            "ai": ("🤖 هوش مصنوعی\n\n• پیوی ۱/۲/۳\n• خاموش پیوی\n• گروه ۱/۲/۳\n• خاموش گروه", lambda uid: get_ai_menu_keyboard(uid, db.get_selfbot_settings(uid))),
            "report": ("📊 گزارش\n\n• تنظیم گزارش\n• گروه گزارش", get_report_menu_keyboard),
            "broadcast": ("📢 پیام همگانی\n\n• ارسال پیام به همه کاربران\n• مشاهده آمار کاربران", get_broadcast_menu_keyboard)
        }
        if action in menu_configs and parts[1] == "menu":
            text, keyboard_func = menu_configs[action]
            await query.edit_message_text(text, reply_markup=keyboard_func(user_id))

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
    owner_id = None
    for part in reversed(parts):
        if part.isdigit() and len(part) >= 5:
            owner_id = part
            break
    if owner_id and str(owner_id) != user_id_str:
        await query.answer("⛔ این پنل مال شما نیست", show_alert=True)
        return
    
    if user_id_str not in selfbot_managers:
        await query.edit_message_text("❌ سلف‌بات شما فعال نیست")
        return
    
    manager = selfbot_managers[user_id_str]
    
    cmd_parts = data.replace(f'exec_', '').split('_')
    cmd_parts = [p for p in cmd_parts if not (p.isdigit() and len(p) >= 5)]
    cmd = '_'.join(cmd_parts)
    
    msg = await context.bot.send_message(chat_id=query.message.chat_id, text=f"⏳ در حال اجرا...")
    
    # ====== دستورات انیمیشن ======
    if cmd == 'advanced_heart':
        try:
            heart_msg = await manager.client.send_message(query.message.chat_id, "❤️")
            await advanced_heart_animation(heart_msg)
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
        return
    
    if cmd == 'love':
        try:
            love_msg = await manager.client.send_message(query.message.chat_id, "💝")
            await advanced_heart_animation(love_msg)
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
        return
    
    if cmd == 'santet':
        try:
            santet_msg = await manager.client.send_message(query.message.chat_id, "🕯️")
            for i in range(101):
                bar_len = int(i / 100 * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                await santet_msg.edit(f"🕯️ {i}% [{bar}]")
                await asyncio.sleep(0.03)
            await asyncio.sleep(1)
            await santet_msg.edit("✅ انجام شد 🥴")
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
        return
    
    if cmd == 'hack':
        try:
            hack_msg = await manager.client.send_message(query.message.chat_id, "💻")
            await asyncio.sleep(2)
            await hack_msg.edit("User online: True\nTelegram access: True\nRead Storage: True")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 25%\n[█████░░░░░░░░░░░░░░░]")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 50%\n[██████████░░░░░░░░░░]")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 75%\n[███████████████░░░░░]")
            await asyncio.sleep(2)
            await hack_msg.edit("Hacking... 100%\n[████████████████████]")
            await asyncio.sleep(2)
            await hack_msg.edit("✅ هک کامل شد")
        except Exception as e:
            await msg.edit_text(f"❌ خطا: {e}")
        return
    
    if cmd == 'heart':
        asyncio.create_task(manager.heart_animation(query.message.chat_id))
        await msg.edit_text("❤️ انیمیشن قلب شروع شد")
        return
    
    if cmd == 'moon':
        asyncio.create_task(manager.moon_animation(query.message.chat_id))
        await msg.edit_text("🌙 انیمیشن ماه شروع شد")
        return
    
    # ====== دستورات زمان و پروفایل ======
    if cmd == 'time_on':
        db.update_selfbot_setting(user_id, 'time_enabled', 1)
        db.update_selfbot_setting(user_id, 'flag_enabled', 0)
        await manager.update_profile_name()
        await msg.edit_text("✅ تایم روشن شد")
        await query.edit_message_text("🕐 دستورات زمان و پروفایل\n\n• تایم روشن ✓\n• تایمر پرچم\n• تایم خاموش\n• تایم [اعداد]\n• تاریخ کامل", reply_markup=get_time_menu_keyboard(user_id, db.get_selfbot_settings(user_id)))
        return
    
    if cmd == 'time_flag':
        db.update_selfbot_setting(user_id, 'time_enabled', 1)
        db.update_selfbot_setting(user_id, 'flag_enabled', 1)
        await manager.update_profile_name()
        await msg.edit_text("✅ تایمر پرچم روشن شد")
        await query.edit_message_text("🕐 دستورات زمان و پروفایل\n\n• تایم روشن\n• تایمر پرچم ✓\n• تایم خاموش\n• تایم [اعداد]\n• تاریخ کامل", reply_markup=get_time_menu_keyboard(user_id, db.get_selfbot_settings(user_id)))
        return
    
    if cmd == 'time_off':
        db.update_selfbot_setting(user_id, 'time_enabled', 0)
        db.update_selfbot_setting(user_id, 'flag_enabled', 0)
        await manager.restore_profile_name()
        await msg.edit_text("✅ تایم خاموش شد")
        await query.edit_message_text("🕐 دستورات زمان و پروفایل\n\n• تایم روشن\n• تایمر پرچم\n• تایم خاموش ✓\n• تایم [اعداد]\n• تاریخ کامل", reply_markup=get_time_menu_keyboard(user_id, db.get_selfbot_settings(user_id)))
        return
    
    if cmd == 'full_date':
        await msg.edit_text(get_full_date_info())
        return
    
    # ====== دستورات قفل رسانه ======
    if cmd.startswith('lock_'):
        lock_type = cmd.replace('lock_', '')
        target_id = None
        for part in data.split('_'):
            if part.isdigit() and part != str(user_id) and len(part) >= 5:
                target_id = int(part)
                break
        if not target_id:
            target_id = 0
        
        current_locks = db.get_media_locks(user_id, target_id)
        new_value = not current_locks.get(f'lock_{lock_type}', 0)
        db.set_media_lock(user_id, target_id, f'lock_{lock_type}', new_value)
        
        status = "فعال" if new_value else "غیرفعال"
        await msg.edit_text(f"✅ قفل {lock_type} {status} شد")
        await query.edit_message_text(f"🔒 قفل رسانه {'(برای کاربر خاص)' if target_id and target_id != 0 else '(برای همه کاربران)'}\n\n• قفل لینک\n• قفل عکس\n• قفل ویدیو\n• قفل استیکر\n• قفل گیف\n• قفل ویس\n• قفل فایل\n• قفل موزیک\n• قفل ویدیو نوت\n• قفل کانتکت\n• قفل لوکیشن\n• قفل ایموجی\n• قفل متن", reply_markup=get_lock_menu_keyboard(user_id, target_id))
        return
    
    # ====== دستورات استایل متن ======
    if cmd.startswith('style_'):
        style = cmd.replace('style_', '')
        current_style = db.get_selfbot_settings(user_id).get('text_style', 'هیچ')
        if current_style == style:
            db.update_selfbot_setting(user_id, 'text_style', None)
            await msg.edit_text(f"✅ استایل {style} غیرفعال شد")
        else:
            db.update_selfbot_setting(user_id, 'text_style', style)
            await msg.edit_text(f"✅ استایل {style} فعال شد")
        await query.edit_message_text("✍️ استایل متن\n\n• بولد\n• زیرخط\n• خط خورده\n• نقل قول\n• اسپویلر\n• کج\n• کد\n• پیش", reply_markup=get_style_menu_keyboard(user_id, db.get_selfbot_settings(user_id).get('text_style', 'هیچ')))
        return
    
    # ====== دستورات هوش مصنوعی ======
    if cmd.startswith('ai_'):
        ai_cmd = cmd.replace('ai_', '')
        settings = db.get_selfbot_settings(user_id)
        ai_status = settings.get('ai_status', {})
        
        if ai_cmd == 'pm_1':
            ai_status['ai_1_pm'] = not ai_status.get('ai_1_pm', 0)
            ai_status['ai_2_pm'] = 0
            ai_status['ai_3_pm'] = 0
        elif ai_cmd == 'pm_2':
            ai_status['ai_1_pm'] = 0
            ai_status['ai_2_pm'] = not ai_status.get('ai_2_pm', 0)
            ai_status['ai_3_pm'] = 0
        elif ai_cmd == 'pm_3':
            ai_status['ai_1_pm'] = 0
            ai_status['ai_2_pm'] = 0
            ai_status['ai_3_pm'] = not ai_status.get('ai_3_pm', 0)
        elif ai_cmd == 'pm_off':
            ai_status['ai_1_pm'] = 0
            ai_status['ai_2_pm'] = 0
            ai_status['ai_3_pm'] = 0
        elif ai_cmd == 'group_1':
            ai_status['ai_1_group'] = not ai_status.get('ai_1_group', 0)
            ai_status['ai_2_group'] = 0
            ai_status['ai_3_group'] = 0
        elif ai_cmd == 'group_2':
            ai_status['ai_1_group'] = 0
            ai_status['ai_2_group'] = not ai_status.get('ai_2_group', 0)
            ai_status['ai_3_group'] = 0
        elif ai_cmd == 'group_3':
            ai_status['ai_1_group'] = 0
            ai_status['ai_2_group'] = 0
            ai_status['ai_3_group'] = not ai_status.get('ai_3_group', 0)
        elif ai_cmd == 'group_off':
            ai_status['ai_1_group'] = 0
            ai_status['ai_2_group'] = 0
            ai_status['ai_3_group'] = 0
        
        db.update_ai_status(user_id, ai_status)
        await msg.edit_text("✅ وضعیت هوش مصنوعی به‌روزرسانی شد")
        await query.edit_message_text("🤖 هوش مصنوعی\n\n• پیوی ۱/۲/۳\n• خاموش پیوی\n• گروه ۱/۲/۳\n• خاموش گروه", reply_markup=get_ai_menu_keyboard(user_id, db.get_selfbot_settings(user_id)))
        return
    
    # ====== دستورات ترجمه ======
    if cmd.startswith('translate_'):
        lang = cmd.replace('translate_', '')
        manager.translate_mode[lang] = not manager.translate_mode.get(lang, False)
        await msg.edit_text(f"✅ ترجمه {lang} {'فعال' if manager.translate_mode[lang] else 'غیرفعال'} شد")
        await query.edit_message_text("🌐 ترجمه خودکار\n\n• انگلیسی روشن/خاموش\n• عربی روشن/خاموش\n• عبری روشن/خاموش\n• روسی روشن/خاموش\n• ترکی روشن/خاموش", reply_markup=get_translate_menu_keyboard(user_id, manager.translate_mode))
        return
    
    # ====== دستورات عمومی ======
    if cmd == 'status':
        await msg.edit_text(manager.format_status_info(db.get_selfbot_settings(user_id)))
        return
    
    if cmd == 'about':
        await msg.edit_text(f"ℹ️ درباره بات\n\n🤖 نسخه: v{BOT_VERSION}\n👨‍💻 سازنده: {BOT_CREATOR}")
        return
    
    if cmd == 'ping':
        start = time.time()
        await msg.edit_text("🏓 پینگ: ...")
        end = time.time()
        ping = round((end - start) * 1000, 2)
        await msg.edit_text(f"🏓 پینگ: {ping} ms")
        return
    
    if cmd == 'music':
        await msg.edit_text("🎵 دستور اهنگ\n\nبرای جستجو و پخش آهنگ از فرمت زیر استفاده کنید:\n\n`.اهنگ [نام آهنگ]`\n\nمثال: `.اهنگ مهدیار احمدی`")
        return
    
    if cmd == 'search_on':
        manager.search_mode = True
        await msg.edit_text("🔍 حالت سرچ فعال شد")
        return
    
    if cmd == 'search_off':
        manager.search_mode = False
        await msg.edit_text("✅ حالت سرچ غیرفعال شد")
        return
    
    # ====== دستورات مدیریت کاربران ======
    if cmd == 'enemy':
        target_id = await get_target_user_from_callback(query, manager)
        if target_id:
            db.add_enemy(user_id, target_id, 'pv')
            await msg.edit_text(f"✅ دشمن اضافه شد")
            asyncio.create_task(manager.spam_enemy(target_id))
        else:
            await msg.edit_text("⚠️ روی پیام کاربر ریپلای کنید (در پیوی خودتان)")
        return
    
    if cmd == 'friend':
        target_id = await get_target_user_from_callback(query, manager)
        if target_id:
            db.remove_enemy(user_id, target_id, 'pv')
            if target_id in manager.spam_tasks:
                manager.spam_tasks[target_id].cancel()
                del manager.spam_tasks[target_id]
            await msg.edit_text(f"✅ دوست حذف شد")
        else:
            await msg.edit_text("⚠️ روی پیام کاربر ریپلای کنید (در پیوی خودتان)")
        return
    
    if cmd == 'lock_pv':
        target_id = await get_target_user_from_callback(query, manager)
        if target_id:
            db.add_locked_pv(user_id, target_id)
            await msg.edit_text(f"✅ قفل پیوی فعال شد")
        else:
            await msg.edit_text("⚠️ روی پیام کاربر ریپلای کنید (در پیوی خودتان)")
        return
    
    if cmd == 'unlock_pv':
        target_id = await get_target_user_from_callback(query, manager)
        if target_id:
            db.remove_locked_pv(user_id, target_id)
            await msg.edit_text(f"✅ قفل پیوی غیرفعال شد")
        else:
            await msg.edit_text("⚠️ روی پیام کاربر ریپلای کنید (در پیوی خودتان)")
        return
    
    if cmd == 'lock_all':
        db.update_selfbot_setting(user_id, 'pv_lock_all', 1)
        await msg.edit_text("✅ قفل پیوی همگانی فعال شد")
        return
    
    if cmd == 'unlock_all':
        db.update_selfbot_setting(user_id, 'pv_lock_all', 0)
        await msg.edit_text("✅ قفل پیوی همگانی غیرفعال شد")
        return
    
    if cmd == 'block':
        target_id = await get_target_user_from_callback(query, manager)
        if target_id:
            try:
                await manager.client(BlockRequest(id=target_id))
                await msg.edit_text("✅ کاربر بلاک شد")
            except Exception as e:
                await msg.edit_text(f"❌ خطا: {e}")
        else:
            await msg.edit_text("⚠️ روی پیام کاربر ریپلای کنید (در پیوی خودتان)")
        return
    
    await msg.edit_text(f"✅ دستور {cmd} اجرا شد")

async def get_target_user_from_callback(query, manager):
    try:
        return None
    except:
        return None

# ========== هندلرهای start و message ==========
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
        text = f"👋 سلام {full_name} عزیز!\n\n✅ حساب شما فعال است.\n• /panel - پنل مدیریت\n• @{BOT_USERNAME} - پنل اینلاین\n• .پنل - پنل در همین چت\n• .اهنگ [نام آهنگ] - پخش آهنگ\n\n⚠️ پنل فقط مخصوص شماست"
        keyboard = [[InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]]
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel")])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    text = f"👋 سلام {full_name} عزیز!\n\n🌟 به ربات سلف‌بات خوش آمدید.\n\n📌 برای استفاده:\n1️⃣ روی دکمه عضویت کلیک کنید\n2️⃣ شماره تلفن خود را وارد کنید\n3️⃣ کد تأیید را وارد کنید\n\n✅ پس از فعال شدن:\n• /panel - پنل مدیریت\n• @{BOT_USERNAME} - پنل اینلاین\n• .پنل - پنل در همین چت\n• .اهنگ [نام آهنگ] - پخش آهنگ"
    keyboard = [[InlineKeyboardButton("📝 عضویت", callback_data=f"membership_request_{user_id}")], [InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]]
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
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🌟 پنل مدیریت سلف‌بات\n\nبرای باز کردن پنل، روی دکمه کلیک کنید:\n\n⚠️ توجه: این پنل فقط مخصوص شماست", reply_markup=keyboard)

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
    admin_text = f"📋 درخواست عضویت جدید\n━━━━━━━━━━━━━━━━━━━━\n👤 نام: {user_data['full_name']}\n🆔 آیدی: {user_id_str}\n👤 یوزرنیم: @{user_data['username'] if user_data['username'] else 'ندارد'}\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n━━━━━━━━━━━━━━━━━━━━"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{user_id_str}"), InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id_str}")]])
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = update.message.text
    text = convert_persian_to_english(text)
    
    if context.user_data.get('broadcast_mode') and user_id == ADMIN_ID:
        if text == '/cancel':
            context.user_data['broadcast_mode'] = False
            await update.message.reply_text("✅ ارسال پیام همگانی لغو شد")
            return
        all_users = db.get_all_users()
        active_users = [u for u in all_users if u.get('self_active')]
        sent_count = 0
        failed_count = 0
        broadcast_id = db.add_broadcast(user_id, text, 'text')
        await update.message.reply_text("⏳ در حال ارسال پیام همگانی...")
        for user in active_users:
            try:
                await context.bot.send_message(chat_id=int(user['user_id']), text=f"📢 **پیام همگانی**\n━━━━━━━━━━━━━━━━━━━━\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🕐 {datetime.now().strftime('%Y/%m/%d %H:%M')}", parse_mode='Markdown')
                sent_count += 1
                await asyncio.sleep(0.1)
            except:
                failed_count += 1
        db.update_broadcast_stats(broadcast_id, sent_count, failed_count)
        result_text = f"✅ ارسال پیام همگانی کامل شد!\n\n📊 آمار ارسال:\n• کل کاربران فعال: {len(active_users)}\n• ارسال موفق: {sent_count}\n• ارسال ناموفق: {failed_count}\n\n🕐 زمان: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
        await update.message.reply_text(result_text)
        context.user_data['broadcast_mode'] = False
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
                await update.message.reply_text("⚠️ فایل سشن یافت نشد")
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
            API_ID = user_api["api_id"]
            API_HASH = user_api["api_hash"]
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            sent_code = await client.send_code_request(text)
            phone_code_hash = sent_code.phone_code_hash
            db.update_user(user_id_str, phone_code_hash=phone_code_hash)
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
            await client.sign_in(phone=user_data['phone'], code=code_for_telegram, phone_code_hash=user_data['phone_code_hash'])
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
            API_ID = user_api["api_id"]
            API_HASH = user_api["api_hash"]
            client = TelegramClient(session_path, API_ID, API_HASH)
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

async def main():
    print("=" * 60)
    print("🤖 سیستم جامع عضویت و سلف‌بات")
    print(f"👑 ادمین: {ADMIN_ID}")
    print(f"📁 پوشه سشن‌ها: {SESSIONS_FOLDER}")
    print("=" * 60)
    
    if not os.path.exists(SESSIONS_FOLDER):
        os.makedirs(SESSIONS_FOLDER)
    
    app = Application.builder().token(BOT_TOKEN).request(HTTPXRequest(connection_pool_size=10, connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0, pool_timeout=30.0)).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel_command))
    app.add_handler(InlineQueryHandler(inline_panel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    
    print("✅ ربات شروع شد")
    print("=" * 60)
    
    active_users = db.get_active_users()
    success_count = 0
    fail_count = 0
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
