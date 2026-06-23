import os, sqlite3, logging, asyncio, json, re, time, requests, random, uuid, threading, qrcode
from datetime import datetime, timedelta
from urllib.parse import quote
import pytz, jdatetime
from hijridate import Gregorian
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler
from telegram.request import HTTPXRequest
from telethon import TelegramClient, events, types
from telethon.tl.types import PeerUser, PeerChannel, PeerChat, MessageMediaPhoto, MessageMediaDocument, ReactionEmoji, MessageEntityBold, MessageEntityUnderline, MessageEntityStrike, MessageEntityBlockquote, MessageEntitySpoiler, MessageEntityItalic, MessageEntityCode, MessageEntityPre
from telethon.tl.functions.messages import SendReactionRequest, DeleteMessagesRequest, SetTypingRequest, ReadHistoryRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest, GetUserPhotosRequest
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins
from deep_translator import GoogleTranslator

# ========== وب سرور ==========
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return jsonify({"status": "running", "bot": "SelfBot", "version": "4.6.0"})
@flask_app.route('/health')
def health(): return jsonify({"status": "healthy"}), 200
def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 وب سرور روی پورت {port} در حال اجراست")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== تنظیمات ==========
os.environ['TZ'] = 'Asia/Tehran'
try: time.tzset()
except: pass

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

BOT_TOKEN = "8304449635:AAHTqMEke8e1z1ZeMdgkFJGD9gV8EWtmfVk"
ADMIN_ID = 6443963679
BOT_USERNAME = "Gap_5_bot"
MUSIC_BOT = "Gap_4_bot"

SESSIONS_FOLDER, MEDIA_FOLDER, REPORT_MEDIA_FOLDER = 'user_sessions', 'media_storage', 'reported_media'
for f in [SESSIONS_FOLDER, MEDIA_FOLDER, REPORT_MEDIA_FOLDER]:
    if not os.path.exists(f): os.makedirs(f)

GROUP_ID, REPORT_CONFIG_FILE = -1002817019483, "report_config.json"
BOT_VERSION, BOT_CREATOR = "4.6.0", "Self-Bot AI Assistant"

API_CONFIGS = [
    {"api_id": 22409632, "api_hash": "b74c1ee200ad9ced6315859e9bd4125a"},
    {"api_id": 28297221, "api_hash": "8d682eb5c41a9762ef73f9ebe06c4eff"},
    {"api_id": 28039994, "api_hash": "00877cdcd706564a4de6abf7f7d64349"},
    {"api_id": 29031463, "api_hash": "64f122a7094dbab7e32b911eae6589e9"},
    {"api_id": 12832882, "api_hash": "1953c708cb3c47ecba74dc618b209e22"},
    {"api_id": 26645489, "api_hash": "6a212d0a400c97264600b3f932de5c2f"},
]

ALLOWED_EMOJIS = ["🤯","🐳","😍","💩","👏","🍌","🤓","😢","🙉","🤩","🤝","👀","🌚","🗿","🤡","😐","👨‍💻","😭","🙈","❤","🙏","😴","💋","🥰","🤪","✍️","🥱","👻","🤣","🌭","😨","🍓","🔥","🖕","🤗","🤔","🤬","😁","🎄","🫡","⚡","🥴","😈","🏆","😇","🎃","☃️","🤮","👍","👎","😱","😖","🕊","💯","💔","🤨","❤️‍🔥","💘","😘","💊","🆒","🤷‍♂","🤷‍♀","🎅"]

classic_fonts = [
    "⊘𝟷ϩӠ4ƼϬ7𝟾९","𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡","𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗","𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵","⓿①❷③❹⑤❻⑦❽⑨",
    "₀₁₂₃₄₅₆₇₈₉","⁰¹²³⁴⁵⁶⁷⁸⁹","𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿","₀¹²³⁴⁵⁶₇₈₉","𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡","０１２３４５６７８９","₀₁₂₃₄₅₆₇₈₉","⁰¹²³⁴⁵⁶⁷⁸⁹","0123456789",
    "⓪①②③④⑤⑥⑦⑧⑨","⓿❶❷❸❹❺❻❼❽❾","🄀🄁🄂🄃🄄🄅🄆🄇🄈🄉","🄞🄟🄠🄡🄢🄣🄤🄥🄦🄧🄨","０１２３４５６７８９",
    "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗","𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿","𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵","𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫","０１２３４５６７８９",
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡","𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗","𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿","𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵",
    {'0':'0','1':'1','2':'2','3':'3','4':'4','5':'5','6':'6','7':'7','8':'8','9':'9',':':':'},
    {'0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓','6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗',':':':'},
    {'0':'𝟶','1':'𝟷','2':'𝟸','3':'𝟹','4':'𝟺','5':'𝟻','6':'𝟼','7':'𝟽','8':'𝟾','9':'𝟿',':':':'},
    {'0':'⓪','1':'①','2':'②','3':'③','4':'④','5':'⑤','6':'⑥','7':'⑦','8':'⑧','9':'⑨',':':':'},
    {'0':'🄋','1':'➊','2':'➋','3':'➌','4':'➍','5':'➎','6':'➏','7':'➐','8':'➑','9':'➒',':':':'},
    {'0':'⓿','1':'❶','2':'❷','3':'❸','4':'❹','5':'❺','6':'❻','7':'❼','8':'❽','9':'❾',':':':'},
    {'0':'𝟘','1':'𝟙','2':'𝟚','3':'𝟛','4':'𝟜','5':'𝟝','6':'𝟞','7':'𝟟','8':'𝟠','9':'𝟡',':':':'},
    {'0':'⒒','1':'⑴','2':'⑵','3':'⑶','4':'⑷','5':'⑸','6':'⑹','7':'⑺','8':'⑻','9':'⑼',':':':'},
    {'0':'０','1':'１','2':'２','3':'３','4':'４','5':'５','6':'６','7':'７','8':'８','9':'９',':':'：'},
    {'0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵',':':':'},
    {'0':'〇','1':'一','2':'二','3':'三','4':'四','5':'五','6':'六','7':'七','8':'八','9':'九',':':':'}
]

flags = ["🇦🇱","🇩🇿","🇦🇸","🇦🇩","🇦🇼","🇦🇼","🇦🇹","🇦🇿","🇧🇸","🇧🇭","🇧🇩","🇧🇧","🇧🇾","🇧🇪","🇧🇿","🇧🇯","🇧??","🇧🇴","🇧🇦","🇧🇼","🇧🇷","🇮🇴","🇻🇬","🇧🇳","🇧🇬","🇧🇫","🇧🇮","🇰🇭","🇨🇲","🇨🇦","🇨🇻","🇰🇾","🇨🇫","🇹🇩","🇨🇱","🇨🇴","🇰🇲","🇨🇬","🇨🇩","🇨🇽","🇨🇨","🇨🇴","🇰🇲","🇨🇬","🇨🇩","🇨🇰","🇨🇰","🕋"]

SPAM_MESSAGES = ["مادربزرگت کسده، کسشو تو قبرم اجاره داده", "پدربزرگت کونی، هنوزم تو گور کونشو به شیاطین می‌سپره", "کس ننت چنان بازه، کل شهر توش چادر زدن", "بابات کسکش، تو خیابون کونشو به موتورسوارا نشون می‌ده", "خواهرت فاحشه، تو کلوپ شبانه کسشو به حراج گذاشته", "برادرت کیرکش، تو کوچه کونشو به گربه‌ها می‌ده", "بچه‌هات جنده‌ان، تو پارک کسشونو به نیمکت‌ها می‌مالن", "عمه‌ت کس‌کش، کسشو تو حموم عمومی به همه نشون می‌ده", "خاله‌ت کونی، کیر هر غریبه‌ای رو تو کوچه می‌گیره", "جدت کسده، تو گور هم کسشو به فرشته‌ها اجاره می‌ده", "یا الله کیرم به قلب مادرت", "مادرتو میدم سگ بگاد", "با کیرم ناموستو پاره میکنم", "کیرمو حلقه میکنم دور گردن مادرت", "کسخارتو بتن ریزی کردم", "ننتو تو پورن هاب دیدم", "کیر و خایه هام به کل اجدادت", "فیلم ننت فروشی", "کسننت پدرتم", "میرم تو کسمادرت با بیل پارش میکنم", "کیر به ناموس گشادت", "خسته نشدی ننتو گاییدم؟", "کیرم شلاقی به ناموس جندت", "با ناموست تریسام زدم", "برج خلیفه تو مادرت", "دو پایی میرم تو کسمادرت", "داگی استایل ننتو گاییدم", "هندل زدم به کون مادرت گاییدمش", "یگام دو گام ننتو میگام", "کیرمو نکن تو کسمادرت", "کیر و خایم به توان دو تو کسمادرت", "قمه تو کسمادرت", "نود ننتو دارم مادرکسده", "با کله میرم تو کسمادرت", "دستام تو کسمادرت", "کیرم به استخون های ننت", "مادرتو حراج زدم مادرجنده", "بریم برای راند بعد با ننت", "کیرم به رحم نجس ننت", "کیرم به چش و چال ننت", "کیروم به فرق سر ناموست", "مادرجنده کیری ناموس", "با کون ننت ناگت درست کردم", "خایه هام به کسمادرت", "برج میلاد تو کسمادرت", "یخچال تو کسمادرت", "کیرم به پوزه مادرت", "مادرتو زدم به سیخ", "کسمادرت","کیر شتر تو ناموست","نودا ننت فروشی","خایه با پرزش تو ننت","چشای ننت تو کون خارت بره","ننتو ریدم","لال شو مادرجنده اوبنه ای","اوب از کون ننت میباره","ماهی تو کسمادرت","کیر هرچی خره تو کسمادرت","کیر رونالدو به کس خار و مادرت","مادرت زیر کیرم شهید شد","اسپنک زدم به کون مادر جندت","کیرم یهویی به مردع و زندت","کیر به فیس ننت","برو مادرجنده بی غیرت","استخون های مرده هات تو کسمادرت","اسپرمم تو نوامیست","مادرتو با پوزیشن های مختلف گاییدم","میز و صندلی تو کسمادرت","کیر به ناموس دلقکت","دمپایی تو کون ننت","دماغ پینوکیو رو گذاشتم جلو کص مادرت و بهش گفتم که بگه مادرت جنده نیست تا با دراز شدن دماغش کص مادرت پاره بشه","مادر فلش شده جوری با کیر میزنم ب فرق سر ننت ک حافظش بپره","كيرم شيك تو كس ننت","مادرتو کردم تو بشکه نفت از بالا کوه قل دادم پایین","با کیرم مادرتو هیپنوتیزم کردم","ناموستو تو کوچه موقع عید دیدنی دیدم رفتم خونه به یادش جق زدم","با خیسی عرق کون مادرت جقیدم","با سرعت نور تو فضا حرکت میکنم تا پیر نشم و بزارم آبجی کوچیکت بزرگ بشه تا وقتی بزرگ شد باهاش سکس کنم","مادرتو پودر میکنم ازش سنگ توالت میسازم هر روز صبح رو مادرت میرینم","مادرتو مجبور میکنم خودکشی کوانتومی کنه تا در بی نهایت جهان موازی یتیم بشی","دیدی چه لگدی به مادرت زدم ؟","فرشی که مادرت روش کونشو گذاشته بو کردم","مادرتو جوری گاییدم که همسایه ها فکر کردن اسب ترکمن اومده خونتون"]

media_cache, message_cache, user_inline_messages, selfbot_managers = {}, {}, {}, {}

action_types = {
    'تایپ': types.SendMessageTypingAction(), 'ویس': types.SendMessageRecordAudioAction(),
    'ویدیو': types.SendMessageRecordVideoAction(), 'عکس': types.SendMessageUploadPhotoAction(progress=0),
    'فیلم': types.SendMessageUploadVideoAction(progress=0), 'فایل': types.SendMessageUploadDocumentAction(progress=0),
    'بازی': types.SendMessageGamePlayAction(), 'استیکر': types.SendMessageChooseStickerAction(),
    'موقعیت': types.SendMessageGeoLocationAction(), 'تماس': types.SendMessageChooseContactAction(),
    'صحبت': types.SpeakingInGroupCallAction(), 'لغو': types.SendMessageCancelAction(),
}

