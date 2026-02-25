import asyncio, aiosqlite, random, difflib, os, telethon, re
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from io import StringIO

# --- [ تنظیمات و لود متغیرها ] ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
        load_dotenv(stream=StringIO(f.read()))

ADMIN_ID = 157537833  # آیدی عددی معین

try:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 
    CHANNEL_URL = "https://t.me/songbartender" 
except (TypeError, ValueError):
    print("Error: Please check your .env file for API_ID, API_HASH, BOT_TOKEN and CHANNEL_ID.")
    exit()

bot_client = TelegramClient('bot_session', API_ID, API_HASH)
user_client = TelegramClient('user_session', API_ID, API_HASH)

# تگ‌های شخصی‌سازی شده
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
    "playlist": "playlist 🎧", "gospel": "gospel ⛪️", "french": "French 🇫🇷", "arabic": "Arabic 🇦🇪", 
    "persian": "Persian 🇮🇷", "german": "German 🇩🇪", "norwegian": "Norwegian 🇳🇴", "latin": "Latin 📜", 
    "chinese": "Chinese 🇨🇳", "korean": "Korean 🇰🇷", "turkic": "Turkic 🇹🇷", "italian": "Italian 🇮🇹", "czech": "Czech 🇨🇿"
}

user_states = {}

def get_init_state():
    return {'tags': {}, 'search_text': None, 'artists': set(), 'pl_count': None, 'logic': 'AND', 'mode': 'MAIN', 'art_q': None}

# --- [ ابزارهای کمکی و ادمین ] ---

async def is_member(uid):
    try:
        await bot_client.get_permissions(CHANNEL_ID, uid)
        return True
    except telethon.errors.rpcerrorlist.UserNotParticipantError:
        return False
    except Exception:
        return True

async def sync_database(event):
    """تابع همگام‌سازی دیتابیس - حل مشکل AttributeError و آپدیت تگ‌ها"""
    await event.edit("🔄 در حال اسکن کانال و آپدیت دیتابیس... لطفا صبور باش معین جان.")
    count = 0
    async with aiosqlite.connect('music_archive.db') as db:
        async for msg in user_client.iter_messages(CHANNEL_ID):
            if msg.audio:
                artist = "Unknown Artist"
                title = "Unknown Title"
                
                # استخراج متادیتا از لایه‌های داخلی فایل (رفع ارور AttributeError)
                for attr in msg.document.attributes:
                    if isinstance(attr, telethon.tl.types.DocumentAttributeAudio):
                        artist = attr.performer or "Unknown Artist"
                        title = attr.title or "Unknown Title"
                        break
                
                # پیدا کردن تمام هشتگ‌ها در متن پیام
                tags = " ".join(re.findall(r'#\w+', msg.text or ""))
                
                await db.execute(
                    "INSERT OR REPLACE INTO songs (msg_id, artist, title, tags) VALUES (?, ?, ?, ?)",
                    (msg.id, artist, title, tags)
                )
                count += 1
        await db.commit()
    await event.respond(f"✅ دیتابیس با موفقیت آپدیت شد!\n📥 تعداد {count} آهنگ بررسی و همگام شد.")

def join_btns():
    return [
        [Button.url("📢 عضویت در کانال", CHANNEL_URL)],
        [Button.inline("✅ عضو شدم (تایید)", data="check_join")]
    ]

def main_menu_btns(uid):
    s = user_states.get(uid, get_init_state())
    tag_count = len([v for v in s['tags'].values() if v != 0])
    art_count = len(s['artists'])
    label = f"🚀 ساخت پلی‌لیست ({s['pl_count']})" if isinstance(s.get('pl_count'), int) else "🔎 مشاهده نتایج"
    
    btns = [
        [Button.inline(label, data="search_p:0")],
        [Button.inline(f"🎭 تگ‌ها ({tag_count})", data="tag_p:0"), Button.inline(f"👨‍🎤 هنرمندان ({art_count})", data="list_art:0")],
        [Button.inline("🎲 آهنگ رندوم", data="pl_ask"), Button.inline("🏠 ریست و خانه", data="clear")]
    ]
    if uid == ADMIN_ID:
        btns.append([Button.inline("🔄 آپدیت دیتابیس (مدیریتی)", data="update_db")])
    return btns

