# 🍷 SongBartender Bot
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-Telethon-0088cc.svg" alt="Telethon">
  <img src="https://img.shields.io/badge/Database-SQLite-lightgrey.svg" alt="Database">
  <img src="https://img.shields.io/badge/Async-aiosqlite-purple.svg" alt="Async DB">
  <img src="https://img.shields.io/badge/Search-Fuzzy%20Matching-yellow.svg" alt="Fuzzy Search">
  <img src="https://img.shields.io/badge/Logic-AND%20%7C%20OR-orange.svg" alt="Logic System">
  <img src="https://img.shields.io/badge/Architecture-Dual%20Client-red.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/Platform-Telegram%20Bot-26A5E4.svg" alt="Platform">
</p>
A smart Telegram music discovery bot that helps users find songs based on **mood, tags, artists, and fuzzy search queries** — just like a bartender mixing the perfect drink, but for music.

🔗 **Bot:** [https://t.me/songbartenderbot](https://t.me/songbartenderbot)
📢 **Channel (Music Source):** [https://t.me/songbartender](https://t.me/songbartender)

---

## ✨ Overview

**SongBartender** is an advanced Telegram bot built with **Python + Telethon** that allows users to:

* Search songs by **name or artist**
* Filter using **mood/style tags**
* Combine filters using **AND / OR logic**
* Select multiple artists
* Generate **custom playlists**
* Discover music through **fuzzy matching**

Unlike standard bots, it uses a **Dual-Client Architecture**:
1. **Bot Client:** Handles user interactions, UI, and inline buttons.
2. **User Client:** Scans the channel, extracts audio metadata, and syncs the database.

The bot uses a **locally optimized SQLite database** to store and retrieve songs efficiently from a Telegram channel.

---

## 🧠 Core Features

### 🔎 Smart Search Engine

* Supports **free-text search** (song title / artist)
* Uses **weighted scoring system** to rank results
* Combines:

  * Exact matches
  * Partial matches
  * Word-level matches

### 🎭 Tag-Based Filtering & Education System

* Users can:
  * ✅ Include tags
  * 🔄 Reset tags
* Supports moods & genres like:
  * `sad`, `romantic`, `jazz`, `gospel`, `rock`, etc.
* **Interactive Help Mode:** Users can toggle a "Learn Tags" mode to get Persian explanations and examples for what each tag means directly via inline alerts.
* **Tag Counts:** Displays the exact number of songs available for each tag in Persian digits.

---

### ⚙️ Logical Filtering (AND / OR)

Users can dynamically switch between:

* **AND logic** → All selected tags must match
* **OR logic** → At least one tag must match

This is implemented directly at the SQL query level for performance.

---

### 🎤 Artist Selection System

* Browse all artists with pagination
* Select multiple artists simultaneously
* Includes:

  * **Fuzzy artist search**
  * Prioritization of selected artists

---

### 🎲 Playlist Generator

* Users can request a random playlist
* Bot selects songs based on:

  * Current filters
  * Requested playlist size

---

## 🧮 Search Algorithm & Ranking

### 📊 Scoring Mechanism

The bot assigns a **score** to each result:

```sql
CASE WHEN (title LIKE ? OR artist LIKE ?) THEN 10
+ CASE WHEN word match THEN 2 ...
```

#### Key Ideas:

* **Exact match → +10 score**
* **Partial word matches → +2 per word**
* Results sorted by:

  ```sql
  ORDER BY score DESC, msg_id DESC
  ```

👉 This ensures:

* Most relevant results appear first
* Newer songs are prioritized when scores are equal

---

### 🤖 Fuzzy Matching (difflib)

When user input is not exact:

* Uses:

  ```python
  difflib.get_close_matches()
  ```
* Finds similar strings from:

  ```
  "Artist - Title"
  ```
* Adds them to results if not already found

#### Example:

Input:

```
adele hello
```

Can match:

```
Adele - Hello
Adel - Helo
```

---

## 🗄️ Database Design

### 📁 SQLite Schema

```sql
songs (
    msg_id INTEGER PRIMARY KEY,
    artist TEXT,
    title TEXT,
    tags TEXT
)
```

---

### ⚡ Optimization Techniques

* **Primary Key (msg_id)** → fast lookup
* **LIKE queries with indexed text fields**
* Minimal joins → single-table design
* Async DB access using `aiosqlite` (with timeout to prevent `database is locked` errors)

---

### 🔄 Database Sync

Admin-only feature:

* Scans Telegram channel messages via **User Client**
* Extracts:

  * Audio metadata (artist/title)
  * Hashtags from caption
* Uses:

  ```python
  INSERT OR REPLACE
  ```

👉 Prevents duplicates & keeps DB updated

---

## 🧩 Query Builder Logic

Dynamic SQL generation based on user state:

### Includes:

* Text search conditions
* Artist filters
* Tag filters:

  * AND / OR logic

Example:

```sql
WHERE
  artist IN (...)
  AND (title LIKE ... OR artist LIKE ...)
  AND tags LIKE '%#sad%'
```

---

## 🧠 State Management

Each user has a session state:

```python
{
  tags: {},
  search_text: str,
  artists: set(),
  pl_count: int,
  logic: 'AND' | 'OR',
  mode: str
}
```

👉 Enables:

* Personalized experience
* Multi-step interactions
* Stateless Telegram handling workaround

---

## 🔐 Access Control

* Users **must join the channel** before using the bot
* Membership is verified using:

  ```python
  get_permissions()
  ```

---

## 🧱 Tech Stack

* **Python 3**
* **Telethon** → Telegram API (Dual client setup)
* **aiosqlite** → async DB
* **SQLite** → storage
* **difflib** → fuzzy matching
* **dotenv** → environment config

---

## 🧪 Performance Considerations

* Async architecture → non-blocking operations
* Pagination → avoids large payloads
* Hybrid search:

  * SQL (fast filtering)
  * Python (fuzzy refinement)
* **Absolute Paths:** Used `os.path.join(BASE_DIR, ...)` for database and session files to prevent path resolution issues in Cron Jobs.
* **Async Loop Management:** Used `asyncio.get_event_loop()` and `asyncio.gather()` to run both Bot and User clients concurrently without `attached to a different loop` errors.

---

## 🚀 Deployment Guide

### 1. Prerequisites
* Python 3.9+
* A Telegram `API_ID` and `API_HASH` (from my.telegram.org)
* A Bot Token (from @BotFather)
* Channel ID (with negative sign, e.g., `-1001234567890`)

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
CHANNEL_ID=-1001234567890
```

### 3. Generating User Session (Crucial)
Because the bot requires a User Client to read channel messages, you must generate a `user_session.session` file locally:
1. Install Telethon on your local machine: `pip install telethon`
2. Run a simple script to login with your phone number.
3. Once `user_session.session` is generated, upload it to your server alongside `core.py`.

### 4. Running on Shared Hosting (cPanel / Cron Job)
Shared hosting environments kill long-running processes. To keep the bot alive, use a Cron Job with `flock` to prevent multiple instances:

**Cron Command (Every Minute):**
```bash
cd /home/username/moein_bot && flock -n /tmp/moein_bot.lock /usr/bin/python3 -u core.py >> bot.log 2>&1
```

### 5. Running on VPS / Dedicated Server
For standard servers, simply run:
```bash
python3 core.py
```
*(Or use process managers like `PM2` or `Systemd` for 24/7 uptime).*

---

## 📌 Key Design Decisions

* ✅ SQLite instead of heavy DB → simplicity + speed
* ✅ Hybrid search (SQL + Python) → better accuracy
* ✅ Inline buttons UI → no typing complexity
* ✅ Dual Client architecture → safe channel scraping + responsive bot UI

---

## 💡 Future Improvements

* Add **full-text search (FTS5)** for better performance
* Improve ranking using **TF-IDF or embeddings**
* Cache frequent queries
* Add user-based recommendation system

---

## ❤️ Final Note

If you enjoy discovering music in a smarter way, give it a try:

👉 [https://t.me/songbartenderbot](https://t.me/songbartenderbot)
🎧 [https://t.me/songbartender](https://t.me/songbartender)