R, W, SLEEP = "❤️", "🤍", 0.1
def create_heart_matrix(size):
    heart = []
    for i in range(size):
        row = ""
        for j in range(size):
            if (i == 0 and (j == 0 or j == size-1)) or (i == 1 and (j == 0 or j == 1 or j == size-2 or j == size-1)) or (i == 2 and (j == 0 or j == 1 or j == 2 or j == size-3 or j == size-2 or j == size-1)) or (i >= 3 and i < size-1 and (j >= i-2 and j <= size-(i-2)-1)) or (i == size-1 and (j >= size//2 - 1 and j <= size//2 + 1)):
                row += R
            else: row += W
        heart.append(row)
    return "\n".join(heart)
JOINED_HEART, HEARTLET_LEN = create_heart_matrix(7), create_heart_matrix(7).count(R)

# ========== توابع کمکی ==========
def get_user_api(user_id):
    conn = sqlite3.connect('main_database.db'); cursor = conn.cursor()
    cursor.execute('SELECT api_id, api_hash FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row and row[0] and row[1]:
        conn.close(); return {"api_id": row[0], "api_hash": row[1]}
    api_count = {}
    for api in API_CONFIGS:
        cursor.execute('SELECT COUNT(*) FROM users WHERE api_id = ?', (api["api_id"],))
        api_count[api["api_id"]] = cursor.fetchone()[0]
    best_api = min(API_CONFIGS, key=lambda x: api_count.get(x["api_id"], 0))
    cursor.execute('UPDATE users SET api_id = ?, api_hash = ? WHERE user_id = ?', (best_api["api_id"], best_api["api_hash"], user_id))
    conn.commit(); conn.close()
    return best_api

def convert_persian_to_english(text):
    if not text: return text
    p2e = {'۰':'0','۱':'1','۲':'2','۳':'3','۴':'4','۵':'5','۶':'6','۷':'7','۸':'8','۹':'9','٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'}
    for p, e in p2e.items(): text = text.replace(p, e)
    return text

def get_full_date_info():
    now = datetime.now(pytz.timezone('Asia/Tehran'))
    try:
        jdate = jdatetime.date.fromgregorian(date=now.date())
        hijri = Gregorian(now.year, now.month, now.day).to_hijri()
        return f"""📅 تاریخ کامل\n━━━━━━━━━━━━━━━━━━━━\n🕐 ساعت: {now.strftime('%H:%M:%S')}\n\n📆 شمسی:\n{['دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه','شنبه','یک‌شنبه'][jdate.weekday()]} - {jdate.day} {jdate.strftime('%B')} {jdate.year}\n\n📆 میلادی:\n{['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][now.weekday()]} - {now.strftime('%B %d, %Y')}\n\n📆 قمری:\n{hijri.day} {hijri.month_name()} {hijri.year}\n━━━━━━━━━━━━━━━━━━━━"""
    except: return f"📅 تاریخ: {now.strftime('%Y/%m/%d %H:%M:%S')}"

def is_channel_post(message):
    try:
        if not message: return False
        if hasattr(message, 'post') and message.post: return True
        if hasattr(message, 'is_channel') and message.is_channel:
            if hasattr(message, 'is_group') and not message.is_group: return True
            if not message.from_id: return True
        if hasattr(message, 'chat') and message.chat:
            chat = message.chat
            if hasattr(chat, 'broadcast') and chat.broadcast: return True
            if hasattr(chat, 'megagroup') and not chat.megagroup and hasattr(chat, 'broadcast') and chat.broadcast: return True
        if hasattr(message, 'fwd_from') and message.fwd_from and hasattr(message.fwd_from, 'from_id'):
            if hasattr(message.fwd_from.from_id, 'channel_id'): return True
        if hasattr(message, 'peer_id') and isinstance(message.peer_id, PeerChannel):
            if not message.sender_id or message.sender_id == message.chat_id: return True
        return False
    except: return False

def is_link_message(text):
    if not text: return False
    patterns = [r'https?://\S+', r't\.me/\S+', r'www\.\S+', r'\S+\.(com|ir|org|net|info)\S*']
    for p in patterns:
        if re.search(p, text, re.IGNORECASE): return True
    return False

def is_emoji_message(text):
    if not text: return False
    text = text.strip()
    if not text: return False
    return bool(re.compile(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U000024C2-\U0001F251\U0001F900-\U0001F9FF]+$', flags=re.UNICODE).match(text))

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
            response = requests.post(f"{GEMINI_URL}?key={GEMINI_KEY}", json={"contents": [{"parts": [{"text": text}]}]}, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
        elif ai_type == 2:
            response = requests.post(PAXSENIX_API_URL, headers={'Authorization': f'Bearer {PAXSENIX_API_KEY}', 'Content-Type': 'application/json'}, json={'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': text}]}, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result:
                    return result['choices'][0]['message']['content'].strip()
        elif ai_type == 3:
            response = requests.get(DEEPSEEK_FREE_URL + quote(text), timeout=30)
            if response.status_code == 200:
                return response.text.strip()
    except: pass
    return None

async def apply_text_style(message_text, style):
    if not message_text or not style: return message_text, []
    entities = []
    if style == 'بولد': entities.append(MessageEntityBold(offset=0, length=len(message_text)))
    elif style == 'زیرخط': entities.append(MessageEntityUnderline(offset=0, length=len(message_text)))
    elif style == 'خط خورده': entities.append(MessageEntityStrike(offset=0, length=len(message_text)))
    elif style == 'نقل قول': entities.append(MessageEntityBlockquote(offset=0, length=len(message_text)))
    elif style == 'اسپویلر': entities.append(MessageEntitySpoiler(offset=0, length=len(message_text)))
    elif style == 'کج': entities.append(MessageEntityItalic(offset=0, length=len(message_text)))
    elif style == 'کد': entities.append(MessageEntityCode(offset=0, length=len(message_text)))
    elif style == 'پیش': entities.append(MessageEntityPre(offset=0, length=len(message_text), language=""))
    return message_text, entities

async def get_target_user(event, client=None):
    try:
        if event.is_reply:
            return (await event.get_reply_message()).sender_id
        elif client and isinstance(event.message.peer_id, PeerUser) and not event.is_reply:
            return event.message.peer_id.user_id
        return None
    except: return None

async def _wrap_edit(message, text: str):
    try: await message.edit(text)
    except FloodWaitError as fl: await asyncio.sleep(fl.seconds)

async def advanced_heart_animation(message):
    BIG_SCROLL = "🧡💛💚💙💜🖤🤎"
    await _wrap_edit(message, JOINED_HEART)
    for heart in BIG_SCROLL:
        await _wrap_edit(message, JOINED_HEART.replace(R, heart))
        await asyncio.sleep(SLEEP)
    ALL = ["❤️"] + list("🧡💛💚💙💜🤎🖤")
    format_heart = JOINED_HEART.replace(R, "{}")
    for _ in range(5):
        await _wrap_edit(message, format_heart.format(*random.choices(ALL, k=HEARTLET_LEN)))
        await asyncio.sleep(SLEEP)
    await _wrap_edit(message, JOINED_HEART)
    await asyncio.sleep(SLEEP * 2)
    repl = JOINED_HEART
    for _ in range(JOINED_HEART.count(W)):
        repl = repl.replace(W, R, 1)
        await _wrap_edit(message, repl)
        await asyncio.sleep(SLEEP)
    for i in range(7, 0, -1):
        await _wrap_edit(message, "\n".join([R * i] * i))
        await asyncio.sleep(SLEEP)
    await asyncio.sleep(0.5)
    for txt in ["❤️ I", "❤️ I Love", "❤️ I Love You"]:
        await message.edit(txt)
        await asyncio.sleep(0.5)
    await asyncio.sleep(3)
    await message.edit("❤️ I Love You <3")

# ========== کلاس دیتابیس ==========
class MainDatabase:
    def __init__(self, db_name='main_database.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, full_name TEXT, username TEXT, phone TEXT, self_active BOOLEAN DEFAULT 0, admin_approved BOOLEAN DEFAULT 0, rejected BOOLEAN DEFAULT 0, request_sent BOOLEAN DEFAULT 0, step TEXT, phone_code_hash TEXT, code TEXT, password TEXT, request_date TEXT, activation_date TEXT, expiration_date TEXT, session_file TEXT, api_id INTEGER, api_hash TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS selfbot_settings (user_id INTEGER PRIMARY KEY, time_enabled BOOLEAN DEFAULT 0, flag_enabled BOOLEAN DEFAULT 0, pv_lock_all BOOLEAN DEFAULT 0, autosend_mode BOOLEAN DEFAULT 0, text_style TEXT, report_group_id INTEGER DEFAULT -1002817019483, ai_1_pm BOOLEAN DEFAULT 0, ai_2_pm BOOLEAN DEFAULT 0, ai_3_pm BOOLEAN DEFAULT 0, ai_1_group BOOLEAN DEFAULT 0, ai_2_group BOOLEAN DEFAULT 0, ai_3_group BOOLEAN DEFAULT 0, translate_english BOOLEAN DEFAULT 0, translate_arabic BOOLEAN DEFAULT 0, translate_hebrew BOOLEAN DEFAULT 0, translate_russian BOOLEAN DEFAULT 0, translate_turkish BOOLEAN DEFAULT 0, panel_mode BOOLEAN DEFAULT 1, time_font_indices TEXT, filter_enabled BOOLEAN DEFAULT 0, selfbot_enabled BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS enemies (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, enemy_id INTEGER, chat_type TEXT DEFAULT 'pv', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, enemy_id, chat_type))''')
        c.execute('''CREATE TABLE IF NOT EXISTS locked_pvs (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, locked_user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, locked_user_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS reactions (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, chat_id INTEGER, target_id INTEGER, emoji TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, chat_id, target_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS auto_comments (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, channel_id INTEGER, comment_text TEXT, channel_title TEXT, channel_type TEXT, channel_username TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, channel_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS sent_comments (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, channel_id INTEGER, message_id INTEGER, comment_sent BOOLEAN DEFAULT 0, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, channel_id, message_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS filter_words (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, word TEXT, enabled BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, word))''')
        c.execute('''CREATE TABLE IF NOT EXISTS spam_settings (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, spam_protection BOOLEAN DEFAULT 0, spam_limit INTEGER DEFAULT 10, mute_duration INTEGER DEFAULT 10, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_locks (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, target_id INTEGER, lock_type TEXT, enabled BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, target_id, lock_type))''')
        c.execute('''CREATE TABLE IF NOT EXISTS enemy_spam_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, spam_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_memory (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, known_name TEXT, chat_id INTEGER, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_info (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, key TEXT, value TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES user_memory (user_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS message_cache (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, chat_id INTEGER, message_id INTEGER, message_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(owner_id, chat_id, message_id))''')
        conn.commit(); conn.close()
        logger.info("✓ دیتابیس اصلی ایجاد شد")
    
    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        columns = [d[0] for d in c.description]; row = c.fetchone()
        conn.close()
        return dict(zip(columns, row)) if row else None
    
    def update_user(self, user_id, **kwargs):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute(f'UPDATE users SET {", ".join([f"{k} = ?" for k in kwargs.keys()])}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', list(kwargs.values()) + [user_id])
        conn.commit(); conn.close()
    
    def get_selfbot_settings(self, user_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT * FROM selfbot_settings WHERE user_id = ?', (user_id,))
        columns = [d[0] for d in c.description]; row = c.fetchone()
        conn.close()
        if row:
            settings = dict(zip(columns, row))
            settings['ai_status'] = {'ai_1_pm': bool(settings.get('ai_1_pm',0)), 'ai_2_pm': bool(settings.get('ai_2_pm',0)), 'ai_3_pm': bool(settings.get('ai_3_pm',0)), 'ai_1_group': bool(settings.get('ai_1_group',0)), 'ai_2_group': bool(settings.get('ai_2_group',0)), 'ai_3_group': bool(settings.get('ai_3_group',0))}
            settings['translate'] = {'english': bool(settings.get('translate_english',0)), 'arabic': bool(settings.get('translate_arabic',0)), 'hebrew': bool(settings.get('translate_hebrew',0)), 'russian': bool(settings.get('translate_russian',0)), 'turkish': bool(settings.get('translate_turkish',0))}
            tf = settings.get('time_font_indices', 'all')
            settings['time_font_indices'] = [int(x) for x in tf.split(',')] if tf and tf != 'all' else 'all'
            settings.setdefault('selfbot_enabled', 1)
            return settings
        else:
            default = {'user_id': user_id, 'time_enabled': 0, 'flag_enabled': 0, 'pv_lock_all': 0, 'autosend_mode': 0, 'text_style': None, 'report_group_id': GROUP_ID, 'ai_1_pm': 0, 'ai_2_pm': 0, 'ai_3_pm': 0, 'ai_1_group': 0, 'ai_2_group': 0, 'ai_3_group': 0, 'translate_english': 0, 'translate_arabic': 0, 'translate_hebrew': 0, 'translate_russian': 0, 'translate_turkish': 0, 'panel_mode': 1, 'time_font_indices': 'all', 'filter_enabled': 0, 'selfbot_enabled': 1}
            self.set_selfbot_settings(user_id, default)
            return default
    
    def set_selfbot_settings(self, user_id, settings):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        s = settings.copy()
        s.pop('ai_status', None); s.pop('translate', None)
        if 'time_font_indices' in s and isinstance(s['time_font_indices'], list):
            s['time_font_indices'] = ','.join(map(str, s['time_font_indices']))
        c.execute(f'INSERT OR REPLACE INTO selfbot_settings ({", ".join(s.keys())}, updated_at) VALUES ({", ".join(["?" for _ in s])}, CURRENT_TIMESTAMP)', list(s.values()))
        conn.commit(); conn.close()
    
    def update_selfbot_setting(self, user_id, key, value):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute(f'UPDATE selfbot_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?', (value, user_id))
        conn.commit(); conn.close()
    
    def add_enemy(self, owner_id, enemy_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO enemies (owner_id, enemy_id, chat_type) VALUES (?, ?, "pv")', (owner_id, enemy_id))
        conn.commit(); conn.close()
    
    def remove_enemy(self, owner_id, enemy_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM enemies WHERE owner_id = ? AND enemy_id = ? AND chat_type = "pv"', (owner_id, enemy_id))
        conn.commit(); conn.close()
    
    def get_enemies(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT enemy_id FROM enemies WHERE owner_id = ? AND chat_type = "pv"', (owner_id,))
        enemies = [row[0] for row in c.fetchall()]
        conn.close(); return enemies
    
    def is_enemy(self, owner_id, enemy_id): return enemy_id in self.get_enemies(owner_id)
    
    def add_locked_pv(self, owner_id, locked_user_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO locked_pvs (owner_id, locked_user_id) VALUES (?, ?)', (owner_id, locked_user_id))
        conn.commit(); conn.close()
    
    def remove_locked_pv(self, owner_id, locked_user_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM locked_pvs WHERE owner_id = ? AND locked_user_id = ?', (owner_id, locked_user_id))
        conn.commit(); conn.close()
    
    def get_locked_pvs(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT locked_user_id FROM locked_pvs WHERE owner_id = ?', (owner_id,))
        locked = [row[0] for row in c.fetchall()]
        conn.close(); return locked
    
    def get_user_lock(self, owner_id, target_id, lock_type):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT enabled FROM user_locks WHERE owner_id = ? AND target_id = ? AND lock_type = ?', (owner_id, target_id, lock_type))
        result = c.fetchone()
        conn.close(); return bool(result[0]) if result else False
    
    def set_user_lock(self, owner_id, target_id, lock_type, enabled):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO user_locks (owner_id, target_id, lock_type, enabled) VALUES (?, ?, ?, ?)', (owner_id, target_id, lock_type, 1 if enabled else 0))
        conn.commit(); conn.close()
    
    def set_reaction(self, owner_id, chat_id, target_id, emoji):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO reactions (owner_id, chat_id, target_id, emoji) VALUES (?, ?, ?, ?)', (owner_id, chat_id, target_id, emoji))
        conn.commit(); conn.close()
    
    def get_reaction(self, owner_id, chat_id, target_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT emoji FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
        result = c.fetchone()
        conn.close(); return result[0] if result else None
    
    def remove_reaction(self, owner_id, chat_id, target_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM reactions WHERE owner_id = ? AND chat_id = ? AND target_id = ?', (owner_id, chat_id, target_id))
        conn.commit(); conn.close()
    
    def get_auto_comments(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT * FROM auto_comments WHERE owner_id = ?', (owner_id,))
        columns = [d[0] for d in c.description]; rows = c.fetchall()
        conn.close(); return [dict(zip(columns, row)) for row in rows]
    
    def get_auto_comment(self, owner_id, channel_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT * FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
        columns = [d[0] for d in c.description]; row = c.fetchone()
        conn.close(); return dict(zip(columns, row)) if row else None
    
    def remove_auto_comment(self, owner_id, channel_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM auto_comments WHERE owner_id = ? AND channel_id = ?', (owner_id, channel_id))
        conn.commit(); conn.close()
    
    def mark_comment_sent(self, owner_id, channel_id, message_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO sent_comments (owner_id, channel_id, message_id, comment_sent) VALUES (?, ?, ?, 1)', (owner_id, channel_id, message_id))
        conn.commit(); conn.close()
    
    def add_filter_word(self, owner_id, word):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO filter_words (owner_id, word) VALUES (?, ?)', (owner_id, word))
        conn.commit(); conn.close()
    
    def remove_filter_word(self, owner_id, word):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM filter_words WHERE owner_id = ? AND word = ?', (owner_id, word))
        conn.commit(); conn.close()
    
    def get_filter_words(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT word, enabled FROM filter_words WHERE owner_id = ?', (owner_id,))
        results = c.fetchall()
        conn.close(); return [{'word': row[0], 'enabled': bool(row[1])} for row in results]
    
    def get_filter_enabled(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        try:
            c.execute('SELECT filter_enabled FROM selfbot_settings WHERE user_id = ?', (owner_id,))
            result = c.fetchone()
            conn.close(); return result[0] if result else 0
        except:
            conn.close(); return 0
    
    def set_filter_enabled(self, owner_id, enabled):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        try:
            c.execute('UPDATE selfbot_settings SET filter_enabled = ? WHERE user_id = ?', (1 if enabled else 0, owner_id))
        except:
            try:
                c.execute('ALTER TABLE selfbot_settings ADD COLUMN filter_enabled BOOLEAN DEFAULT 0')
                c.execute('UPDATE selfbot_settings SET filter_enabled = ? WHERE user_id = ?', (1 if enabled else 0, owner_id))
            except: pass
        conn.commit(); conn.close()
    
    def get_spam_settings(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT * FROM spam_settings WHERE owner_id = ?', (owner_id,))
        columns = [d[0] for d in c.description]; row = c.fetchone()
        conn.close()
        if row: return dict(zip(columns, row))
        return {'owner_id': owner_id, 'spam_protection': 0, 'spam_limit': 10, 'mute_duration': 10}
    
    def set_spam_settings(self, owner_id, spam_protection=None, spam_limit=None, mute_duration=None):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT id FROM spam_settings WHERE owner_id = ?', (owner_id,))
        exists = c.fetchone()
        settings = {}
        if spam_protection is not None: settings['spam_protection'] = spam_protection
        if spam_limit is not None: settings['spam_limit'] = spam_limit
        if mute_duration is not None: settings['mute_duration'] = mute_duration
        if exists:
            c.execute(f'UPDATE spam_settings SET {", ".join([f"{k} = ?" for k in settings.keys()])} WHERE owner_id = ?', list(settings.values()) + [owner_id])
        else:
            default = {'owner_id': owner_id, 'spam_protection': 0, 'spam_limit': 10, 'mute_duration': 10}
            default.update(settings)
            c.execute(f'INSERT INTO spam_settings ({", ".join(default.keys())}) VALUES ({", ".join(["?" for _ in default])})', list(default.values()))
        conn.commit(); conn.close()
    
    def get_original_name(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "original_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
        result = c.fetchone()
        conn.close(); return result[0] if result else None
    
    def set_original_name(self, owner_id, original_name):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "original_name", ?)', (owner_id, original_name))
        conn.commit(); conn.close()
    
    def get_current_name(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT value FROM user_info WHERE user_id = ? AND key = "current_name" ORDER BY timestamp DESC LIMIT 1', (owner_id,))
        result = c.fetchone()
        conn.close(); return result[0] if result else None
    
    def set_current_name(self, owner_id, current_name):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT INTO user_info (user_id, key, value) VALUES (?, "current_name", ?)', (owner_id, current_name))
        conn.commit(); conn.close()
    
    def get_user_name(self, user_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT known_name, first_name, username FROM user_memory WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        if result:
            known, first, username = result
            if known: return known
            if first: return first
            if username: return f"@{username}"
        return f"کاربر {user_id}"
    
    def update_user_memory(self, user_id, username, first_name, last_name, chat_id, known_name=None):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT user_id FROM user_memory WHERE user_id = ?', (user_id,))
        if c.fetchone():
            c.execute('UPDATE user_memory SET username = ?, first_name = ?, last_name = ?, known_name = ?, chat_id = ?, last_seen = CURRENT_TIMESTAMP WHERE user_id = ?', (username, first_name, last_name, known_name, chat_id, user_id))
        else:
            c.execute('INSERT INTO user_memory (user_id, username, first_name, last_name, known_name, chat_id, last_seen) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)', (user_id, username, first_name, last_name, known_name, chat_id))
        conn.commit(); conn.close()
    
    def add_enemy_spam_message(self, owner_id, spam_text):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT INTO enemy_spam_messages (owner_id, spam_text) VALUES (?, ?)', (owner_id, spam_text))
        conn.commit(); conn.close()
    
    def get_enemy_spam_messages(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT id, spam_text FROM enemy_spam_messages WHERE owner_id = ? ORDER BY created_at', (owner_id,))
        results = c.fetchall()
        conn.close(); return [{'id': row[0], 'text': row[1]} for row in results]
    
    def clear_enemy_spam_messages(self, owner_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ?', (owner_id,))
        conn.commit(); conn.close()
    
    def delete_enemy_spam_message(self, owner_id, message_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('DELETE FROM enemy_spam_messages WHERE owner_id = ? AND id = ?', (owner_id, message_id))
        conn.commit(); conn.close()
    
    def cache_message(self, owner_id, chat_id, message_id, message_text):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO message_cache (owner_id, chat_id, message_id, message_text) VALUES (?, ?, ?, ?)', (owner_id, chat_id, message_id, message_text))
        conn.commit(); conn.close()
    
    def get_cached_message(self, owner_id, chat_id, message_id):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('SELECT message_text FROM message_cache WHERE owner_id = ? AND chat_id = ? AND message_id = ?', (owner_id, chat_id, message_id))
        result = c.fetchone()
        conn.close(); return result[0] if result else None

db = MainDatabase()

# ========== کلاس گزارش ==========
class ReportConfig:
    def __init__(self, user_id, config_file=REPORT_CONFIG_FILE):
        self.user_id, self.config_file = user_id, config_file
        self.report_group_id, self.auto_save_media = GROUP_ID, True
        self.report_deleted_media, self.report_edited_messages, self.report_ttl_media = True, True, True
        self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    us = data.get(str(self.user_id), {})
                    self.report_group_id = us.get('report_group_id', GROUP_ID)
                    self.auto_save_media = us.get('auto_save_media', True)
                    self.report_deleted_media = us.get('report_deleted_media', True)
                    self.report_edited_messages = us.get('report_edited_messages', True)
                    self.report_ttl_media = us.get('report_ttl_media', True)
        except Exception as e: logger.error(f"خطا در بارگذاری تنظیمات: {e}")
    
    def save_config(self):
        try:
            data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f: data = json.load(f)
            data[str(self.user_id)] = {'report_group_id': self.report_group_id, 'auto_save_media': self.auto_save_media, 'report_deleted_media': self.report_deleted_media, 'report_edited_messages': self.report_edited_messages, 'report_ttl_media': self.report_ttl_media}
            with open(self.config_file, 'w') as f: json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e: logger.error(f"خطا در ذخیره تنظیمات: {e}")
    
    def set_report_group(self, group_id):
        self.report_group_id = group_id
        self.save_config()
        return f"✅ گروه گزارش به {group_id} تغییر کرد"

# ========== کلاس سلف‌بات ==========
class SelfBotManager:
    def __init__(self, user_id):
        self.user_id, self.client, self.running, self.my_id = int(user_id), None, False, None
        self.BASE_NAME, self.ORIGINAL_NAME, self.spam_tasks = None, None, {}
        self.report_config = ReportConfig(user_id)
        self.adding_spam, self.spam_counters, self.active_actions, self.action_tasks = False, {}, {}, {}
        self.translate_mode = {"english": False, "arabic": False, "hebrew": False, "russian": False, "turkish": False}
        self.search_mode, self.last_search_results, self.connection_attempts, self.max_attempts = False, [], 0, 5
        self._handlers_set, self.panel_mode, self.api_id, self.api_hash = False, True, None, None
        self.time_font_cycle, self.time_font_indices, self.keepalive_running, self.error_count = 0, 'all', False, 0
        self.autosend_enabled = False
    
    async def start(self, session_file):
        try:
            if self.running and self.client and self.client.is_connected(): return True
            self.connection_attempts += 1
            if not os.path.exists(session_file): return False
            user_api = get_user_api(str(self.user_id))
            if not user_api: return False
            self.api_id, self.api_hash = user_api["api_id"], user_api["api_hash"]
            if self.client:
                try: await self.client.disconnect()
                except: pass
                self.client = None
            self.client = TelegramClient(session_file, self.api_id, self.api_hash,
                connection_retries=10, retry_delay=3, timeout=60, flood_sleep_threshold=60,
                device_model="SelfBot", system_version="4.6.0", app_version="4.6.0")
            await self.client.connect()
            if not await self.client.is_user_authorized(): return False
            me = await self.client.get_me()
            if not me: return False
            self.my_id, self.BASE_NAME = me.id, me.first_name or "Self-Bot"
            if not db.get_original_name(self.user_id):
                db.set_original_name(self.user_id, self.BASE_NAME)
                db.set_current_name(self.user_id, self.BASE_NAME)
            self.ORIGINAL_NAME = db.get_original_name(self.user_id) or self.BASE_NAME
            settings = db.get_selfbot_settings(self.user_id)
            self.translate_mode = settings.get('translate', {"english": False, "arabic": False, "hebrew": False, "russian": False, "turkish": False})
            self.panel_mode, self.time_font_indices = settings.get('panel_mode', True), settings.get('time_font_indices', 'all')
            self.autosend_enabled = settings.get('autosend_mode', False)
            if not self._handlers_set:
                self.setup_handlers(); self._handlers_set = True
            asyncio.create_task(self.update_profile_task())
            self.running, self.keepalive_running = True, True
            self.connection_attempts, self.error_count = 0, 0
            asyncio.create_task(self.keep_alive_task())
            return True
        except Exception as e:
            logger.error(f"خطا در شروع سلف‌بات: {e}")
            if self.connection_attempts < self.max_attempts:
                await asyncio.sleep(5 * self.connection_attempts)
                return await self.start(session_file)
            if self.client:
                try: await self.client.disconnect()
                except: pass
                self.client = None
            return False
    
    async def keep_alive_task(self):
        while self.running and self.keepalive_running:
            try:
                await asyncio.sleep(60)
                if not self.running: break
                if self.client and self.client.is_connected():
                    try:
                        await self.client.get_me()
                        self.error_count = 0
                    except Exception as e:
                        self.error_count += 1
                        if self.error_count >= 3:
                            await self.reconnect()
                else:
                    await self.reconnect()
            except asyncio.CancelledError: break
            except Exception as e: logger.error(f"خطا در keep_alive: {e}")
    
    async def reconnect(self):
        try:
            user_data = db.get_user(str(self.user_id))
            if not user_data or not user_data.get('session_file'): return False
            if self.client:
                try: await self.client.disconnect()
                except: pass
                self.client = None
            self.running, self._handlers_set = False, False
            await asyncio.sleep(3)
            return await self.start(user_data['session_file'])
        except Exception as e:
            logger.error(f"خطا در reconnect: {e}")
            return False
    
    async def stop(self):
        try:
            self.running, self.keepalive_running = False, False
            settings = db.get_selfbot_settings(self.user_id)
            settings['panel_mode'] = self.panel_mode
            db.set_selfbot_settings(self.user_id, settings)
            if self.client:
                for t in self.spam_tasks.values(): t.cancel()
                self.spam_tasks.clear()
                try: await self.client.disconnect()
                except: pass
                self.client = None
            self._handlers_set = False
        except Exception as e: logger.error(f"خطا در توقف سلف‌بات: {e}")
    
    def setup_handlers(self):
        try:
            @self.client.on(events.NewMessage(incoming=True))
            async def h_new(event):
                if self.running: await self.handle_new_message(event)
            
            @self.client.on(events.MessageEdited(incoming=True))
            async def h_edit(event):
                if self.running: await self.handle_edited_message(event)
            
            @self.client.on(events.MessageDeleted)
            async def h_delete(event):
                if self.running: await self.handle_deleted_message(event)
            
            @self.client.on(events.NewMessage(pattern=r'^(?:شروع|تایم روشن|تایمر پرچم روشن|تایم خاموش|قلب|ماه|اطلاعات|دانلود پروفایل|تاریخ کامل|فعال اتوسین|غیرفعال اتوسین|حذف کامل|ست پروف|ست بیو|حذف ست پروف|حذف ست بیو|بولد روشن|بولد خاموش|زیرخط روشن|زیرخط خاموش|خط خورده روشن|خط خورده خاموش|نقل قول روشن|نقل قول خاموش|اسپویلر روشن|اسپویلر خاموش|کج روشن|کج خاموش|کد روشن|کد خاموش|پیش روشن|پیش خاموش|بلاک|پیوی ۱|پیوی ۲|پیوی ۳|خاموش پیوی|گروه ۱|گروه ۲|گروه ۳|خاموش گروه|درباره|من کی ام|قفل پیوی همه|باز پی همه|قفل لینک روشن|قفل لینک خاموش|قفل عکس روشن|قفل عکس خاموش|قفل ویدیو روشن|قفل ویدیو خاموش|قفل استیکر روشن|قفل استیکر خاموش|قفل گیف روشن|قفل گیف خاموش|قفل ویس روشن|قفل ویس خاموش|قفل فایل روشن|قفل فایل خاموش|قفل موزیک روشن|قفل موزیک خاموش|قفل ویدیو نوت روشن|قفل ویدیو نوت خاموش|قفل کانتکت روشن|قفل کانتکت خاموش|قفل لوکیشن روشن|قفل لوکیشن خاموش|قفل ایموجی روشن|قفل ایموجی خاموش|قفل متن روشن|قفل متن خاموش|تنظیم گزارش|گروه گزارش|کانال‌ها|حذف کانال|تست کانال|لیست دشمن|پاک کردن اسپم|لیست اسپم|تغییر اسم|تغییر بیو|تغییر پروفایل|پروف|اضافه اسپم|اتمام اسپم|فیلتر روشن|فیلتر خاموش|لیست فیلتر|اسپم روشن|اسپم خاموش|پینگ|سرچ|خروج سرچ|وضعیت|قلب پیشرفته|عشق|سنتت|هک|حذف ریکت|سلف روشن|سلف خاموش|پین|تگ ادمین|امار گپ|\.کد)(?:\s*$|\s+(.+)$)|^حذف\s+(\d+)$|^دشمن\s*(@\w+|-\d+|\d+)?$|^دوست\s*(@\w+|-\d+|\d+)?$|^قفل پیوی\s*(@\w+|-\d+|\d+)?$|^باز پی\s*(@\w+|-\d+|\d+)?$|^اسپم\s+(\d+)\s+(.+)$|^ریکت\s*([\U0001F300-\U0001F9FF]+)?$|^کامنت\s+(.+)$|^حذف اسپم\s+(\d+)$|^تایم\s+([\d\.]+)$|^\.فیلتر\s+(.+)$|^حذف فیلتر\s+(.+)$|^\.پنل$|^پنل$|^/panel$|^\.اهنگ\s+(.+)$|^تنظیم اسپم\s+(\d+)\s+(\d+)$'))
            async def h_cmd(event):
                if self.running: await self.handle_commands(event)
            
            @self.client.on(events.NewMessage(outgoing=True))
            async def h_out(event):
                if self.running: await self.handle_outgoing_message(event)
            
            @self.client.on(events.NewMessage())
            async def h_comment(event):
                if self.running: await self.handle_auto_comment(event)
            
            @self.client.on(events.NewMessage())
            async def h_report(event):
                if self.running: await self.handle_report_message(event)
        except Exception as e: logger.error(f"خطا در تنظیم هندلرها: {e}")
    
    # ========== متدهای اصلی ==========
    async def force_dice(self, chat_id, emoji, target):
        while True:
            msg = await self.client.send_message(chat_id, file=types.InputMediaDice(emoji))
            if msg.media.value == target: break
            await msg.delete()
            await asyncio.sleep(0.3)
    
    async def translate_text(self, text):
        try:
            for lang, status in self.translate_mode.items():
                if status:
                    try: return GoogleTranslator(source='auto', target=lang).translate(text)
                    except: return text
        except: pass
        return text
    
    async def start_action(self, chat_id, action_name):
        if action_name not in action_types: return False
        if chat_id in self.action_tasks: self.action_tasks[chat_id].cancel()
        self.active_actions[chat_id] = action_name
        async def permanent():
            try:
                while True:
                    await self.client(SetTypingRequest(chat_id, action_types[action_name]))
                    await asyncio.sleep(5)
            except: pass
            finally:
                if chat_id in self.active_actions: del self.active_actions[chat_id]
                if chat_id in self.action_tasks: del self.action_tasks[chat_id]
        self.action_tasks[chat_id] = asyncio.create_task(permanent())
        return True
    
    async def stop_action(self, chat_id):
        if chat_id in self.action_tasks:
            self.action_tasks[chat_id].cancel()
            try: await self.client(SetTypingRequest(chat_id, types.SendMessageCancelAction()))
            except: pass
            if chat_id in self.active_actions:
                action = self.active_actions[chat_id]
                del self.active_actions[chat_id], self.action_tasks[chat_id]
                return action
        return None
    
    async def get_user_info(self, user_id):
        try:
            entity = await self.client.get_entity(user_id)
            if entity.username: return f"@{entity.username} ({user_id})"
            if entity.first_name: return f"{entity.first_name} {entity.last_name or ''}".strip() + f" ({user_id})"
            return f"کاربر {user_id}"
        except: return f"کاربر ناشناس ({user_id})"
    
    async def get_chat_title(self, chat_id):
        try:
            entity = await self.client.get_entity(chat_id)
            return entity.title if hasattr(entity, 'title') else entity.first_name or f"چت {chat_id}"
        except: return f"چت {chat_id}"
    
    def get_media_type(self, message):
        if not message.media: return None
        if isinstance(message.media, MessageMediaPhoto): return 'photo'
        if isinstance(message.media, MessageMediaDocument):
            doc = message.media.document
            if hasattr(doc, 'attributes'):
                for attr in doc.attributes:
                    if hasattr(attr, 'voice'): return 'voice'
            if hasattr(doc, 'mime_type'):
                if 'video' in doc.mime_type:
                    for attr in doc.attributes:
                        if hasattr(attr, 'voice'): return 'video_note'
                    return 'video'
                if 'image' in doc.mime_type:
                    for attr in doc.attributes:
                        if hasattr(attr, 'stickerset'): return 'sticker'
                        if hasattr(attr, 'animated'): return 'gif'
                    return 'image'
                if 'audio' in doc.mime_type: return 'music'
            if hasattr(doc, 'attributes'):
                for attr in doc.attributes:
                    if hasattr(attr, 'alt') and attr.alt: return 'sticker'
            return 'file'
        if isinstance(message.media, MessageMediaWebPage): return 'webpage'
        if hasattr(message.media, 'contact'): return 'contact'
        if hasattr(message.media, 'geo'): return 'location'
        return 'unknown'
    
    def get_file_extension(self, media_type):
        return {'photo': '.jpg', 'voice': '.ogg', 'video': '.mp4', 'video_note': '.mp4',
                'sticker': '.webp', 'gif': '.mp4', 'image': '.jpg', 'file': '.bin', 'music': '.mp3'}.get(media_type, '.bin')
    
    async def save_media(self, message, media_type):
        try:
            if not self.report_config.auto_save_media: return None
            chat_id = message.peer_id.user_id if isinstance(message.peer_id, PeerUser) else (message.peer_id.channel_id if isinstance(message.peer_id, PeerChannel) else message.peer_id.chat_id)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(REPORT_MEDIA_FOLDER, f"{media_type}_{message.sender_id}_{message.id}_{ts}{self.get_file_extension(media_type)}")
            downloaded = await self.client.download_media(message.media, file=path)
            if downloaded:
                media_cache[message.id] = {'path': downloaded, 'type': media_type, 'user_id': message.sender_id,
                    'chat_id': chat_id, 'caption': message.text or '', 'timestamp': ts,
                    'file_size': os.path.getsize(downloaded), 'owner_id': self.user_id}
                return downloaded
            return None
        except Exception as e: logger.error(f"خطا در ذخیره رسانه: {e}")
        return None
    
    async def send_report(self, report_text, media_path=None, caption=None):
        try:
            if self.report_config.report_group_id:
                if media_path and os.path.exists(media_path):
                    await self.client.send_file(self.report_config.report_group_id, media_path, caption=caption or report_text)
                else:
                    await self.client.send_message(self.report_config.report_group_id, report_text)
                return True
            return False
        except Exception as e: logger.error(f"خطا در ارسال گزارش: {e}")
        return False
    
    # ========== هندلرهای پیام ==========
    async def handle_media_lock_delete(self, event):
        if not event.message or event.message.out or event.sender_id == self.my_id: return False
        target_id, message, text = event.sender_id, event.message, event.message.text or ""
        lock_types = {
            'lock_link': is_link_message, 'lock_text': lambda x: bool(x and not is_link_message(x) and not is_emoji_message(x)),
            'lock_emoji': is_emoji_message, 'lock_photo': lambda x: message.photo, 'lock_video': lambda x: message.video,
            'lock_sticker': lambda x: message.sticker, 'lock_gif': lambda x: message.gif,
            'lock_voice': lambda x: message.voice, 'lock_file': lambda x: message.document and not message.sticker and not message.gif,
            'lock_music': lambda x: message.audio, 'lock_video_note': lambda x: message.video_note,
            'lock_contact': lambda x: message.contact, 'lock_location': lambda x: message.geo
        }
        for lt, func in lock_types.items():
            if db.get_user_lock(self.user_id, 0, lt) and func(text):
                try: await message.delete(); return True
                except: pass
            if db.get_user_lock(self.user_id, target_id, lt) and func(text):
                try: await message.delete(); return True
                except: pass
        return False
    
    async def handle_new_message(self, event):
        if not self.my_id: return
        settings = db.get_selfbot_settings(self.user_id)
        if not settings.get('selfbot_enabled', 1): return
        peer = event.message.peer_id
        if isinstance(peer, PeerChannel): chat_id = peer.channel_id
        elif isinstance(peer, PeerUser): chat_id = peer.user_id
        elif isinstance(peer, PeerChat): chat_id = peer.chat_id
        else: return
        
        if isinstance(peer, PeerUser) and not event.message.out:
            if settings.get('pv_lock_all') or db.is_pv_locked(self.user_id, event.sender_id):
                try: await event.message.delete()
                except: pass
                return
        
        if await self.handle_media_lock_delete(event): return
        
        if isinstance(peer, PeerUser) and not event.message.out:
            if settings.get('autosend_mode', False):
                try: await self.client.send_read_acknowledge(peer=peer, message=event.message)
                except: pass
        
        if isinstance(peer, PeerUser) and not event.message.out and event.message.text:
            db.cache_message(self.user_id, chat_id, event.message.id, event.message.text)
        
        if not event.message.out and event.message.text and db.get_filter_enabled(self.user_id):
            for w in db.get_filter_words(self.user_id):
                if w['enabled'] and w['word'].lower() in event.message.text.lower():
                    try: await event.message.delete()
                    except: pass
                    return
        
        if isinstance(peer, PeerUser) and not event.message.out:
            sender_id = event.sender_id
            reaction = db.get_reaction(self.user_id, chat_id, sender_id)
            if reaction and reaction in ALLOWED_EMOJIS:
                try: await self.client(SendReactionRequest(peer=peer, msg_id=event.message.id, reaction=[ReactionEmoji(emoticon=reaction)]))
                except: pass
            
            ai_status = settings.get('ai_status', {})
            ai_type = None
            if event.message.text:
                if ai_status.get('ai_1_pm'): ai_type = 1
                elif ai_status.get('ai_2_pm'): ai_type = 2
                elif ai_status.get('ai_3_pm'): ai_type = 3
            if ai_type:
                try:
                    await self.client(SetTypingRequest(event.chat_id, types.SendMessageTypingAction()))
                    response = await get_ai_response(event.message.text, ai_type, self.user_id)
                    if response:
                        text, entities = await apply_text_style(response, settings.get('text_style'))
                        await event.reply(text, formatting_entities=entities)
                    else: await event.reply("❌ خطا در ارتباط با هوش مصنوعی")
                except: pass
        
        spam_settings = db.get_spam_settings(self.user_id)
        if spam_settings.get('spam_protection') and not event.message.out:
            key = f"{chat_id}_{event.sender_id}"
            if key not in self.spam_counters: self.spam_counters[key] = []
            now = time.time()
            self.spam_counters[key].append(now)
            duration = spam_settings.get('mute_duration', 10)
            self.spam_counters[key] = [t for t in self.spam_counters[key] if now - t <= duration]
            if len(self.spam_counters[key]) > spam_settings.get('spam_limit', 10):
                try: await event.message.delete()
                except: pass
        
        if isinstance(peer, PeerUser) and not event.message.out:
            try:
                sender = await event.get_sender()
                if sender:
                    db.update_user_memory(event.sender_id, sender.username, sender.first_name or "", sender.last_name or "", chat_id)
            except: pass
    
    async def handle_auto_comment(self, event):
        try:
            if event.message.out or not is_channel_post(event.message): return
            chat, channel_id = await event.message.get_chat(), event.message.chat.id
            ac = db.get_auto_comment(self.user_id, channel_id)
            if not ac or db.is_comment_sent(self.user_id, channel_id, event.message.id): return
            await asyncio.sleep(0.3)
            await self.client.send_message(chat.id, ac['comment_text'], reply_to=event.message.id)
            db.mark_comment_sent(self.user_id, channel_id, event.message.id)
        except Exception as e: logger.error(f"خطا در ارسال نظر: {e}")
    
    async def handle_report_message(self, event):
        try:
            if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
                if event.message.text:
                    message_cache[(event.message.peer_id.user_id, event.message.id)] = event.message.text
                if event.message.media:
                    mt = self.get_media_type(event.message)
                    if mt:
                        saved = await self.save_media(event.message, mt)
                        sender = await self.get_user_info(event.sender_id)
                        if self.report_config.report_ttl_media and hasattr(event.message.media, 'ttl_seconds') and event.message.media.ttl_seconds:
                            await self.send_report(f"⏰ رسانه نابودشونده از {sender}", saved)
                        elif hasattr(event.message.media, 'noforwards') and event.message.media.noforwards:
                            await self.send_report(f"🚫 رسانه یک‌بارمصرف از {sender}", saved)
        except Exception as e: logger.error(f"خطا در پردازش گزارش: {e}")
    
    async def handle_edited_message(self, event):
        if isinstance(event.message.peer_id, PeerUser) and not event.message.out:
            sender = await event.get_sender()
            if sender.id == self.my_id: return
            settings = db.get_selfbot_settings(self.user_id)
            if settings.get('pv_lock_all') or db.is_pv_locked(self.user_id, sender.id):
                try: await event.message.delete()
                except: pass
                return
            if self.report_config.report_edited_messages:
                chat_id, mid = event.message.peer_id.user_id, event.message.id
                original = message_cache.get((chat_id, mid), "نامشخص")
                await self.send_report(f"✍️ پیام ویرایش‌شده از {await self.get_user_info(sender.id)}\nمتن اصلی:\n{original[:500]}\nمتن جدید:\n{event.message.text[:500]}")
            db.cache_message(self.user_id, event.message.peer_id.user_id, event.message.id, event.message.text or "")
    
    async def handle_deleted_message(self, event):
        if not self.report_config.report_deleted_media: return
        for mid in event.deleted_ids:
            if mid in media_cache and media_cache[mid].get('owner_id') == self.user_id:
                try:
                    info = media_cache[mid]
                    await self.send_report(f"🗑️ رسانه حذف‌شده از {await self.get_user_info(info['user_id'])}\nچت: {await self.get_chat_title(info['chat_id'])}\nنوع: {info['type']}", info.get('path') if os.path.exists(info.get('path', '')) else None)
                    del media_cache[mid]
                except: pass
    
    # ========== متدهای پروفایل ==========
    async def update_profile_name(self):
        settings = db.get_selfbot_settings(self.user_id)
        if not settings.get('time_enabled'): return
        now, minute = datetime.now(), datetime.now().minute
        if self.time_font_indices == 'all':
            font_index = minute % len(classic_fonts)
        elif isinstance(self.time_font_indices, list) and self.time_font_indices:
            self.time_font_cycle = (self.time_font_cycle + 1) % len(self.time_font_indices)
            font_index = self.time_font_indices[self.time_font_cycle]
            if font_index >= len(classic_fonts): font_index = 0
        else: font_index = 0
        time_now = convert_to_classic_font(now.strftime("%H:%M"), font_index)
        try:
            name = db.get_current_name(self.user_id) or self.BASE_NAME
            if settings.get('flag_enabled'):
                flag = flags[minute % len(flags)]
                new_name = f"『 {flag} 』{name} {time_now}"
            else: new_name = f"{name} | {time_now}"
            await self.client(UpdateProfileRequest(first_name=new_name))
        except: pass
    
    async def restore_profile_name(self):
        try:
            name = db.get_current_name(self.user_id)
            if name: await self.client(UpdateProfileRequest(first_name=name))
            else:
                orig = db.get_original_name(self.user_id)
                if orig:
                    await self.client(UpdateProfileRequest(first_name=orig))
                    db.set_current_name(self.user_id, orig)
                    self.BASE_NAME = orig
        except: pass
    
    async def update_profile_task(self):
        while self.running:
            try: await self.update_profile_name()
            except: pass
            await asyncio.sleep(60)
    
    # ========== توابع کمکی ==========
    async def get_chat_stats(self, chat_id, target_user_id=None):
        try:
            if not target_user_id: return None
            stats = {'my_messages':0,'target_messages':0,'my_photos':0,'target_photos':0,'my_videos':0,'target_videos':0,
                     'my_stickers':0,'target_stickers':0,'my_gifs':0,'target_gifs':0,'my_voices':0,'target_voices':0,
                     'my_files':0,'target_files':0}
            target_user_id = int(target_user_id)
            async for msg in self.client.iter_messages(chat_id, limit=5000):
                sid = msg.sender_id
                if not sid and hasattr(msg, 'from_id') and msg.from_id:
                    if hasattr(msg.from_id, 'user_id'): sid = msg.from_id.user_id
                    elif hasattr(msg.from_id, 'channel_id'): sid = msg.from_id.channel_id
                    elif hasattr(msg.from_id, 'chat_id'): sid = msg.from_id.chat_id
                if not sid: continue
                sid = int(sid)
                if sid == self.my_id:
                    stats['my_messages'] += 1
                    if msg.photo: stats['my_photos'] += 1
                    elif msg.video: stats['my_videos'] += 1
                    elif msg.sticker: stats['my_stickers'] += 1
                    elif msg.gif: stats['my_gifs'] += 1
                    elif msg.voice: stats['my_voices'] += 1
                    elif msg.document: stats['my_files'] += 1
                elif sid == target_user_id:
                    stats['target_messages'] += 1
                    if msg.photo: stats['target_photos'] += 1
                    elif msg.video: stats['target_videos'] += 1
                    elif msg.sticker: stats['target_stickers'] += 1
                    elif msg.gif: stats['target_gifs'] += 1
                    elif msg.voice: stats['target_voices'] += 1
                    elif msg.document: stats['target_files'] += 1
            return stats
        except Exception as e: logger.error(f"خطا در دریافت آمار: {e}")
        return None
    
    async def generate_qr_code(self, text_or_photo, is_photo=False):
        try:
            if is_photo:
                path = await self.client.download_media(text_or_photo)
                if not path: return None, "خطا در دانلود عکس"
                text = f"Image: {os.path.basename(path)}"
                os.remove(path)
            else: text = text_or_photo
            if not text: return None, "متن خالی است"
            qr = qrcode.make(text)
            qr_path = f"qr_{self.user_id}_{int(time.time())}.png"
            qr.save(qr_path)
            return qr_path, text
        except Exception as e: return None, str(e)
    
    async def get_admins(self, chat_id):
        try:
            admins = []
            async for user in self.client.iter_participants(chat_id, filter=ChannelParticipantsAdmins):
                admins.append(user)
            return admins
        except Exception as e: logger.error(f"خطا در دریافت ادمین‌ها: {e}")
        return []
    
    async def pin_message(self, chat_id, message_id):
        try: await self.client.pin_message(chat_id, message_id); return True
        except Exception as e: logger.error(f"خطا در پین: {e}")
        return False
    
    # ========== هندلر اصلی دستورات ==========
    async def handle_commands(self, event):
        if event.sender_id != self.my_id: return
        cmd = event.text.strip()
        
        if cmd == 'سلف روشن':
            db.update_selfbot_setting(self.user_id, 'selfbot_enabled', 1)
            await event.edit("✅ سلف‌بات فعال شد"); return
        if cmd == 'سلف خاموش':
            db.update_selfbot_setting(self.user_id, 'selfbot_enabled', 0)
            await event.edit("✅ سلف‌بات غیرفعال شد"); return
        
        settings = db.get_selfbot_settings(self.user_id)
        if not settings.get('selfbot_enabled', 1):
            await event.edit("⚠️ سلف‌بات غیرفعال است. برای فعال کردن: سلف روشن")
            return
        
        chat_id = None
        if isinstance(event.message.peer_id, PeerUser): chat_id = event.message.peer_id.user_id
        elif isinstance(event.message.peer_id, PeerChannel): chat_id = event.message.peer_id.channel_id
        elif isinstance(event.message.peer_id, PeerChat): chat_id = event.message.peer_id.chat_id
        
        # ========== دستورات ==========
        if cmd == 'تگ ادمین':
            if not isinstance(event.message.peer_id, (PeerChannel, PeerChat)):
                await event.edit("⚠️ فقط در گروه"); return
            admins = await self.get_admins(chat_id)
            if admins:
                text = "👑 ادمین‌ها:\n\n"
                for a in admins:
                    text += f"• @{a.username}" if a.username else f"• {a.first_name or 'ادمین'}\n"
                await event.edit(text)
            else: await event.edit("⚠️ ادمینی یافت نشد")
            return
        
        if cmd == 'پین':
            if event.is_reply:
                reply = await event.get_reply_message()
                if await self.pin_message(chat_id, reply.id):
                    await event.edit("📌 پیام پین شد")
                else: await event.edit("⚠️ خطا در پین")
            else: await event.edit("⚠️ روی پیام ریپلای کنید")
            return
        
        if cmd.startswith('.کد'):
            await event.delete()
            try:
                if event.is_reply:
                    reply = await event.get_reply_message()
                    if reply.text: path, text = await self.generate_qr_code(reply.text)
                    elif reply.photo: path, text = await self.generate_qr_code(reply.media, True)
                    else: await event.respond("⚠️ روی متن یا عکس ریپلای کنید"); return
                else:
                    t = cmd.replace('.کد', '').strip()
                    if t: path, text = await self.generate_qr_code(t)
                    else: await event.respond("⚠️ متن را مشخص کنید"); return
                if path and os.path.exists(path):
                    await self.client.send_file(chat_id, path, caption=f"🝰 کد QR\n📝 متن: {text[:100]}")
                    os.remove(path)
                else: await event.respond(f"⚠️ خطا: {text}")
            except Exception as e: await event.respond(f"⚠️ خطا: {str(e)[:100]}")
            return
        
        if cmd == 'امار گپ':
            await event.delete()
            target = None
            if event.is_reply: target = (await event.get_reply_message()).sender_id
            if not target and isinstance(event.message.peer_id, PeerUser): target = chat_id
            if not target:
                await event.respond("⚠️ روی پیام ریپلای کنید یا در پی‌وی باشید")
                return
            stats = await self.get_chat_stats(chat_id, target)
            if not stats:
                await event.respond("⚠️ خطا در دریافت آمار")
                return
            try:
                target_name, my_name = await self.get_user_info(target), await self.get_user_info(self.my_id)
                tm, tt = stats['my_messages'], stats['target_messages']
                winner = my_name if tm > tt else (target_name if tt > tm else "مساوی")
                ratio = f"{tm} به {tt}" if tt > 0 else f"{tm} به 0"
                await self.client.send_message(chat_id, f"""
📊 آمار گفتگو
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نوع                {my_name[:10]}        {target_name[:10]}
────────────────────────────────────
💬 پیام            {tm:>5}        {tt:>5}
📸 عکس             {stats['my_photos']:>5}        {stats['target_photos']:>5}
🎙️ ویس             {stats['my_voices']:>5}        {stats['target_voices']:>5}
🎬 ویدیو           {stats['my_videos']:>5}        {stats['target_videos']:>5}
🎨 استیکر          {stats['my_stickers']:>5}        {stats['target_stickers']:>5}
🎞️ گیف             {stats['my_gifs']:>5}        {stats['target_gifs']:>5}
📁 فایل            {stats['my_files']:>5}        {stats['target_files']:>5}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 بیشترین پیام: {winner}
📈 نسبت: {ratio}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
            except Exception as e: await event.respond(f"⚠️ خطا: {str(e)[:100]}")
            return
        
        if cmd in ['.پنل', 'پنل', '/panel']:
            try:
                results = await self.client.inline_query(BOT_USERNAME.replace('@', ''), '')
                if results and len(results) > 0:
                    await results[0].click(chat_id)
                    await event.delete()
                else: await event.edit("❌ پنل یافت نشد")
            except Exception as e: await event.edit(f"❌ خطا: {str(e)[:100]}")
            return
        
        if cmd.startswith('.اهنگ '):
            song = cmd[6:].strip()
            if not song: await event.edit("❌ نام آهنگ را وارد کنید"); return
            await event.edit(f"🎵 جستجو: {song}...")
            try:
                results = await self.client.inline_query(MUSIC_BOT.replace('@', ''), song)
                if results and len(results) > 0:
                    await results[0].click(chat_id)
                    await event.delete()
                else: await event.edit(f"❌ '{song}' پیدا نشد")
            except Exception as e: await event.edit(f"❌ خطا: {str(e)[:100]}")
            return
        
        if cmd.startswith('تایم ') and not cmd.startswith('تایم روشن') and not cmd.startswith('تایم خاموش') and not cmd.startswith('تایمر'):
            m = re.match(r'^تایم\s+([\d\.]+)$', cmd)
            if m:
                indices = []
                for p in m.group(1).split('.'):
                    try:
                        idx = int(p)
                        if 0 <= idx < len(classic_fonts): indices.append(idx)
                    except: pass
                if indices:
                    self.time_font_indices = indices
                    db.update_selfbot_setting(self.user_id, 'time_font_indices', ','.join(map(str, indices)))
                    await event.edit(f"✅ فونت‌های تایم: {indices}")
                else: await event.edit(f"❌ ایندکس نامعتبر (0 تا {len(classic_fonts)-1})")
            return
        
        if cmd.startswith('.فیلتر '):
            word = cmd[8:].strip()
            if word:
                db.add_filter_word(self.user_id, word)
                await event.edit(f"✅ {word} اضافه شد")
            else: await event.edit("❌ کلمه را وارد کنید")
            return
        
        if cmd.startswith('حذف فیلتر '):
            word = cmd[11:].strip()
            if word:
                db.remove_filter_word(self.user_id, word)
                await event.edit(f"✅ {word} حذف شد")
            else: await event.edit("❌ کلمه را وارد کنید")
            return
        
        if cmd == 'لیست فیلتر':
            words = db.get_filter_words(self.user_id)
            if words:
                text = "📜 کلمات فیلتر:\n\n"
                for i, w in enumerate(words, 1):
                    text += f"{i}. {w['word']} - {'فعال' if w['enabled'] else 'غیرفعال'}\n"
                await event.edit(text)
            else: await event.edit("📭 لیست خالی است")
            return
        
        if cmd == 'فیلتر روشن':
            db.set_filter_enabled(self.user_id, True)
            await event.edit("✅ فیلتر فعال شد")
            return
        
        if cmd == 'فیلتر خاموش':
            db.set_filter_enabled(self.user_id, False)
            await event.edit("✅ فیلتر غیرفعال شد")
            return
        
        # قفل رسانه
        lock_cmds = {'قفل لینک':'lock_link','قفل عکس':'lock_photo','قفل ویدیو':'lock_video','قفل استیکر':'lock_sticker',
                     'قفل گیف':'lock_gif','قفل ویس':'lock_voice','قفل فایل':'lock_file','قفل موزیک':'lock_music',
                     'قفل ویدیو نوت':'lock_video_note','قفل کانتکت':'lock_contact','قفل لوکیشن':'lock_location',
                     'قفل ایموجی':'lock_emoji','قفل متن':'lock_text'}
        for name, lt in lock_cmds.items():
            if cmd == f'{name} روشن':
                target = 0
                if event.is_reply: target = (await event.get_reply_message()).sender_id
                elif isinstance(event.message.peer_id, PeerUser): target = chat_id
                db.set_user_lock(self.user_id, target, lt, True)
                await event.edit(f"✅ {name} برای {'همه' if target == 0 else f'کاربر {target}'} فعال شد")
                return
            if cmd == f'{name} خاموش':
                target = 0
                if event.is_reply: target = (await event.get_reply_message()).sender_id
                elif isinstance(event.message.peer_id, PeerUser): target = chat_id
                db.set_user_lock(self.user_id, target, lt, False)
                await event.edit(f"✅ {name} برای {'همه' if target == 0 else f'کاربر {target}'} غیرفعال شد")
                return
        
        if cmd == 'وضعیت':
            await event.edit(self.format_status_info(settings))
            return
        
        if re.match(r'^حذف\s+(\d+)$', cmd):
            num = int(re.match(r'^حذف\s+(\d+)$', cmd).group(1))
            msgs = []
            async for m in self.client.iter_messages(chat_id, limit=num):
                if m.sender_id == self.my_id: msgs.append(m.id)
            if msgs:
                await self.client.delete_messages(chat_id, msgs)
                await event.edit(f"✅ {len(msgs)} پیام حذف شد")
            else: await event.edit("⚠️ پیامی یافت نشد")
            return
        
        if cmd == 'حذف کامل':
            await event.edit("⏳ در حال حذف...")
            deleted, failed, batch = 0, 0, []
            try:
                async for m in self.client.iter_messages(chat_id, limit=None, from_user='me'):
                    batch.append(m.id)
                    if len(batch) >= 50:
                        try:
                            await self.client.delete_messages(chat_id, batch)
                            deleted += len(batch)
                            batch = []
                            await asyncio.sleep(0.5)
                        except FloodWaitError as e:
                            await asyncio.sleep(e.seconds + 1)
                            try:
                                await self.client.delete_messages(chat_id, batch)
                                deleted += len(batch)
                                batch = []
                            except: failed += len(batch); batch = []
                        except: failed += len(batch); batch = []
                if batch:
                    try:
                        await self.client.delete_messages(chat_id, batch)
                        deleted += len(batch)
                    except: failed += len(batch)
                await event.edit(f"✅ {deleted} پیام حذف شد" + (f"\n❌ {failed} ناموفق" if failed > 0 else ""))
            except Exception as e: await event.edit(f"⚠️ خطا: {str(e)[:100]}")
            return
        
        if cmd == 'پینگ':
            start = time.time()
            await event.edit("🏓 پینگ: ...")
            await event.edit(f"🏓 پینگ: {round((time.time() - start) * 1000, 2)} ms")
            return
        
        # استایل
        style_cmds = {'بولد':'بولد','زیرخط':'زیرخط','خط خورده':'خط خورده','نقل قول':'نقل قول','اسپویلر':'اسپویلر','کج':'کج','کد':'کد','پیش':'پیش'}
        for name, style in style_cmds.items():
            if cmd == f'{name} روشن':
                db.update_selfbot_setting(self.user_id, 'text_style', style)
                await event.edit(f"✅ استایل {name} فعال شد")
                return
            if cmd == f'{name} خاموش':
                if db.get_selfbot_settings(self.user_id).get('text_style') == style:
                    db.update_selfbot_setting(self.user_id, 'text_style', None)
                    await event.edit(f"✅ استایل {name} غیرفعال شد")
                else: await event.edit(f"⚠️ استایل {name} فعال نیست")
                return
        
        if cmd == 'تایم روشن':
            db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
            await self.update_profile_name()
            await event.delete()
            return
        
        if cmd == 'تایمر پرچم روشن':
            db.update_selfbot_setting(self.user_id, 'time_enabled', 1)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 1)
            await self.update_profile_name()
            await event.delete()
            return
        
        if cmd == 'تایم خاموش':
            db.update_selfbot_setting(self.user_id, 'time_enabled', 0)
            db.update_selfbot_setting(self.user_id, 'flag_enabled', 0)
            await self.restore_profile_name()
            await event.delete()
            return
        
        if cmd == 'فعال اتوسین':
            db.update_selfbot_setting(self.user_id, 'autosend_mode', 1)
            self.autosend_enabled = True
            await event.edit("✅ اتوسین فعال شد")
            return
        
        if cmd == 'غیرفعال اتوسین':
            db.update_selfbot_setting(self.user_id, 'autosend_mode', 0)
            self.autosend_enabled = False
            await event.edit("✅ اتوسین غیرفعال شد")
            return
        
        if cmd == 'اسپم روشن':
            db.set_spam_settings(self.user_id, spam_protection=1)
            await event.edit("✅ حفاظت اسپم فعال شد")
            return
        
        if cmd == 'اسپم خاموش':
            db.set_spam_settings(self.user_id, spam_protection=0)
            await event.edit("✅ حفاظت اسپم غیرفعال شد")
            return
        
        if cmd == 'وضعیت اسپم':
            s = db.get_spam_settings(self.user_id)
            await event.edit(f"🛡️ حفاظت اسپم:\n🔒 وضعیت: {'فعال' if s.get('spam_protection') else 'غیرفعال'}\n📊 محدودیت: {s.get('spam_limit', 10)} پیام\n⏱️ زمان: {s.get('mute_duration', 10)} ثانیه")
            return
        
        if cmd.startswith('تنظیم اسپم '):
            try:
                parts = cmd.split()
                if len(parts) == 3:
                    db.set_spam_settings(self.user_id, spam_limit=int(parts[1]), mute_duration=int(parts[2]))
                    await event.edit(f"✅ تنظیم شد: {parts[1]} پیام در {parts[2]} ثانیه")
                else: await event.edit("⚠️ فرمت: تنظیم اسپم [تعداد] [زمان]")
            except: await event.edit("⚠️ اعداد معتبر وارد کنید")
            return
        
        # انیمیشن‌ها
        if cmd == 'قلب پیشرفته':
            await event.delete()
            try:
                msg = await self.client.send_message(chat_id, "❤️")
                await advanced_heart_animation(msg)
            except: pass
            return
        
        if cmd == 'عشق':
            await event.delete()
            try:
                msg = await event.respond("💝")
                await advanced_heart_animation(msg)
            except: pass
            return
        
        if cmd == 'سنتت':
            await event.delete()
            try:
                msg = await event.respond("🕯️")
                for i in range(101):
                    bar = "█" * int(i / 100 * 20) + "░" * (20 - int(i / 100 * 20))
                    await msg.edit(f"🕯️ {i}% [{bar}]")
                    await asyncio.sleep(0.03)
                await asyncio.sleep(1)
                await msg.edit("✅ انجام شد 🥴")
            except: pass
            return
        
        if cmd == 'هک':
            await event.delete()
            try:
                msg = await event.respond("🔍")
                for step in ["User online: True\nTelegram access: True\nRead Storage: True",
                             "Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]",
                             "Hacking... 25%\n[█████░░░░░░░░░░░░░░░]",
                             "Hacking... 50%\n[██████████░░░░░░░░░░]",
                             "Hacking... 75%\n[███████████████░░░░░]",
                             "Hacking... 100%\n[████████████████████]",
                             "✅ هک کامل شد"]:
                    await asyncio.sleep(2)
                    await msg.edit(step)
            except: pass
            return
        
        if cmd == 'شروع':
            await event.delete()
            try: await event.respond("🌟 سلف‌بات شروع شد")
            except: pass
            return
        
        if cmd == 'قلب':
            await event.delete()
            await self.heart_animation(chat_id)
            return
        
        if cmd == 'ماه':
            await event.delete()
            await self.moon_animation(chat_id)
            return
        
        # لیست دشمن
        if cmd == 'لیست دشمن':
            await self.handle_list_enemies_command(event)
            return
        
        # اسپم
        if cmd == 'لیست اسپم':
            await self.handle_list_spam_command(event)
            return
        if cmd == 'پاک کردن اسپم':
            await self.handle_clear_spam_command(event)
            return
        if re.match(r'^حذف اسپم\s+(\d+)$', cmd):
            await self.handle_delete_spam_command(event)
            return
        if cmd == 'اضافه اسپم':
            await self.handle_add_spam_command(event)
            return
        if cmd == 'اتمام اسپم':
            await self.handle_end_spam_command(event)
            return
        
        # تغییر نام و بیو
        if re.match(r'^تغییر اسم\s+(.+)$', cmd):
            await self.handle_change_name_command(event)
            return
        if re.match(r'^تغییر بیو\s+(.+)$', cmd):
            await self.handle_change_bio_command(event)
            return
        
        # کامنت
        if re.match(r'^کامنت\s+(.+)$', cmd):
            await self.handle_comment_command(event)
            return
        
        # کانال‌ها
        if cmd == 'کانال‌ها':
            await self.handle_channels_command(event)
            return
        if cmd == 'حذف کانال':
            await self.handle_delete_channel_command(event)
            return
        if cmd == 'تست کانال':
            await self.handle_test_channel_command(event)
            return
        
        # دشمن/دوست
        if re.match(r'^دشمن\s*(@\w+|-\d+|\d+)?$', cmd):
            await self.handle_enemy_command(event, 'add')
            return
        if re.match(r'^دوست\s*(@\w+|-\d+|\d+)?$', cmd):
            await self.handle_enemy_command(event, 'remove')
            return
        
        # قفل پیوی
        if re.match(r'^قفل پیوی\s*(@\w+|-\d+|\d+)?$', cmd):
            await self.handle_lock_pv_command(event, 'lock')
            return
        if re.match(r'^باز پی\s*(@\w+|-\d+|\d+)?$', cmd):
            await self.handle_lock_pv_command(event, 'unlock')
            return
        if cmd == 'قفل پیوی همه':
            await self.handle_lock_all_pv_command(event, True)
            return
        if cmd == 'باز پی همه':
            await self.handle_lock_all_pv_command(event, False)
            return
        
        # اطلاعات
        if cmd == 'اطلاعات':
            await self.handle_info_command(event)
            return
        if cmd == 'دانلود پروفایل':
            await self.handle_download_profile_command(event)
            return
        if cmd == 'ست پروف':
            await self.handle_set_profile_command(event, 'photo')
            return
        if cmd == 'ست بیو':
            await self.handle_set_profile_command(event, 'bio')
            return
        if cmd == 'حذف ست پروف':
            await self.handle_delete_profile_command(event, 'photo')
            return
        if cmd == 'حذف ست بیو':
            await self.handle_delete_profile_command(event, 'bio')
            return
        if cmd == 'تاریخ کامل':
            await self.handle_full_date_command(event)
            return
        
        # اسپم
        if re.match(r'^اسپم\s+(\d+)\s+(.+)$', cmd):
            await self.handle_spam_command(event)
            return
        if cmd == 'بلاک':
            await self.handle_block_command(event)
            return
        
        # ریکت
        if re.match(r'^ریکت\s*([\U0001F300-\U0001F9FF]+)?$', cmd):
            await self.handle_reaction_command(event, 'set')
            return
        if cmd == 'حذف ریکت':
            await self.handle_reaction_command(event, 'remove')
            return
        
        # هوش مصنوعی
        if cmd in ['پیوی ۱', 'پیوی ۲', 'پیوی ۳', 'خاموش پیوی']:
            await self.handle_ai_command(event, 'pm')
            return
        if cmd in ['گروه ۱', 'گروه ۲', 'گروه ۳', 'خاموش گروه']:
            await self.handle_ai_command(event, 'group')
            return
        
        if cmd == 'من کی ام':
            await self.handle_whoami_command(event)
            return
        
        if cmd == 'تنظیم گزارش':
            await self.handle_report_group_command(event, 'set')
            return
        if cmd == 'گروه گزارش':
            await self.handle_report_group_command(event, 'get')
            return
        
        if cmd == 'سرچ':
            await self.handle_search_command(event)
            return
        if cmd == 'خروج سرچ':
            await self.handle_exit_search_command(event)
            return
        
        return
    
    # ========== توابع کمکی دستورات ==========
    def format_status_info(self, settings):
        try:
            conn = sqlite3.connect('main_database.db')
            user_count = conn.cursor().execute('SELECT COUNT(*) FROM user_memory').fetchone()[0]
            conn.close()
        except: user_count = 0
        ai = settings.get('ai_status', {})
        spam = db.get_spam_settings(self.user_id)
        return f"""
🤖 وضعیت سلف‌بات
━━━━━━━━━━━━━━━━━━━━
🕐 تایم: {'فعال' if settings.get('time_enabled') else 'غیرفعال'}
🏳️ پرچم: {'فعال' if settings.get('flag_enabled') else 'غیرفعال'}
🎨 فونت: {'همه' if self.time_font_indices == 'all' else f'فونت‌های {self.time_font_indices}'}
✍️ استایل: {settings.get('text_style') or 'هیچ'}

🤖 هوش مصنوعی:
• پی‌وی: {'هوش ۱ (Gemini)' if ai.get('ai_1_pm') else 'هوش ۲ (Paxsenix)' if ai.get('ai_2_pm') else 'هوش ۳ (DeepSeek)' if ai.get('ai_3_pm') else 'هیچ'}
• گروه: {'هوش ۱ (Gemini)' if ai.get('ai_1_group') else 'هوش ۲ (Paxsenix)' if ai.get('ai_2_group') else 'هوش ۳ (DeepSeek)' if ai.get('ai_3_group') else 'هیچ'}

🔒 قفل پیوی همگانی: {'فعال' if settings.get('pv_lock_all') else 'غیرفعال'}
🔒 پی‌وی قفل‌شده: {len(db.get_locked_pvs(self.user_id))}
🚫 فیلتر: {'فعال' if db.get_filter_enabled(self.user_id) else 'غیرفعال'}

📊 آمار:
• دشمنان: {len(db.get_enemies(self.user_id))}
• کانال‌ها: {len(db.get_auto_comments(self.user_id))}
• رسانه‌ها: {len([m for m in media_cache.values() if m.get('owner_id') == self.user_id])}
• فیلتر فعال: {len([w for w in db.get_filter_words(self.user_id) if w['enabled']])}
• اسپم‌ها: {len(db.get_enemy_spam_messages(self.user_id))}
• کاربران: {user_count}

🛡️ حفاظت اسپم:
• وضعیت: {'فعال' if spam.get('spam_protection') else 'غیرفعال'}
• محدودیت: {spam.get('spam_limit', 10)} پیام در {spam.get('mute_duration', 10)} ثانیه
━━━━━━━━━━━━━━━━━━━━
✅ Self-Bot v{BOT_VERSION}
"""
    
    async def handle_list_enemies_command(self, event):
        enemies = db.get_enemies(self.user_id)
        if enemies:
            text = "📋 لیست دشمنان:\n\n"
            for i, eid in enumerate(enemies, 1):
                try: text += f"{i}. {(await self.client.get_entity(eid)).first_name or 'کاربر'} ({eid})\n"
                except: text += f"{i}. کاربر {eid}\n"
            await event.edit(text)
        else: await event.edit("📭 لیست خالی است")
    
    async def handle_list_spam_command(self, event):
        msgs = db.get_enemy_spam_messages(self.user_id)
        if msgs:
            text = "📜 پیام‌های اسپم:\n\n" + "\n".join([f"{i}. {m['text']}" for i, m in enumerate(msgs, 1)]) + f"\n\n📊 تعداد: {len(msgs)}"
            await event.edit(text)
        else: await event.edit("📭 لیست خالی است")
    
    async def handle_clear_spam_command(self, event):
        db.clear_enemy_spam_messages(self.user_id)
        await event.edit("✅ اسپم‌ها پاک شدند")
    
    async def handle_delete_spam_command(self, event):
        mid = int(re.match(r'^حذف اسپم\s+(\d+)$', event.text.lower()).group(1))
        msgs = db.get_enemy_spam_messages(self.user_id)
        if 1 <= mid <= len(msgs):
            db.delete_enemy_spam_message(self.user_id, msgs[mid - 1]['id'])
            await event.edit(f"✅ پیام شماره {mid} حذف شد")
        else: await event.edit(f"⚠️ پیام {mid} وجود ندارد")
    
    async def handle_add_spam_command(self, event):
        self.adding_spam = True
        await event.edit("📝 حالت اضافه کردن اسپم فعال شد\nبرای پایان: اتمام اسپم")
    
    async def handle_end_spam_command(self, event):
        self.adding_spam = False
        await event.edit("✅ حالت اضافه کردن اسپم غیرفعال شد")
    
    async def handle_change_name_command(self, event):
        name = re.match(r'^تغییر اسم\s+(.+)$', event.text).group(1)
        db.set_current_name(self.user_id, name)
        await self.client(UpdateProfileRequest(first_name=name))
        self.BASE_NAME = name
        await event.edit(f"✅ نام به {name} تغییر کرد")
    
    async def handle_change_bio_command(self, event):
        bio = re.match(r'^تغییر بیو\s+(.+)$', event.text).group(1)
        await self.client(UpdateProfileRequest(about=bio))
        await event.edit(f"✅ بیو به {bio} تغییر کرد")
    
    async def handle_comment_command(self, event):
        text = event.text[7:].strip()
        chat = await event.get_chat()
        chat_type = "کانال" if hasattr(chat, 'broadcast') and chat.broadcast else "گروه"
        db.set_auto_comment(self.user_id, chat.id, text, chat.title, chat_type, getattr(chat, 'username', None))
        await event.edit(f"✅ کامنت در {chat_type} تنظیم شد")
    
    async def handle_channels_command(self, event):
        comments = db.get_auto_comments(self.user_id)
        if comments:
            text = "📊 کانال‌ها:\n\n"
            for c in comments:
                text += f"• {c['channel_title']} ({c['channel_type']})\n  متن: {c['comment_text'][:30]}...\n\n"
            await event.edit(text)
        else: await event.edit("📭 هیچ کانالی تنظیم نشده")
    
    async def handle_delete_channel_command(self, event):
        chat = await event.get_chat()
        ac = db.get_auto_comment(self.user_id, chat.id)
        if ac:
            db.remove_auto_comment(self.user_id, chat.id)
            await event.edit(f"✅ {ac['channel_title']} حذف شد")
        else: await event.edit("⚠️ این کانال تنظیم نشده")
    
    async def handle_test_channel_command(self, event):
        chat = await event.get_chat() if not event.is_reply else await (await event.get_reply_message()).get_chat()
        text = f"🔍 اطلاعات تست:\n\nچت: {chat.title}\nنوع: {'کانال' if hasattr(chat, 'broadcast') and chat.broadcast else 'گروه'}\nآیدی: {chat.id}\n"
        ac = db.get_auto_comment(self.user_id, chat.id)
        text += f"تنظیم شده: {'✅' if ac else '❌'}"
        await event.edit(text)
    
    async def handle_enemy_command(self, event, action):
        target = await get_target_user(event, self.client)
        if not target and isinstance(event.message.peer_id, PeerUser): target = event.message.peer_id.user_id
        if target:
            if action == 'add':
                db.add_enemy(self.user_id, target)
                await event.edit("✅ دشمن اضافه شد")
                await self.spam_enemy(target)
            else:
                db.remove_enemy(self.user_id, target)
                await event.edit("✅ دوست حذف شد")
                if target in self.spam_tasks:
                    self.spam_tasks[target].cancel()
                    del self.spam_tasks[target]
        else: await event.edit("⚠️ کاربر مشخص نشد")
    
    async def handle_lock_pv_command(self, event, action):
        target = await get_target_user(event, self.client)
        if not target and isinstance(event.message.peer_id, PeerUser): target = event.message.peer_id.user_id
        if target:
            if action == 'lock':
                db.add_locked_pv(self.user_id, target)
                await event.edit(f"✅ قفل پیوی برای {target} فعال شد")
            else:
                db.remove_locked_pv(self.user_id, target)
                await event.edit(f"✅ قفل پیوی برای {target} غیرفعال شد")
        else: await event.edit("⚠️ کاربر مشخص نشد")
    
    async def handle_lock_all_pv_command(self, event, lock):
        db.update_selfbot_setting(self.user_id, 'pv_lock_all', 1 if lock else 0)
        await event.edit("✅ قفل پیوی همگانی " + ("فعال" if lock else "غیرفعال") + " شد")
    
    async def heart_animation(self, chat_id):
        try:
            msg = await self.client.send_message(chat_id, HEARTS[0])
            for i in range(1, 99999):
                await asyncio.sleep(4)
                await self.client.edit_message(chat_id, msg, HEARTS[i % len(HEARTS)])
            if chat_id != abs(self.report_config.report_group_id):
                await self.client.delete_messages(chat_id, msg)
        except: pass
    
    async def moon_animation(self, chat_id):
        try:
            msg = await self.client.send_message(chat_id, MOONS[0])
            for i in range(1, 99999):
                await asyncio.sleep(3)
                await self.client.edit_message(chat_id, msg, MOONS[i % len(MOONS)])
            if chat_id != abs(self.report_config.report_group_id):
                await self.client.delete_messages(chat_id, msg)
        except: pass
    
    async def handle_info_command(self, event):
        user = await (await event.get_reply_message()).get_sender() if event.is_reply else await self.client.get_me()
        try: bio = (await self.client(GetFullUserRequest(user.id))).full_user.about or "ندارد"
        except: bio = "ندارد"
        await event.edit(f"📋 اطلاعات کاربر:\n\n👤 یوزرنیم: @{user.username}" if user.username else "ندارد" + f"\n🆔 ID: {user.id}\n📛 نام: {user.first_name or ''} {user.last_name or ''}\n📝 بیو: {bio}")
        await event.delete()
    
    async def handle_download_profile_command(self, event):
        user = await (await event.get_reply_message()).get_sender() if event.is_reply else await self.client.get_me()
        if user.photo:
            try:
                path = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user.id}.jpg")
                if path:
                    await self.client.send_file(event.chat_id, path, caption=f"📸 پروفایل {user.first_name or 'کاربر'}")
                    os.remove(path)
                else: await event.edit("⚠️ خطا در دانلود")
            except: await event.edit("⚠️ خطا در دانلود")
        else: await event.edit("⚠️ عکس پروفایلی وجود ندارد")
        await event.delete()
    
    async def handle_set_profile_command(self, event, type_):
        if event.is_reply:
            user = await (await event.get_reply_message()).get_sender()
            if type_ == 'photo':
                if user.photo:
                    path = await self.client.download_profile_photo(user, file=f"{MEDIA_FOLDER}/profile_{user.id}.jpg")
                    if path:
                        try:
                            me = await self.client.get_me()
                            if me.photo:
                                photos = await self.client.get_profile_photos(me.id, limit=1)
                                if photos: await self.client(DeletePhotosRequest(id=[photos[0]]))
                            file = await self.client.upload_file(path)
                            await self.client(UploadProfilePhotoRequest(file=file))
                            await event.edit("✅ عکس پروفایل ست شد")
                            os.remove(path)
                        except: await event.edit("⚠️ خطا")
                    else: await event.edit("⚠️ خطا در دانلود")
                else: await event.edit("⚠️ این کاربر عکس پروفایل ندارد")
            else:
                try:
                    bio = (await self.client(GetFullUserRequest(user.id))).full_user.about or ""
                    await self.client(UpdateProfileRequest(about=bio))
                    await event.edit("✅ بیو ست شد")
                except: await event.edit("⚠️ خطا")
        else: await event.edit("⚠️ روی پیام کاربر ریپلای کنید")
        await event.delete()
    
    async def handle_delete_profile_command(self, event, type_):
        if type_ == 'photo':
            me = await self.client.get_me()
            if me.photo:
                try:
                    photos = await self.client.get_profile_photos(me.id, limit=1)
                    if photos: await self.client(DeletePhotosRequest(id=[photos[0]]))
                    await event.edit("✅ عکس پروفایل حذف شد")
                except: await event.edit("⚠️ خطا")
            else: await event.edit("⚠️ عکس پروفایلی وجود ندارد")
        else:
            try:
                await self.client(UpdateProfileRequest(about=""))
                await event.edit("✅ بیو خالی شد")
            except: await event.edit("⚠️ خطا")
        await event.delete()
    
    async def handle_full_date_command(self, event):
        await self.client.send_message(event.chat_id, get_full_date_info())
        await event.delete()
    
    async def handle_spam_command(self, event):
        m = re.match(r'^اسپم\s+(\d+)\s+(.+)$', event.text.lower())
        num, text = int(m.group(1)), m.group(2)
        if event.is_reply: text = (await event.get_reply_message()).text or text
        for _ in range(num):
            await self.client.send_message(event.chat_id, text)
            await asyncio.sleep(0.05)
        await event.edit(f"✅ {num} پیام اسپم ارسال شد")
    
    async def handle_block_command(self, event):
        if isinstance(event.message.peer_id, PeerUser):
            await self.client(BlockRequest(id=event.message.peer_id.user_id))
            await event.edit("✅ کاربر بلاک شد")
        else: await event.edit("⚠️ فقط در پی‌وی")
    
    async def handle_reaction_command(self, event, action):
        chat_id = None
        if isinstance(event.message.peer_id, PeerUser): chat_id = event.message.peer_id.user_id
        elif isinstance(event.message.peer_id, PeerChannel): chat_id = event.message.peer_id.channel_id
        elif isinstance(event.message.peer_id, PeerChat): chat_id = event.message.peer_id.chat_id
        target = await get_target_user(event, self.client)
        if action == 'set':
            emoji = re.match(r'^ریکت\s*([\U0001F300-\U0001F9FF]+)?$', event.text.lower())
            if not emoji or not emoji.group(1):
                await event.edit("⚠️ ایموجی وارد کنید"); return
            if emoji.group(1) in ALLOWED_EMOJIS:
                db.set_reaction(self.user_id, chat_id, target, emoji.group(1))
                await event.edit(f"✅ ریکت {emoji.group(1)} تنظیم شد")
            else: await event.edit(f"⚠️ ایموجی {emoji.group(1)} مجاز نیست")
        else:
            if target:
                db.remove_reaction(self.user_id, chat_id, target)
                await event.edit("✅ ریکت حذف شد")
            else: await event.edit("⚠️ کاربر مشخص نشد")
    
    async def handle_ai_command(self, event, ai_type):
        cmd = event.text.lower()
        ai = db.get_selfbot_settings(self.user_id).get('ai_status', {})
        if ai_type == 'pm':
            if cmd == 'پیوی 1': ai.update({'ai_1_pm': True, 'ai_2_pm': False, 'ai_3_pm': False}); msg = '✅ هوش ۱ (Gemini) در پی‌وی روشن شد'
            elif cmd == 'پیوی 2': ai.update({'ai_1_pm': False, 'ai_2_pm': True, 'ai_3_pm': False}); msg = '✅ هوش ۲ (Paxsenix) در پی‌وی روشن شد'
            elif cmd == 'پیوی 3': ai.update({'ai_1_pm': False, 'ai_2_pm': False, 'ai_3_pm': True}); msg = '✅ هوش ۳ (DeepSeek) در پی‌وی روشن شد'
            else: ai.update({'ai_1_pm': False, 'ai_2_pm': False, 'ai_3_pm': False}); msg = '✅ همه هوش‌ها در پی‌وی خاموش شدند'
        else:
            if cmd == 'گروه 1': ai.update({'ai_1_group': True, 'ai_2_group': False, 'ai_3_group': False}); msg = '✅ هوش ۱ (Gemini) در گروه روشن شد'
            elif cmd == 'گروه 2': ai.update({'ai_1_group': False, 'ai_2_group': True, 'ai_3_group': False}); msg = '✅ هوش ۲ (Paxsenix) در گروه روشن شد'
            elif cmd == 'گروه 3': ai.update({'ai_1_group': False, 'ai_2_group': False, 'ai_3_group': True}); msg = '✅ هوش ۳ (DeepSeek) در گروه روشن شد'
            else: ai.update({'ai_1_group': False, 'ai_2_group': False, 'ai_3_group': False}); msg = '✅ همه هوش‌ها در گروه خاموش شدند'
        db.update_ai_status(self.user_id, ai)
        await event.edit(msg)
    
    async def handle_whoami_command(self, event):
        if isinstance(event.message.peer_id, PeerUser):
            uid = event.sender_id
            info = db.get_user_info(uid)
            text = f"👤 اطلاعات شما:\n• نام: {db.get_user_name(uid)}\n• آی‌دی: {uid}"
            if info: text += "\n📝 اطلاعات ذخیره شده:\n" + "\n".join([f"• {k}: {v}" for k, v in info.items()])
            await event.edit(text)
    
    async def handle_report_group_command(self, event, action):
        if action == 'set':
            if isinstance(event.message.peer_id, (PeerChannel, PeerChat)):
                cid = event.message.peer_id.channel_id if isinstance(event.message.peer_id, PeerChannel) else event.message.peer_id.chat_id
                self.report_config.set_report_group(cid)
                await event.edit(f"✅ گروه گزارش تنظیم شد\nآیدی: {cid}")
            else: await event.edit("⚠️ فقط در گروه")
        else: await event.edit(f"📍 گروه گزارش:\nآیدی: {self.report_config.report_group_id}")
    
    async def handle_search_command(self, event):
        self.search_mode = True
        await event.edit('🔍 حالت سرچ فعال شد.\nبرای خروج: خروج سرچ')
    
    async def handle_exit_search_command(self, event):
        self.search_mode = False
        self.last_search_results = []
        await event.edit('✅ حالت سرچ غیرفعال شد')
    
    async def handle_google_search(self, event, query):
        try:
            await event.edit(f'🔍 در حال جستجو: {query}')
            resp = requests.get(GOOGLE_SEARCH_URL, params={'key': GOOGLE_SEARCH_API_KEY, 'cx': GOOGLE_CSE_ID, 'q': query, 'num': 5}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if 'items' in data:
                    text = f"🔍 نتایج جستجو برای: {query}\n\n"
                    for i, item in enumerate(data['items'][:5], 1):
                        text += f"{i}. {item.get('title', 'بدون عنوان')}\n   {item.get('snippet', 'بدون توضیح')[:100]}...\n   🔗 {item.get('link', '')}\n\n"
                    await event.edit(text)
                else: await event.edit(f'❌ نتیجه‌ای پیدا نشد')
            else: await event.edit(f'❌ خطا: {resp.status_code}')
        except Exception as e: await event.edit(f'❌ خطا: {str(e)}')
    
    async def handle_outgoing_message(self, event):
        text = event.text or ""
        
        if self.adding_spam and text and not text.startswith(('لیست','شروع','تایم','قلب','ماه','اطلاعات','دانلود','تاریخ','فعال','غیرفعال','حذف','ست','بولد','زیرخط','خط خورده','نقل قول','اسپویلر','کج','کد','پیش','اسپم','بلاک','ریکت','پیوی','گروه','درباره','من کی ام','قفل','باز','تنظیم','گروه گزارش','دشمن','دوست','کانال','کامنت','تست','لیست دشمن','لیست اسپم','پاک کردن اسپم','حذف اسپم','اضافه اسپم','اتمام اسپم','تغییر اسم','تغییر بیو','تغییر پروفایل','پروف','اسپم روشن','اسپم خاموش','پینگ','سرچ','خروج سرچ','قلب پیشرفته','عشق','سنتت','هک','وضعیت','.پنل','پنل','/panel','.اهنگ','تنظیم اسپم','سلف روشن','سلف خاموش','پین','تگ ادمین','امار گپ','.کد')):
            db.add_enemy_spam_message(self.user_id, text)
            try: await event.delete()
            except: pass
            return
        
        if event.text:
            style = db.get_selfbot_settings(self.user_id).get('text_style')
            if style and not text.startswith(('لیست','شروع','تایم','قلب','ماه','اطلاعات','دانلود','تاریخ','فعال','غیرفعال','حذف','ست','بولد','زیرخط','خط خورده','نقل قول','اسپویلر','کج','کد','پیش','اسپم','بلاک','ریکت','پیوی','گروه','درباره','من کی ام','قفل','باز','تنظیم','گروه گزارش','دشمن','دوست','کانال','کامنت','تست','لیست دشمن','لیست اسپم','پاک کردن اسپم','حذف اسپم','اضافه اسپم','اتمام اسپم','تغییر اسم','تغییر بیو','تغییر پروفایل','پروف','اسپم روشن','اسپم خاموش','پینگ','سرچ','خروج سرچ','قلب پیشرفته','عشق','سنتت','هک','وضعیت','.پنل','پنل','/panel','.اهنگ','تنظیم اسپم','سلف روشن','سلف خاموش','پین','تگ ادمین','امار گپ','.کد')):
                try:
                    t, entities = await apply_text_style(text, style)
                    if entities: await event.message.edit(t, formatting_entities=entities)
                except: pass
        
        if self.search_mode and text and not text.startswith(('لیست','شروع','تایم','قلب','ماه','اطلاعات','دانلود','تاریخ','فعال','غیرفعال','حذف','ست','بولد','زیرخط','خط خورده','نقل قول','اسپویلر','کج','کد','پیش','اسپم','بلاک','ریکت','پیوی','گروه','درباره','من کی ام','قفل','باز','تنظیم','گروه گزارش','دشمن','دوست','کانال','کامنت','تست','لیست دشمن','لیست اسپم','پاک کردن اسپم','حذف اسپم','اضافه اسپم','اتمام اسپم','تغییر اسم','تغییر بیو','تغییر پروفایل','پروف','اسپم روشن','اسپم خاموش','پینگ','سرچ','خروج سرچ','قلب پیشرفته','عشق','سنتت','هک','وضعیت','.پنل','پنل','/panel','.اهنگ','تنظیم اسپم','سلف روشن','سلف خاموش','پین','تگ ادمین','امار گپ','.کد')):
            await self.handle_google_search(event, text)
            return
        
        if event.text:
            translated = await self.translate_text(event.text)
            if translated != event.text:
                try: await event.edit(translated)
                except: pass
    
    async def spam_enemy(self, enemy_id):
        if enemy_id in self.spam_tasks: return
        async def task():
            while db.is_enemy(self.user_id, enemy_id):
                msgs = db.get_enemy_spam_messages(self.user_id) or SPAM_MESSAGES
                for msg in msgs:
                    try: await self.client.send_message(enemy_id, msg['text'] if isinstance(msg, dict) else msg)
                    except: pass
                    await asyncio.sleep(1)
        self.spam_tasks[enemy_id] = asyncio.create_task(task())
    
    async def handle_translate_commands(self, event):
        text = event.raw_text.strip()
        langs = ["انگلیسی","عربی","عبری","روسی","ترکی"]
        for l in langs:
            if text.startswith(l):
                cmd = text.split()[1] if len(text.split()) > 1 else ""
                key = {'انگلیسی':'english','عربی':'arabic','عبری':'hebrew','روسی':'russian','ترکی':'turkish'}[l]
                self.translate_mode[key] = cmd == "روشن"
                db.update_selfbot_setting(self.user_id, f'translate_{key}', 1 if self.translate_mode[key] else 0)
                await event.edit(f"✅ ترجمه {l} {'روشن' if self.translate_mode[key] else 'خاموش'} شد")
                return
        if text.startswith("تاس"):
            try:
                n = int(text.split()[1])
                if 1 <= n <= 6:
                    await event.delete()
                    await self.force_dice(event.chat_id, "🎲", n)
            except: await event.delete()
            return
        if text in ["دارت","بسکتبال","فوتبال"]:
            await event.delete()
            await self.force_dice(event.chat_id, {"دارت":"🎯","بسکتبال":"🏀","فوتبال":"⚽️"}[text], {"دارت":6,"بسکتبال":5,"فوتبال":5}[text])
            return
    
    async def handle_action_commands(self, event):
        msg = event.text.strip()
        chat_id = event.chat_id
        await self.handle_translate_commands(event)
        if msg in ["دارت","بسکتبال","فوتبال"] or msg.startswith("تاس") or any(msg.startswith(l) and ("روشن" in msg or "خاموش" in msg) for l in ["انگلیسی","عربی","عبری","روسی","ترکی"]):
            return
        if msg.startswith('اکشن '):
            cmd = msg.replace('اکشن ', '').strip()
            if cmd == 'خاموش':
                if chat_id in self.active_actions:
                    action = await self.stop_action(chat_id)
                    await event.edit(f'✅ اکشن {action} خاموش شد')
                else: await event.edit('❌ هیچ اکشن فعالی وجود ندارد')
                return
            if cmd == 'لیست':
                if self.active_actions:
                    text = "🎭 اکشن‌های فعال:\n\n"
                    for cid, action in self.active_actions.items():
                        try: text += f"• {(await self.client.get_entity(cid)).first_name or 'چت'}: {action}\n"
                        except: text += f"• چت {cid}: {action}\n"
                    await event.edit(text)
                else: await event.edit('❌ هیچ اکشن فعالی وجود ندارد')
                return
            if cmd in action_types:
                if chat_id in self.active_actions:
                    old = await self.stop_action(chat_id)
                    await event.edit(f'⏹️ اکشن {old} خاموش شد\n✅ اکشن {cmd} فعال شد')
                else: await event.edit(f'✅ اکشن {cmd} فعال شد')
                await self.start_action(chat_id, cmd)
                await asyncio.sleep(3)
                await event.delete()
                return
            else:
                await event.edit(f'❌ اکشن "{cmd}" پشتیبانی نمی‌شود\n\n✅ اکشن‌های موجود:\n' + "\n".join([f"• {n}" for n in action_types.keys()]))
                return
        if msg == 'سرچ':
            self.search_mode = True
            await event.edit('🔍 حالت سرچ فعال شد.\nبرای خروج: خروج سرچ')
            return
        if msg == 'خروج سرچ':
            self.search_mode = False
            self.last_search_results = []
            await event.edit('✅ حالت سرچ غیرفعال شد')
            return
        if self.search_mode and msg:
            await self.handle_google_search(event, msg)
            return
        lang_map = {"english":"en","arabic":"ar","hebrew":"he","russian":"ru","turkish":"tr"}
        for lang, code in lang_map.items():
            if self.translate_mode.get(lang) and msg:
                try:
                    translated = GoogleTranslator(source='auto', target=code).translate(msg)
                    await event.edit(translated)
                    return
                except: pass

db = MainDatabase()
selfbot_managers = {}

# ========== توابع کیبورد ==========
def get_main_panel_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚈ زمان و پروفایل", callback_data=f"time_menu_{user_id}"), InlineKeyboardButton("☻ انیمیشن", callback_data=f"animation_menu_{user_id}"), InlineKeyboardButton("☗ مدیریت کاربران", callback_data=f"user_menu_{user_id}")],
        [InlineKeyboardButton("⊖ قفل رسانه", callback_data=f"lock_menu_{user_id}"), InlineKeyboardButton("✼ کامنت", callback_data=f"comment_menu_{user_id}"), InlineKeyboardButton("✿ عمومی", callback_data=f"general_menu_{user_id}")],
        [InlineKeyboardButton("☥ اکشن", callback_data=f"action_menu_{user_id}"), InlineKeyboardButton("⚕ بازی‌ها", callback_data=f"games_menu_{user_id}"), InlineKeyboardButton("❍ ترجمه", callback_data=f"translate_menu_{user_id}")],
        [InlineKeyboardButton("𖢅 گوگل", callback_data=f"google_menu_{user_id}"), InlineKeyboardButton("֍ اطلاعاتی", callback_data=f"info_menu_{user_id}"), InlineKeyboardButton("𖢨 پروفایل", callback_data=f"profile_menu_{user_id}")],
        [InlineKeyboardButton("⩐ استایل متن", callback_data=f"style_menu_{user_id}"), InlineKeyboardButton("𑪡 مدیریت پیام", callback_data=f"message_menu_{user_id}"), InlineKeyboardButton("☖ ریکشن", callback_data=f"reaction_menu_{user_id}")],
        [InlineKeyboardButton("𖥞 اسپم", callback_data=f"spam_menu_{user_id}"), InlineKeyboardButton("☗ تغییر پروفایل", callback_data=f"change_menu_{user_id}"), InlineKeyboardButton("⚇ مدیریت دشمنان", callback_data=f"enemy_menu_{user_id}")],
        [InlineKeyboardButton("✿ فیلتر کلمات", callback_data=f"filter_menu_{user_id}"), InlineKeyboardButton("⚉ حفاظت اسپم", callback_data=f"protection_menu_{user_id}"), InlineKeyboardButton("☥ هوش مصنوعی", callback_data=f"ai_menu_{user_id}")],
        [InlineKeyboardButton("֎ گزارش", callback_data=f"report_menu_{user_id}"), InlineKeyboardButton("🛠 ابزار", callback_data=f"tools_menu_{user_id}")],
        [InlineKeyboardButton("❌ بستن پنل", callback_data=f"close_panel_{user_id}")]
    ])

def get_tools_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 امار گپ", callback_data=f"exec_stats_{user_id}"), InlineKeyboardButton("🝰 کد QR", callback_data=f"exec_qr_{user_id}")],
        [InlineKeyboardButton("👑 تگ ادمین", callback_data=f"exec_tag_admin_{user_id}"), InlineKeyboardButton("📌 پین", callback_data=f"exec_pin_{user_id}")],
        [InlineKeyboardButton("🤖 سلف روشن", callback_data=f"exec_self_on_{user_id}"), InlineKeyboardButton("⛔ سلف خاموش", callback_data=f"exec_self_off_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

# ========== بقیه توابع کیبورد (سایر منوها) ==========
def get_time_menu_keyboard(user_id):
    s = db.get_selfbot_settings(user_id)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🕐 تایم روشن {'' if not s.get('time_enabled') else '✓'}", callback_data=f"exec_time_on_{user_id}"), InlineKeyboardButton(f"🏳️ تایمر پرچم {'' if not s.get('flag_enabled') else '✓'}", callback_data=f"exec_time_flag_{user_id}")],
        [InlineKeyboardButton(f"🚫 تایم خاموش {'' if s.get('time_enabled') else '✓'}", callback_data=f"exec_time_off_{user_id}"), InlineKeyboardButton("📅 تاریخ کامل", callback_data=f"exec_full_date_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_animation_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ قلب", callback_data=f"exec_heart_{user_id}"), InlineKeyboardButton("🌙 ماه", callback_data=f"exec_moon_{user_id}")],
        [InlineKeyboardButton("💖 قلب پیشرفته", callback_data=f"exec_advanced_heart_{user_id}"), InlineKeyboardButton("💝 عشق", callback_data=f"exec_love_{user_id}")],
        [InlineKeyboardButton("🕯️ سنتت", callback_data=f"exec_santet_{user_id}"), InlineKeyboardButton("💻 هک", callback_data=f"exec_hack_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_user_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥷 دشمن", callback_data=f"exec_enemy_{user_id}"), InlineKeyboardButton("🧸 دوست", callback_data=f"exec_friend_{user_id}")],
        [InlineKeyboardButton("🔒 قفل پیوی", callback_data=f"exec_lock_pv_{user_id}"), InlineKeyboardButton("🔓 باز پی", callback_data=f"exec_unlock_pv_{user_id}")],
        [InlineKeyboardButton("🔒 قفل پیوی همه", callback_data=f"exec_lock_all_{user_id}"), InlineKeyboardButton("🔓 باز پی همه", callback_data=f"exec_unlock_all_{user_id}"), InlineKeyboardButton("⛔ بلاک", callback_data=f"exec_block_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_lock_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 قفل لینک", callback_data=f"exec_lock_link_{user_id}"), InlineKeyboardButton("📸 قفل عکس", callback_data=f"exec_lock_photo_{user_id}"), InlineKeyboardButton("🎥 قفل ویدیو", callback_data=f"exec_lock_video_{user_id}")],
        [InlineKeyboardButton("🎨 قفل استیکر", callback_data=f"exec_lock_sticker_{user_id}"), InlineKeyboardButton("🎞️ قفل گیف", callback_data=f"exec_lock_gif_{user_id}"), InlineKeyboardButton("🎤 قفل ویس", callback_data=f"exec_lock_voice_{user_id}")],
        [InlineKeyboardButton("📁 قفل فایل", callback_data=f"exec_lock_file_{user_id}"), InlineKeyboardButton("🎵 قفل موزیک", callback_data=f"exec_lock_music_{user_id}"), InlineKeyboardButton("📹 قفل ویدیو نوت", callback_data=f"exec_lock_video_note_{user_id}")],
        [InlineKeyboardButton("📞 قفل کانتکت", callback_data=f"exec_lock_contact_{user_id}"), InlineKeyboardButton("📍 قفل لوکیشن", callback_data=f"exec_lock_location_{user_id}"), InlineKeyboardButton("😀 قفل ایموجی", callback_data=f"exec_lock_emoji_{user_id}")],
        [InlineKeyboardButton("📝 قفل متن", callback_data=f"exec_lock_text_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_comment_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 کامنت", callback_data=f"exec_comment_{user_id}"), InlineKeyboardButton("📊 کانال‌ها", callback_data=f"exec_channels_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف کانال", callback_data=f"exec_delete_channel_{user_id}"), InlineKeyboardButton("🔍 تست کانال", callback_data=f"exec_test_channel_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_general_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 وضعیت", callback_data=f"exec_status_{user_id}"), InlineKeyboardButton("ℹ️ درباره", callback_data=f"exec_about_{user_id}")],
        [InlineKeyboardButton("⏱️ پینگ", callback_data=f"exec_ping_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_action_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 اکشن [نام]", callback_data=f"exec_action_{user_id}"), InlineKeyboardButton("⏹️ اکشن خاموش", callback_data=f"exec_action_off_{user_id}")],
        [InlineKeyboardButton("📋 اکشن لیست", callback_data=f"exec_action_list_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_games_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 تاس ۱", callback_data=f"exec_dice_1_{user_id}"), InlineKeyboardButton("🎲 تاس ۲", callback_data=f"exec_dice_2_{user_id}"), InlineKeyboardButton("🎲 تاس ۳", callback_data=f"exec_dice_3_{user_id}")],
        [InlineKeyboardButton("🎲 تاس ۴", callback_data=f"exec_dice_4_{user_id}"), InlineKeyboardButton("🎲 تاس ۵", callback_data=f"exec_dice_5_{user_id}"), InlineKeyboardButton("🎲 تاس ۶", callback_data=f"exec_dice_6_{user_id}")],
        [InlineKeyboardButton("🎯 دارت", callback_data=f"exec_dart_{user_id}"), InlineKeyboardButton("🏀 بسکتبال", callback_data=f"exec_basketball_{user_id}"), InlineKeyboardButton("⚽️ فوتبال", callback_data=f"exec_football_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_translate_menu_keyboard(user_id):
    tm = selfbot_managers[str(user_id)].translate_mode if str(user_id) in selfbot_managers else {}
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🇬🇧 انگلیسی {'' if not tm.get('english') else '✓'}", callback_data=f"exec_translate_en_{user_id}"), InlineKeyboardButton(f"🇸🇦 عربی {'' if not tm.get('arabic') else '✓'}", callback_data=f"exec_translate_ar_{user_id}")],
        [InlineKeyboardButton(f"🇮🇱 عبری {'' if not tm.get('hebrew') else '✓'}", callback_data=f"exec_translate_he_{user_id}"), InlineKeyboardButton(f"🇷🇺 روسی {'' if not tm.get('russian') else '✓'}", callback_data=f"exec_translate_ru_{user_id}")],
        [InlineKeyboardButton(f"🇹🇷 ترکی {'' if not tm.get('turkish') else '✓'}", callback_data=f"exec_translate_tr_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_google_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 سرچ", callback_data=f"exec_search_on_{user_id}"), InlineKeyboardButton("❌ خروج جستجو", callback_data=f"exec_search_off_{user_id}"), InlineKeyboardButton("🎵 اهنگ", callback_data=f"exec_music_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_info_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 اطلاعات", callback_data=f"exec_info_{user_id}"), InlineKeyboardButton("⬇️ دانلود پروفایل", callback_data=f"exec_download_profile_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_profile_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 ست پروف", callback_data=f"exec_set_profile_{user_id}"), InlineKeyboardButton("✏️ ست بیو", callback_data=f"exec_set_bio_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف ست پروف", callback_data=f"exec_delete_profile_{user_id}"), InlineKeyboardButton("🗑️ حذف ست بیو", callback_data=f"exec_delete_bio_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_style_menu_keyboard(user_id):
    cur = db.get_selfbot_settings(user_id).get('text_style', 'هیچ')
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"بولد {'' if cur != 'بولد' else '✓'}", callback_data=f"exec_bold_{user_id}"), InlineKeyboardButton(f"زیرخط {'' if cur != 'زیرخط' else '✓'}", callback_data=f"exec_underline_{user_id}"), InlineKeyboardButton(f"خط خورده {'' if cur != 'خط خورده' else '✓'}", callback_data=f"exec_strike_{user_id}")],
        [InlineKeyboardButton(f"نقل قول {'' if cur != 'نقل قول' else '✓'}", callback_data=f"exec_quote_{user_id}"), InlineKeyboardButton(f"اسپویلر {'' if cur != 'اسپویلر' else '✓'}", callback_data=f"exec_spoiler_{user_id}"), InlineKeyboardButton(f"کج {'' if cur != 'کج' else '✓'}", callback_data=f"exec_italic_{user_id}")],
        [InlineKeyboardButton(f"کد {'' if cur != 'کد' else '✓'}", callback_data=f"exec_code_{user_id}"), InlineKeyboardButton(f"پیش {'' if cur != 'پیش' else '✓'}", callback_data=f"exec_pre_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_message_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧹 حذف کامل", callback_data=f"exec_delete_all_{user_id}"), InlineKeyboardButton("🧹 حذف کامل ۵۰", callback_data=f"exec_delete_50_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف ۱۰", callback_data=f"exec_delete_10_{user_id}"), InlineKeyboardButton("👁️ فعال اتوسین", callback_data=f"exec_autosend_on_{user_id}")],
        [InlineKeyboardButton("🙈 غیرفعال اتوسین", callback_data=f"exec_autosend_off_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_reaction_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 ریکت", callback_data=f"exec_reaction_{user_id}"), InlineKeyboardButton("❌ حذف ریکت", callback_data=f"exec_reaction_off_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_spam_menu_keyboard(user_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📩 اسپم", callback_data=f"exec_spam_{user_id}")], [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]])

def get_change_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ تغییر اسم", callback_data=f"exec_change_name_{user_id}"), InlineKeyboardButton("✏️ تغییر بیو", callback_data=f"exec_change_bio_{user_id}")],
        [InlineKeyboardButton("📸 تغییر پروفایل", callback_data=f"exec_change_profile_{user_id}"), InlineKeyboardButton("📸 پروف", callback_data=f"exec_change_profile_alt_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_enemy_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 لیست دشمن", callback_data=f"exec_enemy_list_{user_id}"), InlineKeyboardButton("📝 اضافه اسپم", callback_data=f"exec_add_spam_{user_id}")],
        [InlineKeyboardButton("✅ اتمام اسپم", callback_data=f"exec_end_spam_{user_id}"), InlineKeyboardButton("📜 لیست اسپم", callback_data=f"exec_spam_list_{user_id}")],
        [InlineKeyboardButton("🗑️ پاک کردن اسپم", callback_data=f"exec_clear_spam_{user_id}"), InlineKeyboardButton("🗑️ حذف اسپم", callback_data=f"exec_delete_spam_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_filter_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 .فیلتر [کلمه]", callback_data=f"exec_filter_word_{user_id}"), InlineKeyboardButton("✅ فیلتر روشن", callback_data=f"exec_filter_on_{user_id}")],
        [InlineKeyboardButton("❌ فیلتر خاموش", callback_data=f"exec_filter_off_{user_id}"), InlineKeyboardButton("📜 لیست فیلتر", callback_data=f"exec_filter_list_{user_id}")],
        [InlineKeyboardButton("🗑️ حذف فیلتر", callback_data=f"exec_filter_remove_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_protection_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛡️ اسپم روشن", callback_data=f"exec_spam_protection_on_{user_id}"), InlineKeyboardButton("🛡️ اسپم خاموش", callback_data=f"exec_spam_protection_off_{user_id}")],
        [InlineKeyboardButton("⚙️ تنظیم اسپم", callback_data=f"exec_spam_settings_{user_id}"), InlineKeyboardButton("📊 وضعیت اسپم", callback_data=f"exec_spam_status_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_ai_menu_keyboard(user_id):
    s = db.get_selfbot_settings(user_id)
    ai = s['ai_status']
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🟢 پیوی ۱ {'' if not ai['ai_1_pm'] else '✓'}", callback_data=f"exec_ai_pm_1_{user_id}"), InlineKeyboardButton(f"🔵 پیوی ۲ {'' if not ai['ai_2_pm'] else '✓'}", callback_data=f"exec_ai_pm_2_{user_id}"), InlineKeyboardButton(f"🟣 پیوی ۳ {'' if not ai['ai_3_pm'] else '✓'}", callback_data=f"exec_ai_pm_3_{user_id}")],
        [InlineKeyboardButton("⚫ خاموش پیوی", callback_data=f"exec_ai_pm_off_{user_id}")],
        [InlineKeyboardButton(f"🟢 گروه ۱ {'' if not ai['ai_1_group'] else '✓'}", callback_data=f"exec_ai_group_1_{user_id}"), InlineKeyboardButton(f"🔵 گروه ۲ {'' if not ai['ai_2_group'] else '✓'}", callback_data=f"exec_ai_group_2_{user_id}"), InlineKeyboardButton(f"🟣 گروه ۳ {'' if not ai['ai_3_group'] else '✓'}", callback_data=f"exec_ai_group_3_{user_id}")],
        [InlineKeyboardButton("⚫ خاموش گروه", callback_data=f"exec_ai_group_off_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

def get_report_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📍 تنظیم گزارش", callback_data=f"exec_set_report_{user_id}"), InlineKeyboardButton("ℹ️ گروه گزارش", callback_data=f"exec_show_report_{user_id}")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ])

# ========== توابع ربات اصلی ==========
async def inline_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    if not query: return
    user_id = query.from_user.id
    user_data = db.get_user(str(user_id))
    if not user_data or not user_data.get('self_active'):
        await query.answer([InlineQueryResultArticle(id=str(uuid.uuid4()), title="⛔ دسترسی محدود", description="شما عضو سرویس نیستید", input_message_content=InputTextMessageContent("⛔ شما به این پنل دسترسی ندارید\n\nبرای عضویت: /start"))], cache_time=1, is_personal=True)
        return
    if not query.query:
        results = [InlineQueryResultArticle(id=str(uuid.uuid4()), title="🌟 پنل اصلی", description="مدیریت تمام قابلیت‌های سلف‌بات", input_message_content=InputTextMessageContent("🌟 پنل سلف‌بات باز شد\n\n⚠️ توجه: این پنل فقط مخصوص شماست"), reply_markup=get_main_panel_keyboard(user_id))]
        if user_id == ADMIN_ID:
            results.append(InlineQueryResultArticle(id=str(uuid.uuid4()), title="👑 پنل ادمین", description="مدیریت کاربران و سلف‌بات‌ها", input_message_content=InputTextMessageContent("👑 پنل ادمین"), reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"admin_requests"), InlineKeyboardButton("🔐 منتظر ورود", callback_data=f"admin_login")],
                [InlineKeyboardButton("✅ کاربران فعال", callback_data=f"admin_active"), InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data=f"admin_selfbots")],
                [InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats"), InlineKeyboardButton("📢 پیام همگانی", callback_data=f"admin_broadcast")],
                [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
            ])))
        await query.answer(results, cache_time=1, is_personal=True)
        return
    search = query.query.lower()
    results = []
    commands = [("⚈ زمان و پروفایل","time","مدیریت زمان و پروفایل"), ("☻ انیمیشن","animation","انیمیشن قلب و ماه"), ("☗ مدیریت کاربران","user","مدیریت دشمن/دوست/بلاک"), ("⊖ قفل رسانه","lock","قفل انواع رسانه"), ("✼ کامنت","comment","کامنت خودکار"), ("✿ عمومی","general","وضعیت/درباره/پینگ"), ("☥ اکشن","action","اکشن‌های تایپ"), ("⚕ بازی‌ها","games","تاس/دارت/بسکتبال/فوتبال"), ("❍ ترجمه","translate","ترجمه خودکار"), ("𖢅 گوگل","google","جستجوی گوگل"), ("֍ اطلاعاتی","info","اطلاعات کاربر"), ("𖢨 پروفایل","profile","کپی پروفایل"), ("⩐ استایل متن","style","استایل‌های متن"), ("𑪡 مدیریت پیام","message","حذف پیام"), ("☖ ریکشن","reaction","ریکت خودکار"), ("𖥞 اسپم","spam","ارسال اسپم"), ("☗ تغییر پروفایل","change","تغییر نام/بیو"), ("⚇ مدیریت دشمنان","enemy","لیست دشمن"), ("✿ فیلتر کلمات","filter","فیلتر کلمات"), ("⚉ حفاظت اسپم","protection","محافظت اسپم"), ("☥ هوش مصنوعی","ai","مدیریت هوش مصنوعی"), ("֎ گزارش","report","تنظیم گزارش"), ("🛠 ابزار","tools","ابزارهای مختلف")]
    for title, cmd, desc in commands:
        if search in title.lower() or search in desc.lower() or search in cmd.lower():
            results.append(InlineQueryResultArticle(id=str(uuid.uuid4()), title=title, description=desc, input_message_content=InputTextMessageContent(f"✅ دستور {title} ارسال شد"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ℹ️ توضیحات", callback_data=f"desc_{cmd}"), InlineKeyboardButton("▶️ باز کردن", callback_data=f"menu_{cmd}")]])))
    await query.answer(results, cache_time=1, is_personal=True)

# ========== توابع ادمین ==========
async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    await q.edit_message_text("📢 ارسال پیام همگانی\n\nلطفاً پیام خود را ارسال کنید.\n\nبرای لغو: /cancel")
    context.user_data['broadcast_mode'] = True

async def handle_broadcast_message(update, context):
    if not update.message or not update.message.text or update.effective_user.id != ADMIN_ID or not context.user_data.get('broadcast_mode'): return
    if update.message.text == '/cancel':
        context.user_data['broadcast_mode'] = False
        await update.message.reply_text("✅ لغو شد")
        return
    text = update.message.text
    await update.message.reply_text("⏳ در حال ارسال...")
    users = [u for u in db.get_all_users() if u.get('self_active')]
    sent, failed = 0, 0
    for u in users:
        try:
            await context.bot.send_message(int(u['user_id']), f"📢 **پیام همگانی**\n━━━━━━━━━━━━━━━━━━━━\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🕐 {datetime.now().strftime('%Y/%m/%d %H:%M')}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.1)
        except: failed += 1
    await update.message.reply_text(f"✅ ارسال کامل شد!\n\n📊 آمار:\n• کل: {len(users)}\n• موفق: {sent}\n• ناموفق: {failed}")
    context.user_data['broadcast_mode'] = False

# ========== توابع دکمه‌ها ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q: return
    data, user_id = q.data, q.from_user.id
    user_id_str = str(user_id)
    if '_' in data and not data.startswith(('admin_','approve_','reject_','stop_selfbot_','restart_selfbot_','desc_','menu_')):
        for p in data.split('_'):
            if p.isdigit() and len(p) >= 5 and p != user_id_str:
                await q.answer("⛔ این پنل مال شما نیست", show_alert=True); return
    if data.startswith("close_panel_"):
        await q.answer("❌ بستن پنل")
        try: await q.message.delete()
        except: await q.edit_message_text("✅ پنل بسته شد")
        return
    if data == "back_main":
        await q.edit_message_text("🌟 پنل مدیریت سلف‌بات\n\n⚠️ توجه: این پنل فقط مخصوص شماست", reply_markup=get_main_panel_keyboard(user_id))
        return
    if data == "admin_panel": await admin_panel_handler(update, context); return
    if data == "admin_requests": await admin_requests_handler(update, context); return
    if data == "admin_login": await admin_login_handler(update, context); return
    if data == "admin_active": await admin_active_handler(update, context); return
    if data == "admin_selfbots": await admin_selfbots_handler(update, context); return
    if data == "admin_stats": await admin_stats_handler(update, context); return
    if data == "admin_broadcast": await admin_broadcast_handler(update, context); return
    if data.startswith("approve_"): await approve_handler(update, context); return
    if data.startswith("reject_"): await reject_handler(update, context); return
    if data.startswith("stop_selfbot_"): await stop_selfbot_handler(update, context); return
    if data.startswith("restart_selfbot_"): await restart_selfbot_handler(update, context); return
    if data.startswith("membership_request_"): await membership_request_handler(update, context); return
    if data.startswith("membership_status_"): await membership_status_handler(update, context); return
    if data.startswith("exec_"): await exec_command_handler(update, context); return
    parts = data.split('_')
    if len(parts) > 1:
        menus = {"time":("⚈ دستورات زمان و پروفایل",get_time_menu_keyboard),"animation":("☻ انیمیشن‌ها",get_animation_menu_keyboard),"user":("☗ مدیریت کاربران",get_user_menu_keyboard),"lock":("⊖ قفل رسانه",get_lock_menu_keyboard),"comment":("✼ کامنت خودکار",get_comment_menu_keyboard),"general":("✿ دستورات عمومی",get_general_menu_keyboard),"action":("☥ اکشن‌ها",get_action_menu_keyboard),"games":("⚕ بازی‌ها",get_games_menu_keyboard),"translate":("❍ ترجمه خودکار",get_translate_menu_keyboard),"google":("𖢅 گوگل",get_google_menu_keyboard),"info":("֍ اطلاعاتی",get_info_menu_keyboard),"profile":("𖢨 پروفایل",get_profile_menu_keyboard),"style":("⩐ استایل متن",get_style_menu_keyboard),"message":("𑪡 مدیریت پیام",get_message_menu_keyboard),"reaction":("☖ ریکشن",get_reaction_menu_keyboard),"spam":("𖥞 اسپم",get_spam_menu_keyboard),"change":("☗ تغییر پروفایل",get_change_menu_keyboard),"enemy":("⚇ مدیریت دشمنان",get_enemy_menu_keyboard),"filter":("✿ فیلتر کلمات",get_filter_menu_keyboard),"protection":("⚉ حفاظت اسپم",get_protection_menu_keyboard),"ai":("☥ هوش مصنوعی",get_ai_menu_keyboard),"report":("֎ گزارش",get_report_menu_keyboard),"tools":("🛠 ابزارها",get_tools_menu_keyboard)}
        if parts[0] in menus and parts[1] == "menu":
            await q.edit_message_text(menus[parts[0]][0], reply_markup=menus[parts[0]][1](user_id))

# ========== توابع ادمین ==========
async def admin_panel_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    await q.edit_message_text("👑 پنل مدیریت", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 درخواست‌ها", callback_data=f"admin_requests"), InlineKeyboardButton("🔐 منتظر ورود", callback_data=f"admin_login")],
        [InlineKeyboardButton("✅ کاربران فعال", callback_data=f"admin_active"), InlineKeyboardButton("🤖 سلف‌بات‌ها", callback_data=f"admin_selfbots")],
        [InlineKeyboardButton("📊 آمار کلی", callback_data=f"admin_stats"), InlineKeyboardButton("📢 پیام همگانی", callback_data=f"admin_broadcast")],
        [InlineKeyboardButton("⚈ بازگشت", callback_data=f"back_main")]
    ]))

async def admin_requests_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    pending = db.get_pending_requests()
    if pending:
        text, kb = "📋 درخواست‌ها:\n\n", []
        for r in pending[:10]:
            text += f"👤 {r['full_name']}\n🆔 {r['user_id']}\n\n"
            kb.append([InlineKeyboardButton(f"✅ تأیید {r['user_id']}", callback_data=f"approve_{r['user_id']}"), InlineKeyboardButton(f"❌ رد {r['user_id']}", callback_data=f"reject_{r['user_id']}")])
        kb.append([InlineKeyboardButton("⚈ بازگشت", callback_data=f"admin_panel")])
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await q.edit_message_text("📋 هیچ درخواستی نیست")

async def admin_login_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    pending = db.get_pending_login()
    if pending:
        text = "🔐 کاربران در مرحله ورود:\n\n"
        for u in pending[:10]:
            text += f"👤 {u['full_name']}\n🆔 {u['user_id']}\n📞 {u.get('phone', 'نامشخص')}\n\n"
        await q.edit_message_text(text)
    else: await q.edit_message_text("🔐 هیچ کاربری در مرحله ورود نیست")

async def admin_active_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    active = db.get_active_users()
    if active:
        text = "✅ کاربران فعال:\n\n"
        for u in active[:10]:
            text += f"👤 {u['full_name']}\n🆔 {u['user_id']}\n📞 {u.get('phone', 'نامشخص')}\n🤖 سلف‌بات: {'✅' if u['user_id'] in selfbot_managers else '❌'}\n\n"
        await q.edit_message_text(text)
    else: await q.edit_message_text("✅ هیچ کاربر فعالی وجود ندارد")

async def admin_selfbots_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    if selfbot_managers:
        text, kb = "🤖 سلف‌بات‌های فعال:\n\n", []
        for uid in list(selfbot_managers.keys())[:10]:
            u = db.get_user(uid)
            text += f"👤 {u['full_name'] if u else f'کاربر {uid}'}\n🆔 {uid}\n\n"
            kb.append([InlineKeyboardButton(f"🛑 توقف {uid}", callback_data=f"stop_selfbot_{uid}"), InlineKeyboardButton(f"🔄 ریستارت {uid}", callback_data=f"restart_selfbot_{uid}")])
        kb.append([InlineKeyboardButton("⚈ بازگشت", callback_data=f"admin_panel")])
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await q.edit_message_text("🤖 هیچ سلف‌باتی فعال نیست")

async def admin_stats_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    await q.edit_message_text(f"""
📊 آمار کلی
━━━━━━━━━━━━━━━━━━━━
👥 کل کاربران: {len(db.get_all_users())}
✅ کاربران فعال: {len(db.get_active_users())}
📋 درخواست‌ها: {len(db.get_pending_requests())}
🔐 منتظر ورود: {len(db.get_pending_login())}
🤖 سلف‌بات فعال: {len(selfbot_managers)}
━━━━━━━━━━━━━━━━━━━━
""")

async def approve_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    target = q.data.split('_')[1]
    if not db.get_user(target): await q.answer("❌ کاربر یافت نشد", show_alert=True); return
    db.update_user(target, admin_approved=1, activation_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        await context.bot.send_message(int(target), "🎉 درخواست شما تأیید شد!\n\nلطفاً شماره تلفن خود را وارد کنید:")
        db.update_user(target, step='get_phone')
    except: pass
    await q.edit_message_text(f"✅ کاربر {target} تأیید شد")
    await q.message.delete()

async def reject_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    target = q.data.split('_')[1]
    if not db.get_user(target): await q.answer("❌ کاربر یافت نشد", show_alert=True); return
    db.update_user(target, rejected=1, request_sent=0)
    try: await context.bot.send_message(int(target), "⚠ درخواست شما رد شد.")
    except: pass
    await q.edit_message_text(f"❌ کاربر {target} رد شد")
    await q.message.delete()

async def stop_selfbot_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    target = q.data.split('_')[2]
    if target in selfbot_managers:
        await selfbot_managers[target].stop()
        del selfbot_managers[target]
        await q.answer(f"✅ سلف‌بات {target} متوقف شد", show_alert=True)
    else: await q.answer("❌ سلف‌بات فعال نیست", show_alert=True)

async def restart_selfbot_handler(update, context):
    q = update.callback_query
    if not q or q.from_user.id != ADMIN_ID: return
    await q.answer()
    target = q.data.split('_')[2]
    u = db.get_user(target)
    if not u or not u.get('self_active'): await q.answer("❌ کاربر فعال نیست", show_alert=True); return
    if not u.get('session_file') or not os.path.exists(u['session_file']): await q.answer("❌ فایل سشن یافت نشد", show_alert=True); return
    if target in selfbot_managers:
        await selfbot_managers[target].stop()
        del selfbot_managers[target]
    m = SelfBotManager(target)
    if await m.start(u['session_file']):
        selfbot_managers[target] = m
        await q.answer(f"✅ سلف‌بات {target} راه‌اندازی شد", show_alert=True)
    else: await q.answer("❌ خطا در راه‌اندازی", show_alert=True)

# ========== اجرای دستورات پنل ==========
async def exec_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not q.data.startswith('exec_'): return
    await q.answer()
    data, user_id = q.data, q.from_user.id
    user_id_str = str(user_id)
    parts = data.split('_')
    owner = None
    for p in reversed(parts):
        if p.isdigit(): owner = p; break
    if owner and owner != user_id_str:
        await q.answer("⛔ این پنل مال شما نیست", show_alert=True); return
    if user_id_str not in selfbot_managers:
        await q.edit_message_text("❌ سلف‌بات شما فعال نیست")
        return
    manager = selfbot_managers[user_id_str]
    cmd = data.replace(f'exec_', '').replace(f'_{user_id}', '')
    msg = await context.bot.send_message(q.message.chat_id, "⏳ در حال اجرا...")
    
    # ========== دستورات ==========
    if cmd == 'stats':
        await msg.edit_text("📊 در حال دریافت آمار...")
        target = None
        if q.message.reply_to_message:
            target = q.message.reply_to_message.from_user.id or q.message.reply_to_message.sender_id
        if not target and q.message.chat.type == 'private': target = q.message.chat.id
        if not target: await msg.edit_text("⚠️ روی پیام کاربر ریپلای کنید"); return
        stats = await manager.get_chat_stats(q.message.chat_id, int(target))
        if not stats: await msg.edit_text("⚠️ خطا در دریافت آمار"); return
        try:
            tn, mn = await manager.get_user_info(target), await manager.get_user_info(manager.my_id)
            tm, tt = stats['my_messages'], stats['target_messages']
            winner = mn if tm > tt else (tn if tt > tm else "مساوی")
            ratio = f"{tm} به {tt}" if tt > 0 else f"{tm} به 0"
            await manager.client.send_message(q.message.chat_id, f"""
📊 آمار گفتگو
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نوع                {mn[:15]}        {tn[:15]}
────────────────────────────────────
💬 پیام            {tm:>5}        {tt:>5}
📸 عکس             {stats['my_photos']:>5}        {stats['target_photos']:>5}
🎙️ ویس             {stats['my_voices']:>5}        {stats['target_voices']:>5}
🎬 ویدیو           {stats['my_videos']:>5}        {stats['target_videos']:>5}
🎨 استیکر          {stats['my_stickers']:>5}        {stats['target_stickers']:>5}
🎞️ گیف             {stats['my_gifs']:>5}        {stats['target_gifs']:>5}
📁 فایل            {stats['my_files']:>5}        {stats['target_files']:>5}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 بیشترین پیام: {winner}
📈 نسبت: {ratio}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
            await msg.delete()
        except Exception as e: await msg.edit_text(f"⚠️ خطا: {str(e)[:100]}")
        return
    
    if cmd == 'qr':
        await msg.edit_text("🝰 در حال تولید کد QR...")
        try:
            if q.message.reply_to_message:
                reply = await manager.client.get_messages(q.message.chat_id, ids=q.message.reply_to_message.message_id)
                if reply.text: path, text = await manager.generate_qr_code(reply.text)
                elif reply.photo: path, text = await manager.generate_qr_code(reply.media, True)
                else: await msg.edit_text("⚠️ روی متن یا عکس ریپلای کنید"); return
            else: await msg.edit_text("🝰 لطفاً متن را وارد کنید"); return
            if path and os.path.exists(path):
                await manager.client.send_file(q.message.chat_id, path, caption=f"🝰 کد QR\n📝 متن: {text[:100]}")
                os.remove(path); await msg.delete()
            else: await msg.edit_text(f"⚠️ خطا: {text}")
        except Exception as e: await msg.edit_text(f"⚠️ خطا: {str(e)[:100]}")
        return
    
    if cmd == 'tag_admin':
        if not isinstance(q.message.chat, (types.Channel, types.Chat)):
            await msg.edit_text("⚠️ فقط در گروه"); return
        admins = await manager.get_admins(q.message.chat_id)
        if admins:
            text = "👑 ادمین‌ها:\n\n" + "\n".join([f"• @{a.username}" if a.username else f"• {a.first_name or 'ادمین'}" for a in admins])
            await msg.edit_text(text)
        else: await msg.edit_text("⚠️ ادمینی یافت نشد")
        return
    
    if cmd == 'pin':
        if q.message.reply_to_message:
            reply = await manager.client.get_messages(q.message.chat_id, ids=q.message.reply_to_message.message_id)
            if await manager.pin_message(q.message.chat_id, reply.id): await msg.edit_text("📌 پیام پین شد")
            else: await msg.edit_text("⚠️ خطا در پین")
        else: await msg.edit_text("⚠️ روی پیام ریپلای کنید")
        return
    
    if cmd == 'self_on':
        db.update_selfbot_setting(user_id, 'selfbot_enabled', 1)
        await msg.edit_text("✅ سلف‌بات فعال شد")
        return
    
    if cmd == 'self_off':
        db.update_selfbot_setting(user_id, 'selfbot_enabled', 0)
        await msg.edit_text("✅ سلف‌بات غیرفعال شد")
        return
    
    if cmd.startswith('time_on'):
        db.update_selfbot_setting(user_id, 'time_enabled', 1); db.update_selfbot_setting(user_id, 'flag_enabled', 0)
        await manager.update_profile_name()
        await msg.edit_text("✅ تایم روشن شد")
        await q.message.edit_text(q.message.text, reply_markup=get_time_menu_keyboard(user_id))
        return
    if cmd.startswith('time_flag'):
        db.update_selfbot_setting(user_id, 'time_enabled', 1); db.update_selfbot_setting(user_id, 'flag_enabled', 1)
        await manager.update_profile_name()
        await msg.edit_text("✅ تایمر پرچم روشن شد")
        await q.message.edit_text(q.message.text, reply_markup=get_time_menu_keyboard(user_id))
        return
    if cmd.startswith('time_off'):
        db.update_selfbot_setting(user_id, 'time_enabled', 0); db.update_selfbot_setting(user_id, 'flag_enabled', 0)
        await manager.restore_profile_name()
        await msg.edit_text("✅ تایم خاموش شد")
        await q.message.edit_text(q.message.text, reply_markup=get_time_menu_keyboard(user_id))
        return
    if cmd.startswith('full_date'):
        await msg.edit_text(get_full_date_info())
        return
    
    tr_cmds = {'translate_en':'english','translate_ar':'arabic','translate_he':'hebrew','translate_ru':'russian','translate_tr':'turkish'}
    for p, lang in tr_cmds.items():
        if cmd.startswith(p):
            manager.translate_mode[lang] = not manager.translate_mode[lang]
            db.update_selfbot_setting(user_id, f'translate_{lang}', 1 if manager.translate_mode[lang] else 0)
            await msg.edit_text(f"✅ ترجمه {lang} {'روشن' if manager.translate_mode[lang] else 'خاموش'} شد")
            await q.message.edit_text(q.message.text, reply_markup=get_translate_menu_keyboard(user_id))
            return
    
    if cmd == 'advanced_heart':
        await msg.edit_text("❤️ شروع...")
        try:
            m = await manager.client.send_message(q.message.chat_id, "❤️")
            await advanced_heart_animation(m)
        except: pass
        return
    if cmd == 'love':
        await msg.edit_text("💝 شروع...")
        try:
            m = await manager.client.send_message(q.message.chat_id, "💝")
            await advanced_heart_animation(m)
        except: pass
        return
    if cmd == 'santet':
        await msg.edit_text("🕯️ در حال اجرا...")
        try:
            m = await manager.client.send_message(q.message.chat_id, "🕯️")
            for i in range(101):
                bar = "█" * int(i/100*20) + "░" * (20 - int(i/100*20))
                await m.edit(f"🕯️ {i}% [{bar}]")
                await asyncio.sleep(0.03)
            await asyncio.sleep(1)
            await m.edit("✅ انجام شد 🥴")
        except: pass
        return
    if cmd == 'hack':
        await msg.edit_text("💻 در حال هک...")
        try:
            m = await manager.client.send_message(q.message.chat_id, "💻")
            for s in ["User online: True\nTelegram access: True\nRead Storage: True",
                     "Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]",
                     "Hacking... 25%\n[█████░░░░░░░░░░░░░░░]",
                     "Hacking... 50%\n[██████████░░░░░░░░░░]",
                     "Hacking... 75%\n[███████████████░░░░░]",
                     "Hacking... 100%\n[████████████████████]",
                     "✅ هک کامل شد"]:
                await asyncio.sleep(2); await m.edit(s)
        except: pass
        return
    
    if cmd == 'status':
        await msg.edit_text(manager.format_status_info(db.get_selfbot_settings(user_id)))
        return
    if cmd == 'about':
        await msg.edit_text(f"ℹ️ درباره\n\n🤖 نسخه: v{BOT_VERSION}\n👨‍💻 سازنده: {BOT_CREATOR}")
        return
    if cmd == 'ping':
        start = time.time()
        await msg.edit_text("🏓 پینگ: ...")
        await msg.edit_text(f"🏓 پینگ: {round((time.time() - start) * 1000, 2)} ms")
        return
    if cmd == 'music':
        await msg.edit_text("🎵 `.اهنگ [نام آهنگ]`")
        return
    
    if cmd == 'broadcast' and user_id == ADMIN_ID:
        await msg.edit_text("📢 پیام خود را مستقیم برای ربات ارسال کنید")
        return
    if cmd == 'user_stats' and user_id == ADMIN_ID:
        await msg.edit_text(f"""
📊 آمار کاربران:
━━━━━━━━━━━━━━━━━━━━
👥 کل: {len(db.get_all_users())}
✅ فعال: {len(db.get_active_users())}
📋 در انتظار: {len(db.get_pending_requests())}
🔐 ورود: {len(db.get_pending_login())}
🤖 سلف‌بات: {len(selfbot_managers)}
━━━━━━━━━━━━━━━━━━━━
""")
        return
    
    if cmd == 'heart':
        asyncio.create_task(manager.heart_animation(q.message.chat_id))
        await msg.edit_text("❤️ انیمیشن قلب شروع شد")
        return
    if cmd == 'moon':
        asyncio.create_task(manager.moon_animation(q.message.chat_id))
        await msg.edit_text("🌙 انیمیشن ماه شروع شد")
        return
    
    if cmd in ['enemy','friend','lock_pv','unlock_pv','block']:
        await msg.edit_text(f"⚠️ روی پیام کاربر ریپلای کنید و دستور {cmd} را ارسال کنید")
        return
    if cmd == 'lock_all':
        db.update_selfbot_setting(user_id, 'pv_lock_all', 1)
        await msg.edit_text("✅ قفل پیوی همگانی فعال شد")
        return
    if cmd == 'unlock_all':
        db.update_selfbot_setting(user_id, 'pv_lock_all', 0)
        await msg.edit_text("✅ قفل پیوی همگانی غیرفعال شد")
        return
    
    if cmd == 'enemy_list':
        enemies = db.get_enemies(user_id)
        if enemies:
            text = "📋 لیست دشمنان:\n\n"
            for i, eid in enumerate(enemies, 1):
                try: text += f"{i}. {(await manager.client.get_entity(eid)).first_name or 'کاربر'} ({eid})\n"
                except: text += f"{i}. کاربر {eid}\n"
            await msg.edit_text(text)
        else: await msg.edit_text("📭 لیست خالی است")
        return
    
    if cmd == 'add_spam':
        manager.adding_spam = True
        await msg.edit_text("📝 حالت اضافه کردن اسپم فعال شد\nبرای پایان: اتمام اسپم")
        return
    if cmd == 'end_spam':
        manager.adding_spam = False
        await msg.edit_text("✅ حالت اضافه کردن اسپم غیرفعال شد")
        return
    if cmd == 'spam_list':
        msgs = db.get_enemy_spam_messages(user_id)
        if msgs:
            text = "📜 پیام‌های اسپم:\n\n" + "\n".join([f"{i}. {m['text']}" for i, m in enumerate(msgs, 1)]) + f"\n\n📊 تعداد: {len(msgs)}"
            await msg.edit_text(text)
        else: await msg.edit_text("📭 لیست خالی است")
        return
    if cmd == 'clear_spam':
        db.clear_enemy_spam_messages(user_id)
        await msg.edit_text("✅ اسپم‌ها پاک شدند")
        return
    if cmd == 'delete_spam':
        await msg.edit_text("🗑️ حذف اسپم [شماره]")
        return
    
    if cmd == 'filter_word':
        await msg.edit_text("🚫 .فیلتر [کلمه]")
        return
    if cmd == 'filter_on':
        db.set_filter_enabled(user_id, True)
        await msg.edit_text("✅ فیلتر فعال شد")
        return
    if cmd == 'filter_off':
        db.set_filter_enabled(user_id, False)
        await msg.edit_text("✅ فیلتر غیرفعال شد")
        return
    if cmd == 'filter_list':
        words = db.get_filter_words(user_id)
        if words:
            text = "📜 کلمات فیلتر:\n\n" + "\n".join([f"{i}. {w['word']} - {'فعال' if w['enabled'] else 'غیرفعال'}" for i, w in enumerate(words, 1)])
            await msg.edit_text(text)
        else: await msg.edit_text("📭 لیست خالی است")
        return
    if cmd == 'filter_remove':
        await msg.edit_text("🗑️ حذف فیلتر [کلمه]")
        return
    
    if cmd == 'spam_protection_on':
        db.set_spam_settings(user_id, spam_protection=1)
        await msg.edit_text("✅ حفاظت اسپم فعال شد")
        return
    if cmd == 'spam_protection_off':
        db.set_spam_settings(user_id, spam_protection=0)
        await msg.edit_text("✅ حفاظت اسپم غیرفعال شد")
        return
    if cmd == 'spam_settings':
        await msg.edit_text("⚙️ تنظیم اسپم [تعداد] [زمان]")
        return
    if cmd == 'spam_status':
        s = db.get_spam_settings(user_id)
        await msg.edit_text(f"🛡️ حفاظت اسپم:\n🔒 وضعیت: {'فعال' if s.get('spam_protection') else 'غیرفعال'}\n📊 محدودیت: {s.get('spam_limit', 10)} پیام\n⏱️ زمان: {s.get('mute_duration', 10)} ثانیه")
        return
    if cmd == 'spam_on':
        db.set_spam_settings(user_id, spam_protection=1)
        await msg.edit_text("✅ حفاظت اسپم فعال شد")
        return
    if cmd == 'spam_off':
        db.set_spam_settings(user_id, spam_protection=0)
        await msg.edit_text("✅ حفاظت اسپم غیرفعال شد")
        return
    if cmd == 'spam_set':
        await msg.edit_text("⚙️ تنظیم اسپم [تعداد] [زمان]")
        return
    
    if cmd == 'autosend_on':
        db.update_selfbot_setting(user_id, 'autosend_mode', 1)
        manager.autosend_enabled = True
        await msg.edit_text("✅ اتوسین فعال شد")
        return
    if cmd == 'autosend_off':
        db.update_selfbot_setting(user_id, 'autosend_mode', 0)
        manager.autosend_enabled = False
        await msg.edit_text("✅ اتوسین غیرفعال شد")
        return
    
    lock_cmds = {'lock_link':'لینک','lock_photo':'عکس','lock_video':'ویدیو','lock_sticker':'استیکر','lock_gif':'گیف','lock_voice':'ویس','lock_file':'فایل','lock_music':'موزیک','lock_video_note':'ویدیو نوت','lock_contact':'کانتکت','lock_location':'لوکیشن','lock_emoji':'ایموجی','lock_text':'متن'}
    for p, name in lock_cmds.items():
        if cmd.startswith(p):
            target = 0
            if q.message.reply_to_message: target = q.message.reply_to_message.from_user.id
            elif q.message.chat.type == 'private': target = q.message.chat.id
            current = db.get_user_lock(user_id, target, p)
            db.set_user_lock(user_id, target, p, not current)
            await msg.edit_text(f"✅ قفل {name} برای {'همه' if target == 0 else f'کاربر {target}'} {'فعال' if not current else 'غیرفعال'} شد")
            await q.message.edit_text(q.message.text, reply_markup=get_lock_menu_keyboard(user_id))
            return
    
    style_cmds = {'bold':'بولد','underline':'زیرخط','strike':'خط خورده','quote':'نقل قول','spoiler':'اسپویلر','italic':'کج','code':'کد','pre':'پیش'}
    for p, name in style_cmds.items():
        if cmd.startswith(p):
            cur = db.get_selfbot_settings(user_id).get('text_style')
            if cur == name:
                db.update_selfbot_setting(user_id, 'text_style', None)
                await msg.edit_text(f"✅ استایل {name} غیرفعال شد")
            else:
                db.update_selfbot_setting(user_id, 'text_style', name)
                await msg.edit_text(f"✅ استایل {name} فعال شد")
            await q.message.edit_text(q.message.text, reply_markup=get_style_menu_keyboard(user_id))
            return
    
    ai_cmds = {
        'ai_pm_1': {'ai_1_pm': True, 'ai_2_pm': False, 'ai_3_pm': False, 'msg': 'هوش ۱ (Gemini) در پی‌وی روشن شد'},
        'ai_pm_2': {'ai_1_pm': False, 'ai_2_pm': True, 'ai_3_pm': False, 'msg': 'هوش ۲ (Paxsenix) در پی‌وی روشن شد'},
        'ai_pm_3': {'ai_1_pm': False, 'ai_2_pm': False, 'ai_3_pm': True, 'msg': 'هوش ۳ (DeepSeek) در پی‌وی روشن شد'},
        'ai_pm_off': {'ai_1_pm': False, 'ai_2_pm': False, 'ai_3_pm': False, 'msg': 'همه هوش‌ها در پی‌وی خاموش شدند'},
        'ai_group_1': {'ai_1_group': True, 'ai_2_group': False, 'ai_3_group': False, 'msg': 'هوش ۱ (Gemini) در گروه روشن شد'},
        'ai_group_2': {'ai_1_group': False, 'ai_2_group': True, 'ai_3_group': False, 'msg': 'هوش ۲ (Paxsenix) در گروه روشن شد'},
        'ai_group_3': {'ai_1_group': False, 'ai_2_group': False, 'ai_3_group': True, 'msg': 'هوش ۳ (DeepSeek) در گروه روشن شد'},
        'ai_group_off': {'ai_1_group': False, 'ai_2_group': False, 'ai_3_group': False, 'msg': 'همه هوش‌ها در گروه خاموش شدند'}
    }
    for p, data in ai_cmds.items():
        if cmd.startswith(p):
            db.update_ai_status(user_id, data)
            await msg.edit_text(f"✅ {data['msg']}")
            await q.message.edit_text(q.message.text, reply_markup=get_ai_menu_keyboard(user_id))
            return
    
    if cmd == 'set_report':
        await msg.edit_text("📍 تنظیم گزارش")
        return
    if cmd == 'show_report':
        await msg.edit_text(f"📍 گروه گزارش:\nآیدی: {manager.report_config.report_group_id}")
        return
    
    await msg.edit_text(f"✅ دستور {cmd} اجرا شد")

# ========== توابع شروع و عضویت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user = update.effective_user
    uid = str(user.id)
    db.add_user(uid, user.full_name or "کاربر", user.username or "")
    u = db.get_user(uid)
    if u and u.get('self_active'):
        kb = [[InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{uid}")]]
        if user.id == ADMIN_ID: kb.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel")])
        await update.message.reply_text(f"👋 سلام {user.full_name} عزیز!\n\n✅ حساب شما فعال است.\n• /panel - پنل مدیریت\n• @{BOT_USERNAME} - پنل اینلاین\n• .پنل - پنل در همین چت", reply_markup=InlineKeyboardMarkup(kb))
        return
    kb = [[InlineKeyboardButton("📝 عضویت", callback_data=f"membership_request_{uid}")], [InlineKeyboardButton("📊 وضعیت عضویت", callback_data=f"membership_status_{uid}")]]
    if user.id == ADMIN_ID: kb.append([InlineKeyboardButton("👑 پنل ادمین", callback_data=f"admin_panel")])
    await update.message.reply_text(f"👋 سلام {user.full_name} عزیز!\n\n🌟 به ربات خوش آمدید.\n\n📌 برای استفاده:\n1️⃣ روی دکمه عضویت کلیک کنید\n2️⃣ شماره تلفن خود را وارد کنید\n3️⃣ کد تأیید را وارد کنید", reply_markup=InlineKeyboardMarkup(kb))

async def panel_command(update, context):
    if not update.message: return
    uid = str(update.effective_user.id)
    if not db.get_user(uid) or not db.get_user(uid).get('self_active'):
        await update.message.reply_text("⛔ شما عضو سرویس نیستید"); return
    try: await update.message.delete()
    except: pass
    await context.bot.send_message(update.effective_chat.id, "🌟 پنل مدیریت سلف‌بات\n\n⚠️ توجه: این پنل فقط مخصوص شماست", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌟 باز کردن پنل اینلاین", switch_inline_query_current_chat="")]]))

async def membership_request_handler(update, context):
    q = update.callback_query
    if not q: return
    await q.answer()
    uid = str(q.from_user.id)
    u = db.get_user(uid)
    if not u: await q.edit_message_text("❌ خطا"); return
    if u.get('self_active'): await q.edit_message_text("✅ شما عضو هستید"); return
    if u.get('rejected'): await q.edit_message_text("❌ درخواست شما رد شده"); return
    if u.get('request_sent'): await q.edit_message_text("⏳ در انتظار تأیید"); return
    db.update_user(uid, request_sent=1, request_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    await context.bot.send_message(ADMIN_ID, f"📋 درخواست جدید\n━━━━━━━━━━━━━━━━━━━━\n👤 نام: {u['full_name']}\n🆔 آیدی: {uid}\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"reject_{uid}")]]))
    await q.edit_message_text("✅ درخواست شما ثبت شد!\n\n⏳ منتظر تأیید ادمین باشید")

async def membership_status_handler(update, context):
    q = update.callback_query
    if not q: return
    await q.answer()
    uid = str(q.from_user.id)
    u = db.get_user(uid)
    if not u: await q.edit_message_text("👤 ثبت‌نام نکرده‌اید")
    elif u.get('self_active'): await q.edit_message_text(f"✅ عضو فعال هستید\n\n📅 انقضا: {u.get('expiration_date', 'نامشخص')}")
    elif u.get('admin_approved'): await q.edit_message_text("⏳ شماره تلفن خود را وارد کنید")
    elif u.get('request_sent'): await q.edit_message_text("⏳ در انتظار تأیید")
    elif u.get('rejected'): await q.edit_message_text("❌ درخواست شما رد شده")
    else: await q.edit_message_text("👤 وضعیت نامشخص")

async def handle_message(update, context):
    if not update.message or not update.message.text: return
    uid = str(update.effective_user.id)
    text = convert_persian_to_english(update.message.text)
    if context.user_data.get('broadcast_mode') and update.effective_user.id == ADMIN_ID:
        await handle_broadcast_message(update, context); return
    u = db.get_user(uid)
    if not u: await start(update, context); return
    if u.get('rejected'): await update.message.reply_text("✖ درخواست شما رد شده"); return
    if u.get('self_active'):
        if uid not in selfbot_managers:
            sf = u.get('session_file')
            if sf and os.path.exists(sf):
                m = SelfBotManager(uid)
                if await m.start(sf):
                    selfbot_managers[uid] = m
                    await update.message.reply_text("🚀 سلف‌بات فعال شد")
                else: await update.message.reply_text("⚠️ خطا در شروع سلف‌بات")
        else: await update.message.reply_text("✅ سلف‌بات در حال اجراست")
        return
    step = u.get('step')
    if step == 'get_phone':
        if not u.get('admin_approved'): await update.message.reply_text("⏳ درخواست شما تأیید نشده"); return
        db.update_user(uid, phone=text, step='get_code')
        await update.message.reply_text(f"✅ شماره {text} ذخیره شد\n⏳ در حال ارسال کد...")
        try:
            sp = os.path.join(SESSIONS_FOLDER, f"user_{uid}.session")
            if os.path.exists(sp): os.remove(sp)
            api = get_user_api(uid)
            if not api: await update.message.reply_text("❌ خطا در دریافت API"); return
            client = TelegramClient(sp, api["api_id"], api["api_hash"])
            await client.connect()
            sent = await client.send_code_request(text)
            db.update_user(uid, phone_code_hash=sent.phone_code_hash)
            await update.message.reply_text("✅ کد تأیید ارسال شد!\n\n📩 کد ۵ رقمی را وارد کنید:")
            await client.disconnect()
        except Exception as e:
            await update.message.reply_text(f"✖ خطا: {str(e)[:100]}\nدوباره شماره را وارد کنید")
            db.update_user(uid, step='get_phone')
    elif step == 'get_code':
        db.update_user(uid, code=text)
        await update.message.reply_text("⏳ در حال تأیید کد...")
        try:
            sp = os.path.join(SESSIONS_FOLDER, f"user_{uid}.session")
            api = get_user_api(uid)
            if not api: await update.message.reply_text("❌ خطا در دریافت API"); return
            client = TelegramClient(sp, api["api_id"], api["api_hash"])
            await client.connect()
            u = db.get_user(uid)
            code = text.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
            await client.sign_in(phone=u['phone'], code=code, phone_code_hash=u['phone_code_hash'])
            exp = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            db.update_user(uid, self_active=1, session_file=sp, expiration_date=exp, step=None)
            await update.message.reply_text(f"🎉 عضویت کامل شد!\n\n✅ اکانت فعال شد\n📅 انقضا: {exp}")
            await client.disconnect()
            m = SelfBotManager(uid)
            if await m.start(sp): selfbot_managers[uid] = m; await update.message.reply_text("🚀 سلف‌بات فعال شد")
            try: await context.bot.send_message(ADMIN_ID, f"✅ کاربر {u['full_name']} وارد شد\n🆔 {uid}")
            except: pass
        except SessionPasswordNeededError:
            db.update_user(uid, step='get_password')
            await update.message.reply_text("🔐 رمز دو مرحله‌ای را وارد کنید:")
        except Exception as e:
            await update.message.reply_text(f"✖ کد نامعتبر است\nدوباره شماره را وارد کنید")
            db.update_user(uid, step='get_phone', phone=None, code=None, phone_code_hash=None)
    elif step == 'get_password':
        db.update_user(uid, password=text)
        await update.message.reply_text("⏳ در حال تأیید رمز...")
        try:
            sp = os.path.join(SESSIONS_FOLDER, f"user_{uid}.session")
            api = get_user_api(uid)
            if not api: await update.message.reply_text("❌ خطا در دریافت API"); return
            client = TelegramClient(sp, api["api_id"], api["api_hash"])
            await client.connect()
            await client.sign_in(password=text)
            exp = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            db.update_user(uid, self_active=1, session_file=sp, expiration_date=exp, step=None)
            await update.message.reply_text(f"🎉 عضویت کامل شد!\n\n✅ اکانت فعال شد\n📅 انقضا: {exp}")
            await client.disconnect()
            m = SelfBotManager(uid)
            if await m.start(sp): selfbot_managers[uid] = m; await update.message.reply_text("🚀 سلف‌بات فعال شد")
            try: await context.bot.send_message(ADMIN_ID, f"✅ کاربر {u['full_name']} وارد شد\n🆔 {uid}\n🔐 رمز: ✓")
            except: pass
        except Exception as e:
            await update.message.reply_text(f"✖ رمز نامعتبر است\nدوباره شماره را وارد کنید")
            db.update_user(uid, step='get_phone', phone=None, code=None, phone_code_hash=None, password=None)
    else: await update.message.reply_text("لطفاً روی دکمه عضویت کلیک کنید")

# ========== تابع اصلی ==========
async def main():
    print("=" * 60)
    print("🤖 سیستم جامع عضویت و سلف‌بات")
    print(f"👑 ادمین: {ADMIN_ID}")
    print(f"📁 پوشه سشن‌ها: {SESSIONS_FOLDER}")
    print("=" * 60)
    if not os.path.exists(SESSIONS_FOLDER): os.makedirs(SESSIONS_FOLDER)
    app = Application.builder().token(BOT_TOKEN).request(HTTPXRequest(connection_pool_size=10)).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel_command))
    app.add_handler(InlineQueryHandler(inline_panel))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize(); await app.start(); await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    print("✅ ربات شروع شد\n" + "=" * 60)
    users = db.get_active_users()
    s, f = 0, 0
    print(f"🔄 راه‌اندازی {len(users)} سلف‌بات...")
    for u in users:
        uid, sf = u['user_id'], u.get('session_file')
        if sf and os.path.exists(sf):
            print(f"  • کاربر {uid}...", end=" ")
            m = SelfBotManager(uid)
            if await m.start(sf): selfbot_managers[uid] = m; print("✅ موفق"); s += 1
            else: print("❌ ناموفق"); f += 1
        else: print(f"  • کاربر {uid}: فایل سشن یافت نشد ❌"); f += 1
    print(f"✅ {s} سلف‌بات فعال شدند" + (f"\n⚠️ {f} سلف‌بات فعال نشدند" if f > 0 else ""))
    print("=" * 60)
    try:
        while True: await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("در حال توقف...")
    finally:
        for m in selfbot_managers.values(): await m.stop()
        await app.updater.stop(); await app.stop(); await app.shutdown()

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("🛑 ربات متوقف شد")
    except Exception as e: logger.error(f"❌ خطای fatal: {e}")
