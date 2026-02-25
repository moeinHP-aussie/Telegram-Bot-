# 🍷 SongBartender Bot
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-Telethon-0088cc.svg" alt="Telethon">
  <img src="https://img.shields.io/badge/Database-SQLite-lightgrey.svg" alt="Database">
  <img src="https://img.shields.io/badge/Async-aiosqlite-purple.svg" alt="Async DB">
  <img src="https://img.shields.io/badge/Search-Fuzzy%20Matching-yellow.svg" alt="Fuzzy Search">
  <img src="https://img.shields.io/badge/Logic-AND%20%7C%20OR-orange.svg" alt="Logic System">
  <img src="https://img.shields.io/badge/Ranking-Weighted%20Scoring-green.svg" alt="Ranking">
  <img src="https://img.shields.io/badge/Architecture-Event--Driven-red.svg" alt="Architecture">
  <img src="https://img.shields.io/badge/Platform-Telegram%20Bot-26A5E4.svg" alt="Platform">
</p>
A smart Telegram music discovery bot that helps users find songs based on **mood, tags, artists, and fuzzy search queries** — just like a bartender mixing the perfect drink, but for music.

🔗 **Bot:** [https://t.me/songbartenderbot](https://t.me/songbartenderbot)
📢 **Channel (Music Source):** [https://t.me/songbartender](https://t.me/songbartender)

---

## ✨ Overview

**SongBartender** is a Telegram bot built with **Python + Telethon** that allows users to:

* Search songs by **name or artist**
* Filter using **mood/style tags**
* Combine filters using **AND / OR logic**
* Select multiple artists
* Generate **custom playlists**
* Discover music through **fuzzy matching**

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

### 🎭 Tag-Based Filtering

* Users can:

  * ✅ Include tags
  * ❌ Exclude tags
  * 🔄 Reset tags
* Supports moods & genres like:

  * `sad`, `romantic`, `jazz`, `gospel`, `rock`, etc.

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
* Async DB access using `aiosqlite`

---

### 🔄 Database Sync

Admin-only feature:

* Scans Telegram channel messages
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
* Excluded tags

Example:

```sql
WHERE
  artist IN (...)
  AND (title LIKE ... OR artist LIKE ...)
  AND tags LIKE '%#sad%'
  AND tags NOT LIKE '%#happy%'
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
* **Telethon** → Telegram API
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

---

## 🚀 How It Works (Flow)

1. User sends input or selects filters
2. Bot updates user state
3. SQL query is dynamically built
4. Results fetched & ranked
5. Fuzzy matches added (if needed)
6. Results displayed with pagination

---

## 📌 Key Design Decisions

* ✅ SQLite instead of heavy DB → simplicity + speed
* ✅ Hybrid search (SQL + Python) → better accuracy
* ✅ Inline buttons UI → no typing complexity
* ✅ Tag tri-state system (include/exclude/neutral)

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


