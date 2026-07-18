import sys
import os

# ۱. اول از همه اضافه کردن پوشه packages به مسیرهای پیش‌فرض پایتون
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages'))

# ۲. حالا ایمپورت کتابخانه‌های اصلی که توی پوشه packages داری
import asyncio
import aiosqlite
import random
import difflib
import telethon
import re
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from io import StringIO

# --- [ تنظیمات و لود متغیرها ] ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
DB_PATH = os.path.join(BASE_DIR, 'music_archive.db')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
        load_dotenv(stream=StringIO(f.read()))

ADMIN_ID = 157537833  # آیدی عددی شما

try:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 
    CHANNEL_URL = "https://t.me/songbartender" 
except (TypeError, ValueError):
    print("Error: Please check your .env file.")
    exit()

# کلاینت‌ها بدون حلقه سفارشی (روش استاندارد)
bot_client = TelegramClient(os.path.join(BASE_DIR, 'bot_session'), API_ID, API_HASH)
user_client = TelegramClient(os.path.join(BASE_DIR, 'user_session'), API_ID, API_HASH)

# --- [ تنظیمات تگ‌ها و دسته‌بندی‌ها ] ---
TAG_CATEGORIES = {
    "🎭 حال‌وهوا": [
        "sad", "romantic", "happy", "chill", "emotional", "motivational", 
        "peaceful", "soft", "night", "sleep", "focus", "deepdark", "epic", "energetic"
    ],
    "🎸 سبک موسیقی": [
        "rock", "jazz", "classical", "rap", "hiphop", "opera", "folk", "country", 
        "chanson", "blues", "disco", "funk", "ballad", "soul", "classic", 
        "spokenword", "gospel", "deluxe", "persianclassical", "accordion"
    ],
    "🌍 سایر زبان‌ها": [
        "french", "arabic", "persian", "german", "norwegian", 
        "latin", "chinese", "korean", "turkic", "italian", "czech"
    ],
    "🎤 نوع اجرا": [
        "vocal", "choir", "live", "concert", "soprano", "tenor", 
        "instrumental", "cover", "orchestra", "piano", "soundtrack", "playlist"
    ]
}

ALL_TAGS = {
    "sad": "sad 💔", "romantic": "romantic 🫶🏼", "happy": "happy 💃🏻", "chill": "chill 🫖",
    "emotional": "emotional 🎀", "motivational": "motivational 🌱", "country": "country 🤠",
    "chanson": "chanson 🇫🇷", "energetic": "energetic 💥", "folk": "folk 🎸", "jazz": "jazz 🎷",
    "classical": "classical 🎻", "soprano": "soprano 👩🏻‍🦰🗣", "tenor": "tenor 🧔🏻‍♂️🗣", 
    "vocal": "vocal 🗣", "opera": "opera 🪄🎦", "instrumental": "instrumental 🎼", "rap": "rap 🌪",
    "orchestra": "orchestra 🪈🎻", "choir": "choir 👬👭", "peaceful": "peaceful 🧚🏻‍♀️", 
    "hiphop": "hiphop 🤙", "rock": "rock ☄️", "piano": "piano 🎹", "soft": "soft 🌊", 
    "night": "night 🕯", "sleep": "sleep 🛏", "soundtrack": "soundtrack 🎞", "epic": "epic 🥁", 
    "cover": "cover 🖇", "live": "live 🌌", "deepdark": "deepdark 🌑", "focus": "focus 💆🏼🧘🏻‍♀️", 
    "deluxe": "deluxe 🔃", "classic": "classic 📻", "blues": "blues 📯", "spokenword": "spokenword 🪔", 
    "disco": "disco 🪩", "funk": "funk 🥁", "ballad": "ballad 💘📰", "soul": "soul 🎺", 
    "accordion": "accordion 🪗", "persianclassical": "persianclassical 🕊", "concert": "concert 🎫", 
    "playlist": "playlist 🎧", "gospel": "gospel ⛪️", "french": "French 🇫🇷", 
    "arabic": "Arabic 🇦🇪", "persian": "Persian 🇮🇷", "german": "German 🇩🇪", "norwegian": "Norwegian 🇳🇴", 
    "latin": "Latin 📜", "chinese": "Chinese 🇨🇳", "korean": "Korean 🇰🇷", "turkic": "Turkic 🇹🇷", 
    "italian": "Italian 🇮🇹", "czech": "Czech 🇨🇿"
}