async def build_tags_menu(uid, page):
    s = user_states[uid]
    keys = list(ALL_TAGS.keys()); limit = 30; offset = page * limit
    chunk = keys[offset:offset+limit]; btns = []; row = []
    for k in chunk:
        v = s['tags'].get(k, 0)
        lbl = f"{'✅' if v==1 else '❌' if v==-1 else ''}{ALL_TAGS[k]}"
        row.append(Button.inline(lbl, data=f"tg:{k}:{page}"))
        if len(row) == 3: btns.append(row); row = []
    if row: btns.append(row)
    
    btns.append([Button.inline("⬅️ قبل", data=f"tag_p:{max(0, page-1)}"), Button.inline("بعد ➡️", data=f"tag_p:{page+1}")])
    btns.append([Button.inline(f"🖇 منطق: {s['logic']}", data="toggle_logic"), Button.inline("🔎 جستجو", data="search_p:0")])
    btns.append([Button.inline("🏠 بازگشت", data="clear_to_main")])
    return btns

async def show_artists(event, page, search_q=None):
    uid = event.sender_id; s = user_states[uid]; limit = 12; offset = page * limit
    if search_q is not None: s['art_q'] = search_q
    current_q = s.get('art_q')

    async with aiosqlite.connect('music_archive.db') as db:
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
    if page > 0: nav.append(Button.inline("⬅️ قبل", data=f"list_art:{page-1}"))
    if len(filtered) > offset + limit: nav.append(Button.inline("بعد ➡️", data=f"list_art:{page+1}"))
    if nav: btns.append(nav)
    btns.append([Button.inline("🔎 جستجوی هنرمند", data="art_search_prompt"), Button.inline("🏠 تایید", data="clear_to_main")])
    
    txt = "👨‍🎤 لیست هنرمندان (انتخابی‌ها در صدر):" if current_q else "👨‍🎤 لیست هنرمندان:"
    try:
        if isinstance(event, events.CallbackQuery): await event.edit(txt, buttons=btns)
        else: await event.respond(txt, buttons=btns)
    except telethon.errors.rpcerrorlist.MessageNotModifiedError: pass

# --- [ هندلرهای اصلی ] ---

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    uid = event.sender_id
    if not await is_member(uid):
        return await event.respond("🍷 برای استفاده از ربات، در کانال عضو شو:", buttons=join_btns())
    
    user_states[uid] = get_init_state()
    await event.respond((f"درود {event.sender.first_name or 'عزیز'}! به دنیای موسیقی خوش اومدی ✨\n\n"
        "اینجا می‌تونی با ترکیب سلیقه‌ات، موزیکی که لازم داری رو پیدا کنی.\n\n"
        "🔹 **جستجوی سریع:** اسم آهنگ یا هنرمند رو همین الان تایپ کن.\n"
        "🔹 **میکس تگ‌ها:** سبک و حال‌وهوای آهنگ رو فیلتر کن.\n"
        "🔹 **چندین هنرمند:** می‌تونی چند هنرمند رو همزمان انتخاب کنی."), buttons=main_menu_btns(uid))

