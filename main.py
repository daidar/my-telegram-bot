import asyncio, random, sqlite3, json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ====================== НАСТРОЙКИ ======================
BOT_TOKEN = "8918809137:AAEPzaMMiBwL8rHSGkHJsiIfwAmnKjF56ds"
OWNER_ID = 0  # ваш Telegram ID (узнать у @userinfobot)
START_BALANCE = 1000
DAILY_COOLDOWN_HOURS = 24
XP_PER_CASE = 10
COLLECT_COOLDOWN_HOURS = 1
RP_STEP = 100
RP_PER_CASE = 1
RP_PER_LEGENDARY_SOLD = 5
DUEL_COOLDOWN_SEC = 300
MARKET_COMMISSION = 0.05
MARKET_LOT_HOURS = 24
MIN_BET = 10

CASES = {
    "basic":   {"name": "Обычный", "emoji": "📦", "price": 100,
                "weights": {"common": 60, "rare": 25, "epic": 12, "legendary": 3}},
    "premium": {"name": "Премиум", "emoji": "🎁", "price": 500,
                "weights": {"common": 25, "rare": 40, "epic": 25, "legendary": 10}},
    "vip":     {"name": "VIP",     "emoji": "💎", "price": 2000,
                "weights": {"common": 0,  "rare": 30, "epic": 45, "legendary": 25}},
}

RARITIES = {
    "common":    {"name": "Обычная",     "emoji": "⚪️", "sell": 30,   "passive": 5},
    "rare":      {"name": "Редкая",      "emoji": "🔵", "sell": 120,  "passive": 20},
    "epic":      {"name": "Эпическая",   "emoji": "🟣", "sell": 400,  "passive": 80},
    "legendary": {"name": "Легендарная", "emoji": "🟡", "sell": 1500, "passive": 300},
}

CARDS = {
    "common": [
        {"name": "mumble", "emoji": "🗣️", "desc": "Трэп и клауд на стыке."},
        {"name": "Размаха", "emoji": "💥", "desc": "Девушка в новом олдскуле."},
        {"name": "Tuborosho", "emoji": "🥁", "desc": "Саундклауд с пацанским вайбом."},
        {"name": "mapt0v", "emoji": "🗺️", "desc": "Меланхоличный рэп."},
        {"name": "dope17", "emoji": "💊", "desc": "Воронежский фрешмен."},
        {"name": "KRISTIEE", "emoji": "✨", "desc": "17-летний фрешмен из Москвы."},
        {"name": "Locked23", "emoji": "🔒", "desc": "Автор хита «Татухи»."},
        {"name": "юпи", "emoji": "🎸", "desc": "Поп-панк и гранж."},
        {"name": "euro91", "emoji": "🚗", "desc": "Участник объединения Bouquet."},
        {"name": "fleurnothappy", "emoji": "🥀", "desc": "Меланхоличная новая волна."},
    ],
    "rare": [
        {"name": "Тёмный Принц", "emoji": "🦇", "desc": "Самый загадочный саундклауд-фрешмен."},
        {"name": "whitek3d", "emoji": "💎", "desc": "15+ млн стримов."},
        {"name": "Fortuna 812", "emoji": "🏴", "desc": "Автор хита ParisLove."},
        {"name": "madk1d", "emoji": "🚀", "desc": "Один из лидеров новой волны."},
        {"name": "Урал Гайсин", "emoji": "🎹", "desc": "Продюсер из Уфы."},
        {"name": "паранойя", "emoji": "🌀", "desc": "Мультижанровый исполнитель."},
        {"name": "Anonymous Ember", "emoji": "👤", "desc": "Тайный участник Russia Be Mad."},
        {"name": "tewiq", "emoji": "🎯", "desc": "Автор хита распять."},
        {"name": "королевский XVII", "emoji": "⚔️", "desc": "Мрачный трэп из Волгограда."},
        {"name": "KUDOKUSHI", "emoji": "🏯", "desc": "Легенда русского саундклауда."},
    ],
    "epic": [
        {"name": "CODE80", "emoji": "👑", "desc": "Главный герой касты."},
        {"name": "Sagath", "emoji": "⛓️", "desc": "Король хоррор-трэпа."},
        {"name": "Friendly Thug 52 NGG", "emoji": "🃏", "desc": "Топ новой волны."},
        {"name": "ICEGERGERT", "emoji": "❄️", "desc": "Прорыв года."},
        {"name": "Словетский", "emoji": "📜", "desc": "Формирует новое звучание."},
        {"name": "Aarne", "emoji": "🎛️", "desc": "Продюсер главных хитов."},
        {"name": "LILCAK3", "emoji": "🌶️", "desc": "Локальная звезда."},
        {"name": "unki", "emoji": "🌪️", "desc": "Новейшая волна андерграунда."},
    ],
    "legendary": [
        {"name": "Miyagi", "emoji": "🌴", "desc": "I Got Love — трек десятилетия."},
        {"name": "Баста", "emoji": "🎩", "desc": "Легенда сцены."},
        {"name": "Oxxxymiron", "emoji": "🏛️", "desc": "Горгород."},
        {"name": "Скриптонит", "emoji": "🦅", "desc": "Дом с нормальными явлениями."},
        {"name": "Хаски", "emoji": "🐺", "desc": "Тёмный рэп."},
        {"name": "Noize MC", "emoji": "🎸", "desc": "Рэп с гитарой."},
        {"name": "FACE", "emoji": "🥀", "desc": "Грустный трэп."},
        {"name": "Элджей", "emoji": "🎧", "desc": "Пионер российского трэпа."},
    ],
}

COLLECTIONS = {
    "common":    {"name": "Новички",     "reward": 1000},
    "rare":      {"name": "Андерграунд", "reward": 3000},
    "epic":      {"name": "Элита",       "reward": 10000},
    "legendary": {"name": "Легенды",     "reward": 50000},
}

ACHIEVEMENTS = [
    {"id": "first_case",      "text": "Открой первый кейс",     "reward": 100,  "counter": "cases"},
    {"id": "first_legendary", "text": "Первая легендарка",      "reward": 500,  "counter": "legendary"},
    {"id": "cases_10",        "text": "Открой 10 кейсов",       "reward": 300,  "counter": "cases"},
    {"id": "cases_100",       "text": "Открой 100 кейсов",      "reward": 2000, "counter": "cases"},
    {"id": "sell_10",         "text": "Продай 10 карт",         "reward": 200,  "counter": "sold"},
    {"id": "sell_100",        "text": "Продай 100 карт",        "reward": 2000, "counter": "sold"},
    {"id": "level_10",        "text": "Достигни 10 уровня",     "reward": 500,  "counter": "level"},
    {"id": "level_25",        "text": "Достигни 25 уровня",     "reward": 2000, "counter": "level"},
    {"id": "rp_500",          "text": "Набрать 500 репутации",  "reward": 1500, "counter": "reputation"},
    {"id": "duel_win_10",     "text": "Выиграй 10 дуэлей",      "reward": 1000, "counter": "duel_wins"},
    {"id": "market_sell_5",   "text": "Продай 5 карт на рынке", "reward": 500,  "counter": "market_sold"},
]
ACHIEVEMENT_THRESHOLDS = {
    "first_case": 1, "first_legendary": 1, "cases_10": 10, "cases_100": 100,
    "sell_10": 10, "sell_100": 100, "level_10": 10, "level_25": 25, "rp_500": 500,
    "duel_win_10": 10, "market_sell_5": 5,
}

RANKS = [
    (0,    "🌱 Новичок"),
    (100,  "🎤 Андерграунд"),
    (500,  "🔥 Легенда саундклауда"),
    (2000, "👑 Икона сцены"),
]

def rank_for(rp):
    r = RANKS[0][1]
    for t, n in RANKS:
        if rp >= t: r = n
    return r

def xp_needed(level):
    return int(100 * (1.15 ** (level - 1)))