TAG_DESCRIPTIONS = {
    # 🎭 حال‌وهوا
    "sad": " غمگین؛ حس اندوه و دل‌تنگی", "romantic": " عاشقانه؛ با حال‌وهوا و متن رمانتیک",
    "happy": " شاد؛ ریتمیک، و نشاط‌آور", "chill": " ملایم؛ بدون درگیری احساس",
    "emotional": " عمیقاً احساسی؛ برانگیزاننده عواطف (لزوماً غمگین نیست)", "motivational": " انگیزشی؛ محرک و امیدبخش",
    "peaceful": " آرامشبخش", "soft": " روان و نرم؛ بدون صدای خشن و تیز",
    "night": " مناسب فضای شب", "sleep": " بسیار ملایم با فرکانس پایین؛ مخصوص خواب",
    "focus": "مخصوص تمرکز، کار و مطالعه", "deepdark": " غمگین با فضای آرام و عمیق",
    "epic": " حماسی و کوبنده، حس قدرت", "energetic": "آهنگ پرانرژی",

    # 🎸 سبک موسیقی
    "soul": "آواز پرحس همراه با سازهای بادی برنجی، پیانو، ارگ هموند و بیس",
    "classic": "قطعات قدیمی، ماندگار و نوستالژیک",
    "rap": "کلام‌محور با تمرکز روی تکنیک خوندن، سرعت کلمات، قافیه‌بازی و روایت‌های شخصی",
    "hiphop": "فرهنگ‌محور و ملودیک‌تر از رپ؛ با تمرکز روی دغدغه‌های اجتماعی، جریان زندگی خیابانی",
    "jazz": "شناخته‌شده برای بداهه‌نوازی،با دیالوگ میان ساکسیفون، ترومپت، پیانو،درامز و هارمونی‌های پیچیده",
    "classical": "موسیقی کلاسیک غربی (دوره‌های باروک تا رمانتیک) با ساختار پیچیده و سازهای سمفونیک",
    "opera": "هنر صحنه‌ای که در آن آواز (اغلب سوپرانو و تنور) و موسیقی داستان را روایت می‌کنند",
    "folk": "موسیقی فولکلور، محلی و سنتیِ ریشه‌دار در فرهنگ ملت‌ها",
    "country": "سبک کانتری؛ فولک آمریکایی با گیتار آکوستیک و ویولن",
    "chanson": "سبک شانسون؛ آوازی فرانسوی با اشعار احساسی و غنی",
    "blues": "سبک بلوز؛بر اساس  گیتار، هارمونیکا (سازدهنی)، پیانو و بیس با فرم ۱۲ میزانی",
    "disco": "موسیقی رقص‌محور", "funk": "سبکی با تمرکز بر ریتم،اصرار روی ضرب اول، ریشه در سول و جاز",
    "ballad": "قطعات احساسی و تمپو کند که یک داستان عاشقانه را روایت می‌کنند",
    "spokenword": "دکلمه و شعرخوانی گفتاری",
    "gospel": "موسیقی مذهبی مسیحی که ریشه در کلیسای سیاه‌پوستان آمریکا دارد، اغلب دسته‌جمعی و با گروه کر",
    "deluxe": "نسخه ویژه و کامل‌تر یک قطعه (شامل ترک‌های اضافه یا نسخه‌های متفاوت)",
    "persianclassical": "موسیقی سنتی، دستگاهی و ردیف‌آوازی ایران",
    "accordion": "قطعاتی با محوریت و نقش اصلی ساز آکاردئون", "rock": "سبک راک؛ محوریت با گیتار الکتریک، بیس و درامز",

    # 🌍 سایر زبان‌ها
    "french": "زبان فرانسوی", "arabic": "زبان عربی", "persian": "زبان فارسی", 
    "german": "زبان آلمانی", "norwegian": "زبان نروژی",
    "latin": "زبان‌های خانواده لاتین (اسپانیایی، پرتغالی و...)", "chinese": "زبان چینی",
    "korean": "زبان کره‌ای", "turkic": "زبان‌های خانواده ترکی", "italian": "زبان ایتالیایی", "czech": "زبان چکی",

    # 🎤 نوع اجرا
    "vocal": "تک‌خوانی؛ تمرکز اصلی قطعه روی آواز و صدای انسان است",
    "choir": "گروه کر؛ هم‌سرایی و آواز دسته‌جمعی هماهنگ و چندصدایی",
    "live": "اجرای زنده صمیمی، محفلی یا خیابانی (همراه با صدای محیط)",
    "concert": "اجرای زنده رسمی و ضبط‌شده در سالن‌های بزرگ کنسرت",
    "soprano": "بالاترین زیروبمی صدای انسانی؛ آواز بسیار زیر (معمولاً زنان)",
    "tenor": "بالاترین حد صدای طبیعی مردان؛ آواز قدرتمند، اوج و شفاف",
    "instrumental": "موسیقی بی‌کلام؛ اجرای خالص سازها بدون خواننده",
    "cover": "بازخوانی یا بازنوازی یک اثر معروف توسط هنرمند دیگر",
    "orchestra": "اجرای گروه بزرگ نوازندگان", "piano": "قطعات اجرا شده با ساز اصلی پیانو",
    "soundtrack": "موسیقی متن فیلم، سریال یا بازی‌های ویدیویی", "playlist": "مجموعه‌ای منتخب از قطعات برگزیده"
}