@bot_client.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8'); uid = event.sender_id
    
    if data == "check_join":
        if await is_member(uid):
            await event.delete()
            user_states[uid] = get_init_state()
            return await event.respond("✅ خوش آمدی! بریم برای سرو موزیک:", buttons=main_menu_btns(uid))
        else:
            return await event.answer("⚠️ هنوز عضو کانال نشدی!", alert=False)

    if not await is_member(uid):
        return await event.answer("⛔️ ابتدا باید عضو کانال باشی.", alert=True)

    s = user_states.setdefault(uid, get_init_state())

    if data == "update_db":
        if uid == ADMIN_ID: await sync_database(event)
        else: await event.answer("🚫 مخصوص مدیر.", alert=True)
    elif data.startswith("tag_p:"):
        await event.answer("💡 ۱ بار: ✅ | ۲ بار: ❌ | ۳ بار: پاک", alert=False)
        await event.edit("🎭 تگ‌ها:", buttons=await build_tags_menu(uid, int(data.split(":")[1])))
    elif data == "toggle_logic":
        s['logic'] = 'OR' if s['logic'] == 'AND' else 'AND'
        await event.edit(buttons=await build_tags_menu(uid, 0))
    elif data.startswith("list_art:"): await show_artists(event, int(data.split(":")[1]))
    elif data == "art_search_prompt":
        s['mode'] = 'ARTIST_SEARCH'; await event.respond("🔎 نام هنرمند:")
    elif data.startswith("sel_art:"):
        _, mid, page = data.split(":")
        async with aiosqlite.connect('music_archive.db') as db:
            async with db.execute("SELECT artist FROM songs WHERE msg_id = ?", (mid,)) as c:
                row = await c.fetchone()
                if row:
                    name = row[0]
                    if name in s['artists']: s['artists'].remove(name)
                    else: s['artists'].add(name)
        await show_artists(event, int(page))
    elif data.startswith("tg:"):
        _, tag, page = data.split(":")
        s['tags'][tag] = 1 if s['tags'].get(tag, 0) == 0 else -1 if s['tags'].get(tag) == 1 else 0
        await event.edit(buttons=await build_tags_menu(uid, int(page)))
    elif data.startswith("search_p:"):
        if isinstance(s.get('pl_count'), int): await create_playlist(event)
        else: await show_results(event, int(data.split(":")[1]))
    elif data == "clear":
        user_states[uid] = get_init_state(); await event.respond("🏠 ریست شد.", buttons=main_menu_btns(uid))
    elif data == "clear_to_main": await event.respond("✅ فیلترها ثبت شد.", buttons=main_menu_btns(uid))
    elif data.startswith("get_mu:"):
        await bot_client.forward_messages(event.chat_id, int(data.split(":")[1]), CHANNEL_ID)
    elif data == "pl_ask":
        s['pl_count'] = 'WAIT'; await event.respond("🎲 چند تا آهنگ گلچین کنم؟ (عدد بفرست)")

@bot_client.on(events.NewMessage())
async def message_handler(event):
    if not event.is_private or event.text.startswith('/'): return
    uid = event.sender_id
    if not await is_member(uid): return
        
    s = user_states.setdefault(uid, get_init_state())
    if s.get('mode') == 'ARTIST_SEARCH':
        s['mode'] = 'MAIN'; await show_artists(event, 0, search_q=event.text); return
    if s.get('pl_count') == 'WAIT' and event.text.isdigit():
        s['pl_count'] = int(event.text); await event.respond(f"✅ حله! {event.text} آهنگ رندوم.", buttons=main_menu_btns(uid)); return
    
    s['search_text'] = event.text; await show_results(event, 0, is_callback=False)

# --- [ موتور جستجو و الگوریتم مشابهات ] ---

def build_query(uid):
    s = user_states[uid]; p = []
    must = [t for t, v in s['tags'].items() if v==1]
    nots = [t for t, v in s['tags'].items() if v==-1]
    
    q = "SELECT msg_id, artist, title"
    
    if s['search_text']:
        # وزن‌دهی هوشمند: اگر عین عبارت بود امتیاز بالا، اگر بخشی از کلمات بود امتیاز کمتر
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
    
    # فیلتر هنرمندان انتخابی
    if s['artists']:
        q += f" AND artist IN ({','.join(['?']*len(s['artists']))})"
        p.extend(list(s['artists']))
        
    # فیلتر متن جستجو (حداقل یکی از کلمات یا کل عبارت پیدا شود)
    if s['search_text']:
        words = s['search_text'].split()
        search_conditions = ["title LIKE ?", "artist LIKE ?"]
        p.extend([f"%{s['search_text']}%", f"%{s['search_text']}%"])
        
        for word in words:
            search_conditions.extend(["title LIKE ?", "artist LIKE ?"])
            p.extend([f"%{word}%", f"%{word}%"])
            
        q += f" AND ({' OR '.join(search_conditions)})"
        
    # فیلتر تگ‌ها
    if must:
        if s['logic'] == 'AND':
            for t in must: q += " AND tags LIKE ?"; p.append(f"%#{t}%")
        else: q += f" AND ({' OR '.join(['tags LIKE ?']*len(must))})"; p.extend([f"%#{t}%" for t in must])
        
    for t in nots: q += " AND tags NOT LIKE ?"; p.append(f"%#{t}%")
    
    q += " ORDER BY score DESC, msg_id DESC"
    return q, p


# --- [ بخش اصلاح شده تابع show_results ] ---

