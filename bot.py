
import os
import sys
import sqlite3
import logging
import asyncio
import json
import re
import time
import random
import uuid
import secrets
import threading
import hashlib
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from functools import wraps

import pytz
import jdatetime
from hijridate import Gregorian
import aiohttp
from dotenv import load_dotenv

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InlineQueryResultArticle, InputTextMessageContent,
    InlineQueryResultPhoto, InlineQueryResultGif, InlineQueryResultVideo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, InlineQueryHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler
)
from telegram.request import HTTPXRequest
from telegram.constants import ParseMode

from telethon import TelegramClient, events, utils
from telethon.tl.types import (
    PeerUser, PeerChannel, PeerChat, MessageMediaPhoto, MessageMediaDocument,
    ReactionEmoji, ReactionCustomEmoji, MessageEntityBold, MessageEntityUnderline,
    MessageEntityStrike, MessageEntityBlockquote, MessageEntitySpoiler,
    MessageEntityItalic, MessageEntityCode, MessageEntityPre,
    InputMediaDice, SendMessageTypingAction, SendMessageCancelAction,
    SendMessageRecordAudioAction, SendMessageRecordVideoAction,
    SendMessageUploadPhotoAction, SendMessageUploadVideoAction,
    SendMessageUploadDocumentAction, SendMessageGamePlayAction,
    SendMessageChooseStickerAction, SendMessageGeoLocationAction,
    SendMessageChooseContactAction, SpeakingInGroupCallAction,
    InputPeerUser, InputPeerChannel, InputPeerChat, KeyboardButtonSwitchInline,
    MessageEntityTextUrl, MessageEntityMention, MessageEntityHashtag,
    MessageEntityBotCommand, MessageEntityUrl, MessageEntityEmail,
    MessageEntityPhone, MessageEntityCashtag
)
from telethon.tl.functions.messages import (
    SendReactionRequest, DeleteMessagesRequest, SetTypingRequest,
    GetMessagesReactionsRequest, SendMessageRequest
)
from telethon.tl.functions.account import (
    UpdateProfileRequest, UpdateStatusRequest,
    UpdateUsernameRequest, UpdateEmojiStatusRequest
)
from telethon.tl.functions.photos import (
    UploadProfilePhotoRequest, DeletePhotosRequest, GetUserPhotosRequest
)
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import (
    JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest,
    EditBannedRequest, EditAdminRequest, InviteToChannelRequest
)
from telethon.tl.functions.messages import (
    ExportChatInviteRequest, EditChatDefaultBannedRightsRequest,
    SetBotCallbackAnswerRequest, GetInlineBotResultsRequest
)
from telethon.errors import (
    FloodWaitError, SessionPasswordNeededError, RPCError,
    MessageDeleteForbiddenError, MessageNotModifiedError,
    UserAlreadyParticipantError, ChannelInvalidError, ChatWriteForbiddenError,
    UsernameNotOccupiedError, UsernameInvalidError, PhoneNumberInvalidError,
    PhoneCodeInvalidError, PhoneCodeExpiredError, InvalidPhoneNumberError,
    AuthKeyError, AuthKeyDuplicatedError, AuthKeyInvalidError,
    TakeoutInitDelayError, TimeoutError, RPCError as TelethonRPCError
)

# ========== بارگذاری متغیرهای محیطی ==========
load_dotenv()

# ========== تنظیمات امن - از محیط گرفته می‌شوند ==========
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
BOT_USERNAME = os.getenv('BOT_USERNAME', 'Gap_5_bot')
MUSIC_BOT = os.getenv('MUSIC_BOT', 'Gap_4_bot')
GROUP_ID = int(os.getenv('GROUP_ID', -1002817019483))

GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GEMINI_KEY = os.getenv('GEMINI_KEY')
PAXSENIX_API_KEY = os.getenv('PAXSENIX_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# ========== تنظیمات API ==========
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
PAXSENIX_API_URL = "https://api.paxsenix.org/v1/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
DEEPSEEK_FREE_URL = "https://deepseek.api-sina-free.workers.dev/?text="
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# ========== بررسی توکن ==========
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN در فایل .env تنظیم نشده است!")

# ========== تنظیمات زمانی ==========
os.environ['TZ'] = 'Asia/Tehran'
try:
    time.tzset()
except:
    pass

# ========== لاگینگ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selfbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== پوشه‌ها ==========
SESSIONS_FOLDER = 'user_sessions'
MEDIA_FOLDER = 'media_storage'
REPORT_MEDIA_FOLDER = 'reported_media'
BACKUP_FOLDER = 'backups'
LOG_FOLDER = 'logs'
TEMP_FOLDER = 'temp'

for folder in [SESSIONS_FOLDER, MEDIA_FOLDER, REPORT_MEDIA_FOLDER, BACKUP_FOLDER, LOG_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ========== تنظیمات فایل‌ها ==========
REPORT_CONFIG_FILE = "report_config.json"
USER_DATA_FILE = "user_data.json"
CHANNEL_CONFIG_FILE = "channel_config.json"
AUTO_REPLY_FILE = "auto_reply.json"
SPAM_WORDS_FILE = "spam_words.json"
FILTER_WORDS_FILE = "filter_words.json"
COMMAND_ALIASES_FILE = "command_aliases.json"

# ========== API های ثابت ==========
API_CONFIGS = [
    {"api_id": 22409632, "api_hash": "b74c1ee200ad9ced6315859e9bd4125a"},
    {"api_id": 28297221, "api_hash": "8d682eb5c41a9762ef73f9ebe06c4eff"},
    {"api_id": 28039994, "api_hash": "00877cdcd706564a4de6abf7f7d64349"},
    {"api_id": 29031463, "api_hash": "64f122a7094dbab7e32b911eae6589e9"},
    {"api_id": 12832882, "api_hash": "1953c708cb3c47ecba74dc618b209e22"},
    {"api_id": 26645489, "api_hash": "6a212d0a400c97264600b3f932de5c2f"},
]

# ========== لیست ایموجی‌های مجاز ==========
ALLOWED_EMOJIS = [
    "🤯", "🐳", "😍", "💩", "👏", "🍌", "🤓", "😢", "🙉", "🤩",
    "🤝", "👀", "🌚", "🗿", "🤡", "😐", "👨‍💻", "😭", "🙈", "❤",
    "🙏", "😴", "💋", "🥰", "🤪", "✍️", "🥱", "👻", "🤣", "🌭",
    "😨", "🍓", "🔥", "🖕", "🤗", "🤔", "🤬", "😁", "🎄", "🫡",
    "⚡", "🥴", "😈", "🏆", "😇", "🎃", "☃️", "🤮", "👍", "👎",
    "😱", "😖", "🕊", "💯", "💔", "🤨", "❤️‍🔥", "💘", "😘", "💊",
    "🆒", "🤷‍♂", "🤷‍♀", "🎅", "🤶", "🦌", "⛄", "🕎", "✡", "☸",
    "☯", "✝", "☦", "☪", "☮", "🕉", "🕊", "🔯", "🕎", "🔱"
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
]

# ========== لیست پرچم‌ها ==========
flags = [
    "🇦🇫", "🇦🇽", "🇦🇱", "🇩🇿", "🇦🇸", "🇦🇩", "🇦🇴", "🇦🇮", "🇦🇶", "🇦🇬",
    "🇦🇷", "🇦🇲", "🇦🇼", "🇦🇺", "🇦🇹", "🇦🇿", "🇧🇸", "🇧🇭", "🇧🇩", "🇧🇧",
    "🇧🇾", "🇧🇪", "🇧🇿", "🇧🇯", "🇧🇲", "🇧🇹", "🇧🇴", "🇧🇦", "🇧🇼", "🇧🇷",
    "🇮🇴", "🇻🇬", "🇧🇳", "🇧🇬", "🇧🇫", "🇧🇮", "🇰🇭", "🇨🇲", "🇨🇦", "🇨🇻",
    "🇧🇶", "🇰🇾", "🇨🇫", "🇹🇩", "🇨🇱", "🇨🇳", "🇨🇽", "🇨🇨", "🇨🇴", "🇰🇲",
    "🇨🇬", "🇨🇩", "🇨🇰", "🇨🇷", "🇨🇮", "🇭🇷", "🇨🇺", "🇨🇼", "🇨🇾", "🇨🇿",
    "🇩🇰", "🇩🇯", "🇩🇲", "🇩🇴", "🇪🇨", "🇪🇬", "🇸🇻", "🇬🇶", "🇪🇷", "🇪🇪",
    "🇪🇹", "🇫🇰", "🇫🇴", "🇫🇯", "🇫🇮", "🇫🇷", "🇬🇫", "🇵🇫", "🇹🇫", "🇬🇦",
    "🇬🇲", "🇬🇪", "🇩🇪", "🇬🇭", "🇬🇮", "🇬🇷", "🇬🇱", "🇬🇩", "🇬🇵", "🇬🇺",
    "🇬🇹", "🇬🇬", "🇬🇳", "🇬🇼", "🇬🇾", "🇭🇹", "🇭🇲", "🇻🇦", "🇭🇳", "🇭🇰",
    "🇭🇺", "🇮🇸", "🇮🇳", "🇮🇩", "🇮🇷", "🇮🇶", "🇮🇪", "🇮🇲", "🇮🇱", "🇮🇹",
    "🇯🇲", "🇯🇵", "🇯🇪", "🇯🇴", "🇰🇿", "🇰🇪", "🇰🇮", "🇽🇰", "🇰🇼", "🇰🇬",
    "🇱🇦", "🇱🇻", "🇱🇧", "🇱🇸", "🇱🇷", "🇱🇾", "🇱🇮", "🇱🇹", "🇱🇺", "🇲🇴",
    "🇲🇰", "🇲🇬", "🇲🇼", "🇲🇾", "🇲🇻", "🇲🇱", "🇲🇹", "🇲🇭", "🇲🇶", "🇲🇷",
    "🇲🇺", "🇾🇹", "🇲🇽", "🇫🇲", "🇲🇩", "🇲🇨", "🇲🇳", "🇲🇪", "🇲🇸", "🇲🇦",
    "🇲🇿", "🇲🇲", "🇳🇦", "🇳🇷", "🇳🇵", "🇳🇱", "🇳🇨", "🇳🇿", "🇳🇮", "🇳🇪",
    "🇳🇬", "🇳🇺", "🇳🇫", "🇰🇵", "🇲🇵", "🇳🇴", "🇴🇲", "🇵🇰", "🇵🇼", "🇵🇸",
    "🇵🇦", "🇵🇬", "🇵🇾", "🇵🇪", "🇵🇭", "🇵🇳", "🇵🇱", "🇵🇹", "🇵🇷", "🇶🇦",
    "🇷🇪", "🇷🇴", "🇷🇺", "🇷🇼", "🇼🇸", "🇸🇲", "🇸🇹", "🇸🇦", "🇸🇳", "🇷🇸",
    "🇸🇨", "🇸🇱", "🇸🇬", "🇸🇽", "🇸🇰", "🇸🇮", "🇸🇧", "🇸🇴", "🇿🇦", "🇬🇸",
    "🇰🇷", "🇸🇸", "🇪🇸", "🇱🇰", "🇧🇱", "🇸🇭", "🇰🇳", "🇱🇨", "🇵🇲", "🇻🇨",
    "🇸🇩", "🇸🇷", "🇸🇯", "🇸🇿", "🇸🇪", "🇨🇭", "🇸🇾", "🇹🇼", "🇹🇯", "🇹🇿",
    "🇹🇭", "🇹🇱", "🇹🇬", "🇹🇰", "🇹🇴", "🇹🇹", "🇹🇳", "🇹🇷", "🇹🇲", "🇹🇨",
    "🇹🇻", "🇺🇬", "🇺🇦", "🇦🇪", "🇬🇧", "🇺🇸", "🇺🇾", "🇺🇿", "🇻🇺", "🇻🇪",
    "🇻🇳", "🇻🇮", "🇼🇫", "🇪🇭", "🇾🇪", "🇿🇲", "🇿🇼"
]

# ========== لیست پیام‌های اسپم ==========
SPAM_MESSAGES = [
    "🔥 سلام! چطوری؟",
    "💫 وضعیت چطوره؟",
    "🌟 روزت بخیر!",
    "✨ خبر جدید؟",
    "⭐️ چه خبر؟",
    "💥 وقت بخیر!",
    "🎯 چیکار میکنی؟",
    "💪 آنلاینی؟",
    "🤝 در خدمتم!",
    "🙏 سلام دادش!",
    "😎 درود بر تو!",
    "💎 وقتت بخیر!",
    "🎉 حال چطوره؟",
    "💖 خوبی داداش؟",
    "🌹 عزیز دل!",
    "🍀 سلامت باشی!",
    "🌟 نوروزت مبارک!",
    "💫 موفق باشی!",
    "🔥 قوی باش!",
    "⚡️ همیشه شاد!"
]

# ========== تنظیمات پیش‌فرض ==========
DEFAULT_LOCK_SETTINGS = {
    'link': False, 'photo': False, 'video': False, 'sticker': False,
    'gif': False, 'voice': False, 'file': False, 'music': False,
    'video_note': False, 'contact': False, 'location': False,
    'emoji': False, 'text': False, 'forward': False, 'reply': False
}

BOT_VERSION = "6.0.0"
BOT_CREATOR = "Self-Bot Team"
BOT_SITE = "https://t.me/Gap_5_bot"

# ========== لیست‌های انیمیشن ==========
HEARTS = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💖", "💗", "💓", "💞", "💕", "💟", "❣️"]
MOONS = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌙", "🌚", "🌛", "🌜", "🌝"]
STARS = ["⭐️", "🌟", "🌠", "✨", "💫", "⭐", "🌟", "✨", "⚡️"]
FIRE = ["🔥", "💥", "⚡️", "✨", "🌟", "⭐️"]

# ========== اکشن‌های تایپ ==========
action_types = {
    'تایپ': SendMessageTypingAction(),
    'ویس': SendMessageRecordAudioAction(),
    'ویدیو': SendMessageRecordVideoAction(),
    'عکس': SendMessageUploadPhotoAction(progress=0),
    'فیلم': SendMessageUploadVideoAction(progress=0),
    'فایل': SendMessageUploadDocumentAction(progress=0),
    'بازی': SendMessageGamePlayAction(),
    'استیکر': SendMessageChooseStickerAction(),
    'موقعیت': SendMessageGeoLocationAction(),
    'تماس': SendMessageChooseContactAction(),
    'صحبت': SpeakingInGroupCallAction(),
    'لغو': SendMessageCancelAction(),
}

# ========== متغیرهای سراسری ==========
media_cache: Dict[int, dict] = {}
message_cache: Dict[tuple, str] = {}
user_inline_messages: Dict[int, List] = {}
spam_tasks: Dict[int, asyncio.Task] = {}
action_tasks: Dict[int, asyncio.Task] = {}
active_selfbots: Dict[int, 'SelfBotManager'] = {}
search_results_cache: Dict[int, dict] = {}

# ========== کلاس دیتابیس امن ==========
class Database:
    """کلاس مدیریت دیتابیس با قابلیت‌های امنیتی"""
    
    def __init__(self, db_name: str = 'main_database.db'):
        self.db_name = db_name
        self._local = threading.local()
        self._lock = threading.RLock()
        self._init_database()
    
    def _get_conn(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_database(self):
        """ایجاد تمام جدول‌های مورد نیاز"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # جدول کاربران اصلی
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
                    password_hash TEXT,
                    password_salt TEXT,
                    two_factor_secret TEXT,
                    request_date TEXT,
                    activation_date TEXT,
                    expiration_date TEXT,
                    session_file TEXT,
                    api_id INTEGER,
                    api_hash TEXT,
                    last_active TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    warning_count INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول تنظیمات سلف‌بات
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
                    ai_4_pm BOOLEAN DEFAULT 0,
                    ai_1_group BOOLEAN DEFAULT 0,
                    ai_2_group BOOLEAN DEFAULT 0,
                    ai_3_group BOOLEAN DEFAULT 0,
                    ai_4_group BOOLEAN DEFAULT 0,
                    translate_english BOOLEAN DEFAULT 0,
                    translate_arabic BOOLEAN DEFAULT 0,
                    translate_hebrew BOOLEAN DEFAULT 0,
                    translate_russian BOOLEAN DEFAULT 0,
                    translate_turkish BOOLEAN DEFAULT 0,
                    translate_german BOOLEAN DEFAULT 0,
                    translate_french BOOLEAN DEFAULT 0,
                    translate_spanish BOOLEAN DEFAULT 0,
                    panel_mode BOOLEAN DEFAULT 1,
                    time_font_indices TEXT DEFAULT 'all',
                    filter_enabled BOOLEAN DEFAULT 0,
                    auto_delete BOOLEAN DEFAULT 0,
                    auto_delete_time INTEGER DEFAULT 60,
                    welcome_enabled BOOLEAN DEFAULT 0,
                    welcome_message TEXT,
                    goodbye_enabled BOOLEAN DEFAULT 0,
                    goodbye_message TEXT,
                    captcha_enabled BOOLEAN DEFAULT 0,
                    auto_moderate BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول دشمنان
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enemies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    enemy_id INTEGER,
                    chat_type TEXT DEFAULT 'pv',
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, enemy_id, chat_type)
                )
            ''')
            
            # جدول قفل‌های پیوی
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locked_pvs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    locked_user_id INTEGER,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, locked_user_id)
                )
            ''')
            
            # جدول قفل‌های رسانه
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
                    lock_forward BOOLEAN DEFAULT 0,
                    lock_reply BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, target_id)
                )
            ''')
            
            # جدول ریکشن‌ها
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
            
            # جدول کامنت‌های خودکار
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    channel_id INTEGER,
                    comment_text TEXT,
                    channel_title TEXT,
                    channel_type TEXT,
                    channel_username TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, channel_id)
                )
            ''')
            
            # جدول کامنت‌های ارسال شده
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
            
            # جدول کش پیام‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    chat_id INTEGER,
                    message_id INTEGER,
                    message_text TEXT,
                    message_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, chat_id, message_id)
                )
            ''')
            
            # جدول پیام‌های اسپم دشمنان
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enemy_spam_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    spam_text TEXT,
                    spam_type TEXT DEFAULT 'text',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول کلمات فیلتر
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS filter_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    word TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    action_type TEXT DEFAULT 'delete',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id, word)
                )
            ''')
            
            # جدول تنظیمات اسپم
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER,
                    spam_protection BOOLEAN DEFAULT 0,
                    spam_limit INTEGER DEFAULT 10,
                    mute_duration INTEGER DEFAULT 10,
                    warn_enabled BOOLEAN DEFAULT 1,
                    ban_on_repeat BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_id)
                )
            ''')
            
            # جدول حافظه کاربران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    known_name TEXT,
                    chat_id INTEGER,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    warning_count INTEGER DEFAULT 0,
                    is_muted BOOLEAN DEFAULT 0,
                    mute_until TIMESTAMP
                )
            ''')
            
            # جدول اطلاعات کاربران
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
            
            # جدول آمار
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stat_type TEXT,
                    stat_value INTEGER DEFAULT 0,
                    stat_date DATE,
                    UNIQUE(user_id, stat_type, stat_date)
                )
            ''')
            
            # جدول لاگ‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول بکاپ‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_file TEXT,
                    backup_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("✅ دیتابیس با موفقیت ایجاد/بروزرسانی شد")
    
    def hash_password(self, password: str) -> Tuple[str, str]:
        """هش کردن رمز عبور با استفاده از pbkdf2"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed_hex: str, salt: str) -> bool:
        """تأیید رمز عبور"""
        hashed = bytes.fromhex(hashed_hex)
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(hashed, new_hash)
    
    def is_user_active(self, user_id: str) -> bool:
        """بررسی فعال بودن کاربر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT self_active, expiration_date, is_banned FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        if row['is_banned']:
            return False
        
        if not row['self_active']:
            return False
        
        if row['expiration_date']:
            try:
                exp_date = datetime.strptime(row['expiration_date'], '%Y-%m-%d')
                if exp_date < datetime.now():
                    return False
            except:
                pass
        return True
    
    def get_user(self, user_id: str) -> Optional[dict]:
        """دریافت اطلاعات کاربر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_user(self, user_id: str, **kwargs):
        """بروزرسانی اطلاعات کاربر"""
        if 'password' in kwargs:
            password = kwargs.pop('password')
            hashed, salt = self.hash_password(password)
            kwargs['password_hash'] = hashed
            kwargs['password_salt'] = salt
        
        conn = self._get_conn()
        cursor = conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        cursor.execute(f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', values)
        conn.commit()
    
    def add_user(self, user_id: str, full_name: str, username: str):
        """افزودن کاربر جدید"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, full_name, username, updated_at, last_active) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (user_id, full_name, username))
        conn.commit()
    
    def get_active_users(self) -> List[dict]:
        """دریافت لیست کاربران فعال"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE self_active = 1 AND admin_approved = 1 AND is_banned = 0')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_requests(self) -> List[dict]:
        """دریافت درخواست‌های pending"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE request_sent = 1 AND admin_approved = 0 AND rejected = 0')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_login(self) -> List[dict]:
        """دریافت کاربران در حال ورود"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE admin_approved = 1 AND self_active = 0 AND step IS NOT NULL')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_selfbot_settings(self, user_id: int) -> dict:
        """دریافت تنظیمات سلف‌بات"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM selfbot_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            result = dict(row)
            if result.get('time_font_indices') and result['time_font_indices'] != 'all':
                try:
                    result['time_font_indices'] = [int(x) for x in result['time_font_indices'].split(',')]
                except:
                    result['time_font_indices'] = 'all'
            else:
                result['time_font_indices'] = 'all'
            return result
        else:
            default = {
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
                'ai_4_pm': 0,
                'ai_1_group': 0,
                'ai_2_group': 0,
                'ai_3_group': 0,
                'ai_4_group': 0,
                'translate_english': 0,
                'translate_arabic': 0,
                'translate_hebrew': 0,
                'translate_russian': 0,
                'translate_turkish': 0,
                'translate_german': 0,
                'translate_french': 0,
                'translate_spanish': 0,
                'panel_mode': 1,
                'time_font_indices': 'all',
                'filter_enabled': 0,
                'auto_delete': 0,
                'auto_delete_time': 60,
                'welcome_enabled': 0,
                'welcome_message': None,
                'goodbye_enabled': 0,
                'goodbye_message': None,
                'captcha_enabled': 0,
                'auto_moderate': 0,
            }
            self.update_selfbot_setting(user_id, default)
            return default
    
    def update_selfbot_setting(self, user_id: int, key_or_dict, value=None):
        """بروزرسانی تنظیمات سلف‌بات"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if isinstance(key_or_dict, dict):
            settings = key_or_dict.copy()
            if 'time_font_indices' in settings and isinstance(settings['time_font_indices'], list):
                settings['time_font_indices'] = ','.join(map(str, settings['time_font_indices']))
            
            columns = ', '.join(settings.keys())
            placeholders = ', '.join(['?' for _ in settings])
            values = list(settings.values())
            cursor.execute(f'INSERT OR REPLACE INTO selfbot_settings ({columns}, updated_at) VALUES ({placeholders}, CURRENT_TIMESTAMP)', values)
        else:
            cursor.execute(f'UPDATE selfbot_settings SET {key_or_dict} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (value, user_id))
        
        conn.commit()
    
    def get_enemies(self, owner_id: int, chat_type: str = 'pv') -> List[int]:
        """دریافت لیست دشمنان"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT enemy_id FROM enemies WHERE owner_id = ? AND chat_type = ?', (owner_id, chat_type))
        return [row['enemy_id'] for row in cursor.fetchall()]
    
    def add_enemy(self, owner_id: int, enemy_id: int, chat_type: str = 'pv', reason: str = None):
        """افزودن دشمن"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO enemies (owner_id, enemy_id, chat_type, reason) VALUES (?, ?, ?, ?)', (owner_id, enemy_id, chat_type, reason))
        conn.commit()
    
    def remove_enemy(self, owner_id: int, enemy_id: int, chat_type: str = 'pv'):
        """حذف دشمن"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM enemies WHERE owner_id = ? AND enemy_id = ? AND chat_type = ?', (owner_id, enemy_id, chat_type))
        conn.commit()
    
    def is_enemy(self, owner_id: int, enemy_id: int, chat_type: str = 'pv') -> bool:
        """بررسی دشمن بودن"""
        return enemy_id in self.get_enemies(owner_id, chat_type)
    
    def add_locked_pv(self, owner_id: int, locked_user_id: int, reason: str = None):
        """قفل کردن پیوی کاربر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO locked_pvs (owner_id, locked_user_id, reason) VALUES (?, ?, ?)', (owner_id, locked_user_id, reason))
        conn.commit()
    
    def remove_locked_pv(self, owner_id: int, locked_user_id: int):
        """باز کردن قفل پیوی"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM locked_pvs WHERE owner_id = ? AND locked_user_id = ?', (owner_id, locked_user_id))
        conn.commit()
    
    def get_locked_pvs(self, owner_id: int) -> List[int]:
        """دریافت لیست پیوی‌های قفل شده"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT locked_user_id FROM locked_pvs WHERE owner_id = ?', (owner_id,))
        return [row['locked_user_id'] for row in cursor.fetchall()]
    
    def is_pv_locked(self, owner_id: int, user_id: int) -> bool:
        """بررسی قفل بودن پیوی"""
        return user_id in self.get_locked_pvs(owner_id)
    
    def get_media_locks(self, owner_id: int, target_id: int) -> dict:
        """دریافت تنظیمات قفل رسانه"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        
        return {
            'owner_id': owner_id,
            'target_id': target_id,
            'lock_link': 0, 'lock_photo': 0, 'lock_video': 0, 'lock_sticker': 0,
            'lock_gif': 0, 'lock_voice': 0, 'lock_file': 0, 'lock_music': 0,
            'lock_video_note': 0, 'lock_contact': 0, 'lock_location': 0,
            'lock_emoji': 0, 'lock_text': 0, 'lock_forward': 0, 'lock_reply': 0
        }
    
    def set_media_lock(self, owner_id: int, target_id: int, lock_type: str, value: bool):
        """تنظیم قفل رسانه"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM media_locks WHERE owner_id = ? AND target_id = ?', (owner_id, target_id))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(f'UPDATE media_locks SET {lock_type} = ?, created_at = CURRENT_TIMESTAMP WHERE owner_id = ? AND target_id = ?', (1 if value else 0, owner_id, target_id))
        else:
            lock_settings = {
                'owner_id': owner_id, 'target_id': target_id,
                'lock_link': 0, 'lock_photo': 0, 'lock_video': 0, 'lock_sticker': 0,
                'lock_gif': 0, 'lock_voice': 0, 'lock_file': 0, 'lock_music': 0,
                'lock_video_note': 0, 'lock_contact': 0, 'lock_location': 0,
                'lock_emoji': 0, 'lock_text': 0, 'lock_forward': 0, 'lock_reply': 0
            }
            lock_settings[lock_type] = 1 if value else 0
            columns = ', '.join(lock_settings.keys())
            placeholders = ', '.join(['?' for _ in lock_settings])
            cursor.execute(f'INSERT INTO media_locks ({columns}) VALUES ({placeholders})', list(lock_settings.values()))
        
        conn.commit()
    
    def set_reaction(self, owner_id: int, chat_id: int, target_id: int, emoji: str):
        """تنظیم ریکشن خودکار"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO reactions (owner_id, chat_id, target_id, emoji) VALUES (?, ?, ?, ?)', (owner_id, chat_id, target_id, emoji))
        conn.commit()
    
    def get_reaction(self, owner_id: int, chat_id: int, target_id: int) -> Optional[str]:
        """دریافت ریکشن تنظیم شده"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT emoji FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
        row = cursor.fetchone()
        return row['emoji'] if row else None
    
    def remove_reaction(self, owner_id: int, chat_id: int, target_id: int):
        """حذف ریکشن خودکار"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
        conn.commit()
    
    def set_auto_comment(self, owner_id: int, channel_id: int, comment_text: str, channel_title: str, channel_type: str, channel_username: str):
        """تنظیم کامنت خودکار"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO auto_comments (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (owner_id, channel_id, comment_text, channel_title, channel_type, channel_username))
        conn.commit()
    
    def get_auto_comments(self, owner_id: int) -> List[dict]:
        """دریافت لیست کامنت‌های خودکار"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auto_comments WHERE owner_id = ?', (owner_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_auto_comment(self, owner_id: int, channel_id: int) -> Optional[dict]:
        """دریافت کامنت خودکار یک کانال"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def remove_auto_comment(self, owner_id: int, channel_id: int):
        """حذف کامنت خودکار"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
        conn.commit()
    
    def mark_comment_sent(self, owner_id: int, channel_id: int, message_id: int):
        """علامت‌گذاری کامنت ارسال شده"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO sent_comments (owner_id, channel_id, message_id, comment_sent) VALUES (?, ?, ?, 1)', (owner_id, channel_id, message_id))
        conn.commit()
    
    def is_comment_sent(self, owner_id: int, channel_id: int, message_id: int) -> bool:
        """بررسی ارسال کامنت"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT comment_sent FROM sent_comments WHERE owner_id = ? AND channel_id = ? AND message_id = ?', (owner_id, channel_id, message_id))
        row = cursor.fetchone()
        return row and row['comment_sent'] == 1
    
    def cache_message(self, owner_id: int, chat_id: int, message_id: int, message_text: str, message_type: str = 'text'):
        """کش کردن پیام"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO message_cache (owner_id, chat_id, message_id, message_text, message_type) VALUES (?, ?, ?, ?, ?)', (owner_id, chat_id, message_id, message_text, message_type))
        conn.commit()
    
    def get_cached_message(self, owner_id: int, chat_id: int, message_id: int) -> Optional[str]:
        """دریافت پیام کش شده"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT message_text FROM message_cache WHERE owner_id = ? AND chat_id = ? AND message_id = ?', (owner_id, chat_id, message_id))
        row = cursor.fetchone()
        return row['message_text'] if row else None
    
    def add_enemy_spam_message(self, owner_id: int, spam_text: str, spam_type: str = 'text'):
        """افزودن پیام اسپم دشمن"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO enemy_spam_messages (owner_id, spam_text, spam_type) VALUES (?, ?, ?)', (owner_id, spam_text, spam_type))
        conn.commit()
    
    def get_enemy_spam_messages(self, owner_id: int) -> List[dict]:
        """دریافت لیست پیام‌های اسپم"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT id, spam_text, spam_type FROM enemy_spam_messages WHERE owner_id = ? ORDER BY created_at', (owner_id,))
        return [{'id': row['id'], 'text': row['spam_text'], 'type': row['spam_type']} for row in cursor.fetchall()]
    
    def clear_enemy_spam_messages(self, owner_id: int):
        """پاک کردن همه پیام‌های اسپم"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ?', (owner_id,))
        conn.commit()
    
    def delete_enemy_spam_message(self, owner_id: int, message_id: int):
        """حذف یک پیام اسپم"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ? AND id = ?', (owner_id, message_id))
        conn.commit()
    
    def get_filter_words(self, owner_id: int) -> List[dict]:
        """دریافت لیست کلمات فیلتر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT word, enabled, action_type FROM filter_words WHERE owner_id = ?', (owner_id,))
        return [{'word': row['word'], 'enabled': bool(row['enabled']), 'action': row['action_type']} for row in cursor.fetchall()]
    
    def add_filter_word(self, owner_id: int, word: str, action_type: str = 'delete'):
        """افزودن کلمه فیلتر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO filter_words (owner_id, word, action_type) VALUES (?, ?, ?)', (owner_id, word, action_type))
        conn.commit()
    
    def remove_filter_word(self, owner_id: int, word: str):
        """حذف کلمه فیلتر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM filter_words WHERE owner_id = ? AND word = ?', (owner_id, word))
        conn.commit()
    
    def set_filter_enabled(self, owner_id: int, enabled: bool):
        """فعال/غیرفعال کردن فیلتر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE selfbot_settings SET filter_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (1 if enabled else 0, owner_id))
        conn.commit()
    
    def get_filter_enabled(self, owner_id: int) -> bool:
        """بررسی فعال بودن فیلتر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT filter_enabled FROM selfbot_settings WHERE user_id = ?', (owner_id,))
        row = cursor.fetchone()
        return bool(row['filter_enabled']) if row else False
    
    def get_spam_settings(self, owner_id: int) -> dict:
        """دریافت تنظیمات حفاظت اسپم"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM spam_settings WHERE owner_id = ?', (owner_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return {'owner_id': owner_id, 'spam_protection': 0, 'spam_limit': 10, 'mute_duration': 10, 'warn_enabled': 1, 'ban_on_repeat': 0}
    
    def set_spam_settings(self, owner_id: int, **kwargs):
        """تنظیم حفاظت اسپم"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM spam_settings WHERE owner_id = ?', (owner_id,))
        exists = cursor.fetchone()
        
        if exists:
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [owner_id]
            cursor.execute(f'UPDATE spam_settings SET {set_clause} WHERE owner_id = ?', values)
        else:
            default = {'owner_id': owner_id, 'spam_protection': 0, 'spam_limit': 10, 'mute_duration': 10, 'warn_enabled': 1, 'ban_on_repeat': 0}
            default.update(kwargs)
            columns = ', '.join(default.keys())
            placeholders = ', '.join(['?' for _ in default])
            cursor.execute(f'INSERT INTO spam_settings ({columns}) VALUES ({placeholders})', list(default.values()))
        
        conn.commit()
    
    def update_user_memory(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, chat_id: int = None, known_name: str = None):
        """بروزرسانی حافظه کاربر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_memory WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            updates = []
            values = []
            if username is not None:
                updates.append('username = ?')
                values.append(username)
            if first_name is not None:
                updates.append('first_name = ?')
                values.append(first_name)
            if last_name is not None:
                updates.append('last_name = ?')
                values.append(last_name)
            if known_name is not None:
                updates.append('known_name = ?')
                values.append(known_name)
            if chat_id is not None:
                updates.append('chat_id = ?')
                values.append(chat_id)
            
            if updates:
                values.append(user_id)
                cursor.execute(f'UPDATE user_memory SET {", ".join(updates)}, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?', values)
                cursor.execute('UPDATE user_memory SET message_count = message_count + 1 WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('''
                INSERT INTO user_memory (user_id, username, first_name, last_name, known_name, chat_id, last_seen, message_count)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
            ''', (user_id, username, first_name, last_name, known_name, chat_id))
        
        conn.commit()
    
    def get_user_name(self, user_id: int) -> str:
        """دریافت نام کاربر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT known_name, first_name, username FROM user_memory WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            if row['known_name']:
                return row['known_name']
            elif row['first_name']:
                return row['first_name']
            elif row['username']:
                return f"@{row['username']}"
        return f"کاربر {user_id}"
    
    def get_original_name(self, owner_id: int) -> Optional[str]:
        """دریافت نام اصلی کاربر"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "original_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def set_original_name(self, owner_id: int, original_name: str):
        """ذخیره نام اصلی"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "original_name", ?)', (owner_id, original_name))
        conn.commit()
    
    def get_current_name(self, owner_id: int) -> Optional[str]:
        """دریافت نام جاری"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "current_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
        row = cursor.fetchone()
        return row['value'] if row else None
    
    def set_current_name(self, owner_id: int, current_name: str):
        """ذخیره نام جاری"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "current_name", ?)', (owner_id, current_name))
        conn.commit()
    
    def update_last_active(self, user_id: str):
        """بروزرسانی آخرین فعالیت"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_active = ?, login_count = login_count + 1 WHERE user_id = ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
        conn.commit()
    
    def add_log(self, user_id: int, action: str, details: str = None, ip_address: str = None):
        """افزودن لاگ"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO logs (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)', (user_id, action, details, ip_address))
        conn.commit()
    
    def add_statistic(self, user_id: int, stat_type: str, value: int = 1):
        """افزودن آمار"""
        conn = self._get_conn()
        cursor = conn.cursor()
        today = datetime.now().date()
        cursor.execute('''
            INSERT INTO statistics (user_id, stat_type, stat_value, stat_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, stat_type, stat_date) DO UPDATE SET stat_value = stat_value + ?
        ''', (user_id, stat_type, value, today, value))
        conn.commit()

db = Database()

# ادامه در بخش 2 از 8...
# ========== بخش 2 - ادامه کد ==========

# ========== توابع کمکی ==========

def get_user_api(user_id: str) -> dict:
    """اختصاص API به کاربر"""
    conn = sqlite3.connect('main_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT api_id, api_hash FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row and row[0] and row[1]:
        conn.close()
        return {"api_id": row[0], "api_hash": row[1]}
    
    # توزیع عادلانه API ها
    api_usage = {}
    for api in API_CONFIGS:
        cursor.execute('SELECT COUNT(*) FROM users WHERE api_id = ?', (api["api_id"],))
        api_usage[api["api_id"]] = cursor.fetchone()[0]
    
    best_api = min(API_CONFIGS, key=lambda x: api_usage.get(x["api_id"], 0))
    cursor.execute('UPDATE users SET api_id = ?, api_hash = ? WHERE user_id = ?', 
                   (best_api["api_id"], best_api["api_hash"], user_id))
    conn.commit()
    conn.close()
    
    logger.info(f"API اختصاص یافته به کاربر {user_id}: {best_api['api_id']}")
    return best_api


def convert_persian_to_english(text: str) -> str:
    """تبدیل اعداد فارسی به انگلیسی"""
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


def get_full_date_info() -> str:
    """دریافت اطلاعات کامل تاریخ"""
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
    except Exception as e:
        logger.error(f"خطا در دریافت تاریخ: {e}")
        return f"📅 تاریخ: {now.strftime('%Y/%m/%d %H:%M:%S')}"


def is_channel_post(message) -> bool:
    """تشخیص پست کانال بودن"""
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
        
        return False
    except Exception as e:
        logger.error(f"خطا در تشخیص پست کانال: {e}")
        return False


def is_link_message(text: str) -> bool:
    """تشخیص لینک بودن پیام"""
    if not text:
        return False
    
    patterns = [
        r'https?://\S+',
        r't\.me/\S+',
        r'www\.\S+',
        r'\S+\.(com|ir|org|net|info|io|xyz|online|site|club|shop|store|tech|space|live|blog)\S*',
        r'bit\.ly/\S+',
        r'goo\.gl/\S+',
        r'is\.gd/\S+',
        r'ow\.ly/\S+',
        r'tinyurl\.com/\S+',
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def is_emoji_message(text: str) -> bool:
    """تشخیص ایموجی بودن پیام"""
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
        r'\U0001FA70-\U0001FAFF'
        r'\U00002600-\U000026FF'
        r'\U0000FE00-\U0000FE0F'
        r']+$', 
        flags=re.UNICODE
    )
    
    return bool(emoji_pattern.match(text))


async def is_premium_emoji(message) -> bool:
    """تشخیص ایموجی پریمیوم"""
    try:
        if message.media and hasattr(message.media, 'document'):
            document = message.media.document
            if hasattr(document, 'attributes'):
                for attr in document.attributes:
                    if hasattr(attr, 'alt') and attr.alt:
                        return True
    except Exception as e:
        logger.error(f"خطا در تشخیص ایموجی پریمیوم: {e}")
    return False


def convert_to_classic_font(text: str, font_index: int) -> str:
    """تبدیل به فونت کلاسیک"""
    if font_index >= len(classic_fonts):
        font_index = 0
    
    font = classic_fonts[font_index]
    if isinstance(font, dict):
        return ''.join(font.get(c, c) for c in text)
    else:
        result = []
        for c in text:
            if c.isdigit():
                idx = int(c)
                if idx < len(font):
                    result.append(font[idx])
                else:
                    result.append(c)
            else:
                result.append(c)
        return ''.join(result)


async def get_ai_response(text: str, ai_type: int, user_id: int = None) -> Optional[str]:
    """دریافت پاسخ از هوش مصنوعی"""
    try:
        async with aiohttp.ClientSession() as session:
            # هوش 1: Gemini
            if ai_type == 1 and GEMINI_KEY:
                url = f"{GEMINI_URL}?key={GEMINI_KEY}"
                payload = {
                    "contents": [{
                        "parts": [{"text": text}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topK": 40,
                        "topP": 0.95,
                        "maxOutputTokens": 1024,
                    }
                }
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        candidates = result.get('candidates', [])
                        if candidates:
                            return candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '').strip()
            
            # هوش 2: Paxsenix
            elif ai_type == 2 and PAXSENIX_API_KEY:
                url = PAXSENIX_API_URL
                headers = {
                    'Authorization': f'Bearer {PAXSENIX_API_KEY}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {'role': 'system', 'content': 'شما یک دستیار هوشمند و مفید هستید.'},
                        {'role': 'user', 'content': text}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        choices = result.get('choices', [])
                        if choices:
                            return choices[0].get('message', {}).get('content', '').strip()
            
            # هوش 3: DeepSeek (رایگان)
            elif ai_type == 3:
                url = f"{DEEPSEEK_FREE_URL}{quote(text)}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return (await resp.text()).strip()
            
            # هوش 4: OpenAI
            elif ai_type == 4 and OPENAI_API_KEY:
                url = OPENAI_API_URL
                headers = {
                    'Authorization': f'Bearer {OPENAI_API_KEY}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [{'role': 'user', 'content': text}],
                    'temperature': 0.7,
                    'max_tokens': 1000
                }
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        choices = result.get('choices', [])
                        if choices:
                            return choices[0].get('message', {}).get('content', '').strip()
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout در هوش {ai_type}")
        return None
    except Exception as e:
        logger.error(f"خطا در هوش {ai_type}: {e}")
        return None
    
    return None


async def apply_text_style(message_text: str, style: Optional[str]) -> Tuple[str, list]:
    """اعمال استایل به متن"""
    if not message_text or not style:
        return message_text, []
    
    entities = []
    length = len(message_text)
    
    style_map = {
        'بولد': lambda: MessageEntityBold(offset=0, length=length),
        'زیرخط': lambda: MessageEntityUnderline(offset=0, length=length),
        'خط خورده': lambda: MessageEntityStrike(offset=0, length=length),
        'نقل قول': lambda: MessageEntityBlockquote(offset=0, length=length),
        'اسپویلر': lambda: MessageEntitySpoiler(offset=0, length=length),
        'کج': lambda: MessageEntityItalic(offset=0, length=length),
        'کد': lambda: MessageEntityCode(offset=0, length=length),
        'پیش': lambda: MessageEntityPre(offset=0, length=length, language=""),
    }
    
    if style in style_map:
        entities.append(style_map[style]())
    
    return message_text, entities


async def get_target_user(event, client: TelegramClient = None) -> Optional[int]:
    """دریافت آی‌دی کاربر هدف (از ریپلای یا خود پیام)"""
    try:
        if event.is_reply:
            replied_msg = await event.get_reply_message()
            if replied_msg and replied_msg.sender_id:
                return replied_msg.sender_id
        
        if client and isinstance(event.message.peer_id, PeerUser) and not event.is_reply:
            return event.message.peer_id.user_id
        
        return None
    except Exception as e:
        logger.error(f"خطا در دریافت کاربر هدف: {e}")
        return None


def extract_name_from_message(text: str) -> Optional[str]:
    """استخراج نام از متن پیام"""
    patterns = [
        r'من\s+([\u0600-\u06FF\s]+)\s+هستم',
        r'اسمم\s+([\u0600-\u06FF\s]+)\s+است',
        r'نامم\s+([\u0600-\u06FF\s]+)\s+است',
        r'من\s+([\u0600-\u06FF\s]+)\s+ام',
        r'([\u0600-\u06FF\s]+)\s+هستم',
        r'اسم\s+([\u0600-\u06FF\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            stop_words = ['من', 'هستم', 'اسمم', 'است', 'نامم', 'ام', 'اسم']
            words = name.split()
            filtered_words = [word for word in words if word.lower() not in stop_words]
            return ' '.join(filtered_words).strip()
    
    return None


async def _wrap_edit(message, text: str):
    """ویرایش پیام با مدیریت خطا"""
    try:
        await message.edit(text)
    except FloodWaitError as fl:
        logger.warning(f"FloodWait در ویرایش: {fl.seconds} ثانیه")
        await asyncio.sleep(fl.seconds)
        try:
            await message.edit(text)
        except:
            pass
    except Exception as e:
        logger.error(f"خطا در ویرایش پیام: {e}")


async def advanced_heart_phase1(message):
    """مرحله 1 انیمیشن قلب پیشرفته"""
    R = "❤️"
    W = "🤍"
    SLEEP = 0.1
    
    BIG_SCROLL = "🧡💛💚💙💜🖤🤎"
    JOINED_HEART = "\n".join([
        "❤️🤍🤍❤️",
        "🤍❤️❤️🤍",
        "🤍🤍❤️🤍",
        "🤍🤍🤍❤️"
    ])
    
    await _wrap_edit(message, JOINED_HEART)
    for heart in BIG_SCROLL:
        await _wrap_edit(message, JOINED_HEART.replace(R, heart))
        await asyncio.sleep(SLEEP)


async def advanced_heart_phase2(message):
    """مرحله 2 انیمیشن قلب پیشرفته"""
    R = "❤️"
    W = "🤍"
    SLEEP = 0.1
    
    ALL = ["❤️"] + list("🧡💛💚💙💜🤎🖤")
    JOINED_HEART = "\n".join([
        "❤️🤍🤍❤️",
        "🤍❤️❤️🤍",
        "🤍🤍❤️🤍",
        "🤍🤍🤍❤️"
    ])
    HEARTLET_LEN = JOINED_HEART.count(R)
    format_heart = JOINED_HEART.replace(R, "{}")
    
    for _ in range(5):
        heart = format_heart.format(*random.choices(ALL, k=HEARTLET_LEN))
        await _wrap_edit(message, heart)
        await asyncio.sleep(SLEEP)


async def advanced_heart_phase3(message):
    """مرحله 3 انیمیشن قلب پیشرفته"""
    R = "❤️"
    W = "🤍"
    SLEEP = 0.1
    
    JOINED_HEART = "\n".join([
        "❤️🤍🤍❤️",
        "🤍❤️❤️🤍",
        "🤍🤍❤️🤍",
        "🤍🤍🤍❤️"
    ])
    
    await _wrap_edit(message, JOINED_HEART)
    await asyncio.sleep(SLEEP * 2)
    repl = JOINED_HEART
    for _ in range(JOINED_HEART.count(W)):
        repl = repl.replace(W, R, 1)
        await _wrap_edit(message, repl)
        await asyncio.sleep(SLEEP)


async def advanced_heart_phase4(message):
    """مرحله 4 انیمیشن قلب پیشرفته"""
    R = "❤️"
    SLEEP = 0.1
    
    for i in range(7, 0, -1):
        heart_matrix = "\n".join([R * i] * i)
        await _wrap_edit(message, heart_matrix)
        await asyncio.sleep(SLEEP)


async def advanced_heart_animation(message):
    """انیمیشن کامل قلب پیشرفته"""
    try:
        await advanced_heart_phase1(message)
        await asyncio.sleep(0.3)
        await advanced_heart_phase2(message)
        await asyncio.sleep(0.2)
        await advanced_heart_phase3(message)
        await asyncio.sleep(0.2)
        await advanced_heart_phase4(message)
        await asyncio.sleep(0.5)
        
        texts = ["❤️ I", "❤️ I Love", "❤️ I Love You", "❤️ I Love You <3"]
        for text in texts:
            await _wrap_edit(message, text)
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"خطا در انیمیشن قلب: {e}")


# ========== کلاس منشی موقت ==========

class TempAssistant:
    """مدیریت منشی موقت برای پاسخ خودکار به پیام‌ها"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.enabled = False
        self.responses: List[str] = []
        self.replied_users: Dict[int, bool] = {}
        self._lock = asyncio.Lock()
    
    def is_enabled(self) -> bool:
        return self.enabled
    
    def enable(self) -> str:
        self.enabled = True
        return """✅ منشی موقت روشن شد.

📝 حالا چند تا جواب ذخیره کن:
`جواب 1 سلام دادش چطوری؟`
`جواب 2 بفرمایید جانم`
`جواب 3 در خدمتم`
`جواب 4 چشم حتما`
`جواب 5 باشه انجام میشه`

🔹 هر کاربر فقط ۱ بار جواب میگیره
🔹 جواب‌ها تصادفی فرستاده میشن
🔹 میتونی تا ۵ جواب مختلف ذخیره کنی"""
    
    def disable(self) -> str:
        self.enabled = False
        return "❌ منشی موقت خاموش شد."
    
    def add_response(self, response_text: str) -> str:
        if len(self.responses) < 5:
            self.responses.append(response_text)
            return f"✅ جواب {len(self.responses)} ذخیره شد: {response_text}"
        return "❌ حداکثر ۵ جواب میتونی ذخیره کنی.\nاول با `پاک کردن جوابها` پاک کن."
    
    def get_responses_list(self) -> str:
        if self.responses:
            msg = "📋 **جواب‌های ذخیره شده:**\n\n"
            for i, r in enumerate(self.responses, 1):
                msg += f"{i}️⃣ {r}\n"
            return msg
        return "❌ هنوز جوابی ذخیره نشده.\nبا `جواب 1 متن` جواب ذخیره کن."
    
    def clear_responses(self) -> str:
        count = len(self.responses)
        user_count = len(self.replied_users)
        self.responses = []
        self.replied_users = {}
        return f"✅ {count} جواب و حافظه {user_count} کاربر پاک شد."
    
    def get_random_response(self) -> Optional[str]:
        if self.responses:
            return random.choice(self.responses)
        return None
    
    def has_user_replied(self, chat_id: int) -> bool:
        return self.replied_users.get(chat_id, False)
    
    async def mark_user_replied(self, chat_id: int):
        async with self._lock:
            self.replied_users[chat_id] = True
    
    def get_stats(self) -> str:
        return f"""📊 وضعیت منشی:
━━━━━━━━━━━━━━━━━━━━
🔹 وضعیت: {'روشن' if self.enabled else 'خاموش'}
🔹 جواب‌های ذخیره شده: {len(self.responses)}/5
🔹 کاربرانی که جواب گرفتن: {len(self.replied_users)}
━━━━━━━━━━━━━━━━━━━━"""
    
    def get_help(self) -> str:
        return """🤵 **راهنمای منشی موقت**

━━━━━━━━━━━━━━━━━━━━━━
📌 **دستورات:**
`منشی موقت روشن` - روشن کردن منشی
`منشی موقت خاموش` - خاموش کردن منشی
`جواب 1 متن` - ذخیره جواب شماره 1
`جواب 2 متن` - ذخیره جواب شماره 2
`جواب 3 متن` - ذخیره جواب شماره 3
`جواب 4 متن` - ذخیره جواب شماره 4
`جواب 5 متن` - ذخیره جواب شماره 5
`نمایش جوابها` - دیدن جواب‌های ذخیره شده
`پاک کردن جوابها` - حذف همه جواب‌ها

━━━━━━━━━━━━━━━━━━━━━━
💡 **نحوه کار:**
1️⃣ منشی رو روشن کن
2️⃣ چند جواب مختلف ذخیره کن (حداکثر 5 عدد)
3️⃣ هر کاربری بهت پیام بده، یک جواب تصادفی از جواب‌های ذخیره شده میگیره

⚠️ **توجه مهم:**
• هر کاربر فقط یک بار میتونه جواب بگیره (تکراری نیست)
• میتونی از دکمه‌های پایین برای ذخیره جواب استفاده کنی
• برای غیرفعال کردن موقت، منشی رو خاموش کن

━━━━━━━━━━━━━━━━━━━━━━
✅ **منشی موقت نسخه 1.0**
        """


# ========== کلاس مدیریت گزارش ==========

class ReportConfig:
    """مدیریت تنظیمات گزارش‌گیری"""
    
    def __init__(self, user_id: int, config_file: str = REPORT_CONFIG_FILE):
        self.user_id = user_id
        self.config_file = config_file
        self.report_group_id = GROUP_ID
        self.auto_save_media = True
        self.report_deleted_media = True
        self.report_edited_messages = True
        self.report_ttl_media = True
        self.report_voice_messages = True
        self.report_video_messages = True
        self.report_photo_messages = True
        self.report_document_messages = True
        self._load_config()
    
    def _load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_settings = data.get(str(self.user_id), {})
                    self.report_group_id = user_settings.get('report_group_id', GROUP_ID)
                    self.auto_save_media = user_settings.get('auto_save_media', True)
                    self.report_deleted_media = user_settings.get('report_deleted_media', True)
                    self.report_edited_messages = user_settings.get('report_edited_messages', True)
                    self.report_ttl_media = user_settings.get('report_ttl_media', True)
                    self.report_voice_messages = user_settings.get('report_voice_messages', True)
                    self.report_video_messages = user_settings.get('report_video_messages', True)
                    self.report_photo_messages = user_settings.get('report_photo_messages', True)
                    self.report_document_messages = user_settings.get('report_document_messages', True)
                logger.info(f"تنظیمات گزارش برای کاربر {self.user_id} لود شد")
        except Exception as e:
            logger.error(f"خطا در بارگذاری تنظیمات: {e}")
    
    def _save_config(self):
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data[str(self.user_id)] = {
                'report_group_id': self.report_group_id,
                'auto_save_media': self.auto_save_media,
                'report_deleted_media': self.report_deleted_media,
                'report_edited_messages': self.report_edited_messages,
                'report_ttl_media': self.report_ttl_media,
                'report_voice_messages': self.report_voice_messages,
                'report_video_messages': self.report_video_messages,
                'report_photo_messages': self.report_photo_messages,
                'report_document_messages': self.report_document_messages,
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"خطا در ذخیره تنظیمات: {e}")
    
    def set_report_group(self, group_id: int) -> str:
        self.report_group_id = group_id
        self._save_config()
        return f"✅ گروه گزارش به {group_id} تغییر کرد"
    
    def toggle_auto_save(self) -> str:
        self.auto_save_media = not self.auto_save_media
        self._save_config()
        status = "فعال" if self.auto_save_media else "غیرفعال"
        return f"✅ ذخیره خودکار رسانه‌ها {status} شد"
    
    def get_report_group(self) -> int:
        return self.report_group_id


# ========== کلاس اصلی SelfBotManager ==========

class SelfBotManager:
    """مدیریت اصلی سلف‌بات"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client: Optional[TelegramClient] = None
        self.running = False
        self.my_id = None
        self.BASE_NAME = None
        self.ORIGINAL_NAME = None
        self.spam_tasks: Dict[int, asyncio.Task] = {}
        self.spam_counters: Dict[str, List[float]] = {}
        self.spam_counter_lock = asyncio.Lock()
        self.mode = 'all'  # all, pv, off
        self.current_chat_id = None
        self.active_actions: Dict[int, str] = {}
        self.action_tasks: Dict[int, asyncio.Task] = {}
        self.translate_mode = {
            "english": False, "arabic": False, "hebrew": False,
            "russian": False, "turkish": False, "german": False,
            "french": False, "spanish": False
        }
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
        self.temp_assistant = TempAssistant(user_id)
        self.report_config = ReportConfig(user_id)
        self.adding_spam = False
        self.media_cache: Dict[int, dict] = {}
        self.msg_cache: Dict[tuple, str] = {}
        self._reconnect_task: Optional[asyncio.Task] = None
    
    async def start(self, session_file: str) -> bool:
        """شروع سلف‌بات"""
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
                connection_retries=10,
                retry_delay=3,
                timeout=60,
                receive_updates=True,
                auto_reconnect=True
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
            self.translate_mode = {
                "english": settings.get('translate_english', False),
                "arabic": settings.get('translate_arabic', False),
                "hebrew": settings.get('translate_hebrew', False),
                "russian": settings.get('translate_russian', False),
                "turkish": settings.get('translate_turkish', False),
                "german": settings.get('translate_german', False),
                "french": settings.get('translate_french', False),
                "spanish": settings.get('translate_spanish', False),
            }
            self.panel_mode = settings.get('panel_mode', True)
            self.time_font_indices = settings.get('time_font_indices', 'all')
            
            if not self._handlers_set:
                self._setup_handlers()
                self._handlers_set = True
                logger.info(f"هندلرها برای کاربر {self.user_id} تنظیم شدند")
            
            asyncio.create_task(self._update_profile_task())
            asyncio.create_task(self._keep_alive_task())
            
            self.running = True
            self.connection_attempts = 0
            logger.info(f"✅ سلف‌بات برای کاربر {self.user_id} با موفقیت شروع شد")
            return True
            
        except FloodWaitError as e:
            logger.error(f"FloodWait در شروع سلف‌بات: {e.seconds} ثانیه")
            await asyncio.sleep(e.seconds)
            return await self.start(session_file)
        except Exception as e:
            logger.error(f"خطا در شروع سلف‌بات برای کاربر {self.user_id}: {str(e)}")
            
            if self.connection_attempts < self.max_attempts:
                logger.info(f"تلاش مجدد برای کاربر {self.user_id} - {self.connection_attempts + 1}")
                await asyncio.sleep(5)
                return await self.start(session_file)
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            
            return False
    
    async def stop(self):
        """توقف سلف‌بات"""
        try:
            settings = db.get_selfbot_settings(self.user_id)
            settings['panel_mode'] = self.panel_mode
            db.update_selfbot_setting(self.user_id, settings)
            
            if self.client:
                for task in self.spam_tasks.values():
                    task.cancel()
                self.spam_tasks.clear()
                
                for task in self.action_tasks.values():
                    task.cancel()
                self.action_tasks.clear()
                
                if self._reconnect_task:
                    self._reconnect_task.cancel()
                
                await self.client.disconnect()
                self.client = None
            
            self.running = False
            logger.info(f"✅ سلف‌بات برای کاربر {self.user_id} متوقف شد")
        except Exception as e:
            logger.error(f"خطا در توقف سلف‌بات برای کاربر {self.user_id}: {e}")
    
    async def _keep_alive_task(self):
        """وظیفه نگهداری اتصال"""
        while self.running:
            try:
                if self.client and self.client.is_connected():
                    await self.client.get_me()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"خطا در keep_alive برای کاربر {self.user_id}: {e}")
                if "disconnect" in str(e).lower() or "Connection" in str(e):
                    logger.info(f"اتصال قطع شد، تلاش برای reconnect...")
                    user_data = db.get_user(str(self.user_id))
                    if user_data and user_data.get('session_file'):
                        await self.stop()
                        await asyncio.sleep(5)
                        await self.start(user_data['session_file'])

# ادامه در بخش 3 از 8...
# ========== بخش 3 - ادامه کد ==========

    def _setup_handlers(self):
        """تنظیم هندلرهای رویداد"""
        try:
            @self.client.on(events.NewMessage(incoming=True))
            async def handle_new_message(event):
                await self._handle_new_message(event)
            
            @self.client.on(events.MessageEdited(incoming=True))
            async def handle_edited_message(event):
                await self._handle_edited_message(event)
            
            @self.client.on(events.MessageDeleted)
            async def handle_deleted_message(event):
                await self._handle_deleted_message(event)
            
            @self.client.on(events.NewMessage(pattern=r'^(?:شروع|تایم روشن|تایمر پرچم روشن|تایم خاموش|قلب|ماه|اطلاعات|دانلود پروفایل|تاریخ کامل|فعال اتوسین|غیرفعال اتوسین|حذف کامل|ست پروف|ست بیو|حذف ست پروف|حذف ست بیو|بولد روشن|بولد خاموش|زیرخط روشن|زیرخط خاموش|خط خورده روشن|خط خورده خاموش|نقل قول روشن|نقل قول خاموش|اسپویلر روشن|اسپویلر خاموش|کج روشن|کج خاموش|کد روشن|کد خاموش|پیش روشن|پیش خاموش|بلاک|پیوی ۱|پیوی ۲|پیوی ۳|پیوی ۴|خاموش پیوی|گروه ۱|گروه ۲|گروه ۳|گروه ۴|خاموش گروه|درباره|من کی ام|قفل پیوی همه|باز پی همه|قفل لینک روشن|قفل لینک خاموش|قفل عکس روشن|قفل عکس خاموش|قفل ویدیو روشن|قفل ویدیو خاموش|قفل استیکر روشن|قفل استیکر خاموش|قفل گیف روشن|قفل گیف خاموش|قفل ویس روشن|قفل ویس خاموش|قفل فایل روشن|قفل فایل خاموش|قفل موزیک روشن|قفل موزیک خاموش|قفل ویدیو نوت روشن|قفل ویدیو نوت خاموش|قفل کانتکت روشن|قفل کانتکت خاموش|قفل لوکیشن روشن|قفل لوکیشن خاموش|قفل ایموجی روشن|قفل ایموجی خاموش|قفل متن روشن|قفل متن خاموش|قفل فوروارد روشن|قفل فوروارد خاموش|تنظیم گزارش|گروه گزارش|کانال‌ها|حذف کانال|تست کانال|لیست دشمن|پاک کردن اسپم|لیست اسپم|تغییر اسم|تغییر بیو|تغییر پروفایل|پروف|اضافه اسپم|اتمام اسپم|فیلتر روشن|فیلتر خاموش|لیست فیلتر|اسپم روشن|اسپم خاموش|پینگ|سرچ|خروج سرچ|وضعیت|قلب پیشرفته|عشق|سنتت|هک|حذف ریکت|منشی موقت روشن|منشی موقت خاموش|نمایش جوابها|پاک کردن جوابها|همه جا|فقط اینجا|خاموش|اینلاین|اکشن|تاس|دارت|بسکتبال|فوتبال|انگلیسی روشن|انگلیسی خاموش|عربی روشن|عربی خاموش|عبری روشن|عبری خاموش|روسی روشن|روسی خاموش|ترکی روشن|ترکی خاموش)(?:\s*$|\s+(.+)$)|^حذف\s+(\d+)$|^دشمن\s*(@\w+|-\d+|\d+)?$|^دوست\s*(@\w+|-\d+|\d+)?$|^قفل پیوی\s*(@\w+|-\d+|\d+)?$|^باز پی\s*(@\w+|-\d+|\d+)?$|^اسپم\s+(\d+)\s+(.+)$|^ریکت\s*([\U0001F300-\U0001F9FF]+)?$|^کامنت\s+(.+)$|^حذف اسپم\s+(\d+)$|^تایم\s+([\d\.]+)$|^\.فیلتر\s+(.+)$|^حذف فیلتر\s+(.+)$|^\.پنل$|^پنل$|^/panel$|^\.اهنگ\s+(.+)$|^تنظیم اسپم\s+(\d+)\s+(\d+)$|^جواب\s+(\d+)\s+(.+)$'))
            async def handle_commands(event):
                await self._handle_commands(event)
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def handle_outgoing_message(event):
                await self._handle_outgoing_message(event)
            
            @self.client.on(events.NewMessage())
            async def auto_comment_handler(event):
                await self._handle_auto_comment(event)
            
            @self.client.on(events.NewMessage(incoming=True))
            async def temp_assistant_reply(event):
                await self._handle_temp_assistant_reply(event)
                
        except Exception as e:
            logger.error(f"خطا در تنظیم هندلرها برای کاربر {self.user_id}: {e}")
    
    async def _handle_temp_assistant_reply(self, event):
        """پاسخ منشی موقت به پیام‌های دریافتی"""
        if event.out:
            return
        if not event.is_private:
            return
        if not self.temp_assistant.is_enabled():
            return
        if self.temp_assistant.has_user_replied(event.chat_id):
            return
        
        response = self.temp_assistant.get_random_response()
        if not response:
            return
        
        await self.temp_assistant.mark_user_replied(event.chat_id)
        
        try:
            await event.reply(response)
            sender = await event.get_sender()
            sender_name = sender.first_name or "کاربر"
            logger.info(f"✅ منشی موقت - جواب به {sender_name}: {response[:50]}")
        except Exception as e:
            logger.error(f"خطا در ارسال پاسخ منشی موقت: {e}")
    
    async def _handle_temp_assistant_commands(self, event, text: str) -> bool:
        """پردازش دستورات منشی موقت"""
        if text == 'منشی موقت روشن':
            await event.edit(self.temp_assistant.enable())
            return True
        elif text == 'منشی موقت خاموش':
            await event.edit(self.temp_assistant.disable())
            return True
        elif text == 'نمایش جوابها':
            await event.edit(self.temp_assistant.get_responses_list())
            return True
        elif text == 'پاک کردن جوابها':
            await event.edit(self.temp_assistant.clear_responses())
            return True
        elif text.startswith('جواب '):
            match = re.match(r'جواب \d+ (.+)', text)
            if match:
                response_text = match.group(1)
                await event.edit(self.temp_assistant.add_response(response_text))
                return True
        return False
    
    async def _force_dice(self, chat_id: int, emoji: str, target: int):
        """اجبار به زدن تاس با عدد مشخص"""
        while True:
            try:
                msg = await self.client.send_message(chat_id, file=InputMediaDice(emoji))
                if msg.media.value == target:
                    break
                await msg.delete()
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"خطا در تاس: {e}")
                break
    
    async def _handle_translate_commands(self, event):
        """پردازش دستورات ترجمه"""
        text = event.raw_text.strip()
        
        langs = {
            "انگلیسی": "english", "عربی": "arabic", "عبری": "hebrew",
            "روسی": "russian", "ترکی": "turkish", "آلمانی": "german",
            "فرانسوی": "french", "اسپانیایی": "spanish"
        }
        
        for persian, english in langs.items():
            if text.startswith(persian):
                parts = text.split()
                if len(parts) > 1:
                    cmd = parts[1]
                    if cmd in ["روشن", "خاموش"]:
                        self.translate_mode[english] = (cmd == "روشن")
                        status = "روشن" if self.translate_mode[english] else "خاموش"
                        await event.edit(f"✅ ترجمه {persian} {status} شد")
                        
                        # ذخیره در دیتابیس
                        db.update_selfbot_setting(self.user_id, f'translate_{english}', 1 if self.translate_mode[english] else 0)
                        return
        
        # بازی‌ها
        if text == "تاس ۱":
            await event.delete()
            await self._force_dice(event.chat_id, "🎲", 1)
        elif text == "تاس ۲":
            await event.delete()
            await self._force_dice(event.chat_id, "🎲", 2)
        elif text == "تاس ۳":
            await event.delete()
            await self._force_dice(event.chat_id, "🎲", 3)
        elif text == "تاس ۴":
            await event.delete()
            await self._force_dice(event.chat_id, "🎲", 4)
        elif text == "تاس ۵":
            await event.delete()
            await self._force_dice(event.chat_id, "🎲", 5)
        elif text == "تاس ۶":
            await event.delete()
            await self._force_dice(event.chat_id, "🎲", 6)
        elif text == "دارت":
            await event.delete()
            await self._force_dice(event.chat_id, "🎯", 6)
        elif text == "بسکتبال":
            await event.delete()
            await self._force_dice(event.chat_id, "🏀", 5)
        elif text == "فوتبال":
            await event.delete()
            await self._force_dice(event.chat_id, "⚽️", 5)
    
    async def _translate_text(self, text: str) -> str:
        """ترجمه خودکار متن"""
        try:
            from deep_translator import GoogleTranslator
            
            active_langs = [lang for lang, status in self.translate_mode.items() if status]
            if not active_langs:
                return text
            
            # استفاده از اولین زبان فعال
            target_lang = active_langs[0]
            lang_map = {
                "english": "en", "arabic": "ar", "hebrew": "he",
                "russian": "ru", "turkish": "tr", "german": "de",
                "french": "fr", "spanish": "es"
            }
            
            if target_lang in lang_map:
                translated = GoogleTranslator(source='auto', target=lang_map[target_lang]).translate(text)
                return translated
        except Exception as e:
            logger.error(f"خطا در ترجمه: {e}")
        return text
    
    async def _start_action(self, chat_id: int, action_name: str):
        """شروع اکشن در چت"""
        if action_name in action_types:
            action = action_types[action_name]
            
            if chat_id in self.action_tasks:
                self.action_tasks[chat_id].cancel()
            
            self.active_actions[chat_id] = action_name
            
            async def permanent_action():
                try:
                    while chat_id in self.active_actions:
                        await self.client(SetTypingRequest(chat_id, action))
                        await asyncio.sleep(5)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"خطا در اکشن {action_name}: {e}")
                finally:
                    if chat_id in self.active_actions:
                        del self.active_actions[chat_id]
                    if chat_id in self.action_tasks:
                        del self.action_tasks[chat_id]
            
            task = asyncio.create_task(permanent_action())
            self.action_tasks[chat_id] = task
            return True
        return False
    
    async def _stop_action(self, chat_id: int) -> Optional[str]:
        """توقف اکشن در چت"""
        if chat_id in self.action_tasks:
            self.action_tasks[chat_id].cancel()
            try:
                await self.client(SetTypingRequest(chat_id, SendMessageCancelAction()))
            except:
                pass
            
            if chat_id in self.active_actions:
                action_name = self.active_actions[chat_id]
                del self.active_actions[chat_id]
                del self.action_tasks[chat_id]
                return action_name
        return None
    
    async def _stop_all_actions(self) -> List[str]:
        """توقف همه اکشن‌ها"""
        stopped = []
        for chat_id in list(self.action_tasks.keys()):
            action_name = await self._stop_action(chat_id)
            if action_name:
                stopped.append(action_name)
        return stopped
    
    async def _handle_action_commands(self, event):
        """پردازش دستورات اکشن"""
        msg = event.text.strip()
        chat_id = event.chat_id
        
        if self.mode == 'pv' and chat_id != self.current_chat_id:
            return
        if self.mode == 'off':
            return
        
        await self._handle_translate_commands(event)
        
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
            stopped = await self._stop_all_actions()
            if stopped:
                await event.edit(f'✅ بات خاموش شد\n\n⏹️ اکشن‌های متوقف شده:\n{", ".join(stopped)}')
            else:
                await event.edit('✅ بات خاموش شد')
            return
        
        if msg.startswith('اکشن '):
            command = msg.replace('اکشن ', '').strip()
            
            if command == 'خاموش':
                if chat_id in self.active_actions:
                    action_name = await self._stop_action(chat_id)
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
                        await self._stop_action(chat_id)
                        await event.edit(f'⏹️ اکشن قبلی {old_action} خاموش شد\n✅ اکشن جدید {command} فعال شد')
                    else:
                        await event.edit(f'✅ اکشن {command} فعال شد')
                    
                    await self._start_action(chat_id, command)
                    await asyncio.sleep(3)
                    await event.delete()
                    return
                else:
                    available = "\n".join([f"• {name}" for name in action_types.keys()])
                    await event.edit(f'❌ اکشن "{command}" پشتیبانی نمی‌شود\n\n✅ اکشن‌های موجود:\n{available}')
                    return
        
        # حالت سرچ
        if msg == 'سرچ':
            self.search_mode = True
            await event.edit('🔍 حالت سرچ فعال شد.\n\nاکنون هر متنی که ارسال کنید در گوگل جستجو می‌شود.\nبرای خروج از حالت سرچ، دستور خروج سرچ را ارسال کنید.')
            return
        elif msg == 'خروج سرچ':
            self.search_mode = False
            self.last_search_results = []
            await event.edit('✅ حالت سرچ غیرفعال شد.')
            return
        
        # ترجمه خودکار
        if self.search_mode and msg:
            await self._handle_google_search(event, msg)
            return
        
        # ترجمه خودکار پیام‌ها
        translated = await self._translate_text(msg)
        if translated != msg:
            await event.edit(translated)
            return
    
    async def _handle_google_search(self, event, query: str):
        """جستجو در گوگل"""
        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_CSE_ID:
            await event.edit("❌ کلیدهای Google Search تنظیم نشده است")
            return
        
        try:
            await event.edit(f'🔍 در حال جستجو: {query}')
            
            async with aiohttp.ClientSession() as session:
                params = {
                    'key': GOOGLE_SEARCH_API_KEY,
                    'cx': GOOGLE_CSE_ID,
                    'q': query,
                    'num': 5,
                    'safe': 'active'
                }
                async with session.get(GOOGLE_SEARCH_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        
                        if 'items' in results and results['items']:
                            self.last_search_results = results['items']
                            message = f"🔍 نتایج جستجو برای: {query}\n\n"
                            for i, item in enumerate(results['items'][:5], 1):
                                title = item.get('title', 'بدون عنوان')
                                link = item.get('link', '')
                                snippet = item.get('snippet', 'بدون توضیح')[:150]
                                message += f"{i}. {title}\n   {snippet}...\n   🔗 {link}\n\n"
                            
                            if len(message) > 4000:
                                chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                                for chunk in chunks:
                                    await event.respond(chunk)
                            else:
                                await event.edit(message)
                        else:
                            await event.edit(f'❌ هیچ نتیجه‌ای برای "{query}" پیدا نشد.')
                    else:
                        await event.edit(f'❌ خطا در جستجو. کد خطا: {resp.status}')
        except asyncio.TimeoutError:
            await event.edit('❌ زمان جستجو به پایان رسید')
        except Exception as e:
            logger.error(f"خطا در جستجوی گوگل: {e}")
            await event.edit(f'❌ خطا در جستجو: {str(e)[:100]}')
    
    async def _get_user_info(self, user_id: int) -> str:
        """دریافت اطلاعات کاربر"""
        try:
            entity = await self.client.get_entity(user_id)
            if entity.username:
                return f"@{entity.username} ({user_id})"
            elif entity.first_name:
                name = f"{entity.first_name} {entity.last_name or ''}".strip()
                return f"{name} ({user_id})"
            return f"کاربر {user_id}"
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات کاربر {user_id}: {e}")
            return f"کاربر ناشناس ({user_id})"
    
    async def _get_chat_title(self, chat_id: int) -> str:
        """دریافت عنوان چت"""
        try:
            entity = await self.client.get_entity(chat_id)
            if hasattr(entity, 'title'):
                return entity.title
            elif hasattr(entity, 'first_name'):
                return entity.first_name
            return f"چت {chat_id}"
        except:
            return f"چت {chat_id}"
    
    def _get_media_type(self, message) -> Optional[str]:
        """تشخیص نوع رسانه"""
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
        elif hasattr(message.media, 'contact'):
            return 'contact'
        elif hasattr(message.media, 'geo'):
            return 'location'
        return 'unknown'
    
    def _get_file_extension(self, media_type: str) -> str:
        """دریافت پسوند فایل بر اساس نوع"""
        extensions = {
            'photo': '.jpg', 'voice': '.ogg', 'video': '.mp4',
            'video_note': '.mp4', 'sticker': '.webp', 'gif': '.mp4',
            'image': '.jpg', 'file': '.bin', 'music': '.mp3',
            'contact': '.vcf', 'location': '.loc'
        }
        return extensions.get(media_type, '.bin')
    
    async def _save_media(self, message, media_type: str) -> Optional[str]:
        """ذخیره رسانه"""
        try:
            if not self.report_config.auto_save_media:
                return None
            
            chat_id = None
            if isinstance(message.peer_id, PeerUser):
                chat_id = message.peer_id.user_id
            elif isinstance(message.peer_id, PeerChannel):
                chat_id = message.peer_id.channel_id
            elif isinstance(message.peer_id, PeerChat):
                chat_id = message.peer_id.chat_id
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"{media_type}_{message.sender_id}_{message.id}_{timestamp}"
            file_extension = self._get_file_extension(media_type)
            file_path = os.path.join(REPORT_MEDIA_FOLDER, file_name + file_extension)
            
            downloaded_path = await self.client.download_media(message.media, file=file_path)
            
            if downloaded_path and os.path.exists(downloaded_path):
                self.media_cache[message.id] = {
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
    
    async def _send_report(self, report_text: str, media_path: str = None, caption: str = None) -> bool:
        """ارسال گزارش"""
        try:
            if self.report_config.report_group_id:
                if media_path and os.path.exists(media_path):
                    await self.client.send_file(
                        self.report_config.report_group_id,
                        media_path,
                        caption=caption or report_text[:1024]
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
    
    async def _handle_media_lock_delete(self, event) -> bool:
        """بررسی و حذف پیام‌های قفل شده"""
        if not event.message or event.message.out:
            return False
        
        target_id = event.sender_id
        if target_id == self.my_id:
            return False
        
        media_locks = db.get_media_locks(self.user_id, target_id)
        message = event.message
        message_text = message.text or ""
        
        lock_checks = [
            (media_locks.get('lock_link') and is_link_message(message_text), "لینک"),
            (media_locks.get('lock_text') and message_text, "متن"),
            (media_locks.get('lock_emoji') and is_emoji_message(message_text), "ایموجی"),
            (media_locks.get('lock_photo') and message.photo, "عکس"),
            (media_locks.get('lock_video') and message.video, "ویدیو"),
            (media_locks.get('lock_sticker') and message.sticker, "استیکر"),
            (media_locks.get('lock_gif') and message.gif, "گیف"),
            (media_locks.get('lock_voice') and message.voice, "ویس"),
            (media_locks.get('lock_file') and message.document and not message.sticker and not message.gif, "فایل"),
            (media_locks.get('lock_music') and message.audio, "موزیک"),
            (media_locks.get('lock_video_note') and message.video_note, "ویدیو نوت"),
            (media_locks.get('lock_contact') and message.contact, "کانتکت"),
            (media_locks.get('lock_location') and message.geo, "لوکیشن"),
            (media_locks.get('lock_forward') and message.fwd_from, "فوروارد"),
        ]
        
        for should_delete, lock_name in lock_checks:
            if should_delete:
                try:
                    await message.delete()
                    logger.info(f"{lock_name} از کاربر {target_id} حذف شد")
                    return True
                except Exception as e:
                    logger.error(f"خطا در حذف {lock_name}: {e}")
        
        return False
    
    async def _handle_new_message(self, event):
        """پردازش پیام جدید دریافتی"""
        if not self.my_id:
            return
        
        settings = db.get_selfbot_settings(self.user_id)
        
        # تعیین chat_id
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
        
        # قفل پیوی همگانی
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            if settings.get('pv_lock_all'):
                try:
                    await event.message.delete()
                    logger.info(f"پیوی همگانی: پیام از {event.sender_id} حذف شد")
                    return
                except:
                    pass
        
        # قفل پیوی اختصاصی
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            if db.is_pv_locked(self.user_id, event.sender_id):
                try:
                    await event.message.delete()
                    logger.info(f"پیوی اختصاصی: پیام از {event.sender_id} حذف شد")
                    return
                except:
                    pass
        
        # قفل رسانه
        if await self._handle_media_lock_delete(event):
            return
        
        # کش کردن پیام
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out and event.message.text:
            db.cache_message(self.user_id, chat_id, event.message.id, event.message.text)
        
        # فیلتر کلمات
        if not event.message.out and event.message.text:
            if db.get_filter_enabled(self.user_id):
                filter_words = db.get_filter_words(self.user_id)
                text_lower = event.message.text.lower()
                for word_info in filter_words:
                    if word_info['enabled'] and word_info['word'].lower() in text_lower:
                        try:
                            if word_info.get('action', 'delete') == 'delete':
                                await event.message.delete()
                            else:
                                await event.message.delete()
                            logger.info(f"پیام حاوی کلمه فیلتر شده '{word_info['word']}' از {event.sender_id} حذف شد")
                            return
                        except:
                            pass
        
        # ریکت خودکار
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
        
        # هوش مصنوعی در پیوی
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            
            ai_status = {
                1: settings.get('ai_1_pm', False),
                2: settings.get('ai_2_pm', False),
                3: settings.get('ai_3_pm', False),
                4: settings.get('ai_4_pm', False)
            }
            
            ai_active = False
            ai_type = None
            
            if event.message.text:
                for atype, active in ai_status.items():
                    if active:
                        ai_active = True
                        ai_type = atype
                        break
            
            if ai_active and ai_type:
                try:
                    await self.client(SetTypingRequest(event.chat_id, SendMessageTypingAction()))
                    response = await get_ai_response(event.message.text, ai_type, self.user_id)
                    
                    if response:
                        text, entities = await apply_text_style(response, settings.get('text_style'))
                        await event.reply(text, formatting_entities=entities)
                        logger.info(f"✅ پاسخ هوش مصنوعی {ai_type} به کاربر {sender_id} ارسال شد")
                    else:
                        await event.reply("❌ خطا در ارتباط با هوش مصنوعی. لطفاً بعداً تلاش کنید.")
                except Exception as e:
                    logger.error(f"خطا در پاسخ هوش مصنوعی: {e}")
        
        # حفاظت اسپم
        spam_settings = db.get_spam_settings(self.user_id)
        if spam_settings.get('spam_protection') and not event.message.out:
            sender_id = event.sender_id
            chat_key = f"{chat_id}_{sender_id}"
            
            async with self.spam_counter_lock:
                if chat_key not in self.spam_counters:
                    self.spam_counters[chat_key] = []
                
                now = time.time()
                mute_duration = spam_settings.get('mute_duration', 10)
                self.spam_counters[chat_key] = [t for t in self.spam_counters[chat_key] if now - t <= mute_duration]
                self.spam_counters[chat_key].append(now)
                
                spam_limit = spam_settings.get('spam_limit', 10)
                if len(self.spam_counters[chat_key]) > spam_limit:
                    try:
                        await event.message.delete()
                        logger.info(f"پیام اسپم از کاربر {sender_id} در {chat_id} حذف شد (ارسال بیش از {spam_limit} پیام در {mute_duration} ثانیه)")
                    except:
                        pass
        
        # ذخیره اطلاعات کاربر
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            try:
                sender = await event.get_sender()
                if sender:
                    db.update_user_memory(
                        sender_id=sender.id,
                        username=sender.username,
                        first_name=sender.first_name or "",
                        last_name=sender.last_name or "",
                        chat_id=chat_id
                    )
            except Exception as e:
                logger.error(f"خطا در ذخیره اطلاعات کاربر: {e}")

# ادامه در بخش 4 از 8...
# ========== بخش 5 - ادامه کد ==========

    async def _handle_commands(self, event):
        """پردازش دستورات متنی"""
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
        
        # دستورات منشی موقت
        if await self._handle_temp_assistant_commands(event, command_text):
            return
        
        # پنل اینلاین
        if command_text in ['.پنل', 'پنل', '/panel']:
            try:
                bot_username = BOT_USERNAME.replace('@', '')
                results = await self.client.inline_query(bot_username, '')
                if results and len(results) > 0:
                    await results[0].click(chat_id)
                    await event.delete()
                else:
                    await event.edit("❌ پنل یافت نشد. لطفاً مطمئن شوید ربات فعال است.")
            except Exception as e:
                await event.edit(f"❌ خطا در باز کردن پنل: {str(e)[:100]}")
            return
        
        # پخش آهنگ
        if command_text.startswith('.اهنگ '):
            song_name = command_text[6:].strip()
            if not song_name:
                await event.edit("❌ لطفاً نام آهنگ را وارد کنید\nمثال: .اهنگ مهدیار احمدی")
                return
            
            await event.edit(f"🎵 در حال جستجوی آهنگ: {song_name}...")
            
            try:
                bot_username = MUSIC_BOT.replace('@', '')
                results = await self.client.inline_query(bot_username, song_name)
                
                if results and len(results) > 0:
                    await results[0].click(chat_id)
                    await event.delete()
                    logger.info(f"✅ آهنگ {song_name} ارسال شد")
                else:
                    await event.edit(f"❌ آهنگی با نام '{song_name}' پیدا نشد")
            except Exception as e:
                await event.edit(f"❌ خطا در ارسال آهنگ: {str(e)[:100]}")
            return
        
        # تنظیم فونت تایم
        if command_text.startswith('تایم ') and not command_text.startswith('تایم روشن') and not command_text.startswith('تایم خاموش') and not command_text.startswith('تایمر'):
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
        
        # فیلتر کلمات
        if command_text.startswith('.فیلتر '):
            word = command_text[8:].strip()
            if word:
                db.add_filter_word(self.user_id, word)
                await event.edit(f"✅ کلمه {word} به لیست فیلتر اضافه شد")
            else:
                await event.edit("❌ لطفاً یک کلمه وارد کنید")
            return
        
        if command_text.startswith('حذف فیلتر '):
            word = command_text[11:].strip()
            if word:
                db.remove_filter_word(self.user_id, word)
                await event.edit(f"✅ کلمه {word} از لیست فیلتر حذف شد")
            else:
                await event.edit("❌ لطفاً یک کلمه وارد کنید")
            return
        
        if command_text == 'لیست فیلتر':
            filters = db.get_filter_words(self.user_id)
            if filters:
                message_text = "📜 لیست کلمات فیلتر شده:\n\n"
                for i, word_info in enumerate(filters, 1):
                    status = "فعال" if word_info['enabled'] else "غیرفعال"
                    message_text += f"{i}. {word_info['word']} - {status}\n"
                await event.edit(message_text)
            else:
                await event.edit("📭 لیست کلمات فیلتر خالی است")
            return
        
        if command_text == 'فیلتر روشن':
            db.set_filter_enabled(self.user_id, True)
            await event.edit("✅ فیلتر کلمات فعال شد")
            return
        
        if command_text == 'فیلتر خاموش':
            db.set_filter_enabled(self.user_id, False)
            await event.edit("✅ فیلتر کلمات غیرفعال شد")
            return
        
        # قفل لینک
        if command_text == 'قفل لینک روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_link', 1)
                await event.edit(f"✅ قفل لینک برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_link', 1)
                await event.edit("✅ قفل لینک برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل لینک خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_link', 0)
                await event.edit(f"✅ قفل لینک برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_link', 0)
                await event.edit("✅ قفل لینک برای همه کاربران غیرفعال شد")
            return
        
        # قفل عکس
        if command_text == 'قفل عکس روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_photo', 1)
                await event.edit(f"✅ قفل عکس برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_photo', 1)
                await event.edit("✅ قفل عکس برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل عکس خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_photo', 0)
                await event.edit(f"✅ قفل عکس برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_photo', 0)
                await event.edit("✅ قفل عکس برای همه کاربران غیرفعال شد")
            return
        
        # قفل ویدیو
        if command_text == 'قفل ویدیو روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_video', 1)
                await event.edit(f"✅ قفل ویدیو برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_video', 1)
                await event.edit("✅ قفل ویدیو برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل ویدیو خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_video', 0)
                await event.edit(f"✅ قفل ویدیو برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_video', 0)
                await event.edit("✅ قفل ویدیو برای همه کاربران غیرفعال شد")
            return
        
        # قفل استیکر
        if command_text == 'قفل استیکر روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_sticker', 1)
                await event.edit(f"✅ قفل استیکر برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_sticker', 1)
                await event.edit("✅ قفل استیکر برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل استیکر خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_sticker', 0)
                await event.edit(f"✅ قفل استیکر برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_sticker', 0)
                await event.edit("✅ قفل استیکر برای همه کاربران غیرفعال شد")
            return
        
        # قفل گیف
        if command_text == 'قفل گیف روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_gif', 1)
                await event.edit(f"✅ قفل گیف برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_gif', 1)
                await event.edit("✅ قفل گیف برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل گیف خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_gif', 0)
                await event.edit(f"✅ قفل گیف برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_gif', 0)
                await event.edit("✅ قفل گیف برای همه کاربران غیرفعال شد")
            return
        
        # قفل ویس
        if command_text == 'قفل ویس روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_voice', 1)
                await event.edit(f"✅ قفل ویس برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_voice', 1)
                await event.edit("✅ قفل ویس برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل ویس خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_voice', 0)
                await event.edit(f"✅ قفل ویس برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_voice', 0)
                await event.edit("✅ قفل ویس برای همه کاربران غیرفعال شد")
            return
        
        # قفل فایل
        if command_text == 'قفل فایل روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_file', 1)
                await event.edit(f"✅ قفل فایل برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_file', 1)
                await event.edit("✅ قفل فایل برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل فایل خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_file', 0)
                await event.edit(f"✅ قفل فایل برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_file', 0)
                await event.edit("✅ قفل فایل برای همه کاربران غیرفعال شد")
            return
        
        # قفل موزیک
        if command_text == 'قفل موزیک روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_music', 1)
                await event.edit(f"✅ قفل موزیک برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_music', 1)
                await event.edit("✅ قفل موزیک برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل موزیک خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_music', 0)
                await event.edit(f"✅ قفل موزیک برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_music', 0)
                await event.edit("✅ قفل موزیک برای همه کاربران غیرفعال شد")
            return
        
        # قفل ویدیو نوت
        if command_text == 'قفل ویدیو نوت روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_video_note', 1)
                await event.edit(f"✅ قفل ویدیو نوت برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_video_note', 1)
                await event.edit("✅ قفل ویدیو نوت برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل ویدیو نوت خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_video_note', 0)
                await event.edit(f"✅ قفل ویدیو نوت برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_video_note', 0)
                await event.edit("✅ قفل ویدیو نوت برای همه کاربران غیرفعال شد")
            return
        
        # قفل کانتکت
        if command_text == 'قفل کانتکت روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_contact', 1)
                await event.edit(f"✅ قفل کانتکت برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_contact', 1)
                await event.edit("✅ قفل کانتکت برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل کانتکت خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_contact', 0)
                await event.edit(f"✅ قفل کانتکت برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_contact', 0)
                await event.edit("✅ قفل کانتکت برای همه کاربران غیرفعال شد")
            return
        
        # قفل لوکیشن
        if command_text == 'قفل لوکیشن روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_location', 1)
                await event.edit(f"✅ قفل لوکیشن برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_location', 1)
                await event.edit("✅ قفل لوکیشن برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل لوکیشن خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_location', 0)
                await event.edit(f"✅ قفل لوکیشن برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_location', 0)
                await event.edit("✅ قفل لوکیشن برای همه کاربران غیرفعال شد")
            return
        
        # قفل ایموجی
        if command_text == 'قفل ایموجی روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_emoji', 1)
                await event.edit(f"✅ قفل ایموجی برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_emoji', 1)
                await event.edit("✅ قفل ایموجی برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل ایموجی خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_emoji', 0)
                await event.edit(f"✅ قفل ایموجی برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_emoji', 0)
                await event.edit("✅ قفل ایموجی برای همه کاربران غیرفعال شد")
            return
        
        # قفل متن
        if command_text == 'قفل متن روشن':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_text', 1)
                await event.edit(f"✅ قفل متن برای کاربر {target_id} فعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_text', 1)
                await event.edit("✅ قفل متن برای همه کاربران فعال شد")
            return
        
        if command_text == 'قفل متن خاموش':
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                target_id = reply_msg.sender_id
                db.set_media_lock(self.user_id, target_id, 'lock_text', 0)
                await event.edit(f"✅ قفل متن برای کاربر {target_id} غیرفعال شد")
            else:
                db.set_media_lock(self.user_id, 0, 'lock_text', 0)
                await event.edit("✅ قفل متن برای همه کاربران غیرفعال شد")
            return
        
        # وضعیت
        if command_text == 'وضعیت':
            settings = db.get_selfbot_settings(self.user_id)
            await event.edit(self._format_status_info(settings))
            return
        
        # حذف پیام
        match = re.match(r'^حذف\s+(\d+)$', command_text)
        if match:
            num = int(match.group(1))
            messages = []
            async for msg in self.client.iter_messages(event.chat_id, limit=num):
                if msg.sender_id == self.my_id:
                    messages.append(msg.id)
            if messages:
                await self.client.delete_messages(event.chat_id, messages)
                await event.edit(f"✅ {len(messages)} پیام حذف شد")
            else:
                await event.edit("⚠️ هیچ پیامی یافت نشد")
            return
        
        # حذف کامل
        if command_text == 'حذف کامل':
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
        
        # پینگ
        if command_text == 'پینگ':
            start = time.time()
            await event.edit("🏓 پینگ: ...")
            end = time.time()
            ping = round((end - start) * 1000, 2)
            await event.edit(f"🏓 پینگ: {ping} ms")
            return
        
        # استایل متن
        style_commands = ['بولد', 'زیرخط', 'خط خورده', 'نقل قول', 'اسپویلر', 'کج', 'کد', 'پیش']
        for style in style_commands:
            if command_text == f'{style} روشن':
                db.update_selfbot_setting(self.user_id, 'text_style', style)
                await event.edit(f"✅ استایل {style} فعال شد")
                return
            elif command_text == f'{style} خاموش':
                current = db.get_selfbot_settings(self.user_id).get('text_style')
                if current == style:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.edit(f"✅ استایل {style} غیرفعال شد")
                else:
                    await event.edit(f"⚠️ استایل {style} فعال نیست")
                return
        
        # انیمیشن قلب پیشرفته
        if command_text == 'قلب پیشرفته':
            await event.delete()
            try:
                msg = await self.client.send_message(event.chat_id, "❤️ شروع...")
                await advanced_heart_animation(msg)
            except Exception as e:
                logger.error(f"خطا: {e}")
            return
        
        # عشق
        if command_text == 'عشق':
            await event.delete()
            try:
                msg = await event.respond("💝 شروع...")
                await advanced_heart_animation(msg)
            except Exception as e:
                logger.error(f"خطا: {e}")
            return
        
        # سنتت
        if command_text == 'سنتت':
            await event.delete()
            try:
                msg = await event.respond("🕯️ در حال اجرا...")
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
        
        # هک
        if command_text == 'هک':
            await event.delete()
            try:
                msg = await event.respond("🔍 در حال هک...")
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
        
        # شروع
        if command_text == 'شروع':
            await event.delete()
            try:
                await event.respond("🌟 سلف‌بات شروع شد")
            except:
                pass
            return
        
        # تایم روشن
        if command_text == 'تایم روشن':
            db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
            await self._update_profile_name()
            await event.delete()
            return
        
        # تایمر پرچم روشن
        if command_text == "تایمر پرچم روشن":
            db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 1)
            await self._update_profile_name()
            await event.delete()
            return
        
        # تایم خاموش
        if command_text == "تایم خاموش":
            db.update_selfbot_setting(self.user_id, 'time_enabled', 0)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
            await self._restore_profile_name()
            await event.delete()
            return
        
        # لیست دشمن
        if command_text == 'لیست دشمن':
            await self._handle_list_enemies_command(event)
            return
        
        # لیست اسپم
        if command_text == 'لیست اسپم':
            await self._handle_list_spam_command(event)
            return
        
        # پاک کردن اسپم
        if command_text == 'پاک کردن اسپم':
            await self._handle_clear_spam_command(event)
            return
        
        # حذف اسپم
        match = re.match(r'^حذف اسپم\s+(\d+)$', command_text)
        if match:
            await self._handle_delete_spam_command(event)
            return
        
        # اضافه اسپم
        if command_text == 'اضافه اسپم':
            await self._handle_add_spam_command(event)
            return
        
        # اتمام اسپم
        if command_text == 'اتمام اسپم':
            await self._handle_end_spam_command(event)
            return
        
        # تغییر اسم
        match = re.match(r'^تغییر اسم\s+(.+)$', event.text)
        if match:
            await self._handle_change_name_command(event)
            return
        
        # تغییر بیو
        match = re.match(r'^تغییر بیو\s+(.+)$', event.text)
        if match:
            await self._handle_change_bio_command(event)
            return
        
        # تغییر پروفایل
        if command_text in ['تغییر پروفایل', 'پروف']:
            await self._handle_change_profile_command(event)
            return
        
        # کامنت
        match = re.match(r'^کامنت\s+(.+)$', event.text)
        if match:
            await self._handle_comment_command(event)
            return
        
        # کانال‌ها
        if command_text == 'کانال‌ها':
            await self._handle_channels_command(event)
            return
        
        # حذف کانال
        if command_text == 'حذف کانال':
            await self._handle_delete_channel_command(event)
            return
        
        # تست کانال
        if command_text == 'تست کانال':
            await self._handle_test_channel_command(event)
            return
        
        # دشمن
        match = re.match(r'^دشمن\s*(@\w+|-\d+|\d+)?$', command_text)
        if match:
            await self._handle_enemy_command(event, 'add')
            return
        
        # دوست
        match = re.match(r'^دوست\s*(@\w+|-\d+|\d+)?$', command_text)
        if match:
            await self._handle_enemy_command(event, 'remove')
            return
        
        # قفل پیوی
        match = re.match(r'^قفل پیوی\s*(@\w+|-\d+|\d+)?$', command_text)
        if match:
            await self._handle_lock_pv_command(event, 'lock')
            return
        
        # باز پی
        match = re.match(r'^باز پی\s*(@\w+|-\d+|\d+)?$', command_text)
        if match:
            await self._handle_lock_pv_command(event, 'unlock')
            return
        
        # قفل پیوی همه
        if command_text == "قفل پیوی همه":
            await self._handle_lock_all_pv_command(event, True)
            return
        
        # باز پی همه
        if command_text == "باز پی همه":
            await self._handle_lock_all_pv_command(event, False)
            return
        
        # قلب
        if command_text == "قلب":
            await self._handle_heart_animation(event)
            return
        
        # ماه
        if command_text == "ماه":
            await self._handle_moon_animation(event)
            return
        
        # اطلاعات
        if command_text == "اطلاعات":
            await self._handle_info_command(event)
            return
        
        # دانلود پروفایل
        if command_text == "دانلود پروفایل":
            await self._handle_download_profile_command(event)
            return
        
        # ست پروف
        if command_text == "ست پروف":
            await self._handle_set_profile_command(event, 'photo')
            return
        
        # ست بیو
        if command_text == "ست بیو":
            await self._handle_set_profile_command(event, 'bio')
            return
        
        # حذف ست پروف
        if command_text == "حذف ست پروف":
            await self._handle_delete_profile_command(event, 'photo')
            return
        
        # حذف ست بیو
        if command_text == "حذف ست بیو":
            await self._handle_delete_profile_command(event, 'bio')
            return
        
        # تاریخ کامل
        if command_text == "تاریخ کامل":
            await self._handle_full_date_command(event)
            return
        
        # فعال اتوسین
        if command_text == "فعال اتوسین":
            await self._handle_autosend_command(event, True)
            return
        
        # غیرفعال اتوسین
        if command_text == "غیرفعال اتوسین":
            await self._handle_autosend_command(event, False)
            return
        
        # اسپم
        match = re.match(r'^اسپم\s+(\d+)\s+(.+)$', command_text)
        if match:
            await self._handle_spam_command(event)
            return
        
        # بلاک
        if command_text == "بلاک":
            await self._handle_block_command(event)
            return
        
        # ریکت
        match = re.match(r'^ریکت\s*([\U0001F300-\U0001F9FF]+)?$', command_text)
        if match:
            await self._handle_reaction_command(event, 'set')
            return
        
        # حذف ریکت
        if command_text == "حذف ریکت":
            await self._handle_reaction_command(event, 'remove')
            return
        
        # هوش مصنوعی پیوی
        if command_text in ['پیوی ۱', 'پیوی ۲', 'پیوی ۳', 'پیوی ۴', 'خاموش پیوی']:
            await self._handle_ai_command(event, 'pm')
            return
        
        # هوش مصنوعی گروه
        if command_text in ['گروه ۱', 'گروه ۲', 'گروه ۳', 'گروه ۴', 'خاموش گروه']:
            await self._handle_ai_command(event, 'group')
            return
        
        # درباره
        if command_text == 'درباره':
            await event.delete()
            return
        
        # من کی ام
        if command_text == 'من کی ام':
            await self._handle_whoami_command(event)
            return
        
        # تنظیم گزارش
        if command_text == "تنظیم گزارش":
            await self._handle_report_group_command(event, 'set')
            return
        
        # گروه گزارش
        if command_text == "گروه گزارش":
            await self._handle_report_group_command(event, 'get')
            return

# ادامه در بخش 6 از 8...
# ========== بخش 6 - ادامه کد ==========

    async def _handle_list_enemies_command(self, event):
        """نمایش لیست دشمنان"""
        try:
            enemies = db.get_enemies(self.user_id, 'pv')
            
            if enemies:
                message = "📋 لیست دشمنان:\n\n"
                for i, enemy_id in enumerate(enemies, 1):
                    try:
                        enemy = await self.client.get_entity(enemy_id)
                        enemy_name = enemy.first_name or f"کاربر {enemy_id}"
                        message += f"{i}. {enemy_name} ({enemy_id})\n"
                    except:
                        message += f"{i}. کاربر {enemy_id}\n"
                
                await event.edit(message)
            else:
                await event.edit("📭 لیست دشمنان خالی است")
        except Exception as e:
            logger.error(f"خطا در لیست دشمنان: {e}")
            await event.delete()
    
    async def _handle_list_spam_command(self, event):
        """نمایش لیست پیام‌های اسپم"""
        try:
            spam_messages = db.get_enemy_spam_messages(self.user_id)
            
            if spam_messages:
                message = "📜 لیست پیام‌های اسپم:\n\n"
                for i, spam_msg in enumerate(spam_messages, 1):
                    message += f"{i}. {spam_msg['text'][:100]}\n"
                
                message += f"\n📊 تعداد: {len(spam_messages)}\n"
                message += "🗑️ برای حذف: حذف اسپم [شماره]\n"
                message += "🧹 برای پاک کردن همه: پاک کردن اسپم"
                
                if len(message) > 4000:
                    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                    for chunk in chunks:
                        await event.respond(chunk)
                else:
                    await event.edit(message)
            else:
                await event.edit("📭 لیست پیام‌های اسپم خالی است")
        except Exception as e:
            logger.error(f"خطا در لیست اسپم: {e}")
            await event.delete()
    
    async def _handle_clear_spam_command(self, event):
        """پاک کردن همه پیام‌های اسپم"""
        try:
            db.clear_enemy_spam_messages(self.user_id)
            await event.edit("✅ لیست پیام‌های اسپم پاک شد")
        except Exception as e:
            logger.error(f"خطا در پاک کردن اسپم: {e}")
            await event.delete()
    
    async def _handle_delete_spam_command(self, event):
        """حذف یک پیام اسپم خاص"""
        try:
            match = re.match(r'^حذف اسپم\s+(\d+)$', event.text.lower())
            if not match:
                return
            message_id = int(match.group(1))
            
            spam_messages = db.get_enemy_spam_messages(self.user_id)
            
            if 1 <= message_id <= len(spam_messages):
                spam_msg = spam_messages[message_id - 1]
                db.delete_enemy_spam_message(self.user_id, spam_msg['id'])
                await event.edit(f"✅ پیام شماره {message_id} حذف شد")
            else:
                await event.edit(f"⚠️ پیام شماره {message_id} وجود ندارد")
        except Exception as e:
            logger.error(f"خطا در حذف اسپم: {e}")
            await event.delete()
    
    async def _handle_add_spam_command(self, event):
        """فعال کردن حالت اضافه کردن اسپم"""
        try:
            self.adding_spam = True
            await event.edit("📝 حالت اضافه کردن اسپم فعال شد\nبرای پایان: اتمام اسپم")
        except Exception as e:
            logger.error(f"خطا: {e}")
            await event.delete()
    
    async def _handle_end_spam_command(self, event):
        """غیرفعال کردن حالت اضافه کردن اسپم"""
        try:
            self.adding_spam = False
            await event.edit("✅ حالت اضافه کردن اسپم غیرفعال شد")
        except Exception as e:
            logger.error(f"خطا: {e}")
            await event.delete()
    
    async def _handle_change_name_command(self, event):
        """تغییر نام کاربری"""
        try:
            match = re.match(r'^تغییر اسم\s+(.+)$', event.text)
            if not match:
                return
            new_name = match.group(1).strip()
            
            current_name = db.get_current_name(self.user_id)
            if not current_name:
                db.set_current_name(self.user_id, self.BASE_NAME)
                current_name = self.BASE_NAME
            
            db.set_current_name(self.user_id, new_name)
            
            await self.client(UpdateProfileRequest(first_name=new_name))
            
            settings = db.get_selfbot_settings(self.user_id)
            if settings.get('time_enabled'):
                self.BASE_NAME = new_name
                await self._update_profile_name()
            else:
                self.BASE_NAME = new_name
            
            await event.edit(f"✅ نام به {new_name} تغییر کرد")
        except Exception as e:
            logger.error(f"خطا در تغییر نام: {e}")
            await event.delete()
    
    async def _handle_change_bio_command(self, event):
        """تغییر بیوگرافی"""
        try:
            match = re.match(r'^تغییر بیو\s+(.+)$', event.text)
            if not match:
                return
            new_bio = match.group(1).strip()
            
            await self.client(UpdateProfileRequest(about=new_bio))
            await event.edit(f"✅ بیو به {new_bio} تغییر کرد")
        except Exception as e:
            logger.error(f"خطا در تغییر بیو: {e}")
            await event.delete()
    
    async def _handle_change_profile_command(self, event):
        """تغییر عکس پروفایل"""
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
                        await event.edit("✅ عکس پروفایل تغییر کرد")
                    else:
                        await event.edit("⚠️ خطا در دانلود عکس")
                else:
                    await event.edit("⚠️ روی یک عکس ریپلای کنید")
            else:
                await event.edit("⚠️ روی عکس مورد نظر ریپلای کنید")
        except Exception as e:
            logger.error(f"خطا در تغییر پروفایل: {e}")
            await event.delete()
    
    async def _handle_comment_command(self, event):
        """تنظیم کامنت خودکار برای کانال"""
        try:
            comment_text = event.text[7:].strip()
            if not comment_text:
                await event.edit("⚠️ متن کامنت را وارد کنید")
                return
            
            chat = await event.get_chat()
            chat_type = "کانال" if hasattr(chat, 'broadcast') and chat.broadcast else "گروه"
            
            db.set_auto_comment(
                self.user_id,
                chat.id,
                comment_text,
                chat.title or "بدون عنوان",
                chat_type,
                getattr(chat, 'username', None)
            )
            
            await event.edit(f"✅ کامنت در {chat_type} '{chat.title}' تنظیم شد\n\nمتن: {comment_text[:100]}")
            logger.info(f"✅ کامنت در {chat_type}: {chat.title}")
        except Exception as e:
            logger.error(f"خطا در تنظیم کامنت: {e}")
            await event.delete()
    
    async def _handle_channels_command(self, event):
        """نمایش لیست کانال‌های تنظیم شده"""
        try:
            auto_comments = db.get_auto_comments(self.user_id)
            
            if auto_comments:
                msg = "📊 کانال‌های تنظیم شده:\n\n"
                for comment in auto_comments:
                    msg += f"• {comment['channel_title']} ({comment['channel_type']})\n"
                    msg += f"  آیدی: {comment['channel_id']}\n"
                    msg += f"  متن: {comment['comment_text'][:50]}...\n\n"
                
                if len(msg) > 4000:
                    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
                    for chunk in chunks:
                        await event.respond(chunk)
                else:
                    await event.edit(msg)
            else:
                await event.edit("📭 هیچ کانالی تنظیم نشده")
        except Exception as e:
            logger.error(f"خطا در نمایش کانال‌ها: {e}")
            await event.delete()
    
    async def _handle_delete_channel_command(self, event):
        """حذف کامنت خودکار یک کانال"""
        try:
            chat = await event.get_chat()
            channel_id = chat.id
            
            auto_comment = db.get_auto_comment(self.user_id, channel_id)
            
            if auto_comment:
                db.remove_auto_comment(self.user_id, channel_id)
                await event.edit(f"✅ تنظیمات {auto_comment['channel_title']} حذف شد")
            else:
                await event.edit("⚠️ این کانال تنظیم نشده است")
        except Exception as e:
            logger.error(f"خطا در حذف کانال: {e}")
            await event.delete()
    
    async def _handle_test_channel_command(self, event):
        """تست کانال برای کامنت خودکار"""
        try:
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                chat = await reply_msg.get_chat()
            else:
                chat = await event.get_chat()
            
            info = f"🔍 اطلاعات تست:\n\n"
            info += f"چت: {chat.title}\n"
            info += f"نوع: {'کانال' if hasattr(chat, 'broadcast') and chat.broadcast else 'گروه'}\n"
            info += f"آیدی: {chat.id}\n"
            
            auto_comment = db.get_auto_comment(self.user_id, chat.id)
            info += f"تنظیم شده: {'✅' if auto_comment else '❌'}\n"
            
            if auto_comment:
                info += f"متن: {auto_comment['comment_text'][:100]}...\n"
            
            await event.edit(info)
        except Exception as e:
            logger.error(f"خطا در تست کانال: {e}")
            await event.delete()
    
    async def _handle_enemy_command(self, event, action):
        """مدیریت دشمنان"""
        try:
            target_id = await get_target_user(event, self.client)
            if not target_id:
                await event.edit("⚠️ روی پیام کاربر ریپلای کنید یا کاربر را مشخص کنید")
                return
            
            if action == 'add':
                db.add_enemy(self.user_id, target_id, 'pv')
                await event.edit(f"✅ کاربر به لیست دشمنان اضافه شد")
                await self._spam_enemy(target_id)
            else:
                db.remove_enemy(self.user_id, target_id, 'pv')
                await event.edit(f"✅ کاربر از لیست دشمنان حذف شد")
                
                if target_id in self.spam_tasks:
                    self.spam_tasks[target_id].cancel()
                    del self.spam_tasks[target_id]
        except Exception as e:
            logger.error(f"خطا در مدیریت دشمن: {e}")
            await event.delete()
    
    async def _handle_lock_pv_command(self, event, action):
        """قفل/باز کردن پیوی کاربر"""
        try:
            target_id = await get_target_user(event, self.client)
            if not target_id:
                await event.edit("⚠️ روی پیام کاربر ریپلای کنید یا کاربر را مشخص کنید")
                return
            
            if action == 'lock':
                db.add_locked_pv(self.user_id, target_id)
                await event.edit(f"✅ قفل پیوی برای کاربر {target_id} فعال شد")
            else:
                db.remove_locked_pv(self.user_id, target_id)
                await event.edit(f"✅ قفل پیوی برای کاربر {target_id} غیرفعال شد")
        except Exception as e:
            logger.error(f"خطا در قفل پیوی: {e}")
            await event.delete()
    
    async def _handle_lock_all_pv_command(self, event, lock):
        """قفل/باز کردن همه پیوی‌ها"""
        try:
            db.update_selfbot_setting(self.user_id, 'pv_lock_all', 1 if lock else 0)
            
            if lock:
                await event.edit("✅ قفل پیوی همگانی فعال شد")
            else:
                await event.edit("✅ قفل پیوی همگانی غیرفعال شد")
        except Exception as e:
            logger.error(f"خطا در قفل همگانی: {e}")
            await event.delete()
    
    async def _handle_heart_animation(self, event):
        """انیمیشن قلب ساده"""
        try:
            await event.delete()
            message = await self.client.send_message(event.chat_id, HEARTS[0])
            for i in range(1, len(HEARTS) * 10):
                await asyncio.sleep(4)
                await self.client.edit_message(event.chat_id, message, HEARTS[i % len(HEARTS)])
        except Exception as e:
            logger.error(f"خطا در انیمیشن قلب: {e}")
    
    async def _handle_moon_animation(self, event):
        """انیمیشن ماه"""
        try:
            await event.delete()
            message = await self.client.send_message(event.chat_id, MOONS[0])
            for i in range(1, len(MOONS) * 5):
                await asyncio.sleep(3)
                await self.client.edit_message(event.chat_id, message, MOONS[i % len(MOONS)])
        except Exception as e:
            logger.error(f"خطا در انیمیشن ماه: {e}")
    
    async def _handle_info_command(self, event):
        """نمایش اطلاعات کاربر"""
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
            
            info_text = f"📋 اطلاعات کاربر:\n\n"
            info_text += f"👤 یوزرنیم: {username}\n"
            info_text += f"🆔 ID: {user_id}\n"
            info_text += f"📛 نام: {name}\n"
            info_text += f"📝 بیو: {bio}\n"
            info_text += f"📸 تعداد عکس: {photo_count}"
            
            if user.photo:
                try:
                    photo = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user_id}.jpg")
                    if photo:
                        await self.client.send_file(event.chat_id, photo, caption=info_text)
                        os.remove(photo)
                    else:
                        await event.edit(info_text)
                except:
                    await event.edit(info_text)
            else:
                await event.edit(info_text)
            
            await event.delete()
        except Exception as e:
            logger.error(f"خطا در اطلاعات کاربر: {e}")
            await event.delete()
    
    async def _handle_download_profile_command(self, event):
        """دانلود عکس پروفایل کاربر"""
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
                        await event.edit(f"⚠️ خطا در دانلود")
                except:
                    await event.edit(f"⚠️ خطا در دانلود")
            else:
                await event.edit(f"⚠️ عکس پروفایلی وجود ندارد")
            
            await event.delete()
        except Exception as e:
            logger.error(f"خطا در دانلود پروفایل: {e}")
            await event.delete()
    
    async def _handle_set_profile_command(self, event, type_):
        """ست کردن پروفایل از روی کاربر دیگر"""
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
                                await event.edit("✅ عکس پروفایل ست شد")
                                os.remove(photo_path)
                            except FloodWaitError as e:
                                await event.edit(f"⚠️ {e.seconds} ثانیه صبر کنید")
                            except Exception as e:
                                await event.edit(f"⚠️ خطا: {str(e)[:50]}")
                        else:
                            await event.edit("⚠️ خطا در دانلود")
                    else:
                        await event.edit("⚠️ این کاربر عکس پروفایل ندارد")
                else:
                    try:
                        full_user = await self.client(GetFullUserRequest(user.id))
                        bio = full_user.full_user.about or ""
                        await self.client(UpdateProfileRequest(about=bio))
                        await event.edit("✅ بیو ست شد")
                    except Exception as e:
                        await event.edit(f"⚠️ خطا: {str(e)[:50]}")
            else:
                await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
            
            await event.delete()
        except Exception as e:
            logger.error(f"خطا در ست پروفایل: {e}")
            await event.delete()
    
    async def _handle_delete_profile_command(self, event, type_):
        """حذف عکس یا بیو پروفایل"""
        try:
            if type_ == 'photo':
                me = await self.client.get_me()
                if me.photo:
                    try:
                        photos = await self.client.get_profile_photos(me.id, limit=1)
                        if photos:
                            await self.client(DeletePhotosRequest(id=[photos[0]]))
                        await event.edit("✅ عکس پروفایل حذف شد")
                    except FloodWaitError as e:
                        await event.edit(f"⚠️ {e.seconds} ثانیه صبر کنید")
                    except Exception as e:
                        await event.edit(f"⚠️ خطا: {str(e)[:50]}")
                else:
                    await event.edit("⚠️ عکس پروفایلی وجود ندارد")
            else:
                try:
                    await self.client(UpdateProfileRequest(about=""))
                    await event.edit("✅ بیو خالی شد")
                except Exception as e:
                    await event.edit(f"⚠️ خطا: {str(e)[:50]}")
            
            await event.delete()
        except Exception as e:
            logger.error(f"خطا در حذف پروفایل: {e}")
            await event.delete()
    
    async def _handle_full_date_command(self, event):
        """نمایش تاریخ کامل"""
        try:
            date_info = get_full_date_info()
            settings = db.get_selfbot_settings(self.user_id)
            text, entities = await apply_text_style(date_info, settings.get('text_style'))
            await self.client.send_message(event.chat_id, text, formatting_entities=entities)
            await event.delete()
        except Exception as e:
            logger.error(f"خطا در تاریخ کامل: {e}")
            await event.delete()
    
    async def _handle_autosend_command(self, event, enable):
        """فعال/غیرفعال کردن اتوسین"""
        try:
            db.update_selfbot_setting(self.user_id, 'autosend_mode', 1 if enable else 0)
            
            if enable:
                await event.edit("✅ اتوسین فعال شد")
            else:
                await event.edit("✅ اتوسین غیرفعال شد")
        except Exception as e:
            logger.error(f"خطا: {e}")
            await event.delete()
    
    async def _handle_spam_command(self, event):
        """ارسال پیام اسپم"""
        try:
            match = re.match(r'^اسپم\s+(\d+)\s+(.+)$', event.text.lower())
            if not match:
                return
            num = int(match.group(1))
            message = match.group(2)
            
            if num > 100:
                await event.edit("⚠️ حداکثر تعداد اسپم 100 است")
                return
            
            if event.is_reply:
                reply_message = await event.get_reply_message()
                if reply_message.text:
                    message = reply_message.text
            
            for i in range(num):
                settings = db.get_selfbot_settings(self.user_id)
                text, entities = await apply_text_style(message, settings.get('text_style'))
                await self.client.send_message(event.chat_id, text, formatting_entities=entities)
                await asyncio.sleep(0.05)
            
            await event.edit(f"✅ {num} پیام اسپم ارسال شد")
        except Exception as e:
            logger.error(f"خطا در اسپم: {e}")
            await event.delete()
    
    async def _handle_block_command(self, event):
        """بلاک کردن کاربر"""
        try:
            if isinstance(event.message.peer_id, PeerUser):
                target_id = event.message.peer_id.user_id
                await self.client(BlockRequest(id=target_id))
                await event.edit("✅ کاربر بلاک شد")
            else:
                target_id = await get_target_user(event, self.client)
                if target_id:
                    await self.client(BlockRequest(id=target_id))
                    await event.edit("✅ کاربر بلاک شد")
                else:
                    await event.edit("⚠️ کاربر هدف مشخص نشد")
        except Exception as e:
            logger.error(f"خطا در بلاک: {e}")
            await event.delete()
    
    async def _handle_reaction_command(self, event, action):
        """مدیریت ریکشن خودکار"""
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
                    await event.edit("⚠️ ایموجی وارد کنید")
                    return
                
                if emoji in ALLOWED_EMOJIS:
                    db.set_reaction(self.user_id, chat_id, target_id, emoji)
                    await event.edit(f"✅ ریکت {emoji} برای کاربر {target_id} تنظیم شد")
                else:
                    await event.edit(f"⚠️ ایموجی {emoji} مجاز نیست")
            else:
                if target_id:
                    db.remove_reaction(self.user_id, chat_id, target_id)
                    await event.edit(f"✅ ریکت برای کاربر {target_id} حذف شد")
                else:
                    await event.edit("⚠️ کاربر هدف مشخص نشد")
        except Exception as e:
            logger.error(f"خطا در ریکشن: {e}")
            await event.delete()
    
    async def _handle_ai_command(self, event, ai_type):
        """مدیریت هوش مصنوعی"""
        try:
            command_text = event.text.lower()
            settings = db.get_selfbot_settings(self.user_id)
            
            if ai_type == 'pm':
                # خاموش کردن همه هوش‌های پیوی
                db.update_selfbot_setting(self.user_id, 'ai_1_pm', 0)
                db.update_selfbot_setting(self.user_id, 'ai_2_pm', 0)
                db.update_selfbot_setting(self.user_id, 'ai_3_pm', 0)
                db.update_selfbot_setting(self.user_id, 'ai_4_pm', 0)
                
                if command_text == 'پیوی ۱':
                    db.update_selfbot_setting(self.user_id, 'ai_1_pm', 1)
                    message = '✅ هوش ۱ (Gemini) در پی‌وی روشن شد'
                elif command_text == 'پیوی ۲':
                    db.update_selfbot_setting(self.user_id, 'ai_2_pm', 1)
                    message = '✅ هوش ۲ (Paxsenix) در پی‌وی روشن شد'
                elif command_text == 'پیوی ۳':
                    db.update_selfbot_setting(self.user_id, 'ai_3_pm', 1)
                    message = '✅ هوش ۳ (DeepSeek) در پی‌وی روشن شد'
                elif command_text == 'پیوی ۴':
                    db.update_selfbot_setting(self.user_id, 'ai_4_pm', 1)
                    message = '✅ هوش ۴ (OpenAI) در پی‌وی روشن شد'
                else:
                    message = '✅ همه هوش‌ها در پی‌وی خاموش شدند'
            else:
                # خاموش کردن همه هوش‌های گروه
                db.update_selfbot_setting(self.user_id, 'ai_1_group', 0)
                db.update_selfbot_setting(self.user_id, 'ai_2_group', 0)
                db.update_selfbot_setting(self.user_id, 'ai_3_group', 0)
                db.update_selfbot_setting(self.user_id, 'ai_4_group', 0)
                
                if command_text == 'گروه ۱':
                    db.update_selfbot_setting(self.user_id, 'ai_1_group', 1)
                    message = '✅ هوش ۱ (Gemini) در گروه روشن شد'
                elif command_text == 'گروه ۲':
                    db.update_selfbot_setting(self.user_id, 'ai_2_group', 1)
                    message = '✅ هوش ۲ (Paxsenix) در گروه روشن شد'
                elif command_text == 'گروه ۳':
                    db.update_selfbot_setting(self.user_id, 'ai_3_group', 1)
                    message = '✅ هوش ۳ (DeepSeek) در گروه روشن شد'
                elif command_text == 'گروه ۴':
                    db.update_selfbot_setting(self.user_id, 'ai_4_group', 1)
                    message = '✅ هوش ۴ (OpenAI) در گروه روشن شد'
                else:
                    message = '✅ همه هوش‌ها در گروه خاموش شدند'
            
            await event.edit(message)
        except Exception as e:
            logger.error(f"خطا در هوش مصنوعی: {e}")
            await event.delete()
    
    async def _handle_whoami_command(self, event):
        """نمایش اطلاعات خود"""
        try:
            if isinstance(event.message.peer_id, PeerUser):
                user_id = event.sender_id
                user_name = db.get_user_name(user_id)
                
                info_text = f"👤 اطلاعات شما:\n"
                info_text += f"• نام: {user_name}\n"
                info_text += f"• آی‌دی: {user_id}\n"
                
                await event.edit(info_text)
        except Exception as e:
            logger.error(f"خطا در من کی ام: {e}")
            await event.delete()
    
    async def _handle_report_group_command(self, event, action):
        """مدیریت گروه گزارش"""
        try:
            if action == 'set':
                if isinstance(event.message.peer_id, (PeerChannel, PeerChat)):
                    chat_id = event.message.peer_id.channel_id if isinstance(event.message.peer_id, PeerChannel) else event.message.peer_id.chat_id
                    self.report_config.set_report_group(chat_id)
                    await event.edit(f"✅ گروه گزارش تنظیم شد\nآیدی: {chat_id}")
                else:
                    await event.edit("⚠️ این دستور فقط در گروه کار می‌کند")
            else:
                await event.edit(f"📍 گروه گزارش فعلی:\nآیدی: {self.report_config.report_group_id}")
        except Exception as e:
            logger.error(f"خطا در تنظیم گزارش: {e}")
            await event.delete()

# ادامه در بخش 7 از 8...
# ========== بخش 7 - ادامه کد ==========

# ========== توابع کیبورد اینلاین ==========

def get_main_panel_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد اصلی پنل"""
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
            InlineKeyboardButton("🤵 منشی موقت", callback_data=f"temp_assistant_menu_{user_id}")
        ],
        [
            InlineKeyboardButton("❌ بستن پنل", callback_data="close_panel")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_temp_assistant_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد منشی موقت"""
    keyboard = [
        [
            InlineKeyboardButton("✅ روشن", callback_data=f"exec_temp_on_{user_id}"),
            InlineKeyboardButton("❌ خاموش", callback_data=f"exec_temp_off_{user_id}")
        ],
        [
            InlineKeyboardButton("📋 نمایش جوابها", callback_data=f"exec_temp_show_{user_id}"),
            InlineKeyboardButton("🗑️ پاک کردن جوابها", callback_data=f"exec_temp_clear_{user_id}")
        ],
        [
            InlineKeyboardButton("➕ جواب 1 (سلام)", callback_data=f"exec_temp_add1_{user_id}"),
            InlineKeyboardButton("➕ جواب 2 (بفرمایید)", callback_data=f"exec_temp_add2_{user_id}"),
            InlineKeyboardButton("➕ جواب 3 (در خدمتم)", callback_data=f"exec_temp_add3_{user_id}")
        ],
        [
            InlineKeyboardButton("➕ جواب 4 (چشم)", callback_data=f"exec_temp_add4_{user_id}"),
            InlineKeyboardButton("➕ جواب 5 (باشه)", callback_data=f"exec_temp_add5_{user_id}")
        ],
        [
            InlineKeyboardButton("📊 وضعیت منشی", callback_data=f"exec_temp_status_{user_id}"),
            InlineKeyboardButton("📖 راهنما", callback_data=f"exec_temp_help_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_time_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد زمان و پروفایل"""
    keyboard = [
        [
            InlineKeyboardButton("🕐 تایم روشن", callback_data=f"exec_time_on_{user_id}"),
            InlineKeyboardButton("🏳️ تایمر پرچم", callback_data=f"exec_time_flag_{user_id}")
        ],
        [
            InlineKeyboardButton("🚫 تایم خاموش", callback_data=f"exec_time_off_{user_id}"),
            InlineKeyboardButton("📅 تاریخ کامل", callback_data=f"exec_full_date_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_animation_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد انیمیشن"""
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
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_user_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد مدیریت کاربران"""
    keyboard = [
        [
            InlineKeyboardButton("🥷 دشمن", callback_data=f"exec_enemy_{user_id}"),
            InlineKeyboardButton("🧸 دوست", callback_data=f"exec_friend_{user_id}")
        ],
        [
            InlineKeyboardButton("🔒 قفل پیوی", callback_data=f"exec_lock_pv_{user_id}"),
            InlineKeyboardButton("🔓 باز پی", callback_data=f"exec_unlock_pv_{user_id}")
        ],
        [
            InlineKeyboardButton("🔒 قفل پیوی همه", callback_data=f"exec_lock_all_{user_id}"),
            InlineKeyboardButton("🔓 باز پی همه", callback_data=f"exec_unlock_all_{user_id}"),
            InlineKeyboardButton("⛔ بلاک", callback_data=f"exec_block_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_lock_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد قفل رسانه"""
    keyboard = [
        [
            InlineKeyboardButton("🔗 قفل لینک", callback_data=f"exec_lock_link_{user_id}"),
            InlineKeyboardButton("📸 قفل عکس", callback_data=f"exec_lock_photo_{user_id}"),
            InlineKeyboardButton("🎥 قفل ویدیو", callback_data=f"exec_lock_video_{user_id}")
        ],
        [
            InlineKeyboardButton("🎨 قفل استیکر", callback_data=f"exec_lock_sticker_{user_id}"),
            InlineKeyboardButton("🎞️ قفل گیف", callback_data=f"exec_lock_gif_{user_id}"),
            InlineKeyboardButton("🎤 قفل ویس", callback_data=f"exec_lock_voice_{user_id}")
        ],
        [
            InlineKeyboardButton("📁 قفل فایل", callback_data=f"exec_lock_file_{user_id}"),
            InlineKeyboardButton("🎵 قفل موزیک", callback_data=f"exec_lock_music_{user_id}"),
            InlineKeyboardButton("📹 قفل ویدیو نوت", callback_data=f"exec_lock_video_note_{user_id}")
        ],
        [
            InlineKeyboardButton("📞 قفل کانتکت", callback_data=f"exec_lock_contact_{user_id}"),
            InlineKeyboardButton("📍 قفل لوکیشن", callback_data=f"exec_lock_location_{user_id}"),
            InlineKeyboardButton("😀 قفل ایموجی", callback_data=f"exec_lock_emoji_{user_id}")
        ],
        [
            InlineKeyboardButton("📝 قفل متن", callback_data=f"exec_lock_text_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_comment_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد کامنت خودکار"""
    keyboard = [
        [
            InlineKeyboardButton("💬 کامنت", callback_data=f"exec_comment_{user_id}"),
            InlineKeyboardButton("📊 کانال‌ها", callback_data=f"exec_channels_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ حذف کانال", callback_data=f"exec_delete_channel_{user_id}"),
            InlineKeyboardButton("🔍 تست کانال", callback_data=f"exec_test_channel_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_general_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد عمومی"""
    keyboard = [
        [
            InlineKeyboardButton("📊 وضعیت", callback_data=f"exec_status_{user_id}"),
            InlineKeyboardButton("ℹ️ درباره", callback_data=f"exec_about_{user_id}")
        ],
        [
            InlineKeyboardButton("⏱️ پینگ", callback_data=f"exec_ping_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_action_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد اکشن"""
    keyboard = [
        [
            InlineKeyboardButton("🎮 اکشن [نام]", callback_data=f"exec_action_{user_id}"),
            InlineKeyboardButton("⏹️ اکشن خاموش", callback_data=f"exec_action_off_{user_id}")
        ],
        [
            InlineKeyboardButton("📋 اکشن لیست", callback_data=f"exec_action_list_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_games_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد بازی‌ها"""
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
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_translate_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد ترجمه"""
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 انگلیسی", callback_data=f"exec_translate_en_{user_id}"),
            InlineKeyboardButton("🇸🇦 عربی", callback_data=f"exec_translate_ar_{user_id}")
        ],
        [
            InlineKeyboardButton("🇮🇱 عبری", callback_data=f"exec_translate_he_{user_id}"),
            InlineKeyboardButton("🇷🇺 روسی", callback_data=f"exec_translate_ru_{user_id}")
        ],
        [
            InlineKeyboardButton("🇹🇷 ترکی", callback_data=f"exec_translate_tr_{user_id}"),
            InlineKeyboardButton("🇩🇪 آلمانی", callback_data=f"exec_translate_de_{user_id}")
        ],
        [
            InlineKeyboardButton("🇫🇷 فرانسوی", callback_data=f"exec_translate_fr_{user_id}"),
            InlineKeyboardButton("🇪🇸 اسپانیایی", callback_data=f"exec_translate_es_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_google_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد گوگل و اهنگ"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 سرچ", callback_data=f"exec_search_on_{user_id}"),
            InlineKeyboardButton("❌ خروج جستجو", callback_data=f"exec_search_off_{user_id}")
        ],
        [
            InlineKeyboardButton("🎵 اهنگ", callback_data=f"exec_music_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_info_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد اطلاعاتی"""
    keyboard = [
        [
            InlineKeyboardButton("📋 اطلاعات", callback_data=f"exec_info_{user_id}"),
            InlineKeyboardButton("⬇️ دانلود پروفایل", callback_data=f"exec_download_profile_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_profile_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد پروفایل"""
    keyboard = [
        [
            InlineKeyboardButton("📸 ست پروف", callback_data=f"exec_set_profile_{user_id}"),
            InlineKeyboardButton("✏️ ست بیو", callback_data=f"exec_set_bio_{user_id}")
        ],
        [
            InlineKeyboardButton("🗑️ حذف ست پروف", callback_data=f"exec_delete_profile_{user_id}"),
            InlineKeyboardButton("🗑️ حذف ست بیو", callback_data=f"exec_delete_bio_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_style_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد استایل متن"""
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
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_message_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد مدیریت پیام"""
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
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reaction_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد ریکشن"""
    keyboard = [
        [
            InlineKeyboardButton("👍 ریکت", callback_data=f"exec_reaction_{user_id}"),
            InlineKeyboardButton("❌ حذف ریکت", callback_data=f"exec_reaction_off_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_spam_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد اسپم"""
    keyboard = [
        [
            InlineKeyboardButton("📩 اسپم", callback_data=f"exec_spam_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_change_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد تغییر پروفایل"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ تغییر اسم", callback_data=f"exec_change_name_{user_id}"),
            InlineKeyboardButton("✏️ تغییر بیو", callback_data=f"exec_change_bio_{user_id}")
        ],
        [
            InlineKeyboardButton("📸 تغییر پروفایل", callback_data=f"exec_change_profile_{user_id}"),
            InlineKeyboardButton("📸 پروف", callback_data=f"exec_change_profile_alt_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_enemy_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد مدیریت دشمنان"""
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
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_filter_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد فیلتر کلمات"""
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
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_protection_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد حفاظت اسپم"""
    keyboard = [
        [
            InlineKeyboardButton("🛡️ اسپم روشن", callback_data=f"exec_spam_protection_on_{user_id}"),
            InlineKeyboardButton("🛡️ اسپم خاموش", callback_data=f"exec_spam_protection_off_{user_id}")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیم اسپم", callback_data=f"exec_spam_settings_{user_id}"),
            InlineKeyboardButton("📊 وضعیت اسپم", callback_data=f"exec_spam_status_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_ai_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد هوش مصنوعی"""
    settings = db.get_selfbot_settings(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton(f"🟢 پیوی ۱ {'✅' if settings.get('ai_1_pm') else '❌'}", callback_data=f"exec_ai_pm_1_{user_id}"),
            InlineKeyboardButton(f"🔵 پیوی ۲ {'✅' if settings.get('ai_2_pm') else '❌'}", callback_data=f"exec_ai_pm_2_{user_id}"),
            InlineKeyboardButton(f"🟣 پیوی ۳ {'✅' if settings.get('ai_3_pm') else '❌'}", callback_data=f"exec_ai_pm_3_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🟡 پیوی ۴ {'✅' if settings.get('ai_4_pm') else '❌'}", callback_data=f"exec_ai_pm_4_{user_id}"),
            InlineKeyboardButton("⚫ خاموش پیوی", callback_data=f"exec_ai_pm_off_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🟢 گروه ۱ {'✅' if settings.get('ai_1_group') else '❌'}", callback_data=f"exec_ai_group_1_{user_id}"),
            InlineKeyboardButton(f"🔵 گروه ۲ {'✅' if settings.get('ai_2_group') else '❌'}", callback_data=f"exec_ai_group_2_{user_id}"),
            InlineKeyboardButton(f"🟣 گروه ۳ {'✅' if settings.get('ai_3_group') else '❌'}", callback_data=f"exec_ai_group_3_{user_id}")
        ],
        [
            InlineKeyboardButton(f"🟡 گروه ۴ {'✅' if settings.get('ai_4_group') else '❌'}", callback_data=f"exec_ai_group_4_{user_id}"),
            InlineKeyboardButton("⚫ خاموش گروه", callback_data=f"exec_ai_group_off_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_report_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد گزارش"""
    keyboard = [
        [
            InlineKeyboardButton("📍 تنظیم گزارش", callback_data=f"exec_set_report_{user_id}"),
            InlineKeyboardButton("ℹ️ گروه گزارش", callback_data=f"exec_show_report_{user_id}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== توابع اینلاین پنل ==========

async def inline_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل اینلاین"""
    query = update.inline_query
    if not query:
        return
    
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    # بررسی عضویت کاربر
    if not db.is_user_active(user_id_str):
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⛔ دسترسی محدود",
                description="شما عضو سرویس نیستید. برای عضویت /start را بزنید",
                input_message_content=InputTextMessageContent("⛔ شما به این پنل دسترسی ندارید\n\nبرای عضویت: /start")
            )
        ]
        await query.answer(results, cache_time=1, is_personal=True)
        return
    
    # به‌روزرسانی زمان آخرین فعالیت
    db.update_last_active(user_id_str)
    
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
                    description="مدیریت کاربران و سلف‌بات‌ها",
                    input_message_content=InputTextMessageContent("👑 پنل ادمین"),
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 درخواست‌ها", callback_data="admin_requests"),
                            InlineKeyboardButton("🔐 منتظر ورود", callback_data="admin_login")
                        ],
                        [
                            InlineKeyboardButton("✅ کاربران فعال", callback_data="admin_active"),
                            InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data="admin_selfbots")
                        ],
                        [
                            InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")
                        ],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
                    ])
                )
            )
    
    await query.answer(results, cache_time=1, is_personal=True)

# ادامه در بخش 8 از 8...
# ========== بخش 8 - ادامه و پایان کد ==========

# ========== توابع مدیریت ادمین ==========

async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل مدیریت ادمین"""
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
            InlineKeyboardButton("📋 درخواست‌ها", callback_data="admin_requests"),
            InlineKeyboardButton("🔐 منتظر ورود", callback_data="admin_login")
        ],
        [
            InlineKeyboardButton("✅ کاربران فعال", callback_data="admin_active"),
            InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data="admin_selfbots")
        ],
        [
            InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])
    
    await query.edit_message_text("👑 پنل مدیریت\n\nلطفاً انتخاب کنید:", reply_markup=keyboard)


async def admin_requests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش درخواست‌های عضویت"""
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
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("📋 هیچ درخواستی در انتظار نیست")


async def admin_login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش کاربران در مرحله ورود"""
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
    """نمایش کاربران فعال"""
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
            text += f"🤖 سلف‌بات: {'✅' if str(user['user_id']) in active_selfbots else '❌'}\n\n"
        await query.edit_message_text(text)
    else:
        await query.edit_message_text("✅ هیچ کاربر فعالی وجود ندارد")


async def admin_selfbots_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سلف‌بات‌های فعال"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    if active_selfbots:
        text = "🤖 سلف‌بات‌های فعال:\n\n"
        keyboard = []
        for uid, manager in list(active_selfbots.items())[:10]:
            user_data = db.get_user(uid)
            name = user_data['full_name'] if user_data else f"کاربر {uid}"
            text += f"👤 {name}\n🆔 {uid}\n\n"
            keyboard.append([
                InlineKeyboardButton(f"🛑 توقف {uid}", callback_data=f"stop_selfbot_{uid}"),
                InlineKeyboardButton(f"🔄 ریستارت {uid}", callback_data=f"restart_selfbot_{uid}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("🤖 هیچ سلف‌باتی در حال اجرا نیست")


async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی"""
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
    active_selfbots_count = len(active_selfbots)
    
    stats = f"""
📊 آمار کلی
━━━━━━━━━━━━━━━━━━━━
👥 کل کاربران: {total_users}
✅ کاربران فعال: {active_users}
📋 درخواست‌ها: {pending_requests}
🔐 منتظر ورود: {pending_login}
🤖 سلف‌بات فعال: {active_selfbots_count}

🕐 آخرین به‌روزرسانی: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━
    """
    await query.edit_message_text(stats)


async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید درخواست عضویت"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[1]
    
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
    except Exception as e:
        logger.error(f"خطا در ارسال پیام تأیید: {e}")
    
    await query.edit_message_text(f"✅ کاربر {target_id} تأیید شد")
    await query.message.delete()


async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد درخواست عضویت"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[1]
    
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
    except Exception as e:
        logger.error(f"خطا در ارسال پیام رد: {e}")
    
    await query.edit_message_text(f"❌ کاربر {target_id} رد شد")
    await query.message.delete()


async def stop_selfbot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """توقف سلف‌بات"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[2]
    
    if target_id in active_selfbots:
        await active_selfbots[target_id].stop()
        del active_selfbots[target_id]
        await query.answer(f"✅ سلف‌بات کاربر {target_id} متوقف شد", show_alert=True)
    else:
        await query.answer("❌ سلف‌بات فعال نیست", show_alert=True)


async def restart_selfbot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راه‌اندازی مجدد سلف‌بات"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return
    
    data = query.data
    target_id = data.split('_')[2]
    
    user_data = db.get_user(target_id)
    if not user_data or not user_data.get('self_active'):
        await query.answer("❌ کاربر فعال نیست", show_alert=True)
        return
    
    session_file = user_data.get('session_file')
    if not session_file or not os.path.exists(session_file):
        await query.answer("❌ فایل سشن یافت نشد", show_alert=True)
        return
    
    if target_id in active_selfbots:
        await active_selfbots[target_id].stop()
        del active_selfbots[target_id]
    
    manager = SelfBotManager(int(target_id))
    if await manager.start(session_file):
        active_selfbots[target_id] = manager
        await query.answer(f"✅ سلف‌بات کاربر {target_id} راه‌اندازی مجدد شد", show_alert=True)
    else:
        await query.answer("❌ خطا در راه‌اندازی مجدد", show_alert=True)


# ========== توابع اصلی ربات ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور start"""
    if not update.message:
        return
    
    user = update.effective_user
    user_id = str(user.id)
    
    full_name = user.full_name or "کاربر"
    username = user.username or ""
    db.add_user(user_id, full_name, username)
    
    user_data = db.get_user(user_id)
    
    if user_data and user_data.get('self_active') == 1:
        # بررسی انقضا
        expiration_date = user_data.get('expiration_date')
        if expiration_date:
            try:
                exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                if exp_date < datetime.now():
                    db.update_user(user_id, self_active=0)
                    await update.message.reply_text(
                        "⚠️ عضویت شما منقضی شده است!\n\n"
                        "لطفاً برای تمدید با ادمین تماس بگیرید.\n"
                        f"📅 تاریخ انقضا: {exp_date}"
                    )
                    return
            except:
                pass
        
        text = f"""
👋 سلام {full_name} عزیز!

✅ حساب شما فعال است.
• /panel - پنل مدیریت
• @{BOT_USERNAME} - پنل اینلاین
• .پنل - پنل در همین چت
• .اهنگ [نام آهنگ] - پخش آهنگ

⚠️ پنل فقط مخصوص شماست
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{user_id}")]
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel")])
        
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
        keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel")])
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور panel"""
    if not update.message:
        return
    
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    if not db.is_user_active(user_id_str):
        await update.message.reply_text("⛔ شما عضو سرویس نیستید یا عضویت شما منقضی شده است.\n\nبرای عضویت: /start")
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
        text="🌟 پنل مدیریت سلف‌بات\n\nبرای باز کردن پنل، روی دکمه کلیک کنید:\n\n⚠️ توجه: این پنل فقط مخصوص شماست",
        reply_markup=keyboard
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های دریافتی"""
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
        await update.message.reply_text("✖ درخواست شما رد شده است")
        return

    if user_data.get('self_active'):
        expiration_date = user_data.get('expiration_date')
        if expiration_date:
            try:
                exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                if exp_date < datetime.now():
                    db.update_user(user_id_str, self_active=0)
                    await update.message.reply_text(
                        "⚠️ عضویت شما منقضی شده است!\n\n"
                        "لطفاً برای تمدید با ادمین تماس بگیرید."
                    )
                    return
            except:
                pass
        
        if user_id_str not in active_selfbots:
            session_file = user_data.get('session_file')
            if session_file and os.path.exists(session_file):
                manager = SelfBotManager(user_id)
                if await manager.start(session_file):
                    active_selfbots[user_id_str] = manager
                    await update.message.reply_text("🚀 سلف‌بات فعال شد")
                else:
                    await update.message.reply_text("⚠️ خطا در شروع سلف‌بات")
            else:
                await update.message.reply_text("⚠️ فایل سشن یافت نشد. لطفاً مجدداً ثبت‌نام کنید.")
        else:
            await update.message.reply_text("✅ سلف‌بات در حال اجراست")
        return

    step = user_data.get('step')
    
    if step == 'get_phone':
        if not user_data.get('admin_approved'):
            await update.message.reply_text("⏳ درخواست شما تأیید نشده است")
            return
        
        db.update_user(user_id_str, phone=text, step='get_code')
        
        await update.message.reply_text(
            f"✅ شماره {text} ذخیره شد\n"
            "⏳ در حال ارسال کد..."
        )
        
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
            
            await update.message.reply_text(
                "✅ کد تأیید ارسال شد!\n\n"
                "📩 کد ۵ رقمی را وارد کنید:"
            )
            
            await client.disconnect()
            
        except FloodWaitError as e:
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
                          step=None,
                          last_active=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            await update.message.reply_text(
                f"🎉 عضویت کامل شد!\n\n"
                f"✅ اکانت فعال شد\n"
                f"📅 انقضا: {expiration_date}"
            )
            
            await client.disconnect()
            
            manager = SelfBotManager(user_id)
            if await manager.start(session_path):
                active_selfbots[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات فعال شد")
            
            admin_message = (
                f"✅ کاربر {user_data['full_name']} وارد شد\n"
                f"🆔 {user_id_str}\n"
                f"📞 {user_data['phone']}\n"
                f"🔑 API: {user_data.get('api_id', 'نامشخص')}"
            )
            
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
            
            db.update_user(user_id_str,
                          self_active=1,
                          session_file=session_path,
                          expiration_date=expiration_date,
                          step=None,
                          last_active=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            await update.message.reply_text(
                f"🎉 عضویت کامل شد!\n\n"
                f"✅ اکانت فعال شد\n"
                f"📅 انقضا: {expiration_date}"
            )
            
            await client.disconnect()
            
            manager = SelfBotManager(user_id)
            if await manager.start(session_path):
                active_selfbots[user_id_str] = manager
                await update.message.reply_text("🚀 سلف‌بات فعال شد")
            
            admin_message = (
                f"✅ کاربر {user_data['full_name']} وارد شد\n"
                f"🆔 {user_id_str}\n"
                f"📞 {user_data['phone']}\n"
                f"🔐 رمز: ✓\n"
                f"🔑 API: {user_data.get('api_id', 'نامشخص')}"
            )
            
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


# ========== تابع اصلی ==========

async def main():
    """تابع اصلی برنامه"""
    print("=" * 60)
    print("🤖 سیستم جامع عضویت و سلف‌بات")
    print(f"👑 ادمین: {ADMIN_ID}")
    print(f"📁 پوشه سشن‌ها: {SESSIONS_FOLDER}")
    print("=" * 60)
    
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
        
        expiration_date = user.get('expiration_date')
        if expiration_date:
            try:
                exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                if exp_date < datetime.now():
                    db.update_user(user_id_str, self_active=0)
                    print(f"  • کاربر {user_id_str}: عضویت منقضی شده ❌")
                    fail_count += 1
                    continue
            except:
                pass
        
        if session_file and os.path.exists(session_file):
            print(f"  • کاربر {user_id_str}...", end=" ")
            
            manager = SelfBotManager(int(user_id_str))
            if await manager.start(session_file):
                active_selfbots[user_id_str] = manager
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
            for user in db.get_active_users():
                exp_date_str = user.get('expiration_date')
                if exp_date_str:
                    try:
                        exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                        if exp_date < datetime.now():
                            db.update_user(user['user_id'], self_active=0)
                            if user['user_id'] in active_selfbots:
                                await active_selfbots[user['user_id']].stop()
                                del active_selfbots[user['user_id']]
                            print(f"⏰ کاربر {user['user_id']} عضویت منقضی شد و غیرفعال گردید")
                    except:
                        pass
    except (KeyboardInterrupt, SystemExit):
        logger.info("در حال توقف...")
    finally:
        for manager in active_selfbots.values():
            await manager.stop()
        
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش دکمه‌های اینلاین"""
    query = update.callback_query
    if not query:
        return
    
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    if data == "close_panel":
        await query.delete_message()
        return
    
    if data == "back_main":
        if not db.is_user_active(user_id_str):
            await query.edit_message_text("⛔ عضویت شما منقضی شده یا فعال نیست. لطفاً مجدداً ثبت‌نام کنید.")
            return
        await query.edit_message_text(
            "🌟 پنل مدیریت سلف‌بات\n\n⚠️ توجه: این پنل فقط مخصوص شماست",
            reply_markup=get_main_panel_keyboard(user_id)
        )
        return
    
    # دستورات ادمین
    if data.startswith('admin_') or data.startswith('approve_') or data.startswith('reject_') or data.startswith('stop_selfbot_') or data.startswith('restart_selfbot_'):
        if user_id != ADMIN_ID:
            await query.answer("⛔ دسترسی غیرمجاز", show_alert=True)
            return
    
    if data == "admin_panel":
        await admin_panel_handler(update, context)
        return
    elif data == "admin_requests":
        await admin_requests_handler(update, context)
        return
    elif data == "admin_login":
        await admin_login_handler(update, context)
        return
    elif data == "admin_active":
        await admin_active_handler(update, context)
        return
    elif data == "admin_selfbots":
        await admin_selfbots_handler(update, context)
        return
    elif data == "admin_stats":
        await admin_stats_handler(update, context)
        return
    elif data.startswith("approve_"):
        await approve_handler(update, context)
        return
    elif data.startswith("reject_"):
        await reject_handler(update, context)
        return
    elif data.startswith("stop_selfbot_"):
        await stop_selfbot_handler(update, context)
        return
    elif data.startswith("restart_selfbot_"):
        await restart_selfbot_handler(update, context)
        return
    elif data.startswith("membership_request_"):
        await membership_request_handler(update, context)
        return
    elif data.startswith("membership_status_"):
        await membership_status_handler(update, context)
        return
    
    # منوهای مختلف
    if not db.is_user_active(user_id_str):
        await query.edit_message_text("⛔ عضویت شما منقضی شده یا فعال نیست. لطفاً مجدداً ثبت‌نام کنید.")
        return
    
    parts = data.split('_')
    if len(parts) > 1:
        action = parts[0]
        
        menu_keyboards = {
            "time": ("🕐 دستورات زمان و پروفایل", get_time_menu_keyboard),
            "animation": ("❤️ انیمیشن‌ها", get_animation_menu_keyboard),
            "user": ("👥 مدیریت کاربران", get_user_menu_keyboard),
            "lock": ("🔒 قفل رسانه", get_lock_menu_keyboard),
            "comment": ("💬 کامنت خودکار", get_comment_menu_keyboard),
            "general": ("📋 دستورات عمومی", get_general_menu_keyboard),
            "action": ("🎮 اکشن‌ها", get_action_menu_keyboard),
            "games": ("🎲 بازی‌ها", get_games_menu_keyboard),
            "translate": ("🌐 ترجمه خودکار", get_translate_menu_keyboard),
            "google": ("🔍 گوگل و اهنگ", get_google_menu_keyboard),
            "info": ("ℹ️ دستورات اطلاعاتی", get_info_menu_keyboard),
            "profile": ("📸 مدیریت پروفایل", get_profile_menu_keyboard),
            "style": ("✍️ استایل متن", get_style_menu_keyboard),
            "message": ("📨 مدیریت پیام", get_message_menu_keyboard),
            "reaction": ("😊 ریکشن خودکار", get_reaction_menu_keyboard),
            "spam": ("📩 ارسال اسپم", get_spam_menu_keyboard),
            "change": ("✏️ تغییر پروفایل", get_change_menu_keyboard),
            "enemy": ("🥷 مدیریت دشمنان", get_enemy_menu_keyboard),
            "filter": ("🚫 فیلتر کلمات", get_filter_menu_keyboard),
            "protection": ("🛡️ حفاظت اسپم", get_protection_menu_keyboard),
            "ai": ("🤖 هوش مصنوعی", get_ai_menu_keyboard),
            "report": ("📊 گزارش", get_report_menu_keyboard),
            "temp_assistant": ("🤵 منشی موقت", get_temp_assistant_menu_keyboard)
        }
        
        if action in menu_keyboards and len(parts) > 1 and parts[1] == "menu":
            text, keyboard_func = menu_keyboards[action]
            await query.edit_message_text(text, reply_markup=keyboard_func(user_id))
            return


async def membership_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست عضویت"""
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
    
    await query.edit_message_text(
        "✅ درخواست عضویت شما ثبت شد!\n\n"
        "⏳ منتظر تأیید ادمین باشید"
    )


async def membership_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وضعیت عضویت"""
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


# ========== اجرای اصلی ==========

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
