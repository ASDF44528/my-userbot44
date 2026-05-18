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
from datetime import datetime, timedelta
from urllib.parse import quote
import pytz
import jdatetime
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
from telethon.errors import MessageDeleteForbiddenError, FloodWaitError, SessionPasswordNeededError
from telethon.errors import FloodWaitError as TelethonFloodWaitError
from flask import Flask
from threading import Thread

# ========== سرور Flask برای Render (رفع مشکل پورت) ==========
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "✅ ربات سلف‌بات آنلاین است!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("✅ سرور Flask برای پورت روشن شد")

# ========== تنظیمات لاگ ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== لیست API های رندوم ==========
API_CONFIGS = [
    {"api_id": 28297221, "api_hash": "8d682eb5c41a9762ef73f9ebe06c4eff"},
    {"api_id": 28039994, "api_hash": "00877cdcd706564a4de6abf7f7d64349"}
]

selected_api = random.choice(API_CONFIGS)
API_ID = selected_api["api_id"]
API_HASH = selected_api["api_hash"]

BOT_TOKEN = "8304449635:AAEdj3veIxfoVuPj66KwpdBnxpzP_x0eYyo"
ADMIN_ID = 6443963679
BOT_USERNAME = "Gap_5_bot"

# ========== پوشه سشن‌ها ==========
SESSIONS_FOLDER = 'user_sessions'
if not os.path.exists(SESSIONS_FOLDER):
    os.makedirs(SESSIONS_FOLDER)

# ========== تنظیمات سلف‌بات ==========
GROUP_ID = -1002817019483

# ========== تنظیمات ۳ هوش مصنوعی ==========
FREE_AI_URL = "https://hoshi-app.ir/api/chat-gpt.php?text="
PAXSENIX_API_KEY = "sk-paxsenix-Xo_BAFNGgWVZ_ymWd02Rk1JHbyoDSEzfPhiolJ3F12cY6XZG"
PAXSENIX_API_URL = "https://api.paxsenix.org/v1/chat/completions"
DEEPSEEK_FREE_URL = "https://deepseek.api-sina-free.workers.dev/?text="

# ========== API جستجوی گوگل ==========
GOOGLE_SEARCH_API_KEY = "AIzaSyCMYOU0NpU5xfu7GrffyywVUugd1yD2uDU"
GOOGLE_CSE_ID = "3185e48756dfd482f"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

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
    "0̶1̶2̶3̶4̶5̶6̶7̶8̶9̶"
]