user_states = {}

def get_init_state():
    return {
        'mode': 'MAIN', 'tags': {}, 'help_mode': False,
        'logic': 'AND', 'artists': set(), 'search_text': None, 'art_q': None, 'pl_count': None
    }

# --- [ ابزارهای کمکی و دیتابیس ] ---

async def is_member(uid):
    try:
        await bot_client.get_permissions(CHANNEL_ID, uid)
        return True
    except telethon.errors.rpcerrorlist.UserNotParticipantError:
        return False
    except Exception:
        return True

def to_persian_digits(num):
    persian = '۰۱۲۳۴۵۶۷۸۹'
    return str(num).translate(str.maketrans('0123456789', persian))

async def get_tag_counts():
    counts = {}
    # اضافه کردن timeout برای جلوگیری از خطای database is locked
    async with aiosqlite.connect(DB_PATH, timeout=10.0) as db:
        async with db.execute("SELECT tags FROM songs") as c:
            rows = await c.fetchall()
    for row in rows:
        if row[0]:
            for tag in row[0].split():
                clean_tag = tag.replace('#', '').lower()
                counts[clean_tag] = counts.get(clean_tag, 0) + 1
    return counts

async def sync_database(event):
    try:
        if not user_client.is_connected():
            return await event.respond("❌ خطا: کلاینت کاربر (User Client) متصل نیست!")
            
        await event.edit("🔄 شروع فرآیند آپدیت... این عملیات ممکن است چند دقیقه طول بکشد. لطفا صبور باشید.")
        count = 0
        
        # اضافه کردن timeout به دیتابیس
        async with aiosqlite.connect(DB_PATH, timeout=20.0) as db:
            async for msg in user_client.iter_messages(CHANNEL_ID):
                if msg.audio:
                    artist = "Unknown Artist"
                    title = "Unknown Title"
                    
                    if msg.document and hasattr(msg.document, 'attributes'):
                        for attr in msg.document.attributes:
                            if isinstance(attr, telethon.tl.types.DocumentAttributeAudio):
                                artist = attr.performer or "Unknown Artist"
                                title = attr.title or "Unknown Title"
                                break
                    
                    tags = " ".join(re.findall(r'#\w+', msg.text or ""))
                    await db.execute(
                        "INSERT OR REPLACE INTO songs (msg_id, artist, title, tags) VALUES (?, ?, ?, ?)",
                        (msg.id, artist, title, tags)
                    )
                    count += 1
                    
                    if count % 50 == 0:
                        await db.commit()
                        await asyncio.sleep(0.5)
                        
            await db.commit()
            
        await event.respond(f"✅ دیتابیس با موفقیت آپدیت شد!\n📥 {count} آهنگ بررسی و همگام شد.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        await event.respond(f"❌ خطای بحرانی هنگام آپدیت:\n`{type(e).__name__}: {e}`")

# --- [ ساختار دکمه‌ها (UI) ] ---

def join_btns():
    return [
        [Button.url("📢 عضویت در کانال", CHANNEL_URL)],
        [Button.inline("✅ عضو شدم", data="check_join")]
    ]

def main_menu_btns(uid):
    s = user_states.get(uid, get_init_state())
    has_filters = bool(s['tags']) or bool(s['artists'])
    pl_label = "🎲 پلی‌لیست رندوم (از بین فیلترها)" if has_filters else "🎲 غافلگیرم کن (آهنگ شانسی)"
    
    btns = [
        [Button.inline("🎨 کاوش با حس‌وحال (فیلترها)", data="cat_p")],
        [Button.inline(pl_label, data="pl_menu")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("🔄 آپدیت دیتابیس (مدیریتی)", data="update_db")])
    return btns

async def build_category_menu(uid):
    s = user_states[uid]
    btns = []
    for idx, cat_name in enumerate(TAG_CATEGORIES.keys()):
        has_tag = any(s['tags'].get(t, 0) != 0 for t in TAG_CATEGORIES[cat_name])
        prefix = "✅ " if has_tag else ""
        btns.append([Button.inline(f"{prefix}{cat_name}", data=f"cat_tags:{idx}")])
    
    nav = []
    if s['artists']: nav.append(Button.inline(f"👨‍🎤 هنرمندان ({len(s['artists'])})", data="list_art:0"))
    nav.append(Button.inline("♻️ شروع مجدد", data="clear"))
    if nav: btns.append(nav)
        
    btns.append([
        Button.inline("🎵 مشاهده نتایج", data="search_p:0"),
        Button.inline("🎲 ساخت پلی‌لیست", data="pl_menu")
    ])
    return btns

async def build_tags_menu(uid, cat_idx):
    s = user_states[uid]
    cat_name = list(TAG_CATEGORIES.keys())[cat_idx]
    tags = TAG_CATEGORIES[cat_name]
    
    btns = []
    counts = await get_tag_counts()
    row = []
    for k in tags:
        v = s['tags'].get(k, 0)
        count = counts.get(k, 0)
        fa_count = to_persian_digits(count)
        lbl = f"{'✅' if v==1 else '➕'} {ALL_TAGS.get(k, k)} ({fa_count})"
        row.append(Button.inline(lbl, data=f"tg:{k}:{cat_idx}"))
        if len(row) == 2: btns.append(row); row = []
    if row: btns.append(row)
    
    prev_cat = (cat_idx - 1) % len(TAG_CATEGORIES)
    next_cat = (cat_idx + 1) % len(TAG_CATEGORIES)
    btns.append([
        Button.inline(f"👈    |{list(TAG_CATEGORIES.keys())[prev_cat]}|", data=f"cat_tags:{prev_cat}"),
        Button.inline(f"|{list(TAG_CATEGORIES.keys())[next_cat]}|    👉", data=f"cat_tags:{next_cat}")
    ])
    
    logic_lbl = "🎯 فیلترها: آهنگ باید همه تگ‌ها رو داشته باشه" if s['logic'] == 'AND' else "🌊 فیلترها: کافیه یکی از تگ‌ها رو داشته باشه"
    btns.append([Button.inline(logic_lbl, data=f"toggle_logic:{cat_idx}")])
    
    help_lbl = "📖  معرفی تگ‌ها (برای دیدن توضیحات هر تگ روی آن کلیک کنید): روشن" if s['help_mode'] else "📖 معرفی تگ‌ها (آموزش): خاموش"
    btns.append([Button.inline(help_lbl, data=f"toggle_help:{cat_idx}")])
    
    btns.append([
        Button.inline("🏠بازگشت", data="cat_p"),
        Button.inline("🎵مشاهده‌نتایج", data="search_p:0"),
        Button.inline("🎲ساخت‌ پلی‌لیست", data="pl_menu")
    ])
    
    return btns

async def show_artists(event, page, search_q=None):
    uid = event.sender_id; s = user_states[uid]; limit = 12; offset = page * limit
    if search_q is not None: s['art_q'] = search_q
    current_q = s.get('art_q')

    async with aiosqlite.connect(DB_PATH, timeout=10.0) as db:
        async with db.execute("SELECT artist, COUNT(*), MIN(msg_id) FROM songs GROUP BY artist") as c:
            all_data = await c.fetchall()

    if current_q:
        q_low = current_q.lower().strip()
        names = [r[0] for r in all_data]
        matches = difflib.get_close_matches(q_low, names, n=20, cutoff=0.4)
        filtered = [r for name in matches for r in all_data if r[0] == name]
        for r in all_data:
            if q_low in r[0].lower() and r not in filtered: filtered.append(r)
        selected_rows = [r for r in all_data if r[0] in s['artists']]
        filtered = selected_rows + [r for r in filtered if r not in selected_rows]
    else:
        filtered = sorted(all_data, key=lambda x: x[0])

    if not filtered: return await event.respond(f"❌ هنرمندی شبیه به '{current_q}' پیدا نشد.")
    
    display = filtered[offset:offset+limit]; btns = []
    for name, count, mid in display:
        is_sel = "✅ " if name in s['artists'] else ""
        btns.append([Button.inline(f"{is_sel}{name} ({count})", data=f"sel_art:{mid}:{page}")])

    nav = []
    if page > 0: nav.append(Button.inline("  ⬅️ قبل", data=f"list_art:{page-1}"))
    if len(filtered) > offset + limit: nav.append(Button.inline( "بعد➡️  ", data=f"list_art:{page+1}"))
    if nav: btns.append(nav)
    btns.append([Button.inline("🔎 جستجوی هنرمند", data="art_search_prompt"), Button.inline("🏠 بازگشت", data="cat_p")])
    
    txt = "👨‍🎤 لیست هنرمندان (انتخابی‌ها در صدر):" if current_q else "👨‍🎤 لیست هنرمندان:"
    try:
        if isinstance(event, events.CallbackQuery): await event.edit(txt, buttons=btns)
        else: await event.respond(txt, buttons=btns)
    except: pass

# --- [ هندلرهای اصلی ] ---

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    uid = event.sender_id
    if not await is_member(uid):
        return await event.respond("🍷 برای استفاده از ربات، ابتدا در کانال عضو شو:", buttons=join_btns())
    
    user_states[uid] = get_init_state()
    await event.respond(
        f"سلام {event.sender.first_name or ''}! به دنیای موسیقی خوش اومدی ✨\n\n"
        "🍷 آماده‌ی سرو کردن موزیک‌های دلخواهتم!\n\n"
        "👈 می‌تونی مستقیم اسم آهنگ یا خواننده مد نظرت رو برام تایپ کنی و نتایج مرتبط بر اساس کانال SongBartender فرستاده میشن .\n"
        "👈 یا از دکمه‌های زیر برای کاوش و ساخت پلی‌لیست استفاده کنی:", 
        buttons=main_menu_btns(uid)
    )

@bot_client.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8'); uid = event.sender_id
    
    if data == "check_join":
        if await is_member(uid):
            await event.delete()
            user_states[uid] = get_init_state()
            return await event.respond("✅ خوش اومدی! بریم برای سرو موزیک:", buttons=main_menu_btns(uid))
        else:
            return await event.answer("⚠️ هنوز عضو کانال نشدی!", alert=True)

    if not await is_member(uid):
        return await event.answer("⛔️ ابتدا باید عضو کانال باشی.", alert=True)

    s = user_states.setdefault(uid, get_init_state())

    if data == "update_db":
        if uid == ADMIN_ID: await sync_database(event)
        else: await event.answer("🚫 مخصوص مدیر.", alert=True)
        
    elif data == "cat_p":
        s['mode'] = 'EXPLORE_CAT'
        await event.edit("🎨 یه دسته رو برای فیلتر کردن انتخاب کن:", buttons=await build_category_menu(uid))
        
    elif data.startswith("cat_tags:"):
        s['mode'] = 'TAG_SELECT'
        cat_idx = int(data.split(":")[1])
        await event.edit("تگ‌های مورد نظرت رو انتخاب کن:", buttons=await build_tags_menu(uid, cat_idx))
        
    elif data.startswith("tg:"):
        _, tag, cat_idx = data.split(":")
        
        if s.get('help_mode'):
            desc = TAG_DESCRIPTIONS.get(tag, "توضیحاتی برای این تگ ثبت نشده است.")
            return await event.answer(desc, alert=True)
            
        current = s['tags'].get(tag, 0)
        s['tags'][tag] = 1 if current == 0 else 0
        await event.edit(buttons=await build_tags_menu(uid, int(cat_idx)))
        
    elif data.startswith("toggle_help:"):
        cat_idx = int(data.split(":")[1])
        s['help_mode'] = not s['help_mode']
        await event.edit(buttons=await build_tags_menu(uid, cat_idx))
        
    elif data.startswith("toggle_logic:"):
        cat_idx = int(data.split(":")[1])
        s['logic'] = 'OR' if s['logic'] == 'AND' else 'AND'
        await event.edit(buttons=await build_tags_menu(uid, cat_idx))
        
    elif data.startswith("list_art:"): 
        await show_artists(event, int(data.split(":")[1]))
        
    elif data == "art_search_prompt":
        s['mode'] = 'ARTIST_SEARCH'; await event.respond("🔎 نام هنرمند رو تایپ کن:")
        
    elif data.startswith("sel_art:"):
        _, mid, page = data.split(":")
        async with aiosqlite.connect(DB_PATH, timeout=10.0) as db:
            async with db.execute("SELECT artist FROM songs WHERE msg_id = ?", (mid,)) as c:
                row = await c.fetchone()
                if row:
                    name = row[0]
                    if name in s['artists']: s['artists'].remove(name)
                    else: s['artists'].add(name)
        await show_artists(event, int(page))

    elif data == "pl_menu":
        has_filters = bool(s['tags']) or bool(s['artists'])
        txt = "🎲 چند آهنگ توی پلی‌لیستت باشه؟\n(از بین فیلترهای انتخابی)" if has_filters else "🎲 چند آهنگ توی پلی‌لیستت باشه؟\n"
        btns = [
            [Button.inline("5 آهنگ", data="set_pl:5"), Button.inline("10 آهنگ", data="set_pl:10")],
            [Button.inline("15 آهنگ", data="set_pl:15"), Button.inline("20 آهنگ", data="set_pl:20")],
            [Button.inline("🏠 منوی اصلی", data="clear_to_main")]
        ]
        await event.edit(txt, buttons=btns)
        
    elif data.startswith("set_pl:"):
        s['pl_count'] = int(data.split(":")[1])
        await event.answer(f"{s['pl_count']} آهنگ تنظیم شد!")
        await create_playlist(event)
        
    elif data.startswith("search_p:"):
        await show_results(event, int(data.split(":")[1]))
        
    elif data == "clear":
        user_states[uid] = get_init_state()
        try:
            await event.delete()
        except:
            pass
        await event.respond("♻️ همه چیز reset شد. بریم از اول:", buttons=main_menu_btns(uid))
        
    elif data == "clear_to_main":
        s['mode'] = 'MAIN'
        await event.edit("✅ فیلترها ثبت شدند. چیکار کنیم؟", buttons=main_menu_btns(uid))
        
    elif data.startswith("get_mu:"):
        await bot_client.forward_messages(event.chat_id, int(data.split(":")[1]), CHANNEL_ID)

@bot_client.on(events.NewMessage())
async def message_handler(event):
    if not event.is_private or event.text.startswith('/'): return
    uid = event.sender_id
    if not await is_member(uid): return
        
    s = user_states.setdefault(uid, get_init_state())
    
    if s.get('mode') == 'ARTIST_SEARCH':
        s['mode'] = 'MAIN'; await show_artists(event, 0, search_q=event.text); return
        
    s['search_text'] = event.text
    s['mode'] = 'MAIN'
    await show_results(event, 0, is_callback=False)

# --- [ موتور جستجو و الگوریتم مشابهات ] ---

def build_query(uid):
    s = user_states[uid]; p = []
    must = [t for t, v in s['tags'].items() if v==1]
    
    q = "SELECT msg_id, artist, title"
    
    if s['search_text']:
        q += ", (CASE WHEN (title LIKE ? OR artist LIKE ?) THEN 10 ELSE 0 END"
        p.extend([f"%{s['search_text']}%", f"%{s['search_text']}%"])
        words = s['search_text'].split()
        if len(words) > 1:
            for word in words:
                q += " + CASE WHEN (title LIKE ? OR artist LIKE ?) THEN 2 ELSE 0 END"
                p.extend([f"%{word}%", f"%{word}%"])
        q += ") as score "
    else:
        q += ", 0 as score "
        
    q += " FROM songs WHERE 1=1"
    
    if s['artists']:
        q += f" AND artist IN ({','.join(['?']*len(s['artists']))})"
        p.extend(list(s['artists']))
        
    if s['search_text']:
        words = s['search_text'].split()
        search_conditions = ["title LIKE ?", "artist LIKE ?"]
        p.extend([f"%{s['search_text']}%", f"%{s['search_text']}%"])
        for word in words:
            search_conditions.extend(["title LIKE ?", "artist LIKE ?"])
            p.extend([f"%{word}%", f"%{word}%"])
        q += f" AND ({' OR '.join(search_conditions)})"
        
    if must:
        if s['logic'] == 'AND':
            for t in must: q += " AND tags LIKE ?"; p.append(f"%#{t}%")
        else: q += f" AND ({' OR '.join(['tags LIKE ?']*len(must))})"; p.extend([f"%#{t}%" for t in must])
            
    q += " ORDER BY score DESC, msg_id DESC"
    return q, p

async def show_results(event, page, is_callback=True):
    uid = event.sender_id; s = user_states[uid]; limit = 12; offset = page * limit
    
    q, p = build_query(uid)
    async with aiosqlite.connect(DB_PATH, timeout=10.0) as db:
        async with db.execute(q, p) as c: 
            sql_rows = await c.fetchall()
            final_results = list(sql_rows) 

        if s['search_text'] and page == 0:
            async with db.execute("SELECT msg_id, artist, title FROM songs") as c2:
                all_songs = await c2.fetchall()
                
            words_set = set()
            word_to_songs = {}
            
            for r in all_songs:
                words = re.findall(r'\w+', f"{r[1]} {r[2]}".lower())
                for w in words:
                    if len(w) > 1: 
                        words_set.add(w)
                        if w not in word_to_songs:
                            word_to_songs[w] = []
                        if r not in word_to_songs[w]:
                            word_to_songs[w].append(r)
                            
            query_words = re.findall(r'\w+', s['search_text'].lower())
            matched_songs = set()
            
            for qw in query_words:
                matches = difflib.get_close_matches(qw, list(words_set), n=5, cutoff=0.5)
                for match_word in matches:
                    for song_data in word_to_songs.get(match_word, []):
                        matched_songs.add(song_data)
                        
            existing_ids = {r[0] for r in final_results}
            for song_data in matched_songs:
                if song_data[0] not in existing_ids:
                    final_results.append((song_data[0], song_data[1], song_data[2], 0))

    display_rows = final_results[offset:offset+limit]
    if not display_rows:
        msg = "❌ چیزی پیدا نشد. دوباره امتحان کن یا فیلترها رو تغییر بده!"
        btns = [[Button.inline("🏠 منوی اصلی", data="clear_to_main")]]
        return await event.respond(msg, buttons=btns) if not is_callback else await event.edit(msg, buttons=btns)

    btns = []
    for r in display_rows:
        label = f"🎵 {r[1]} - {r[2]}"
        if len(label) > 50: label = label[:47] + "..."
        btns.append([Button.inline(label, data=f"get_mu:{r[0]}")])

    nav = []
    if page > 0: nav.append(Button.inline("⬅️ قبل", data=f"search_p:{page-1}"))
    if len(final_results) > offset + limit: nav.append(Button.inline("بعد ➡️", data=f"search_p:{page+1}"))
    if nav: btns.append(nav)
    
    btns.append([Button.inline("🏠 بازگشت (با حفظ فیلترها)", data="clear_to_main"), Button.inline("♻️ شروع مجدد", data="clear")])
    
    msg = f"🔎 نتایج برای: '{s['search_text'] or 'فیلترهای انتخابی'}'"
    try:
        if is_callback: await event.edit(msg, buttons=btns)
        else: await event.respond(msg, buttons=btns)
    except: pass

async def create_playlist(event):
    uid = event.sender_id; s = user_states[uid]; q, p = build_query(uid)
    async with aiosqlite.connect(DB_PATH, timeout=10.0) as db:
        async with db.execute(q + " LIMIT 200", p) as c: songs = await c.fetchall()
    if not songs: 
        return await event.edit("آهنگی با این فیلترها پیدا نشد.", buttons=[[Button.inline("🏠 خانه", data="clear")]])
    
    sel = random.sample(songs, min(s['pl_count'], len(songs)))
    await event.edit(f"🎲 در حال ارسال {len(sel)} آهنگ شانسی..."); 
    for song in sel:
        try: await bot_client.forward_messages(event.chat_id, song[0], CHANNEL_ID); await asyncio.sleep(0.3)
        except: continue
    s['pl_count'] = None
    await event.respond("نوش جان! 🍷", buttons=main_menu_btns(uid))

async def main():
    try:
        async with aiosqlite.connect(DB_PATH, timeout=10.0) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS songs (msg_id INTEGER PRIMARY KEY, artist TEXT, title TEXT, tags TEXT)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_art ON songs(artist)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tit ON songs(title)")
            await db.commit()
            
        print("--- Connecting clients... ---")
        await user_client.start()
        await bot_client.start(bot_token=BOT_TOKEN)
        print("--- Bartender is Online! ---")
        
        # اجرای هر دو کلاینت به صورت همزمان برای جلوگیری از باگ different loop
        await asyncio.gather(
            bot_client.run_until_disconnected(),
            user_client.run_until_disconnected()
        )
        
    except Exception as e:
        import traceback
        print(f"System Error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    # استفاده از get_event_loop به جای asyncio.run برای سازگاری با Telethon
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