async def show_results(event, page, is_callback=True):
    uid = event.sender_id; s = user_states[uid]; limit = 12; offset = page * limit
    
    # 1. گرفتن نتایج مستقیم از دیتابیس (SQL)
    q, p = build_query(uid)
    async with aiosqlite.connect('music_archive.db') as db:
        async with db.execute(q, p) as c: 
            sql_rows = await c.fetchall()
            # تبدیل به لیست برای قابلیت تغییر
            final_results = list(sql_rows) 

        # 2. اگر کاربر متنی تایپ کرده، مشابهات فازی رو هم اضافه کن
        if s['search_text'] and page == 0:
            async with db.execute("SELECT msg_id, artist, title FROM songs") as c2:
                all_songs = await c2.fetchall()
            
            # ساخت لیست کاندیداها برای مقایسه
            candidates = {f"{r[1]} - {r[2]}": r for r in all_songs}
            
            # پیدا کردن مشابهات با difflib
            matches = difflib.get_close_matches(
                s['search_text'].lower(), 
                [name.lower() for name in candidates.keys()], 
                n=10, 
                cutoff=0.4
            )
            
            # اضافه کردن مشابهات به لیست نهایی (اگر قبلاً در نتایج SQL نبودند)
            existing_ids = {r[0] for r in final_results}
            for match_name_low in matches:
                # پیدا کردن نام اصلی (Case-sensitive) از روی نام lowercase
                real_name = next(name for name in candidates.keys() if name.lower() == match_name_low)
                song_data = candidates[real_name]
                if song_data[0] not in existing_ids:
                    # اضافه کردن به انتهای لیست (با امتیاز 0 چون مشابه هست نه دقیق)
                    final_results.append((song_data[0], song_data[1], song_data[2], 0))

    # 3. اعمال صفحه‌بندی (Pagination) روی لیست ترکیبی
    display_rows = final_results[offset:offset+limit]

    if not display_rows:
        return await event.respond("❌ چیزی پیدا نشد. دوباره امتحان کن!")

    # ساخت دکمه‌ها
    btns = []
    for r in display_rows:
        # کوتاه کردن متن برای دکمه تلگرام (حداکثر 64 بایت)
        label = f"🎵 {r[1]} - {r[2]}"
        if len(label) > 50: label = label[:47] + "..."
        btns.append([Button.inline(label, data=f"get_mu:{r[0]}")])

    # ناوبری (بعدی/قبلی)
    nav = []
    if page > 0: nav.append(Button.inline("⬅️ قبل", data=f"search_p:{page-1}"))
    if len(final_results) > offset + limit: nav.append(Button.inline("بعد ➡️", data=f"search_p:{page+1}"))
    if nav: btns.append(nav)
    
    btns.append([Button.inline("🏠 خانه و ریست", data="clear")])
    
    try:
        msg = f"🔎 نتایج برای: '{s['search_text'] or 'فیلترها'}'"
        if is_callback: await event.edit(msg, buttons=btns)
        else: await event.respond(msg, buttons=btns)
    except: pass


async def create_playlist(event):
    uid = event.sender_id; s = user_states[uid]; q, p = build_query(uid)
    async with aiosqlite.connect('music_archive.db') as db:
        async with db.execute(q + " LIMIT 200", p) as c: songs = await c.fetchall()
    if not songs: return await event.respond("آهنگی با این فیلترها پیدا نشد.")
    sel = random.sample(songs, min(s['pl_count'], len(songs)))
    await event.respond(f"🎲 در حال ارسال {len(sel)} آهنگ برای شما..."); 
    for song in sel:
        try: await bot_client.forward_messages(event.chat_id, song[0], CHANNEL_ID); await asyncio.sleep(0.3)
        except: continue
    s['pl_count'] = None; await event.respond("نوش جان! 🍷", buttons=main_menu_btns(uid))

async def main():
    try:
        async with aiosqlite.connect('music_archive.db') as db:
            await db.execute("CREATE TABLE IF NOT EXISTS songs (msg_id INTEGER PRIMARY KEY, artist TEXT, title TEXT, tags TEXT)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_art ON songs(artist)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tit ON songs(title)")
            await db.commit()
        await user_client.start(); await bot_client.start(bot_token=BOT_TOKEN)
        print("--- Bartender is Online! ---")
        await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())
    except Exception as e:
        print(f"System Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())