# ====================== БАЗА ======================
conn = sqlite3.connect("bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, username TEXT,
    balance INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
    last_daily TEXT, daily_streak INTEGER DEFAULT 0,
    quest_data TEXT DEFAULT '{}', quest_date TEXT,
    boosters TEXT DEFAULT '{}',
    counters TEXT DEFAULT '{}',
    achievements TEXT DEFAULT '{}',
    reputation INTEGER DEFAULT 0,
    last_collect TEXT,
    last_duel TEXT
);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    card_name TEXT, rarity TEXT, obtained_at TEXT
);
CREATE TABLE IF NOT EXISTS market (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER, seller_name TEXT,
    card_name TEXT, rarity TEXT, price INTEGER,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS promo (
    code TEXT PRIMARY KEY, reward INTEGER,
    max_uses INTEGER DEFAULT 1, uses INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS promo_used (
    user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code)
);
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, card_name TEXT, rarity TEXT,
    source TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS events (
    name TEXT PRIMARY KEY, expires TEXT
);
CREATE TABLE IF NOT EXISTS bans (
    user_id INTEGER PRIMARY KEY, until TEXT
);
""")
for col, typ in [("counters", "TEXT DEFAULT '{}'"), ("achievements", "TEXT DEFAULT '{}'"),
                 ("reputation", "INTEGER DEFAULT 0"), ("last_collect", "TEXT"),
                 ("last_duel", "TEXT")]:
    try:
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    except sqlite3.OperationalError:
        pass
conn.commit()

# ====================== ПОЛЬЗОВАТЕЛИ ======================
def create_user(uid, un=""):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?,?,?)",
                (uid, un or "", START_BALANCE))
    conn.commit()

def get_user(uid, un=""):
    create_user(uid, un)
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def upd(uid, **kw):
    keys = ", ".join(f"{k}=?" for k in kw)
    cur.execute(f"UPDATE users SET {keys} WHERE user_id=?", (*kw.values(), uid))
    conn.commit()

def add_balance(uid, amt):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
    conn.commit()

def add_card(uid, name, rar, source="unknown"):
    cur.execute("INSERT INTO inventory (user_id,card_name,rarity,obtained_at) VALUES (?,?,?,?)",
                (uid, name, rar, datetime.now().isoformat()))
    cur.execute("INSERT INTO history (user_id,card_name,rarity,source,created_at) VALUES (?,?,?,?,?)",
                (uid, name, rar, source, datetime.now().isoformat()))
    conn.commit()

def get_inv(uid):
    cur.execute("SELECT card_name,rarity FROM inventory WHERE user_id=? ORDER BY id DESC", (uid,))
    return cur.fetchall()

def del_card(uid, name):
    cur.execute("DELETE FROM inventory WHERE id=(SELECT id FROM inventory WHERE user_id=? AND card_name=? LIMIT 1)",
                (uid, name))
    conn.commit()

def get_rep(uid):
    return get_user(uid)["reputation"] or 0

def add_rep(uid, amount):
    amount *= event_mult("x2_rep")
    cur.execute("UPDATE users SET reputation=reputation+? WHERE user_id=?", (amount, uid))
    conn.commit()

def rep_sell_multiplier(rp): return 1 + 0.02 * (rp // RP_STEP)
def rep_passive_multiplier(rp): return 1 + 0.05 * (rp // RP_STEP)

def get_counters(uid): return json.loads(get_user(uid)["counters"] or "{}")
def get_achievements(uid): return json.loads(get_user(uid)["achievements"] or "{}")

async def check_achievements(uid, message=None):
    c = get_counters(uid)
    ach = get_achievements(uid)
    unlocked = []
    for a in ACHIEVEMENTS:
        if ach.get(a["id"]): continue
        val = c.get(a["counter"], 0)
        if a["counter"] == "reputation":
            val = get_rep(uid)
        if val >= ACHIEVEMENT_THRESHOLDS[a["id"]]:
            ach[a["id"]] = True
            add_balance(uid, a["reward"])
            unlocked.append(a)
    if unlocked:
        upd(uid, achievements=json.dumps(ach))
        if message:
            for a in unlocked:
                try:
                    await message.answer(f"🏅 Достижение! {a['text']} +{a['reward']}💰", parse_mode="HTML")
                except: pass

async def bump_counter(uid, key, amount=1, message=None):
    c = get_counters(uid)
    c[key] = c.get(key, 0) + amount
    upd(uid, counters=json.dumps(c))
    await check_achievements(uid, message)

async def give_xp(uid, amount, message=None):
    amount *= event_mult("x2_xp")
    u = get_user(uid)
    new_xp = u["xp"] + amount
    new_lvl = u["level"]
    leveled = False
    while new_xp >= xp_needed(new_lvl):
        new_xp -= xp_needed(new_lvl); new_lvl += 1; leveled = True
    upd(uid, xp=new_xp, level=new_lvl)
    if leveled:
        if message:
            try: await message.answer(f"🎉 Уровень {new_lvl}!", parse_mode="HTML")
            except: pass
        c = get_counters(uid); c["level"] = new_lvl
        upd(uid, counters=json.dumps(c))
        await check_achievements(uid, message)

# ====================== КВЕСТЫ ======================
QUEST_TEMPLATES = [
    {"id": "case3", "text": "Открой 3 кейса", "goal": 3, "reward": 200, "type": "case"},
    {"id": "sell2", "text": "Продай 2 карты", "goal": 2, "reward": 100, "type": "sell"},
    {"id": "case5", "text": "Открой 5 кейсов", "goal": 5, "reward": 400, "type": "case"},
]

def get_quests(uid):
    u = get_user(uid)
    today = datetime.now().date().isoformat()
    if u["quest_date"] != today:
        data = {q["id"]: 0 for q in QUEST_TEMPLATES}
        upd(uid, quest_date=today, quest_data=json.dumps(data))
        return data
    return json.loads(u["quest_data"] or "{}")

def progress_quest(uid, qtype, amount=1):
    data = get_quests(uid)
    for q in QUEST_TEMPLATES:
        if q["type"] == qtype and data.get(q["id"], 0) < q["goal"]:
            data[q["id"]] = min(data[q["id"]] + amount, q["goal"])
    upd(uid, quest_data=json.dumps(data))

def claim_quests(uid):
    data = get_quests(uid)
    total = 0
    for q in QUEST_TEMPLATES:
        if data.get(q["id"], 0) >= q["goal"]:
            total += q["reward"]; data[q["id"]] = 0
    if total > 0:
        add_balance(uid, total); upd(uid, quest_data=json.dumps(data))
    return total

# ====================== БУСТЕРЫ / ПАССИВ ======================
def get_boosters(uid): return json.loads(get_user(uid)["boosters"] or "{}")
def set_boosters(uid, d): upd(uid, boosters=json.dumps(d))

def calc_passive_rate(uid):
    inv = get_inv(uid)
    base = sum(RARITIES[r["rarity"]]["passive"] for r in inv)
    return int(base * rep_passive_multiplier(get_rep(uid)))

# ====================== ИВЕНТЫ ======================
def set_event(name, hours):
    expires = (datetime.now() + timedelta(hours=hours)).isoformat()
    cur.execute("INSERT OR REPLACE INTO events (name, expires) VALUES (?,?)", (name, expires))
    conn.commit()

def event_mult(name):
    cur.execute("SELECT expires FROM events WHERE name=?", (name,))
    row = cur.fetchone()
    if not row: return 1
    try:
        if datetime.fromisoformat(row["expires"]) > datetime.now():
            return 2
    except: pass
    return 1

def active_events():
    cur.execute("SELECT name, expires FROM events WHERE expires > ?", (datetime.now().isoformat(),))
    return cur.fetchall()

# ====================== РЫНОК ======================
def clean_market():
    now = datetime.now()
    cur.execute("SELECT * FROM market")
    rows = cur.fetchall()
    changed = False
    for r in rows:
        try:
            if (now - datetime.fromisoformat(r["created_at"])).total_seconds() > MARKET_LOT_HOURS * 3600:
                add_card(r["seller_id"], r["card_name"], r["rarity"], source="market_return")
                cur.execute("DELETE FROM market WHERE id=?", (r["id"],))
                changed = True
        except: pass
    if changed: conn.commit()

def add_lot(uid, name, price):
    rar, card = find_card(name)
    if not card: return False, "Карта не найдена"
    inv = [r for r in get_inv(uid) if r["card_name"] == name]
    if not inv: return False, "У тебя нет такой карты"
    del_card(uid, name)
    u = get_user(uid)
    cur.execute("INSERT INTO market (seller_id, seller_name, card_name, rarity, price, created_at) VALUES (?,?,?,?,?,?)",
                (uid, u["username"] or f"id{uid}", name, rar, price, datetime.now().isoformat()))
    conn.commit()
    return True, "OK"

def get_lots(limit=10, offset=0):
    cur.execute("SELECT * FROM market ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
    return cur.fetchall()

def get_my_lots(uid):
    cur.execute("SELECT * FROM market WHERE seller_id=? ORDER BY id DESC", (uid,))
    return cur.fetchall()

def buy_lot(uid, lot_id):
    cur.execute("SELECT * FROM market WHERE id=?", (lot_id,))
    lot = cur.fetchone()
    if not lot: return False, "Лот не найден"
    if lot["seller_id"] == uid: return False, "Нельзя купить свой лот"
    u = get_user(uid)
    if u["balance"] < lot["price"]: return False, "Недостаточно монет"
    add_balance(uid, -lot["price"])
    seller_cut = int(lot["price"] * (1 - MARKET_COMMISSION))
    add_balance(lot["seller_id"], seller_cut)
    add_card(uid, lot["card_name"], lot["rarity"], source="market_buy")
    cur.execute("DELETE FROM market WHERE id=?", (lot_id,))
    conn.commit()
    c = get_counters(lot["seller_id"])
    c["market_sold"] = c.get("market_sold", 0) + 1
    upd(lot["seller_id"], counters=json.dumps(c))
    return True, lot["card_name"]

# ====================== ПРОМОКОДЫ ======================
def add_promo(code, reward, uses):
    try:
        cur.execute("INSERT INTO promo (code, reward, max_uses) VALUES (?,?,?)", (code.upper(), reward, uses))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def use_promo(uid, code):
    code = code.upper()
    cur.execute("SELECT * FROM promo WHERE code=?", (code,))
    p = cur.fetchone()
    if not p: return False, "Промокод не найден"
    if p["uses"] >= p["max_uses"]: return False, "Промокод закончился"
    cur.execute("SELECT 1 FROM promo_used WHERE user_id=? AND code=?", (uid, code))
    if cur.fetchone(): return False, "Ты уже использовал этот промокод"
    cur.execute("UPDATE promo SET uses=uses+1 WHERE code=?", (code,))
    cur.execute("INSERT INTO promo_used (user_id, code) VALUES (?,?)", (uid, code))
    conn.commit()
    add_balance(uid, p["reward"])
    return True, p["reward"]

# ====================== КОЛЛЕКЦИИ ======================
def collection_status(uid, rar):
    inv = get_inv(uid)
    owned = set(r["card_name"] for r in inv if r["rarity"] == rar)
    needed = set(c["name"] for c in CARDS[rar])
    return len(owned & needed), len(needed)

def claim_collection(uid, rar):
    owned, total = collection_status(uid, rar)
    if owned < total: return 0
    ach = get_achievements(uid)
    key = f"coll_{rar}"
    if ach.get(key): return 0
    ach[key] = True
    upd(uid, achievements=json.dumps(ach))
    reward = COLLECTIONS[rar]["reward"]
    add_balance(uid, reward)
    return reward

# ====================== ИСТОРИЯ ======================
def get_history(uid, limit=10):
    cur.execute("SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))
    return cur.fetchall()

# ====================== ХЕЛПЕРЫ ======================
def roll_card(case_key):
    w = CASES[case_key]["weights"]
    rar = random.choices(list(w.keys()), weights=list(w.values()), k=1)[0]
    return rar, random.choice(CARDS[rar])

def fmt_time(td):
    t = int(td.total_seconds())
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{h}ч {m}м {s}с"

def sell_price(uid, rar):
    return int(RARITIES[rar]["sell"] * rep_sell_multiplier(get_rep(uid)))

def find_card(name):
    for rar, cards in CARDS.items():
        for c in cards:
            if c["name"] == name:
                return rar, c
    return None, None

# ====================== АДМИН-ПАНЕЛЬ ======================
pending = {}

def is_admin(uid):
    return bool(OWNER_ID) and uid == OWNER_ID

def is_banned(uid):
    cur.execute("SELECT until FROM bans WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row: return False
    try:
        if datetime.fromisoformat(row["until"]) > datetime.now():
            return True
    except: pass
    cur.execute("DELETE FROM bans WHERE user_id=?", (uid,))
    conn.commit()
    return False

def ban_user(uid, hours):
    until = (datetime.now() + timedelta(hours=hours)).isoformat()
    cur.execute("INSERT OR REPLACE INTO bans (user_id, until) VALUES (?,?)", (uid, until))
    conn.commit()

def unban_user(uid):
    cur.execute("DELETE FROM bans WHERE user_id=?", (uid,))
    conn.commit()

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика бота", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_bc")],
        [InlineKeyboardButton(text="🎁 Выдать монеты", callback_data="adm_give_coins"),
         InlineKeyboardButton(text="🎴 Выдать карту", callback_data="adm_give_card")],
        [InlineKeyboardButton(text="📜 Создать промокод", callback_data="adm_promo")],
        [InlineKeyboardButton(text="🎬 Ивент", callback_data="adm_event")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data="adm_ban"),
         InlineKeyboardButton(text="✅ Разбан", callback_data="adm_unban")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
    ])

# ====================== REPLY-КЛАВИАТУРА ======================
def reply_main_menu(uid=None):
    rows = [
        [KeyboardButton(text="📦 Кейсы"), KeyboardButton(text="🎒 Коллекция")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="💱 Продать")],
        [KeyboardButton(text="💵 Собрать"), KeyboardButton(text="📅 Бонус")],
        [KeyboardButton(text="🎮 Игры"), KeyboardButton(text="🏪 Рынок")],
        [KeyboardButton(text="📚 Коллекции"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="🎖️ Репутация"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📋 Квесты"), KeyboardButton(text="🏅 Достижения")],
        [KeyboardButton(text="⚒️ Крафт"), KeyboardButton(text="❓ Помощь")],
    ]
    if uid and is_admin(uid):
        rows.append([KeyboardButton(text="👑 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)

# ====================== INLINE-МЕНЮ ======================
def main_menu(uid=None):
    rows = [
        [InlineKeyboardButton(text="📦 Кейсы", callback_data="cases")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="🎒 Коллекция", callback_data="inv")],
        [InlineKeyboardButton(text="💱 Продать", callback_data="sell"),
         InlineKeyboardButton(text="💵 Собрать", callback_data="collect")],
        [InlineKeyboardButton(text="🎮 Игры", callback_data="games"),
         InlineKeyboardButton(text="🏪 Рынок", callback_data="market")],
        [InlineKeyboardButton(text="📚 Коллекции", callback_data="collections"),
         InlineKeyboardButton(text="📅 Бонус", callback_data="daily")],
        [InlineKeyboardButton(text="📋 Квесты", callback_data="quests"),
         InlineKeyboardButton(text="🏅 Достижения", callback_data="ach")],
        [InlineKeyboardButton(text="🎖️ Репутация", callback_data="rep"),
         InlineKeyboardButton(text="⚒️ Крафт", callback_data="craft")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
    ]
    if uid and is_admin(uid):
        rows.append([InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def cases_menu():
    btns = [[InlineKeyboardButton(text=f"{c['emoji']} {c['name']} — {c['price']}💰", callback_data=f"case:{k}")]
            for k, c in CASES.items()]
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def sell_menu(uid):
    inv = get_inv(uid)
    if not inv: return None
    seen = {}
    for row in inv:
        key = (row["card_name"], row["rarity"])
        seen[key] = seen.get(key, 0) + 1
    order = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
    btns = []
    for (name, rar), cnt in sorted(seen.items(), key=lambda x: order[x[0][1]]):
        price = sell_price(uid, rar)
        btns.append([InlineKeyboardButton(text=f"{RARITIES[rar]['emoji']} {name} ×{cnt} — {price}💰",
                                          callback_data=f"sell:{name}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def collection_menu(uid):
    inv = get_inv(uid)
    if not inv: return None
    grouped = {}
    for r in inv:
        key = (r["card_name"], r["rarity"])
        grouped[key] = grouped.get(key, 0) + 1
    order = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
    btns = []
    for (name, rar), cnt in sorted(grouped.items(), key=lambda x: order[x[0][1]]):
        btns.append([InlineKeyboardButton(text=f"{RARITIES[rar]['emoji']} {name} ×{cnt}",
                                          callback_data=f"cardinfo:{name}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return Inline forKeyboardMarkup(inline_keyboard= (btns)

defname craft_menu(uid):
    inv = get_inv(uid)
    btns = []
    for rar_key in ["common", "rare", "epic"]:
        available = sum(1 for row in inv if row["rarity"] == rar_key)
        if available >= 3:
            nxt = {"common": "rare", "rare": "epic", "epic": "legendary"}[rar_key]
            btns.append([InlineKeyboardButton(
                text=f"3× {RARITIES[rar_key]['name']} → 1× {RARITIES[nxt]['name']}",
                callback_data=f"craft:{rar_key}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns) if len(btns) > 1 else None

def games_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Дуэль — /duel", callback_data="help_duel")],
        [InlineKeyboardButton(text="🎰 Рулетка — /roulette", callback_data="help_roulette")],
        [InlineKeyboardButton(text="🎲 Кости — /dice", callback_data="help_dice")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
    ])

def market_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Витрина", callback_data="market_browse")],
        [InlineKeyboardButton(text="📤 Мои лоты", callback_data="market_my")],
        [InlineKeyboardButton(text="❓ Как продавать", callback_data="help_market")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
    ])

def market_browse_menu(lots):
    btns = []
    for lot in lots:
        emoji = RARITIES[lot["rarity"]]["emoji"]
        btns.append([InlineKeyboardButton(
            text=f"{emoji} {lot['card_name']} — {lot['price']}💰 (от {lot['seller_name']})",
            callback_data=f"buy_lot:{lot['id']}")])
    btns.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="market_browse")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="market")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def collections_menu(uid):
    btns = []
    for rar, info in COLLECTIONS.items():
        owned, total = collection_status(uid, rar)
        emoji = RARITIES[rar]["emoji"]
        ach = get_achievements(uid)
        claimed = "✅" if ach.get(f"coll_{rar}") else ""
        btns.append([InlineKeyboardButton(
            text=f"{emoji} {info['name']} — {owned}/{total} {claimed}",
            callback_data=f"coll_show:{rar}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

# ====================== БОТ ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---- Команды ----
@dp.message(Command("start"))
async def cmd_start(m: Message):
    if is_banned(m.from_user.id):
        await m.answer("🚫 Ты забанен в этом боте."); return
    u = get_user(m.from_user.id, m.from_user.username)
    ev = ""
    for e in active_events():
        ev += f"\n🔥 Ивент: {e['name']}"
    await m.answer(
        f"🎴 Добро пожаловать!\n\n"
        f"💰 Баланс: {u['balance']}\n"
        f"⭐ Уровень: {u['level']} ({u['xp']}/{xp_needed(u['level'])} XP)\n"
        f"🎖️ Репутация: {u['reputation']} — {rank_for(u['reputation'])}{ev}\n\n"
        f"👇 Используй кнопки внизу экрана",
        reply_markup=reply_main_menu(m.from_user.id), parse_mode="HTML")

@dp.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Главное меню 👇", reply_markup=reply_main_menu(m.from_user.id))

@dp.message(Command("top"))
async def cmd_top(m: Message): await show_top(m)

@dp.message(Command("quests"))
async def cmd_quests(m: Message): await show_quests(m, m.from_user.id)

@dp.message(Command("claim"))
async def cmd_claim(m: Message):
    t = claim_quests(m.from_user.id)
    await m.answer(f"🎁 +{t}💰" if t else "Нет выполненных квестов")

@dp.message(Command("sell"))
async def cmd_sell(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    menu = sell_menu(m.from_user.id)
    if not menu:
        await m.answer("🎒 Нечего продавать."); return
    await m.answer("💱 Выбери карту:", reply_markup=menu)

@dp.message(Command("collect"))
async def cmd_collect(m: Message): await do_collect(m.from_user.id, m)

@dp.message(Command("rep"))
async def cmd_rep(m: Message): await show_rep(m.from_user.id, m)

@dp.message(Command("stats"))
async def cmd_stats(m: Message): await show_stats(m.from_user.id, m)

@dp.message(Command("history"))
async def cmd_history(m: Message): await show_history(m.from_user.id, m)

@@dp.message(Command("find"))
async def cmd_find(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Использование: /find имя")
        return
    q = parts[1].lower()
    inv = get_inv(uid)
    found = []
    for r in inv:
        if q in r["card_name"].lower():
            found.append(r)
    if not found:
        await m.answer("Не найдено")
        return
    grouped = {}
    for r in found:
        key = (r["card_name"], r["rarity"])
        grouped[key] = grouped.get(key, 0) + 1
    lines = []
    lines.append("Найдено:")
    for key, cnt in grouped.items():
        name = key[0]
        rar = key[1]
        e = RARITIES[rar]["emoji"]
        lines.append(e + " " + name + " x" + str(cnt))
    await m.answer("\n".join(lines))

@dp.message(Command("cancel"))
async def cmd_cancel(m: Message):
    pending.pop(m.from_user.id, None)
    await m.answer("Отменено")

@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("👑 Только для владельца"); return
    await m.answer("👑 <b>Админ-панель</b>", reply_markup=admin_menu(), parse_mode="HTML")

@dp.message(Command("duel"))
async def cmd_duel(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid):
        return
    if not m.reply_to_message:
        await m.answer("⚔️ Ответь на сообщение игрока командой /duel 100"); return
    opp = m.reply_to_message.from_user
    if opp.id == uid or opp.is_bot:
        await m.answer("Нельзя дуэлить себя или бота"); return
    args = m.text.split()[1:]
    if not args or not args[0].isdigit():
        await m.answer("Использование: /duel 100 (в ответ на сообщение)"); return
    bet = int(args[0])
    if bet < MIN_BET:
        await m.answer(f"Минимум {MIN_BET}💰"); return
    u = get_user(uid); o = get_user(opp.id, opp.username)
    if u["balance"] < bet:
        await m.answer(f"У тебя нет {bet}💰"); return
    if o["balance"] < bet:
        await m.answer(f"У соперника нет {bet}💰"); return
    if u["last_duel"]:
        last = datetime.fromisoformat(u["last_duel"])
        d = (datetime.now() - last).total_seconds()
        if d < DUEL_COOLDOWN_SEC:
            await m.answer(f"⏳ Кулдаун: {int(DUEL_COOLDOWN_SEC - d)}с"); return
    add_balance(uid, -bet); add_balance(opp.id, -bet)
    rar1, c1 = roll_card("basic"); rar2, c2 = roll_card("basic")
    order = {"common": 0, "rare": 1, "epic": 2, "legendary": 3}
    if order[rar1] > order[rar2] or (order[rar1] == order[rar2] and RARITIES[rar1]["sell"] >= RARITIES[rar2]["sell"]):
        winner, wname = uid, m.from_user.first_name
    else:
        winner, wname = opp.id, opp.first_name
    bank = bet * 2
    add_balance(winner, bank)
    upd(uid, last_duel=datetime.now().isoformat())
    if winner == uid:
        await bump_counter(uid, "duel_wins", 1, m)
    await m.answer(
        f"⚔️ <b>Дуэль!</b> Банк: {bank}💰\n\n"
        f"🎴 {m.from_user.first_name}: {RARITIES[rar1]['emoji']} {c1['name']}\n"
        f"🎴 {opp.first_name}: {RARITIES[rar2]['emoji']} {c2['name']}\n\n"
        f"🏆 Победил: <b>{wname}</b> (+{bank}💰)", parse_mode="HTML")

@dp.message(Command("roulette"))
async def cmd_roulette(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid): return
    args = m.text.split()[1:]
    if len(args) < 2 or not args[0].isdigit() or args[1].lower() not in ("red", "black", "green"):
        await m.answer("🎰 /roulette 100 red|black|green"); return
    bet = int(args[0]); color = args[1].lower()
    if bet < MIN_BET:
        await m.answer(f"Минимум {MIN_BET}💰"); return
    u = get_user(uid)
    if u["balance"] < bet:
        await m.answer(f"Нет {bet}💰"); return
    add_balance(uid, -bet)
    roll = random.choices(["red", "black", "green"], weights=[47, 47, 6], k=1)[0]
    if roll == color:
        mult = 2 if color in ("red", "black") else 14
        win = bet * mult
        add_balance(uid, win)
        await m.answer(f"🎰 Выпало: <b>{roll}</b>\n🎉 Победа! +{win}💰 (x{mult})", parse_mode="HTML")
    else:
        await m.answer(f"🎰 Выпало: <b>{roll}</b>\n💀 Проигрыш -{bet}💰", parse_mode="HTML")

@dp.message(Command("dice"))
async def cmd_dice(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid): return
    args = m.text.split()[1:]
    if not args or not args[0].isdigit():
        await m.answer("🎲 /dice 100"); return
    bet = int(args[0])
    if bet < MIN_BET:
        await m.answer(f"Минимум {MIN_BET}💰"); return
    u = get_user(uid)
    if u["balance"] < bet:
        await m.answer(f"Нет {bet}💰"); return
    add_balance(uid, -bet)
    my = random.randint(1, 6); bt = random.randint(1, 6)
    if my > bt:
        add_balance(uid, bet * 2)
        await m.answer(f"🎲 Ты: {my} | Бот: {bt}\n🎉 Победа! +{bet}💰")
    elif my < bt:
        await m.answer(f"🎲 Ты: {my} | Бот: {bt}\n💀 Проигрыш -{bet}💰")
    else:
        add_balance(uid, bet)
        await m.answer(f"🎲 Ты: {my} | Бот: {bt}\n🤝 Ничья, ставка возвращена")

@dp.message(Command("sell_market"))
async def cmd_sell_market(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid): return
    text = m.text[len("/sell_market "):].strip()
    if " " not in text:
        await m.answer("📤 /sell_market ИмяКарты Цена\nПример: /sell_market madk1d 500"); return
    name, price_s = text.rsplit(" ", 1)
    if not price_s.isdigit():
        await m.answer("Цена должна быть числом"); return
    price = int(price_s)
    if price < 10:
        await m.answer("Минимум 10💰"); return
    ok, msg = add_lot(uid, name.strip(), price)
    await m.answer(f"✅ Лот выставлен: {name} за {price}💰" if ok else f"❌ {msg}")

@dp.message(Command("market"))
async def cmd_market(m: Message): await show_market(m)

@dp.message(Command("my_lots"))
async def cmd_my_lots(m: Message): await show_my_lots(m, m.from_user.id)

@dp.message(Command("promo"))
async def cmd_promo(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    args = m.text.split()[1:]
    if not args:
        await m.answer("Использование: /promo КОД"); return
    ok, res = use_promo(uid, args[0])
    if ok:
        await m.answer(f"🎁 Промокод активирован! +{res}💰")
    else:
        await m.answer(f"❌ {res}")

@dp.message(Command("addpromo"))
async def cmd_addpromo(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()[1:]
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await m.answer("Использование: /addpromo КОД 500 10"); return
    code, reward, uses = args[0], int(args[1]), int(args[2])
    if add_promo(code, reward, uses):
        await m.answer(f"✅ Промокод {code} на {reward}💰 ×{uses}")
    else:
        await m.answer("❌ Код уже существует")

@dp.message(Command("event"))
async def cmd_event(m: Message):
    if not is_admin(m.from_user.id): return
    args = m.text.split()[1:]
    if len(args) < 2 or not args[1].isdigit():
        await m.answer("Использование: /event x2_money 24\nДоступные: x2_money, x2_xp, x2_rep"); return
    if args[0] not in ("x2_money", "x2_xp", "x2_rep"):
        await m.answer("Ивенты: x2_money, x2_xp, x2_rep"); return
    set_event(args[0], int(args[1]))
    await m.answer(f"✅ Ивент {args[0]} на {args[1]}ч активирован")

# ---- Callback-навигация ----
@dp.callback_query(F.data == "back")
async def cb_back(c: CallbackQuery):
    await c.message.answer("Главное меню", reply_markup=main_menu(c.from_user.id)); await c.answer()

@dp.callback_query(F.data == "cases")
async def cb_cases(c: CallbackQuery):
    await c.message.answer("Выбери кейс:", reply_markup=cases_menu()); await c.answer()

@dp.callback_query(F.data == "balance")
async def cb_bal(c: CallbackQuery):
    u = get_user(c.from_user.id, c.from_user.username)
    await c.message.answer(
        f"💰 Баланс: {u['balance']}\n⭐ Ур. {u['level']}\n"
        f"XP: {u['xp']}/{xp_needed(u['level'])}\n"
        f"🎖️ RP: {u['reputation']} — {rank_for(u['reputation'])}", parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "inv")
async def cb_inv(c: CallbackQuery):
    await show_collection(c.from_user.id, c.message); await c.answer()

@dp.callback_query(F.data.startswith("cardinfo:"))
async def cb_card_info(c: CallbackQuery):
    name = c.data.split(":", 1)[1]
    ok = await render_card_info(c.message, c.from_user.id, name)
    if ok: await c.answer()
    else: await c.answer("Карта не найдена", show_alert=True)

@dp.callback_query(F.data == "daily")
async def cb_daily(c: CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)
    if u["last_daily"]:
        d = datetime.now() - datetime.fromisoformat(u["last_daily"])
        if d < timedelta(hours=DAILY_COOLDOWN_HOURS):
            await c.answer(f"Через {fmt_time(timedelta(hours=DAILY_COOLDOWN_HOURS)-d)}", show_alert=True); return
        streak = u["daily_streak"] + 1 if d < timedelta(hours=48) else 1
    else:
        streak = 1
    bonus = int(random.randint(300, 700) * (1 + (streak - 1) * 0.1))
    add_balance(uid, bonus)
    upd(uid, last_daily=datetime.now().isoformat(), daily_streak=streak)
    await c.message.answer(f"🎉 Бонус: +{bonus}💰 Streak: {streak} дней", parse_mode="HTML")
    await c.answer("Получено!")

@dp.callback_query(F.data == "quests")
async def cb_quests(c: CallbackQuery):
    await show_quests(c.message, c.from_user.id); await c.answer()

@dp.callback_query(F.data == "top")
async def cb_top(c: CallbackQuery):
    await show_top(c.message); await c.answer()

@dp.callback_query(F.data == "stats")
async def cb_stats(c: CallbackQuery):
    await show_stats(c.from_user.id, c.message); await c.answer()

@dp.callback_query(F.data == "craft")
async def cb_craft(c: CallbackQuery):
    menu = craft_menu(c.from_user.id)
    if not menu:
        await c.answer("Нужно 3 карты одной редкости", show_alert=True); return
    await c.message.answer("⚒️ Что крафтим?", reply_markup=menu); await c.answer()

@dp.callback_query(F.data == "sell")
async def cb_sell_menu(c: CallbackQuery):
    menu = sell_menu(c.from_user.id)
    if not menu:
        await c.answer("Нечего продавать", show_alert=True); return
    await c.message.answer("💱 Выбери карту:", reply_markup=menu); await c.answer()

@dp.callback_query(F.data.startswith("sell:"))
async def cb_sell(c: CallbackQuery):
    uid = c.from_user.id; name = c.data.split(":", 1)[1]
    inv = [r for r in get_inv(uid) if r["card_name"] == name]
    if not inv:
        await c.answer("Карта не найдена", show_alert=True); return
    rar = inv[0]["rarity"]; price = sell_price(uid, rar)
    del_card(uid, name); add_balance(uid, price)
    await bump_counter(uid, "sold", 1, c.message)
    if rar == "legendary": add_rep(uid, RP_PER_LEGENDARY_SOLD)
    progress_quest(uid, "sell", 1)
    await c.answer(f"Продано за {price}💰", show_alert=True)
    if [r for r in get_inv(uid) if r["card_name"] == name]:
        await render_card_info(c.message, uid, name)
    else:
        await show_collection(uid, c.message)

@dp.callback_query(F.data == "collect")
async def cb_collect(c: CallbackQuery):
    await do_collect(c.from_user.id, c.message); await c.answer()

@dp.callback_query(F.data == "ach")
async def cb_ach(c: CallbackQuery):
    await show_achievements(c.from_user.id, c.message); await c.answer()

@dp.callback_query(F.data == "rep")
async def cb_rep(c: CallbackQuery):
    await show_rep(c.from_user.id, c.message); await c.answer()

@dp.callback_query(F.data.startswith("craft:"))
async def cb_do_craft(c: CallbackQuery):
    uid = c.from_user.id; src = c.data.split(":")[1]
    inv = [r for r in get_inv(uid) if r["rarity"] == src]
    if len(inv) < 3:
        await c.answer("Недостаточно карт", show_alert=True); return
    for row in random.sample(inv, 3): del_card(uid, row["card_name"])
    nxt = {"common":"rare","rare":"epic","epic":"legendary"}[src]
    card = random.choice(CARDS[nxt]); add_card(uid, card["name"], nxt, source="craft")
    await c.message.answer(f"⚒️ Крафт: {RARITIES[nxt]['emoji']} {card['emoji']} {card['name']}", parse_mode="HTML")
    await c.answer("Готово!")

@dp.callback_query(F.data.startswith("case:"))
async def cb_case(c: CallbackQuery):
    await open_case(c.from_user.id, c.message, c.data.split(":")[1], c.from_user.username)
    await c.answer()

@dp.callback_query(F.data == "games")
async def cb_games(c: CallbackQuery):
    await c.message.answer("🎮 <b>Игры</b>\n\nВыбирай игру:", reply_markup=games_menu(), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.startswith("help_"))
async def cb_help(c: CallbackQuery):
    kind = c.data.split("_")[1]
    if kind == "duel":
        t = "⚔️ <b>Дуэли</b>\n\nОтветь на сообщение игрока:\n<code>/duel 100</code>\n\nОба открывают кейс, у кого реже — забирает банк. Кулдаун 5 мин."
    elif kind == "roulette":
        t = "🎰 <b>Рулетка</b>\n\n<code>/roulette 100 red</code>\nили <code>black</code>, <code>green</code>\n\n🔴⚫ x2 (47%)\n🟢 x14 (6%)"
    elif kind == "market":
        t = "🏪 <b>Как торговать</b>\n\n📤 /sell_market madk1d 500\n🛒 /market\n📋 /my_lots"
    else:
        t = "🎲 <b>Кости</b>\n\n<code>/dice 100</code>\n\nКидаем кубики с ботом. Больше — победил x2."
    await c.message.answer(t, parse_mode="HTML"); await c.answer()

@dp.callback_query(F.data == "market")
async def cb_market(c: CallbackQuery):
    await c.message.answer("🏪 <b>Рынок</b>", reply_markup=market_menu(), parse_mode="HTML"); await c.answer()

@dp.callback_query(F.data == "market_browse")
async def cb_market_browse(c: CallbackQuery):
    clean_market()
    lots = get_lots(10)
    if not lots:
        await c.answer("Пока лотов нет", show_alert=True); return
    await c.message.answer("🛒 <b>Витрина</b> (свежие лоты):",
                            reply_markup=market_browse_menu(lots), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "market_my")
async def cb_market_my(c: CallbackQuery):
    await show_my_lots(c.message, c.from_user.id); await c.answer()

@dp.callback_query(F.data.startswith("buy_lot:"))
async def cb_buy_lot(c: CallbackQuery):
    uid = c.from_user.id; lot_id = int(c.data.split(":")[1])
    ok, res = buy_lot(uid, lot_id)
    if ok:
        await c.answer(f"✅ Куплено: {res}", show_alert=True)
    else:
        await c.answer(f"❌ {res}", show_alert=True)

@dp.callback_query(F.data == "collections")
async def cb_collections(c: CallbackQuery):
    await c.message.answer("📚 <b>Коллекции</b>\n\nСобери все карты редкости — получи награду!",
                            reply_markup=collections_menu(c.from_user.id), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.startswith("coll_show:"))
async def cb_coll_show(c: CallbackQuery):
    rar = c.data.split(":")[1]; uid = c.from_user.id
    info = COLLECTIONS[rar]
    owned, total = collection_status(uid, rar)
    inv = get_inv(uid)
    owned_names = set(r["card_name"] for r in inv if r["rarity"] == rar)
    lines = [f"{RARITIES[rar]['emoji']} <b>{info['name']}</b>",
             f"Прогресс: <b>{owned}/{total}</b>",
             f"Награда: <b>{info['reward']}💰</b>\n"]
    for card in CARDS[rar]:
        mark = "✅" if card["name"] in owned_names else "⬜"
        lines.append(f"{mark} {card['emoji']} {card['name']}")
    ach = get_achievements(uid)
    if ach.get(f"coll_{rar}"):
        lines.append("\n🏆 Коллекция собрана!")
    elif owned >= total:
        lines.append("\n🎁 Награда готова!")
    kb_rows = []
    if owned >= total and not ach.get(f"coll_{rar}"):
        kb_rows.append([InlineKeyboardButton(text=f"🎁 Забрать {info['reward']}💰", callback_data=f"coll_claim:{rar}")])
    kb_rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="collections")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    try:
        await c.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=kb)
    except:
        await c.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("coll_claim:"))
async def cb_coll_claim(c: CallbackQuery):
    rar = c.data.split(":")[1]; uid = c.from_user.id
    reward = claim_collection(uid, rar)
    if reward:
        await c.answer(f"🎉 +{reward}💰", show_alert=True)
    else:
        await c.answer("Уже получено или не собрано", show_alert=True)

# ---- Админ callback ----
@dp.callback_query(F.data == "admin")
async def cb_admin(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Только для владельца", show_alert=True); return
    await c.message.answer("👑 <b>Админ-панель</b>", reply_markup=admin_menu(), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "adm_stats")
async def cb_adm_stats(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    cur.execute("SELECT COUNT(*) FROM users"); users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM inventory"); cards = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM market"); lots = cur.fetchone()[0]
    cur.execute("SELECT SUM(balance) FROM users"); tb = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM bans WHERE until > ?", (datetime.now().isoformat(),))
    bans = cur.fetchone()[0]
    ev = active_events()
    evt = "\n".join(f"  • {e['name']}" for e in ev) if ev else "  нет"
    await c.message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Игроков: <b>{users}</b>\n"
        f"🎴 Карт: <b>{cards}</b>\n"
        f"🏪 Лотов: <b>{lots}</b>\n"
        f"💰 Монет всего: <b>{tb}</b>\n"
        f"🚫 Забанено: <b>{bans}</b>\n\n"
        f"🔥 Активные ивенты:\n{evt}", parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "adm_bc")
async def cb_adm_bc(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    pending[c.from_user.id] = ("broadcast", None)
    await c.message.answer("📢 Отправь текст рассылки (или /cancel для отмены)")
    await c.answer()

@dp.callback_query(F.data == "adm_give_coins")
async def cb_adm_coins(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    pending[c.from_user.id] = ("give_coins", None)
    await c.message.answer("🎁 Напиши: <code>USER_ID СУММА</code>", parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "adm_give_card")
async def cb_adm_card(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    pending[c.from_user.id] = ("give_card", None)
    await c.message.answer("🎴 Напиши: <code>USER_ID ИмяКарты</code>", parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "adm_promo")
async def cb_adm_promo(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    pending[c.from_user.id] = ("promo", None)
    await c.message.answer("📜 Напиши: <code>КОД НАГРАДА ИСПОЛЬЗОВАНИЙ</code>", parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "adm_event")
async def cb_adm_event(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 x2 монеты", callback_data="adm_ev:x2_money")],
        [InlineKeyboardButton(text="⭐ x2 XP", callback_data="adm_ev:x2_xp")],
        [InlineKeyboardButton(text="🎖️ x2 RP", callback_data="adm_ev:x2_rep")],
        [InlineKeyboardButton(text="❌ Отключить все", callback_data="adm_ev:off")],
    ])
    await c.message.answer("🎬 Выбери ивент на 24 часа:", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("adm_ev:"))
async def cb_adm_ev(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    ev = c.data.split(":")[1]
    if ev == "off":
        cur.execute("DELETE FROM events"); conn.commit()
        await c.answer("Все ивенты отключены", show_alert=True); return
    set_event(ev, 24)
    await c.answer(f"✅ {ev} на 24ч", show_alert=True)

@dp.callback_query(F.data == "adm_ban")
async def cb_adm_ban(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    pending[c.from_user.id] = ("ban", None)
    await c.message.answer("🚫 Напиши: <code>USER_ID ЧАСЫ</code>", parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "adm_unban")
async def cb_adm_unban(c: CallbackQuery):
    if not is_admin(c.from_user.id): return
    pending[c.from_user.id] = ("unban", None)
    await c.message.answer("✅ Напиши USER_ID для разбана")
    await c.answer()

@dp.callback_query(F.data.startswith("mk_help_sell:"))
async def cb_mk_help(c: CallbackQuery):
    name = c.data.split(":", 1)[1]
    await c.message.answer(
        f"📤 Чтобы выставить <b>{name}</b> на рынок:\n\n"
        f"<code>/sell_market {name} 500</code>", parse_mode="HTML")
    await c.answer()

# ====================== ОСНОВНЫЕ ФУНКЦИИ ======================
async def open_case(uid, message, case_key, username=""):
    case = CASES[case_key]
    u = get_user(uid, username)
    if u["balance"] < case["price"]:
        await message.answer(f"❌ Нужно {case['price']}💰, у тебя {u['balance']}💰"); return
    add_balance(uid, -case["price"])
    boosters = get_boosters(uid)
    msg = await message.answer(f"{case['emoji']} Открываем...")
    await asyncio.sleep(1); await msg.edit_text(f"{case['emoji']} Открываем... 🔄")
    await asyncio.sleep(1); await msg.edit_text(f"{case['emoji']} Открываем... ✨")
    await asyncio.sleep(1)
    if boosters.get("guaranteed_rare"):
        rar = random.choices(["rare", "epic", "legendary"], weights=[70, 25, 5], k=1)[0]
        card = random.choice(CARDS[rar]); boosters.pop("guaranteed_rare")
    else:
        rar, card = roll_card(case_key)
    set_boosters(uid, boosters)
    add_card(uid, card["name"], rar, source="case")
    add_rep(uid, RP_PER_CASE)
    await give_xp(uid, XP_PER_CASE)
    progress_quest(uid, "case", 1)
    await bump_counter(uid, "cases", 1)
    if rar == "legendary": await bump_counter(uid, "legendary", 1)
    new_u = get_user(uid)
    caption = (
        f"🎉 Выпала карта!\n\n"
        f"{RARITIES[rar]['emoji']} {card['emoji']} {card['name']}\n"
        f"Редкость: {RARITIES[rar]['name']}\n\n"
        f"📖 {card['desc']}\n\n"
        f"💰 Баланс: {new_u['balance']}\n"
        f"⭐ {new_u['xp']}/{xp_needed(new_u['level'])} XP\n"
        f"🎖️ +{RP_PER_CASE} RP"
    )
    try: await msg.delete()
    except: pass
    await message.answer(caption, parse_mode="HTML", reply_markup=main_menu(uid))
    await check_achievements(uid, message)

async def do_collect(uid, message):
    u = get_user(uid)
    if not u["last_collect"]:
        upd(uid, last_collect=datetime.now().isoformat())
        rate = calc_passive_rate(uid)
        await message.answer(f"💵 Доход запущен! {rate}💰/час.", parse_mode="HTML"); return
    last = datetime.fromisoformat(u["last_collect"])
    hours = (datetime.now() - last).total_seconds() / 3600
    if hours < COLLECT_COOLDOWN_HOURS:
        rem = timedelta(hours=COLLECT_COOLDOWN_HOURS) - timedelta(hours=hours)
        await message.answer(f"⏳ Сбор через: {fmt_time(rem)}", parse_mode="HTML"); return
    hours = min(hours, 24)
    rate = calc_passive_rate(uid)
    earned = int(rate * hours)
    if earned == 0:
        await message.answer("💸 У тебя нет карт."); return
    add_balance(uid, earned)
    upd(uid, last_collect=datetime.now().isoformat())
    await message.answer(f"💵 +{earned}💰 ({rate}💰/час, {hours:.1f}ч)", parse_mode="HTML")

async def show_collection(uid, message):
    menu = collection_menu(uid)
    if not menu:
        text = "🎒 <b>Коллекция пуста.</b>\nОткрой кейс, чтобы получить карту!"
        try: await message.edit_text(text, parse_mode="HTML")
        except: await message.answer(text, parse_mode="HTML")
        return
    inv = get_inv(uid); rate = calc_passive_rate(uid)
    text = (f"🎒 <b>Коллекция</b>\n"
            f"Карт: <b>{len(inv)}</b>\n"
            f"💵 Доход: <b>{rate}💰/час</b>\n\n"
            f"Нажми на карту для инфо:")
    try: await message.edit_text(text, parse_mode="HTML", reply_markup=menu)
    except: await message.answer(text, parse_mode="HTML", reply_markup=menu)

async def render_card_info(message, uid, name):
    rarity, cd = find_card(name)
    if not cd: return False
    inv = get_inv(uid)
    count = sum(1 for r in inv if r["card_name"] == name)
    if count == 0: return False
    price = sell_price(uid, rarity)
    text = (
        f"{RARITIES[rarity]['emoji']} <b>{cd['emoji']} {cd['name']}</b>\n\n"
        f"Редкость: <b>{RARITIES[rarity]['name']}</b>\n"
        f"В коллекции: <b>{count} шт.</b>\n"
        f"💰 Цена: <b>{price}</b>\n"
        f"💵 Пассив: {RARITIES[rarity]['passive']}💰/час\n\n"
        f"📖 <i>{cd['desc']}</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💱 Продать за {price}💰", callback_data=f"sell:{name}")],
        [InlineKeyboardButton(text="📤 На рынок", callback_data=f"mk_help_sell:{name}")],
        [InlineKeyboardButton(text="⬅️ К коллекции", callback_data="inv")],
    ])
    try: await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except: await message.answer(text, parse_mode="HTML", reply_markup=kb)
    return True

async def show_my_lots(message, uid):
    clean_market()
    lots = get_my_lots(uid)
    if not lots:
        await message.answer("📤 У тебя нет лотов."); return
    lines = ["📋 <b>Мои лоты:</b>\n"]
    for lot in lots:
        e = RARITIES[lot["rarity"]]["emoji"]
        lines.append(f"{e} {lot['card_name']} — {lot['price']}💰")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_market(message):
    clean_market()
    lots = get_lots(10)
    if not lots:
        await message.answer("🛒 Пока никто ничего не продаёт."); return
    await message.answer("🛒 <b>Витрина:</b>", reply_markup=market_browse_menu(lots), parse_mode="HTML")

async def show_top(message):
    cur.execute("SELECT username, user_id, balance, level, reputation FROM users ORDER BY balance DESC LIMIT 10")
    rows = cur.fetchall()
    if not rows:
        await message.answer("Пока пусто."); return
    lines = ["🏆 Топ-10:\n"]
    for i, r in enumerate(rows, 1):
        name = r["username"] or f"id{r['user_id']}"
        rep = f" 🎖️{r['reputation']}" if r["reputation"] else ""
        lines.append(f"{i}. {name} — {r['balance']}💰 (ур.{r['level']}{rep})")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_quests(message, uid):
    data = get_quests(uid)
    lines = ["📋 Ежедневные:\n"]
    for q in QUEST_TEMPLATES:
        done = data.get(q["id"], 0)
        mark = "✅" if done >= q["goal"] else "⏳"
        lines.append(f"{mark} {q['text']} — {done}/{q['goal']} (+{q['reward']}💰)")
    lines.append("\n💰 /claim — забрать")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_achievements(uid, message):
    ach = get_achievements(uid)
    lines = ["🏅 Достижения:\n"]
    for a in ACHIEVEMENTS:
        mark = "✅" if ach.get(a["id"]) else "🔒"
        lines.append(f"{mark} {a['text']} (+{a['reward']}💰)")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_rep(uid, message):
    rp = get_rep(uid)
    sm = rep_sell_multiplier(rp); pm = rep_passive_multiplier(rp)
    nxt = (rp // RP_STEP + 1) * RP_STEP
    lines = [f"🎖️ Репутация: {rp} RP", f"🏅 {rank_for(rp)}\n",
             f"💱 Продажа: +{(sm-1)*100:.0f}%", f"💵 Пассив: +{(pm-1)*100:.0f}%\n",
             f"📈 До бонуса: {nxt - rp} RP"]
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_stats(uid, message):
    u = get_user(uid); c = get_counters(uid)
    inv = get_inv(uid)
    unique = len(set(r["card_name"] for r in inv))
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"⭐ Ур. {u['level']}  🎖️ RP {u['reputation']}\n"
        f"💰 Баланс: {u['balance']}\n\n"
        f"📦 Кейсов: {c.get('cases', 0)}\n"
        f"💱 Продано: {c.get('sold', 0)}\n"
        f"⚔️ Побед в дуэлях: {c.get('duel_wins', 0)}\n"
        f"🏪 Продано на рынке: {c.get('market_sold', 0)}\n"
        f"🎒 Коллекция: {len(inv)} (уникальных: {unique})", parse_mode="HTML")

async def show_history(uid, message):
    rows = get_history(uid, 10)
    if not rows:
        await message.answer("📜 История пуста."); return
    lines = ["📜 <b>Последние 10 карт:</b>\n"]
    for r in rows:
        e = RARITIES[r["rarity"]]["emoji"]
        src = {"case": "📦", "craft": "⚒️", "market_buy": "🛒",
               "market_return": "↩️", "duel": "⚔️", "admin": "👑"}.get(r["source"], "?")
        lines.append(f"{src} {e} {r['card_name']}")
    await message.answer("\n".join(lines), parse_mode="HTML")

# ====================== REPLY-КНОПКИ ХЕНДЛЕРЫ ======================
@dp.message(F.text == "📦 Кейсы")
async def rb_cases(m: Message):
    await m.answer("Выбери кейс:", reply_markup=cases_menu())

@dp.message(F.text == "🎒 Коллекция")
async def rb_inv(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    await show_collection(m.from_user.id, m)

@dp.message(F.text == "💰 Баланс")
async def rb_balance(m: Message):
    u = get_user(m.from_user.id, m.from_user.username)
    await m.answer(
        f"💰 Баланс: {u['balance']}\n"
        f"⭐ Ур. {u['level']}\n"
        f"XP: {u['xp']}/{xp_needed(u['level'])}\n"
        f"🎖️ RP: {u['reputation']} — {rank_for(u['reputation'])}", parse_mode="HTML")

@dp.message(F.text == "💱 Продать")
async def rb_sell(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    menu = sell_menu(m.from_user.id)
    if not menu:
        await m.answer("🎒 Нечего продавать."); return
    await m.answer("💱 Выбери карту:", reply_markup=menu)

@dp.message(F.text == "💵 Собрать")
async def rb_collect(m: Message):
    await do_collect(m.from_user.id, m)

@dp.message(F.text == "📅 Бонус")
async def rb_daily(m: Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username)
    if u["last_daily"]:
        d = datetime.now() - datetime.fromisoformat(u["last_daily"])
        if d < timedelta(hours=DAILY_COOLDOWN_HOURS):
            await m.answer(f"⏳ Через {fmt_time(timedelta(hours=DAILY_COOLDOWN_HOURS)-d)}")
            return
        streak = u["daily_streak"] + 1 if d < timedelta(hours=48) else 1
    else:
        streak = 1
    bonus = int(random.randint(300, 700) * (1 + (streak - 1) * 0.1))
    add_balance(uid, bonus)
    upd(uid, last_daily=datetime.now().isoformat(), daily_streak=streak)
    await m.answer(f"🎉 Бонус: +{bonus}💰 Streak: {streak} дней", parse_mode="HTML")

@dp.message(F.text == "🎮 Игры")
async def rb_games(m: Message):
    await m.answer("🎮 <b>Игры</b>\n\nВыбирай:", reply_markup=games_menu(), parse_mode="HTML")

@dp.message(F.text == "🏪 Рынок")
async def rb_market(m: Message):
    await m.answer("🏪 <b>Рынок</b>", reply_markup=market_menu(), parse_mode="HTML")

@dp.message(F.text == "📚 Коллекции")
async def rb_collections(m: Message):
    await m.answer("📚 <b>Коллекции</b>", reply_markup=collections_menu(m.from_user.id), parse_mode="HTML")

@dp.message(F.text == "🏆 Топ")
async def rb_top(m: Message):
    await show_top(m)

@dp.message(F.text == "🎖️ Репутация")
async def rb_rep(m: Message):
    await show_rep(m.from_user.id, m)

@dp.message(F.text == "📊 Статистика")
async def rb_stats(m: Message):
    await show_stats(m.from_user.id, m)

@dp.message(F.text == "📋 Квесты")
async def rb_quests(m: Message):
    await show_quests(m, m.from_user.id)

@dp.message(F.text == "🏅 Достижения")
async def rb_ach(m: Message):
    await show_achievements(m.from_user.id, m)

@dp.message(F.text == "⚒️ Крафт")
async def rb_craft(m: Message):
    menu = craft_menu(m.from_user.id)
    if not menu:
        await m.answer("Нужно 3 карты одной редкости"); return
    await m.answer("⚒️ Что крафтим?", reply_markup=menu)

@dp.message(F.text == "❓ Помощь")
async def rb_help(m: Message):
    await m.answer(
        "❓ <b>Помощь</b>\n\n"
        "📦 Кейсы — открывай карты\n"
        "🎒 Коллекция — все твои карты\n"
        "💱 Продать — продать карту\n"
        "💵 Собрать — пассивный доход\n"
        "🎮 Игры — дуэли, рулетка, кости\n"
        "🏪 Рынок — торговля с игроками\n"
        "📚 Коллекции — собери все карты\n"
        "⚒️ Крафт — 3 карты → 1 выше\n\n"
        "<b>Команды:</b>\n"
        "/duel, /roulette, /dice\n"
        "/sell_market, /market\n"
        "/promo КОД\n"
        "/find ИМЯ\n"
        "/history", parse_mode="HTML")

@dp.message(F.text == "👑 Админ-панель")
async def rb_admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("👑 Только для владельца"); return
    await m.answer("👑 <b>Админ-панель</b>", reply_markup=admin_menu(), parse_mode="HTML")

# ====================== FALLBACK ДЛЯ PENDING ======================
@dp.message()
async def handle_pending(m: Message):
    uid = m.from_user.id
    if uid not in pending:
        return
    if not is_admin(uid):
        pending.pop(uid, None); return
    if not m.text: return
    action, _ = pending.pop(uid)
    text = m.text.strip()

    if action == "broadcast":
        cur.execute("SELECT user_id FROM users")
        users = [r["user_id"] for r in cur.fetchall()]
        ok, fail = 0, 0
        for u in users:
            try:
                await bot.send_message(u, text); ok += 1
            except: fail += 1
            await asyncio.sleep(0.05)
        await m.answer(f"✅ Доставлено: {ok}, ошибок: {fail}")

    elif action == "give_coins":
        p = text.split()
        if len(p) != 2 or not all(x.lstrip("-").isdigit() for x in p):
            await m.answer("❌ Формат: USER_ID СУММА"); return
        t, amt = int(p[0]), int(p[1])
        add_balance(t, amt)
        await m.answer(f"✅ Выдано {amt}💰 юзеру {t}")
        try: await bot.send_message(t, f"🎁 Владелец выдал тебе +{amt}💰")
        except: pass

    elif action == "give_card":
        p = text.rsplit(" ", 1)
        if len(p) != 2 or not p[0].isdigit():
            await m.answer("❌ Формат: USER_ID ИмяКарты"); return
        t = int(p[0]); name = p[1]
        rar, cd = find_card(name)
        if not cd:
            await m.answer("❌ Карта не найдена"); return
        add_card(t, name, rar, source="admin")
        await m.answer(f"✅ Выдана {cd['emoji']} {name} юзеру {t}")
        try: await bot.send_message(t, f"🎁 Владелец выдал тебе карту: {cd['emoji']} {name}")
        except: pass

    elif action == "promo":
        p = text.split()
        if len(p) != 3 or not p[1].isdigit() or not p[2].isdigit():
            await m.answer("❌ Формат: КОД НАГРАДА ИСПОЛЬЗОВАНИЙ"); return
        if add_promo(p[0], int(p[1]), int(p[2])):
            await m.answer(f"✅ Промокод {p[0]} на {p[1]}💰 ×{p[2]}")
        else:
            await m.answer("❌ Такой код уже есть")

    elif action == "ban":
        p = text.split()
        if len(p) != 2 or not all(x.isdigit() for x in p):
            await m.answer("❌ Формат: USER_ID ЧАСЫ"); return
        ban_user(int(p[0]), int(p[1]))
        await m.answer(f"🚫 Забанен {p[0]} на {p[1]}ч")

    elif action == "unban":
        if not text.isdigit():
            await m.answer("❌ USER_ID должен быть числом"); return
        unban_user(int(text))
        await m.answer(f"✅ Разбанен {text}")

# ====================== ЗАПУСК ======================
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