# ========== لیست پرچم‌ها ==========
flags = [
    "🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇼", "🇦🇼", "🇦🇹", "🇦🇿", "🇧🇸", "🇧🇭",
    "🇧🇩", "🇧🇧", "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇴", "🇧🇦", "🇧🇼",
    "🇧🇷", "🇮🇴", "🇻🇬", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦",
    "🇨🇻", "🇰🇾", "🇨🇫", "🇹🇩", "🇨🇱", "🇨🇩", "🇨🇽", "🇨🇨", "🇨🇴", "🇰🇲",
    "🇨🇬", "🇨🇩", "🇨🇰", "🇨🇰", "🕋"
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

# ========== سیستم ترجمه و بازی تاس ==========
translate_mode = {
    "english": False,
    "arabic": False,
    "hebrew": False,
    "russian": False,
    "turkish": False
}

# ========== لیست اکشن‌ها ==========
action_types = {
    'تایپ': types.SendMessageTypingAction(),
    'ویس': types.SendMessageRecordAudioAction(),
    'ویدیو': types.SendMessageRecordVideoAction(),
    'عکس': types.SendMessageUploadPhotoAction(progress=0),
    'فیلم': types.SendMessageUploadVideoAction(progress=0),
    'فایل': types.SendMessageUploadDocumentAction(progress=0),
    'آهنگ': types.SendMessageUploadAudioAction(progress=0),
    'بازی': types.SendMessageGamePlayAction(),
    'استیکر': types.SendMessageChooseStickerAction(),
    'موقعیت': types.SendMessageGeoLocationAction(),
    'تماس': types.SendMessageChooseContactAction(),
    'صحبت': types.SpeakingInGroupCallAction(),
    'لغو': types.SendMessageCancelAction(),
}

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
                song_command_status BOOLEAN DEFAULT 1,
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
            return settings
        else:
            default_settings = {
                'user_id': user_id,
                'time_enabled': 0,
                'flag_enabled': 0,
                'pv_lock_all': 0,
                'autosend_mode': 0,
                'text_style': None,
                'song_command_status': 1,
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
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        settings_to_save = settings.copy()
        settings_to_save.pop('ai_status', None)
        settings_to_save.pop('translate', None)
        
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

# ========== ایجاد دیتابیس ==========
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
📅 **تاریخ کامل**
━━━━━━━━━━━━━━━━━━━━
🕐 **ساعت:** {now.strftime('%H:%M:%S')}

📆 **شمسی:**
{persian_weekdays[jdate.weekday()]} - {jdate.day} {jdate.strftime('%B')} {jdate.year}

📆 **میلادی:**
{gregorian_weekdays[now.weekday()]} - {now.strftime('%B %d, %Y')}

📆 **قمری:**
{hijri.day} {hijri.month_name()} {hijri.year}
━━━━━━━━━━━━━━━━━━━━
        """
    except:
        return f"📅 **تاریخ:** {now.strftime('%Y/%m/%d %H:%M:%S')}"

def is_channel_post(message):
    try:
        if hasattr(message, 'post') and message.post:
            return True
        if message.is_channel and not message.is_group:
            return True
        chat = message.chat
        if hasattr(chat, 'broadcast') and chat.broadcast:
            return True
        return False
    except:
        return False

def is_song_request(text):
    text_lower = text.lower()
    return 'آهنگ' in text_lower and len(text.replace('آهنگ', '').strip()) > 0

def extract_song_name(text):
    text = text.replace('آهنگ', '').strip()
    stop_words = ['لطفا', 'لطفاً', 'برام', 'بفرست', 'بفرسته', 'پیدا', 'کن']
    words = text.split()
    filtered = [w for w in words if w not in stop_words]
    return ' '.join(filtered) or text

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
    
    async def start(self, session_file):
        try:
            if os.path.exists(session_file):
                self.client = TelegramClient(session_file, API_ID, API_HASH)
                await self.client.start()
                
                me = await self.client.get_me()
                self.my_id = me.id
                self.BASE_NAME = me.first_name or "Self-Bot"
                
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
                
                self.setup_handlers()
                asyncio.create_task(self.update_profile_task())
                
                self.running = True
                logger.info(f"سلف‌بات برای کاربر {self.user_id} شروع شد")
                return True
            return False
        except Exception as e:
            logger.error(f"خطا در شروع سلف‌بات: {e}")
            return False
    
    async def stop(self):
        if self.client:
            await self.client.disconnect()
            self.running = False
            for task in self.spam_tasks.values():
                task.cancel()
            for group_tasks in self.group_spam_tasks.values():
                for task in group_tasks.values():
                    task.cancel()
            self.spam_tasks.clear()
            self.group_spam_tasks.clear()
            logger.info(f"سلف‌بات برای کاربر {self.user_id} متوقف شد")
    
    def setup_handlers(self):
        @self.client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            await self.handle_new_message(event)
        
        @self.client.on(events.MessageEdited(incoming=True))
        async def handle_edited_message(event):
            await self.handle_edited_message(event)
        
        @self.client.on(events.MessageDeleted)
        async def handle_deleted_message(event):
            await self.handle_deleted_message(event)
        
        @self.client.on(events.NewMessage(pattern=r'^(لیست|راهنما ۱|راهنما ۲|راهنما ۳)$'))
        async def list_settings(event):
            await self.send_help_message(event, event.text.lower())
        
        @self.client.on(events.NewMessage(pattern=r'^(?:شروع|تایم روشن|تایمر پرچم روشن|تایم خاموش|قلب|ماه|اطلاعات|دانلود پروفایل|تاریخ کامل|فعال اتوسین|غیرفعال اتوسین|حذف کامل|ست پروف|ست بیو|حذف ست پروف|حذف ست بیو|بولد روشن|بولد خاموش|زیرخط روشن|زیرخط خاموش|خط خورده روشن|خط خورده خاموش|نقل قول روشن|نقل قول خاموش|اسپویلر روشن|اسپویلر خاموش|کج روشن|کج خاموش|کد روشن|کد خاموش|پیش روشن|پیش خاموش|بلاک|پیوی ۱|پیوی ۲|پیوی ۳|خاموش پیوی|گروه ۱|گروه ۲|گروه ۳|خاموش گروه|وضعیت ۱|وضعیت ۲|درباره|من کی ام|اهنگ روشن|اهنگ خاموش|قفل پیوی همه|باز پی همه|قفل لینک روشن|قفل لینک خاموش|قفل عکس روشن|قفل عکس خاموش|قفل ویدیو روشن|قفل ویدیو خاموش|قفل استیکر روشن|قفل استیکر خاموش|قفل گیف روشن|قفل گیف خاموش|قفل ایموجی روشن|قفل ایموجی خاموش|قفل ایموجی پرمیوم روشن|قفل ایموجی پرمیوم خاموش|تنظیم گزارش|گروه گزارش|دشمن گروه|دوست گروه|کانال‌ها|حذف کانال|تست کانال|لیست دشمن|پاک کردن اسپم|لیست اسپم|تغییر اسم|تغییر بیو|تغییر پروفایل|پروف|اضافه اسپم|اتمام اسپم|فیلتر|فیلتر روشن|فیلتر خاموش|اسپم روشن|اسپم خاموش|پینگ|سرچ|خروج سرچ)(?:\s*$|\s+(.+)$)|^حذف\s+(\d+)$|^دشمن\s*(@\w+|-\d+|\d+)?$|^دوست\s*(@\w+|-\d+|\d+)?$|^قفل پیوی\s*(@\w+|-\d+|\d+)?$|^باز پی\s*(@\w+|-\d+|\d+)?$|^اسپم\s+(\d+)\s+(.+)$|^ریکت\s*([\U0001F300-\U0001F9FF]+)?$|^حذف ریکت$|^کامنت\s+(.+)$|^حذف اسپم\s+(\d+)$'))
        async def handle_commands(event):
            await self.handle_commands(event)
        
        @self.client.on(events.NewMessage(outgoing=True))
        async def handle_outgoing_message(event):
            await self.handle_outgoing_message(event)
        
        @self.client.on(events.NewMessage(outgoing=True))
        async def handle_action_commands(event):
            await self.handle_action_commands(event)
    
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
    
    def show_help(self):
        return """
🎮 **دستورات اصلی:**
• اکشن [نام] - فعال کردن اکشن
• اکشن خاموش - خاموش کردن اکشن
• اکشن لیست - نمایش اکشن‌ها

🌍 **مکان:**
• همه جا - بات در همه جا
• فقط اینجا - بات فقط اینجا
• خاموش - خاموش کردن بات

🎲 **بازی‌های تاس (چیت):**
• تاس [عدد 1-6] - دریافت امتیاز خاص در تاس 🎲
• دارت - دریافت امتیاز 6 در دارت 🎯
• بسکتبال - دریافت امتیاز 5 در بسکتبال 🏀
• فوتبال - دریافت امتیاز 5 در فوتبال ⚽️

🌐 **ترجمه خودکار:**
• انگلیسی روشن/خاموش
• عربی روشن/خاموش
• عبری روشن/خاموش
• روسی روشن/خاموش
• ترکی روشن/خاموش

🔍 **سرچ گوگل:**
• سرچ [موضوع] - جستجو در گوگل
• خروج سرچ - خروج از حالت سرچ

📊 **دیگر:**
• وضعیت ۱ - نمایش وضعیت کلی
• وضعیت ۲ - نمایش وضعیت کامل
• تست - تست بات
• راهنما - این راهنما
"""
    
    async def send_help_message(self, event, command_type):
        try:
            settings = db.get_selfbot_settings(self.user_id)
            status_info = self.format_status_info(settings)
            
            help_text = self.get_help_text_1(status_info) if command_type == 'راهنما ۱' else (
                self.get_help_text_2(status_info) if command_type == 'راهنما ۲' else self.get_help_text_3(status_info)
            )
            await event.edit(help_text)
        except Exception as e:
            logger.error(f"خطا در نمایش راهنما: {e}")
    
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
        
        return f"""
📊 **وضعیت فعلی:**

↪️ حالت اتوسین: {'✅ فعال' if settings.get('autosend_mode') else '❌ غیرفعال'}
↪️ استایل متن: {settings.get('text_style') or '❌ غیرفعال'}
↪️ قفل پیوی همگانی: {'✅ فعال' if settings.get('pv_lock_all') else '❌ غیرفعال'}
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
    
    def get_help_text_1(self, status_info):
        return f"""
📊 **وضعیت فعلی:**
{status_info}

📋 **دسته‌بندی دستورات:**

### 1️⃣ دستورات عمومی:
├── 📌 `لیست` یا `راهنما ۱` - نمایش این راهنما
├── 🚀 `شروع` - شروع سلف‌بات
├── 📊 `وضعیت ۱` - نمایش وضعیت کلی
├── 📊 `وضعیت ۲` - نمایش وضعیت کامل
├── ℹ️ `درباره` - اطلاعات درباره بات
└── ⏱️ `پینگ` - نمایش پینگ بات

### 2️⃣ دستورات زمان و پروفایل:
├── 🕐 `تایم روشن` - نمایش ساعت در نام پروفایل
├── 🏳️ `تایمر پرچم روشن` - نمایش ساعت + پرچم متحرک
├── 🚫 `تایم خاموش` - غیرفعال کردن ساعت
└── 📅 `تاریخ کامل` - نمایش تاریخ شمسی، میلادی و قمری

### 3️⃣ دستورات انیمیشن:
├── ❤️ `قلب` - انیمیشن قلب‌های متحرک
└── 🌙 `ماه` - انیمیشن فازهای ماه

📎 برای ادامه راهنما `راهنما ۲` را ارسال کنید.
"""
    
    def get_help_text_2(self, status_info):
        return f"""
📊 **وضعیت فعلی:**
{status_info}

### 4️⃣ دستورات مدیریت کاربران:
├── 🥷 `دشمن` - افزودن کاربر به لیست دشمنان (ریپلای)
├── 🧸 `دوست` - حذف کاربر از لیست دشمنان (ریپلای)
├── 🥷 `دشمن گروه` - افزودن کاربر به دشمنان گروه (ریپلای)
├── 🧸 `دوست گروه` - حذف کاربر از دشمنان گروه (ریپلای)
├── 🔒 `قفل پیوی` - قفل پی‌وی کاربر (ریپلای)
├── 🔓 `باز پی` - بازکردن قفل پی‌وی (ریپلای)
├── 🔒 `قفل پیوی همه` - قفل پیوی همگانی
├── 🔓 `باز پی همه` - بازکردن قفل پیوی همگانی
└── ⛔ `بلاک` - بلاک سریع کاربر (فقط در پی‌وی)

### 5️⃣ دستورات قفل رسانه:
├── 🔗 `قفل لینک روشن` / `قفل لینک خاموش` (ریپلای)
├── 📸 `قفل عکس روشن` / `قفل عکس خاموش` (ریپلای)
├── 🎥 `قفل ویدیو روشن` / `قفل ویدیو خاموش` (ریپلای)
├── 🎨 `قفل استیکر روشن` / `قفل استیکر خاموش` (ریپلای)
├── 🎞️ `قفل گیف روشن` / `قفل گیف خاموش` (ریپلای)
├── 😀 `قفل ایموجی روشن` / `قفل ایموجی خاموش` (ریپلای)
└── 💎 `قفل ایموجی پرمیوم روشن` / `قفل ایموجی پرمیوم خاموش` (ریپلای)

### 6️⃣ دستورات نظر‌دهی اتوماتیک:
├── 💬 `کامنت [متن]` - ذخیره متن نظر در کانال/گروه
├── 📊 `کانال‌ها` - نمایش کانال‌های تنظیم شده
├── 🗑️ `حذف کانال` - حذف تنظیمات کانال فعلی
└── 🔍 `تست کانال` - بررسی تشخیص کانال (ریپلای)

📎 برای ادامه راهنما `راهنما ۳` را ارسال کنید.
"""
    
    def get_help_text_3(self, status_info):
        return f"""
📊 **وضعیت فعلی:**
{status_info}

### 7️⃣ دستورات اطلاعاتی:
├── 📋 `اطلاعات` - اطلاعات کامل کاربر (ریپلای)
└── ⬇️ `دانلود پروفایل` - دانلود عکس پروفایل (ریپلای)

### 8️⃣ دستورات کپی پروفایل:
├── 📸 `ست پروف` - کپی عکس پروفایل (ریپلای)
├── ✏️ `ست بیو` - کپی بیو کاربر (ریپلای)
├── 🗑️ `حذف ست پروف` - حذف عکس پروفایل خودتان
└── 🗑️ `حذف ست بیو` - پاک کردن بیو خودتان

### 9️⃣ دستورات استایل متن:
├── **`بولد روشن`** / **`بولد خاموش`**
├── __`زیرخط روشن`__ / __`زیرخط خاموش`__
├── ~~`خط خورده روشن`~~ / ~~`خط خورده خاموش`~~
├── 📝 `نقل قول روشن` / `نقل قول خاموش`
├── 🎭 `اسپویلر روشن` / `اسپویلر خاموش`
├── *`کج روشن`* / *`کج خاموش`*
├── `کد روشن` / `کد خاموش`
└── `پیش روشن` / `پیش خاموش`

### 🔟 دستورات مدیریت پیام:
├── 🧹 `حذف کامل` - حذف همه پیام‌های چت
├── 🧹 `حذف کامل 50` - حذف 50 پیام آخر
├── 🗑️ `حذف 10` - حذف 10 پیام خودتان
├── 👁️ `فعال اتوسین` - فعال کردن سین خودکار
└── 🙈 `غیرفعال اتوسین` - غیرفعال کردن سین خودکار

### 1️⃣1️⃣ دستورات ریکشن:
├── 👍 `ریکت ❤️` - تنظیم ریکشن خودکار (ریپلای + ایموجی)
└── ❌ `حذف ریکت` - حذف ریکشن خودکار (ریپلای)

### 1️⃣2️⃣ دستورات اسپم:
├── 📩 `اسپم 10 سلام` - ارسال 10 بار "سلام"
└── 📩 `اسپم 5 متن` - ارسال 5 بار "متن" (ریپلای)

### 1️⃣3️⃣ دستورات تغییر پروفایل:
├── ✏️ `تغییر اسم [نام جدید]` - تغییر نام پروفایل
├── ✏️ `تغییر بیو [متن جدید]` - تغییر بیوگرافی
├── 📸 `تغییر پروفایل` - تغییر عکس پروفایل (ریپلای روی عکس)
├── 📸 `پروف` - تغییر عکس پروفایل (ریپلای روی عکس)

### 1️⃣4️⃣ دستورات مدیریت دشمنان:
├── 📋 `لیست دشمن` - نمایش لیست دشمنان
├── 📝 `اضافه اسپم` - شروع اضافه کردن پیام اسپم
├── ✅ `اتمام اسپم` - پایان اضافه کردن پیام اسپم
├── 📜 `لیست اسپم` - نمایش لیست پیام‌های اسپم
├── 🗑️ `پاک کردن اسپم` - پاک کردن لیست پیام‌های اسپم
└── 🗑️ `حذف اسپم [شماره]` - حذف پیام اسپم خاص

### 1️⃣5️⃣ دستورات فیلتر کلمات:
├── 🚫 `فیلتر [کلمه]` - افزودن کلمه به لیست فیلتر
├── ✅ `فیلتر روشن` - فعال کردن همه فیلترها
├── ❌ `فیلتر خاموش` - غیرفعال کردن همه فیلترها
├── 📜 `لیست فیلتر` - نمایش لیست کلمات فیلتر شده
└── 🗑️ `حذف فیلتر [کلمه]` - حذف کلمه از لیست فیلتر

### 1️⃣6️⃣ دستورات حفاظت اسپم:
├── 🛡️ `اسپم روشن` - فعال کردن حفاظت اسپم
├── 🛡️ `اسپم خاموش` - غیرفعال کردن حفاظت اسپم
├── ⚙️ `تنظیم اسپم [تعداد] [زمان]` - تنظیم محدودیت اسپم
└── 📊 `وضعیت اسپم` - نمایش تنظیمات حفاظت اسپم

### 1️⃣7️⃣ دستورات هوش مصنوعی:
├── 🟢 `پیوی ۱` - هوش ۱ در پی‌وی (ChatGPT)
├── 🔵 `پیوی ۲` - هوش ۲ در پی‌وی (Paxsenix)
├── 🟣 `پیوی ۳` - هوش ۳ در پی‌وی (DeepSeek)
├── ⚫ `خاموش پیوی` - خاموش کردن هوش پی‌وی
├── 🟢 `گروه ۱` - هوش ۱ در گروه (با ریپلای)
├── 🔵 `گروه ۲` - هوش ۲ در گروه (با ریپلای)
├── 🟣 `گروه ۳` - هوش ۳ در گروه (با ریپلای)
└── ⚫ `خاموش گروه` - خاموش کردن هوش گروه

### 1️⃣8️⃣ دستورات موزیک:
├── 🎶 `اهنگ روشن` - فعال کردن دستور آهنگ
├── 🔇 `اهنگ خاموش` - غیرفعال کردن دستور آهنگ
└── 🔊 `آهنگ [نام]` - جستجو و دانلود آهنگ

### 1️⃣9️⃣ دستورات گروه گزارش:
├── 📍 `تنظیم گزارش` - تنظیم گروه فعلی بعنوان گروه گزارش
└── ℹ️ `گروه گزارش` - نمایش آیدی گروه گزارش فعلی

📝 **نحوه اجرا:**
• 🎯 دستورات عمومی: مستقیم تایپ کنید
• 🔄 دستورات با [ریپلای]: روی پیام کاربر ریپلای کنید + دستور
• 😊 دستورات با ایموجی: دستور + ایموجی (مثال: `ریکت ❤️`)
• 💬 نظر‌دهی: در کانال بنویسید `کامنت سلام`
• 🎲 بازی تاس: در هر چت قابل استفاده است
• 🌐 ترجمه: با فعال کردن هر زبان، پیام‌های شما به آن زبان ترجمه می‌شوند
• 🔍 سرچ: با فعال کردن حالت سرچ، هر متنی ارسال کنید جستجو می‌شود

⚠️ **هشدار:** استفاده از این بات ممکن است منجر به محدودیت اکانت شود!
"""
    
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
        
        elif msg == 'راهنما':
            await event.edit(self.show_help())
            return
        
        elif msg == 'تست':
            current_action = self.active_actions.get(chat_id, "هیچ")
            
            active_langs = []
            lang_names = {
                "english": "انگلیسی",
                "arabic": "عربی",
                "hebrew": "عبری",
                "russian": "روسی",
                "turkish": "ترکی"
            }
            for lang_key, lang_name in lang_names.items():
                if self.translate_mode.get(lang_key):
                    active_langs.append(lang_name)
            
            langs_status = ", ".join(active_langs) if active_langs else "هیچ"
            
            await event.edit(
                f"✅ سلف بات فعال است!\n"
                f"📍 حالت: {'همه جا' if self.mode == 'all' else 'فقط اینجا' if self.mode == 'pv' else 'خاموش'}\n"
                f"🎭 اکشن این چت: **{current_action}**\n"
                f"🌐 ترجمه فعال: **{langs_status}**\n"
                f"🎲 بازی تاس: ✅ فعال\n"
                f"🔍 حالت سرچ: {'✅ فعال' if self.search_mode else '❌ غیرفعال'}\n"
                f"🕐 زمان: {datetime.now().strftime('%H:%M:%S')}"
            )
            return
        
        elif msg == 'وضعیت ۱':
            active_list = ""
            if self.active_actions:
                active_list = "\n🎭 **اکشن‌های فعال:**\n"
                for cid, action in self.active_actions.items():
                    try:
                        chat_obj = await self.client.get_entity(cid)
                        chat_name = chat_obj.first_name if hasattr(chat_obj, 'first_name') else chat_obj.title
                        active_list += f"• **{chat_name}**: {action}\n"
                    except:
                        active_list += f"• چت {cid}: {action}\n"
            
            active_langs = []
            lang_names = {
                "english": "انگلیسی",
                "arabic": "عربی",
                "hebrew": "عبری",
                "russian": "روسی",
                "turkish": "ترکی"
            }
            for lang_key, lang_name in lang_names.items():
                if self.translate_mode.get(lang_key):
                    active_langs.append(lang_name)
            
            langs_list = ", ".join(active_langs) if active_langs else "هیچ"
            
            status_msg = f"""
📊 **وضعیت ۱ - کلی:**
━━━━━━━━━━━━━━━━━━━━
📍 **مکان:** {'همه جا' if self.mode == 'all' else 'فقط اینجا' if self.mode == 'pv' else 'خاموش'}
🌐 **ترجمه فعال:** {langs_list}
🎲 **بازی تاس:** ✅ فعال
🔍 **حالت سرچ:** {'✅ فعال' if self.search_mode else '❌ غیرفعال'}
💾 **حافظه:** فعال
🕐 **زمان:** {datetime.now().strftime("%H:%M:%S")}
{active_list}
━━━━━━━━━━━━━━━━━━━━
✅ **سلف بات فعال**
            """
            await event.edit(status_msg)
            return
        
        elif msg == 'وضعیت ۲':
            settings = db.get_selfbot_settings(self.user_id)
            
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
            
            pv_enemies = len(db.get_enemies(self.user_id, 'pv'))
            
            cached_media = len([m for m in media_cache.values() if m.get('owner_id') == self.user_id])
            
            spam_settings = db.get_spam_settings(self.user_id)
            
            filter_words = db.get_filter_words(self.user_id)
            active_filters = len([w for w in filter_words if w['enabled']])
            
            spam_messages = len(db.get_enemy_spam_messages(self.user_id))
            
            status_msg = f"""
📊 **وضعیت ۲ - کامل:**
━━━━━━━━━━━━━━━━━━━━
🤖 **هوش مصنوعی:**
• پی‌وی: {active_ai_pm}
• گروه: {active_ai_group}

🎵 **دستور آهنگ:** {'✅ فعال' if settings.get('song_command_status') else '❌ غیرفعال'}

🔒 **تنظیمات قفل:**
• قفل پیوی همگانی: {'✅ فعال' if settings.get('pv_lock_all') else '❌ غیرفعال'}
• دشمنان پیوی: {pv_enemies}
• پی‌وی‌های قفل‌شده: {len(db.get_locked_pvs(self.user_id))}

📊 **گزارش‌گیری:**
• گروه گزارش: {self.report_config.report_group_id}
• رسانه‌های ذخیره‌شده: {cached_media}
• ذخیره خودکار: {'✅ فعال' if self.report_config.auto_save_media else '❌ غیرفعال'}

🛡️ **حفاظت‌ها:**
• حفاظت اسپم: {'✅ فعال' if spam_settings.get('spam_protection') else '❌ غیرفعال'}
• کلمات فیلتر فعال: {active_filters}
• پیام‌های اسپم ذخیره شده: {spam_messages}

📅 **آخرین به‌روزرسانی:** {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
✅ **Self-Bot v{BOT_VERSION}**
            """
            await event.edit(status_msg)
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
                    
                    message += "📌 برای دانلود موسیقی، نام آهنگ را وارد کنید."
                    
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
                    music_url = await self.search_and_download_music(query, event.chat_id)
                    if music_url:
                        await event.edit(f'🎵 **آهنگ پیدا شد!**\n\nدر حال دانلود...')
                    else:
                        await event.edit(f'❌ **هیچ نتیجه‌ای برای "{query}" پیدا نشد.**')
            else:
                await event.edit(f'❌ **خطا در جستجو.** کد خطا: {response.status_code}')
                
        except Exception as e:
            logger.error(f"خطا در جستجوی گوگل: {e}")
            await event.edit(f'❌ **خطا در جستجو:** {str(e)}')
    
    async def search_and_download_music(self, song_name, chat_id):
        try:
            params = {
                'key': GOOGLE_SEARCH_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': f'"{song_name}" filetype:mp3 OR "{song_name}" دانلود موسیقی',
                'num': 3,
                'safe': 'active'
            }
            
            response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                
                if 'items' in results and len(results['items']) > 0:
                    for item in results['items']:
                        link = item.get('link', '')
                        
                        if link.lower().endswith('.mp3'):
                            return await self.download_and_send_music(link, song_name, chat_id)
                        
                        mp3_link = self.extract_mp3_from_page(link)
                        if mp3_link:
                            return await self.download_and_send_music(mp3_link, song_name, chat_id)
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در جستجوی موسیقی: {e}")
            return None
    
    def extract_mp3_from_page(self, page_url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(page_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                mp3_patterns = [
                    r'href="([^"]+\.mp3[^"]*)"',
                    r'src="([^"]+\.mp3[^"]*)"',
                    r'data-url="([^"]+\.mp3[^"]*)"',
                    r'download="([^"]+\.mp3[^"]*)"',
                    r'data-src="([^"]+\.mp3[^"]*)"'
                ]
                
                for pattern in mp3_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('http'):
                            return match
                        elif match.startswith('/'):
                            from urllib.parse import urljoin
                            return urljoin(page_url, match)
            
            return None
        except:
            return None
    
    async def download_and_send_music(self, mp3_url, song_name, chat_id):
        try:
            os.makedirs('downloads', exist_ok=True)
            safe_name = re.sub(r'[^\w\s\-]', '', song_name)
            safe_name = re.sub(r'\s+', '_', safe_name.strip())
            filename = f'downloads/{safe_name[:40]}_{self.user_id}.mp3'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(mp3_url, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(filename)
                if file_size > 0:
                    await self.client.send_file(
                        chat_id,
                        filename,
                        caption=f'🎵 **{song_name}**\n📥 دانلود شده با گوگل سرچ',
                        voice_note=True
                    )
                    
                    if os.path.exists(filename):
                        os.remove(filename)
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"خطا در دانلود موسیقی: {e}")
            if 'filename' in locals() and os.path.exists(filename):
                os.remove(filename)
            return False
    
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
    
    async def handle_new_message(self, event):
        if not self.my_id:
            return
        
        settings = db.get_selfbot_settings(self.user_id)
        spam_settings = db.get_spam_settings(self.user_id)
        
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
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out and event.message.text:
            db.cache_message(self.user_id, chat_id, event.message.id, event.message.text)
        
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            
            sender_info = f"کاربر {sender_id}"
            try:
                sender = await event.get_sender()
                if sender:
                    username = sender.username if sender.username else None
                    first_name = sender.first_name if sender.first_name else ""
                    last_name = sender.last_name if sender.last_name else ""
                    db.update_user_memory(sender_id, username, first_name, last_name, chat_id)
                    
                    if event.message.text:
                        extracted_name = extract_name_from_message(event.message.text)
                        if extracted_name:
                            db.update_user_memory(sender_id, username, first_name, last_name, chat_id, extracted_name)
            except:
                pass
            
            if event.message.text:
                filter_words = db.get_filter_words(self.user_id)
                for word_info in filter_words:
                    if word_info['enabled'] and word_info['word'].lower() in event.message.text.lower():
                        try:
                            await event.message.delete()
                            
                            report_group = self.report_config.report_group_id
                            if report_group:
                                await self.send_report(
                                    f"⚠️ پیام حاوی کلمه فیلتر شده '{word_info['word']}' از {sender_info} حذف شد."
                                )
                            
                            return
                        except:
                            pass
            
            if spam_settings.get('spam_protection'):
                if sender_id not in self.spam_counters:
                    self.spam_counters[sender_id] = {
                        'count': 1,
                        'last_message_time': time.time()
                    }
                else:
                    current_time = time.time()
                    time_diff = current_time - self.spam_counters[sender_id]['last_message_time']
                    
                    if time_diff < 5:
                        self.spam_counters[sender_id]['count'] += 1
                        self.spam_counters[sender_id]['last_message_time'] = current_time
                        
                        if self.spam_counters[sender_id]['count'] >= spam_settings.get('spam_limit', 10):
                            try:
                                await event.message.delete()
                                
                                mute_duration = spam_settings.get('mute_duration', 10)
                                for _ in range(mute_duration):
                                    if event.message.text:
                                        try:
                                            await self.client.send_message(chat_id, "سکوت...")
                                            await asyncio.sleep(1)
                                        except:
                                            pass
                                
                                self.spam_counters[sender_id] = {
                                    'count': 0,
                                    'last_message_time': current_time + mute_duration
                                }
                                
                                return
                            except:
                                pass
                    else:
                        self.spam_counters[sender_id] = {
                            'count': 1,
                            'last_message_time': current_time
                        }
            
            if settings.get('pv_lock_all') and sender_id != self.my_id:
                try:
                    await event.message.delete()
                    return
                except:
                    pass
            
            if db.is_pv_locked(self.user_id, sender_id):
                try:
                    await event.message.delete()
                    return
                except:
                    pass
            
            if not db.is_pv_locked(self.user_id, sender_id) and not settings.get('pv_lock_all'):
                should_delete = False
                delete_reason = ""
                
                media_locks = db.get_media_locks(self.user_id, sender_id)
                
                if event.message.text:
                    text = event.message.text
                    
                    if media_locks.get('lock_link') and is_link_message(text):
                        should_delete = True
                        delete_reason = "لینک"
                    
                    if media_locks.get('lock_emoji') and is_emoji_message(text):
                        should_delete = True
                        delete_reason = "ایموجی معمولی"
                
                if media_locks.get('lock_emoji_premium') and await is_premium_emoji(event.message):
                    should_delete = True
                    delete_reason = "ایموجی پرمیوم"
                
                if media_locks.get('lock_photo') and isinstance(event.message.media, MessageMediaPhoto):
                    should_delete = True
                    delete_reason = "عکس"
                
                if media_locks.get('lock_video') and isinstance(event.message.media, MessageMediaDocument):
                    document = event.message.media.document
                    if hasattr(document, 'mime_type') and 'video' in document.mime_type:
                        should_delete = True
                        delete_reason = "ویدیو"
                
                if media_locks.get('lock_sticker') and event.message.sticker:
                    should_delete = True
                    delete_reason = "استیکر"
                
                if media_locks.get('lock_gif') and event.message.gif:
                    should_delete = True
                    delete_reason = "گیف"
                
                if should_delete:
                    try:
                        await event.message.delete()
                        
                        report_group = self.report_config.report_group_id
                        if report_group:
                            await self.send_report(
                                f"⚠️ پیام {delete_reason} از {sender_info} حذف شد."
                            )
                        
                        return
                    except:
                        pass
            
            if db.is_enemy(self.user_id, sender_id, 'pv'):
                try:
                    await event.message.delete()
                    await self.spam_enemy(sender_id)
                    return
                except:
                    pass
            
            if event.message.text and is_song_request(event.message.text) and settings.get('song_command_status', 1):
                await self.handle_song_request(event, sender_id)
                return
            
            if event.message.text:
                ai_type = None
                ai_status = settings.get('ai_status', {})
                if ai_status.get('ai_1_pm'):
                    ai_type = 1
                elif ai_status.get('ai_2_pm'):
                    ai_type = 2
                elif ai_status.get('ai_3_pm'):
                    ai_type = 3
                
                if ai_type:
                    try:
                        response = await get_ai_response(event.message.text, ai_type, sender_id)
                        
                        if response and len(response) > 0:
                            if len(response) > 4000:
                                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                                for i, chunk in enumerate(chunks):
                                    if i == 0:
                                        await event.reply(chunk)
                                    else:
                                        await event.respond(chunk)
                            else:
                                await event.reply(response)
                    except Exception as e:
                        logger.error(f"خطا در پاسخ هوش مصنوعی: {e}")
        
        elif isinstance(event.message.peer_id, (PeerChannel, PeerChat)) and not event.message.out:
            sender_id = event.sender_id
            group_id = chat_id
            
            if db.is_enemy(self.user_id, sender_id, 'group', group_id):
                await self.spam_in_group(group_id, sender_id)
            
            if event.message.text and event.is_reply:
                try:
                    replied_msg = await event.get_reply_message()
                    if replied_msg.sender_id == self.my_id:
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
                        
                        ai_type = None
                        ai_status = settings.get('ai_status', {})
                        if ai_status.get('ai_1_group'):
                            ai_type = 1
                        elif ai_status.get('ai_2_group'):
                            ai_type = 2
                        elif ai_status.get('ai_3_group'):
                            ai_type = 3
                        
                        if ai_type:
                            try:
                                response = await get_ai_response(event.message.text, ai_type, sender_id)
                                
                                if response and len(response) > 0:
                                    if len(response) > 4000:
                                        chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                                        for i, chunk in enumerate(chunks):
                                            if i == 0:
                                                await event.reply(chunk)
                                            else:
                                                await event.respond(chunk)
                                    else:
                                        await event.reply(response)
                                        
                            except Exception as e:
                                logger.error(f"Error responding to group message: {e}")
                except Exception as e:
                    logger.error(f"Error processing group reply: {e}")
        
        if not event.message.out and event.sender_id:
            sender_id = event.sender_id
            reaction = db.get_reaction(self.user_id, chat_id, sender_id)
            if reaction and reaction in ALLOWED_EMOJIS:
                try:
                    await self.client(SendReactionRequest(
                        peer=event.message.peer_id,
                        msg_id=event.message.id,
                        reaction=[ReactionEmoji(emoticon=reaction)]
                    ))
                except:
                    pass
        
        if settings.get('autosend_mode') and isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            try:
                await event.message.mark_read()
            except:
                pass
        
        await self.handle_auto_comment(event)
        
        await self.handle_report_message(event)
    
    async def handle_report_message(self, event):
        try:
            if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
                if event.message.text:
                    chat_id = event.message.peer_id.user_id
                    message_cache[(chat_id, event.message.id)] = event.message.text
                    logger.info(f"پیام متنی از {chat_id} ذخیره شد")
                
                if event.message.media:
                    media_type = self.get_media_type(event.message)
                    
                    if media_type:
                        logger.info(f"رسانه جدید دریافت شد: {media_type} از {event.sender_id}")
                        
                        saved_path = await self.save_media(event.message, media_type)
                        
                        if self.report_config.report_ttl_media and hasattr(event.message.media, 'ttl_seconds') and event.message.media.ttl_seconds:
                            sender_info = await self.get_user_info(event.sender_id)
                            
                            if saved_path:
                                await self.send_report(
                                    f"⏰ **رسانه نابودشونده دریافت شد**\n"
                                    f"👤 از: {sender_info}\n"
                                    f"📦 نوع: {media_type}\n"
                                    f"⏱️ زمان باقی‌مانده: {event.message.media.ttl_seconds} ثانیه\n"
                                    f"💾 ذخیره شده: ✅",
                                    saved_path,
                                    f"⏰ {media_type} نابودشونده از {sender_info}"
                                )
                            else:
                                await self.send_report(
                                    f"⏰ **رسانه نابودشونده دریافت شد**\n"
                                    f"👤 از: {sender_info}\n"
                                    f"📦 نوع: {media_type}\n"
                                    f"⏱️ زمان باقی‌مانده: {event.message.media.ttl_seconds} ثانیه\n"
                                    f"💾 ذخیره شده: ❌"
                                )
                        
                        elif hasattr(event.message.media, 'noforwards') and event.message.media.noforwards:
                            sender_info = await self.get_user_info(event.sender_id)
                            
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
                        
                        else:
                            logger.info(f"رسانه {media_type} از {event.sender_id} دریافت شد")
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
                    
                    logger.info(f"پیام ویرایش‌شده از {sender.id} گزارش شد.")
                    
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
                    
                    logger.info(f"رسانه حذف‌شده از {media_info['user_id']} گزارش شد.")
                    
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
                        
                        logger.info(f"پیام متنی حذف‌شده از {chat_id} گزارش شد.")
                        
                        del message_cache[(chat_id, msg_id)]
                        
                    except Exception as e:
                        logger.error(f"خطا در گزارش حذف پیام: {e}")
                        if (chat_id, msg_id) in message_cache:
                            del message_cache[(chat_id, msg_id)]
    
    async def handle_auto_comment(self, event):
        try:
            message = event.message
            
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
    
    async def handle_commands(self, event):
        if event.sender_id != self.my_id:
            return
        
        command_text = event.text.lower()
        chat_id = None
        
        if isinstance(event.message.peer_id, PeerUser):
            chat_id = event.message.peer_id.user_id
        elif isinstance(event.message.peer_id, PeerChannel):
            chat_id = event.message.peer_id.channel_id
        elif isinstance(event.message.peer_id, PeerChat):
            chat_id = event.message.peer_id.chat_id
        
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
        
        elif command_text in ['وضعیت ۱', 'وضعیت ۲']:
            await self.handle_status_command(event)
        
        elif command_text == 'درباره':
            await event.delete()
        
        elif command_text == 'من کی ام':
            await self.handle_whoami_command(event)
        
        elif command_text == "اهنگ روشن":
            await self.handle_song_command(event, True)
        
        elif command_text == "اهنگ خاموش":
            await self.handle_song_command(event, False)
        
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
                    
                    if event.is_reply:
                        reply_message = await event.get_reply_message()
                        if reply_message.sender_id == target_id:
                            await self.client(SendReactionRequest(
                                peer=event.message.peer_id,
                                msg_id=reply_message.id,
                                reaction=[ReactionEmoji(emoticon=emoji)]
                            ))
                    
                    await event.edit(f"✅ ریکت خودکار {emoji} برای کاربر {target_id} تنظیم شد.")
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
    
    async def handle_status_command(self, event):
        try:
            if event.text.lower() == 'وضعیت ۱':
                await self.handle_action_commands(event)
            elif event.text.lower() == 'وضعیت ۲':
                await self.handle_action_commands(event)
        except Exception as e:
            logger.error(f"خطا در نمایش وضعیت: {e}")
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
    
    async def handle_song_command(self, event, enable):
        try:
            db.update_selfbot_setting(self.user_id, 'song_command_status', 1 if enable else 0)
            
            if enable:
                await event.edit('✅ **دستور آهنگ روشن شد**\n\nاکنون هر کاربری می‌تواند آهنگ درخواست کند.\nمثال: "آهنگ مهدیار" یا "لطفا آهنگ شادمهر بفرست"')
            else:
                await event.edit('✅ **دستور آهنگ خاموش شد**\n\nاکنون درخواست‌های آهنگ نادیده گرفته می‌شوند.')
        except Exception as e:
            logger.error(f"خطا در دستور آهنگ: {e}")
            try:
                await event.delete()
            except:
                pass
    
    async def handle_media_lock_command(self, event, enable):
        try:
            command_text = event.text.lower()
            
            if not event.is_reply:
                await event.edit("⚠️ روی پیام کاربر ریپلای کنید.")
                return
            
            reply_message = await event.get_reply_message()
            target_id = reply_message.sender_id
            
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
                await event.edit(f"✅ قفل {lock_names[lock_type]} برای کاربر {status} شد")
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
    
    async def handle_song_request(self, event, sender_id):
        song_name = extract_song_name(event.text)
        
        if not song_name or len(song_name) < 2:
            await event.reply('❌ **لطفاً نام کامل آهنگ را وارد کنید.**')
            return
        
        search_msg = await event.reply(f'🔍 **در حال جستجوی آهنگ:** {song_name}')
        
        song_url = await self.search_and_download_music(song_name, event.chat_id)
        
        if song_url:
            await search_msg.edit(f'✅ **آهنگ پیدا شد و ارسال شد!**')
            await asyncio.sleep(2)
            await search_msg.delete()
        else:
            await search_msg.edit(f'❌ **آهنگ "{song_name}" یافت نشد**')
    
    async def handle_outgoing_message(self, event):
        message_text = event.text or ""
        
        if self.adding_spam and message_text and not message_text.startswith(('لیست', 'راهنما', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'وضعیت', 'درباره', 'من کی ام', 'اهنگ', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'فیلتر', 'فیلتر روشن', 'فیلتر خاموش', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ')):
            db.add_enemy_spam_message(self.user_id, message_text)
            try:
                await event.delete()
            except:
                pass
            return
        
        if is_song_request(message_text) and event.out:
            await self.handle_song_request(event, self.my_id)
            return
        
        if event.text:
            settings = db.get_selfbot_settings(self.user_id)
            text_style = settings.get('text_style')
            
            if text_style and not message_text.startswith(('/','لیست','راهنما','شروع','تایم','قلب','ماه','اطلاعات','دانلود','تاریخ','فعال','غیرفعال','حذف','ست','بولد','زیرخط','خط خورده','نقل قول','اسپویلر','کج','کد','پیش','اسپم','بلاک','ریکت','پیوی','گروه','وضعیت','درباره','من کی ام','اهنگ','قفل','باز','تنظیم','گروه گزارش','دشمن','دوست','کانال','کامنت','تست','لیست دشمن','لیست اسپم','پاک کردن اسپم','حذف اسپم','اضافه اسپم','اتمام اسپم','تغییر اسم','تغییر بیو','تغییر پروفایل','پروف','فیلتر','فیلتر روشن','فیلتر خاموش','اسپم روشن','اسپم خاموش','پینگ','سرچ','خروج سرچ')):
                try:
                    text, entities = await apply_text_style(message_text, text_style)
                    if entities:
                        await event.message.edit(text, formatting_entities=entities)
                except:
                    pass
        
        if self.search_mode and message_text and not message_text.startswith(('لیست', 'راهنما', 'شروع', 'تایم', 'قلب', 'ماه', 'اطلاعات', 'دانلود', 'تاریخ', 'فعال', 'غیرفعال', 'حذف', 'ست', 'بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش', 'اسپم', 'بلاک', 'ریکت', 'پیوی', 'گروه', 'وضعیت', 'درباره', 'من کی ام', 'اهنگ', 'قفل', 'باز', 'تنظیم', 'گروه گزارش', 'دشمن', 'دوست', 'کانال', 'کامنت', 'تست', 'لیست دشمن', 'لیست اسپم', 'پاک کردن اسپم', 'حذف اسپم', 'اضافه اسپم', 'اتمام اسپم', 'تغییر اسم', 'تغییر بیو', 'تغییر پروفایل', 'پروف', 'فیلتر', 'فیلتر روشن', 'فیلتر خاموش', 'اسپم روشن', 'اسپم خاموش', 'پینگ', 'سرچ', 'خروج سرچ')):
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
            time_now = now.strftime("%H:%M")
            font_index = current_minute % len(classic_fonts)
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
            await asyncio.sleep(10)
    
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

# ========== دیکشنری سلف‌بات‌ها ==========
selfbot_managers = {}

# ========== توابع پنل اینلاین و کلید‌ها (به دلیل طولانی شدن کد، خلاصه شده) ==========
# (بقیه کیبوردها و هندلرهای اینلاین مشابه قبل هستند)

# ========== راه‌اندازی اصلی ==========
async def main():
    print("=" * 60)
    print("🤖 سیستم جامع عضویت و سلف‌بات")
    print(f"👑 ادمین: {ADMIN_ID}")
    print(f"📁 پوشه سشن‌ها: {SESSIONS_FOLDER}")
    print("=" * 60)
    
    # راه‌اندازی سرور Flask برای رندر (رفع مشکل پورت)
    keep_alive()
    print("✅ سرور Flask برای پورت ۱۰۰۰۰ راه‌اندازی شد")
    
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
    for user in active_users:
        user_id_str = user['user_id']
        session_file = user.get('session_file')
        
        if session_file and os.path.exists(session_file):
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_file):
                selfbot_managers[user_id_str] = manager
                print(f"✅ سلف‌بات کاربر {user_id_str} راه‌اندازی شد")
    
    print(f"✅ {len(selfbot_managers)} سلف‌بات فعال شدند")
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

# ========== توابع پنل اینلاین و کیبورد (ادامه) ==========
async def inline_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # این تابع مانند قبل است اما به دلیل طولانی شدن کد خلاصه شده
    pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # این تابع مانند قبل است اما به دلیل طولانی شدن کد خلاصه شده
    pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    user = update.effective_user
    user_id = str(user.id)
    
    full_name = user.full_name or "کاربر"
    username = user.username or ""
    db.add_user(user_id, full_name, username)
    
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
    """
    
    keyboard = [
        [InlineKeyboardButton("📝 عضویت", callback_data=f"membership_request_{user_id}")],
        [InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel_{user.id}")])
    
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
        text="🌟 **پنل مدیریت سلف‌بات**\n\nبرای باز کردن پنل، روی دکمه زیر کلیک کنید:",
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
    
    step = user_data.get('step')
    
    if step == 'get_phone':
        if not user_data.get('admin_approved'):
            await update.message.reply_text("⏳ درخواست شما هنوز تأیید نشده است.")
            return
        
        db.update_user(user_id_str, phone=text, step='get_code')
        
        await update.message.reply_text("⏳ در حال ارسال کد تأیید...")
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            
            if os.path.exists(session_path):
                os.remove(session_path)
            
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            sent_code = await client.send_code_request(text)
            phone_code_hash = sent_code.phone_code_hash
            
            db.update_user(user_id_str, phone_code_hash=phone_code_hash)
            
            await update.message.reply_text("✅ کد تأیید ارسال شد! کد ۵ رقمی را وارد کنید:")
            
            await client.disconnect()
            
        except TelethonFloodWaitError as e:
            await update.message.reply_text(f"⏳ لطفاً {e.seconds} ثانیه صبر کنید")
            db.update_user(user_id_str, step='get_phone')
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            db.update_user(user_id_str, step='get_phone')
    
    elif step == 'get_code':
        db.update_user(user_id_str, code=text)
        
        await update.message.reply_text("⏳ در حال تأیید کد...")
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            user_data = db.get_user(user_id_str)
            
            await client.sign_in(
                phone=user_data['phone'],
                code=text,
                phone_code_hash=user_data['phone_code_hash']
            )
            
            expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            db.update_user(user_id_str,
                          self_active=1,
                          session_file=session_path,
                          expiration_date=expiration_date,
                          step=None)
            
            await update.message.reply_text(f"🎉 عضویت شما کامل شد!\n\n✅ اکانت فعال شد\n⏳ انقضا: {expiration_date}")
            
            await client.disconnect()
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_path):
                selfbot_managers[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات شما فعال شد!\n\nحالا می‌توانید از دستور /panel استفاده کنید.")
            
        except SessionPasswordNeededError:
            db.update_user(user_id_str, step='get_password')
            await update.message.reply_text("🔐 رمز دو مرحله‌ای را وارد کنید:")
        
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            db.update_user(user_id_str, step='get_phone')
    
    elif step == 'get_password':
        db.update_user(user_id_str, password=text)
        
        await update.message.reply_text("⏳ در حال تأیید رمز...")
        
        try:
            session_name = f"user_{user_id_str}"
            session_path = os.path.join(SESSIONS_FOLDER, f"{session_name}.session")
            
            client = TelegramClient(session_path, API_ID, API_HASH)
            await client.connect()
            
            await client.sign_in(password=text)
            
            expiration_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            db.update_user(user_id_str,
                          self_active=1,
                          session_file=session_path,
                          expiration_date=expiration_date,
                          step=None)
            
            await update.message.reply_text(f"🎉 عضویت شما کامل شد!\n\n✅ اکانت فعال شد\n⏳ انقضا: {expiration_date}")
            
            await client.disconnect()
            
            manager = SelfBotManager(user_id_str)
            if await manager.start(session_path):
                selfbot_managers[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات شما فعال شد!\n\nحالا می‌توانید از دستور /panel استفاده کنید.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            db.update_user(user_id_str, step='get_phone')
    
    else:
        if user_data.get('self_active'):
            await update.message.reply_text("✅ اکانت شما فعال است!\n\nبرای استفاده از پنل، دستور /panel را بزنید.")
        else:
            await update.message.reply_text("برای عضویت، روی دکمه /start کلیک کنید.")

if __name__ == '__main__':
    asyncio.run(main())
