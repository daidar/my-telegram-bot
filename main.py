import asyncio
import random
import sqlite3
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

BOT_TOKEN = "8918809137:AAEPzaMMiBwL8rHSGkHJsiIfwAmnKjF56ds"
OWNER_ID = 0
START_BALANCE = 1000
DAILY_CD = 24
XP_PER_CASE = 10
COLLECT_CD = 1
RP_STEP = 100
RP_CASE = 1
RP_LEG = 5
DUEL_CD = 300
COMMISSION = 0.05
LOT_HOURS = 24
MIN_BET = 10

CASES = {
    "basic": {
        "name": "Обычный", "emoji": "📦", "price": 100,
        "w": {"common": 60, "rare": 25, "epic": 12, "legendary": 3},
    },
    "premium": {
        "name": "Премиум", "emoji": "🎁", "price": 500,
        "w": {"common": 25, "rare": 40, "epic": 25, "legendary": 10},
    },
    "vip": {
        "name": "VIP", "emoji": "💎", "price": 2000,
        "w": {"common": 0, "rare": 30, "epic": 45, "legendary": 25},
    },
}

RARITIES = {
    "common": {"name": "Обычная", "e": "⚪", "sell": 30, "pas": 5},
    "rare": {"name": "Редкая", "e": "🔵", "sell": 120, "pas": 20},
    "epic": {"name": "Эпическая", "e": "🟣", "sell": 400, "pas": 80},
    "legendary": {"name": "Легендарная", "e": "🟡", "sell": 1500, "pas": 300},
}

CARDS = {
    "common": [
        ("mumble", "🗣", "Трэп и клауд на стыке."),
        ("Размаха", "💥", "Девушка в новом олдскуле."),
        ("Tuborosho", "🥁", "Саундклауд с пацанским вайбом."),
        ("mapt0v", "🗺", "Меланхоличный рэп."),
        ("dope17", "💊", "Воронежский фрешмен."),
        ("KRISTIEE", "✨", "17-летний фрешмен из Москвы."),
        ("Locked23", "🔒", "Автор хита Татухи."),
        ("юпи", "🎸", "Поп-панк и гранж."),
        ("euro91", "🚗", "Участник Bouquet."),
        ("fleurnothappy", "🥀", "Меланхоличная новая волна."),
    ],
    "rare": [
        ("Тёмный Принц", "🦇", "Самый загадочный фрешмен."),
        ("whitek3d", "💎", "15+ млн стримов."),
        ("Fortuna 812", "🏴", "Автор хита ParisLove."),
        ("madk1d", "🚀", "Лидер новой волны."),
        ("Урал Гайсин", "🎹", "Продюсер из Уфы."),
        ("паранойя", "🌀", "Мультижанровый исполнитель."),
        ("Anonymous Ember", "👤", "Тайный участник Russia Be Mad."),
        ("tewiq", "🎯", "Автор хита распять."),
        ("королевский XVII", "⚔", "Мрачный трэп из Волгограда."),
        ("KUDOKUSHI", "🏯", "Легенда саундклауда."),
    ],
    "epic": [
        ("CODE80", "👑", "Главный герой касты."),
        ("Sagath", "⛓", "Король хоррор-трэпа."),
        ("Friendly Thug 52 NGG", "🃏", "Топ новой волны."),
        ("ICEGERGERT", "❄", "Прорыв года."),
        ("Словетский", "📜", "Формирует новое звучание."),
        ("Aarne", "🎛", "Продюсер главных хитов."),
        ("LILCAK3", "🌶", "Локальная звезда."),
        ("unki", "🌪", "Новейшая волна андерграунда."),
    ],
    "legendary": [
        ("Miyagi", "🌴", "I Got Love - трек десятилетия."),
        ("Баста", "🎩", "Легенда сцены."),
        ("Oxxxymiron", "🏛", "Горгород."),
        ("Скриптонит", "🦅", "Дом с нормальными явлениями."),
        ("Хаски", "🐺", "Тёмный рэп."),
        ("Noize MC", "🎸", "Рэп с гитарой."),
        ("FACE", "🥀", "Грустный трэп."),
        ("Элджей", "🎧", "Пионер трэпа."),
    ],
}

COLLECTIONS = {
    "common": {"name": "Новички", "reward": 1000},
    "rare": {"name": "Андерграунд", "reward": 3000},
    "epic": {"name": "Элита", "reward": 10000},
    "legendary": {"name": "Легенды", "reward": 50000},
}

ACHIEVEMENTS = [
    ("first_case", "Открой первый кейс", 100, "cases", 1),
    ("first_leg", "Первая легендарка", 500, "legendary", 1),
    ("cases_10", "Открой 10 кейсов", 300, "cases", 10),
    ("cases_100", "Открой 100 кейсов", 2000, "cases", 100),
    ("sell_10", "Продай 10 карт", 200, "sold", 10),
    ("sell_100", "Продай 100 карт", 2000, "sold", 100),
    ("level_10", "Достигни 10 уровня", 500, "level", 10),
    ("level_25", "Достигни 25 уровня", 2000, "level", 25),
    ("rp_500", "Набрать 500 репутации", 1500, "reputation", 500),
    ("duel_10", "Выиграй 10 дуэлей", 1000, "duel_wins", 10),
    ("market_5", "Продай 5 карт на рынке", 500, "market_sold", 5),
]

RANKS = [(0, "Новичок"), (100, "Андерграунд"),
         (500, "Легенда саундклауда"), (2000, "Икона сцены")]

def rank_for(rp):
    r = RANKS[0][1]
    for t, n in RANKS:
        if rp >= t:
            r = n
    return r

def xp_need(lv):
    return int(100 * (1.15 ** (lv - 1)))

conn = sqlite3.connect("bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY, username TEXT,
  balance INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
  last_daily TEXT, daily_streak INTEGER DEFAULT 0,
  quest_data TEXT DEFAULT '{}', quest_date TEXT,
  boosters TEXT DEFAULT '{}', counters TEXT DEFAULT '{}',
  achievements TEXT DEFAULT '{}', reputation INTEGER DEFAULT 0,
  last_collect TEXT, last_duel TEXT
);
CREATE TABLE IF NOT EXISTS inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
  card_name TEXT, rarity TEXT, obtained_at TEXT
);
CREATE TABLE IF NOT EXISTS market (
  id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER,
  seller_name TEXT, card_name TEXT, rarity TEXT,
  price INTEGER, created_at TEXT
);
CREATE TABLE IF NOT EXISTS promo (
  code TEXT PRIMARY KEY, reward INTEGER,
  max_uses INTEGER DEFAULT 1, uses INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS promo_used (
  user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code)
);
CREATE TABLE IF NOT EXISTS history (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
  card_name TEXT, rarity TEXT, source TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS events (name TEXT PRIMARY KEY, expires TEXT);
CREATE TABLE IF NOT EXISTS bans (user_id INTEGER PRIMARY KEY, until TEXT);
""")
for col, typ in [("counters", "TEXT DEFAULT '{}'"),
                 ("achievements", "TEXT DEFAULT '{}'"),
                 ("reputation", "INTEGER DEFAULT 0"),
                 ("last_collect", "TEXT"),
                 ("last_duel", "TEXT")]:
    try:
        cur.execute("ALTER TABLE users ADD COLUMN " + col + " " + typ)
    except sqlite3.OperationalError:
        pass
conn.commit()

pending = {}

def is_admin(uid):
    return bool(OWNER_ID) and uid == OWNER_ID

def is_banned(uid):
    cur.execute("SELECT until FROM bans WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        return False
    try:
        if datetime.fromisoformat(row["until"]) > datetime.now():
            return True
    except Exception:
        pass
    cur.execute("DELETE FROM bans WHERE user_id=?", (uid,))
    conn.commit()
    return False

def ban_user(uid, h):
    until = (datetime.now() + timedelta(hours=h)).isoformat()
    cur.execute("INSERT OR REPLACE INTO bans VALUES (?,?)", (uid, until))
    conn.commit()

def unban_user(uid):
    cur.execute("DELETE FROM bans WHERE user_id=?", (uid,))
    conn.commit()

def create_user(uid, un=""):
    cur.execute("INSERT OR IGNORE INTO users (user_id,username,balance) VALUES (?,?,?)",
                (uid, un or "", START_BALANCE))
    conn.commit()

def get_user(uid, un=""):
    create_user(uid, un)
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def upd(uid, **kw):
    keys = ", ".join(k + "=?" for k in kw)
    cur.execute("UPDATE users SET " + keys + " WHERE user_id=?",
                (*kw.values(), uid))
    conn.commit()

def add_bal(uid, amt):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
    conn.commit()

def add_card(uid, name, rar, src="unknown"):
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO inventory (user_id,card_name,rarity,obtained_at) VALUES (?,?,?,?)",
                (uid, name, rar, now))
    cur.execute("INSERT INTO history (user_id,card_name,rarity,source,created_at) VALUES (?,?,?,?,?)",
                (uid, name, rar, src, now))
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

def add_rep(uid, amt):
    amt *= ev_mult("x2_rep")
    cur.execute("UPDATE users SET reputation=reputation+? WHERE user_id=?", (amt, uid))
    conn.commit()

def rep_sell_mult(rp):
    return 1 + 0.02 * (rp // RP_STEP)

def rep_pas_mult(rp):
    return 1 + 0.05 * (rp // RP_STEP)

def get_cnt(uid):
    return json.loads(get_user(uid)["counters"] or "{}")

def get_ach(uid):
    return json.loads(get_user(uid)["achievements"] or "{}")

async def check_ach(uid, msg=None):
    c = get_cnt(uid)
    a = get_ach(uid)
    unlocked = []
    for aid, text, rew, key, thr in ACHIEVEMENTS:
        if a.get(aid):
            continue
        val = c.get(key, 0)
        if key == "reputation":
            val = get_rep(uid)
        if val >= thr:
            a[aid] = True
            add_bal(uid, rew)
            unlocked.append((text, rew))
    if unlocked:
        upd(uid, achievements=json.dumps(a))
        if msg:
            for text, rew in unlocked:
                try:
                    await msg.answer("Достижение: " + text + " +" + str(rew))
                except Exception:
                    pass

async def bump(uid, key, amt=1, msg=None):
    c = get_cnt(uid)
    c[key] = c.get(key, 0) + amt
    upd(uid, counters=json.dumps(c))
    await check_ach(uid, msg)

async def give_xp(uid, amt, msg=None):
    amt *= ev_mult("x2_xp")
    u = get_user(uid)
    xp = u["xp"] + amt
    lv = u["level"]
    leveled = False
    while xp >= xp_need(lv):
        xp -= xp_need(lv)
        lv += 1
        leveled = True
    upd(uid, xp=xp, level=lv)
    if leveled:
        if msg:
            try:
                await msg.answer("Уровень " + str(lv) + "!")
            except Exception:
                pass
        c = get_cnt(uid)
        c["level"] = lv
        upd(uid, counters=json.dumps(c))
        await check_ach(uid, msg)

QUESTS = [
    ("case3", "Открой 3 кейса", 3, 200, "case"),
    ("sell2", "Продай 2 карты", 2, 100, "sell"),
    ("case5", "Открой 5 кейсов", 5, 400, "case"),
]

def get_quests(uid):
    u = get_user(uid)
    today = datetime.now().date().isoformat()
    if u["quest_date"] != today:
        d = {q[0]: 0 for q in QUESTS}
        upd(uid, quest_date=today, quest_data=json.dumps(d))
        return d
    return json.loads(u["quest_data"] or "{}")

def prog_quest(uid, qtype, amt=1):
    d = get_quests(uid)
    for qid, text, goal, rew, t in QUESTS:
        if t == qtype and d.get(qid, 0) < goal:
            d[qid] = min(d.get(qid, 0) + amt, goal)
    upd(uid, quest_data=json.dumps(d))

def claim_quests(uid):
    d = get_quests(uid)
    total = 0
    for qid, text, goal, rew, t in QUESTS:
        if d.get(qid, 0) >= goal:
            total += rew
            d[qid] = 0
    if total > 0:
        add_bal(uid, total)
        upd(uid, quest_data=json.dumps(d))
    return total

def get_boosters(uid):
    return json.loads(get_user(uid)["boosters"] or "{}")

def set_boosters(uid, d):
    upd(uid, boosters=json.dumps(d))

def pas_rate(uid):
    inv = get_inv(uid)
    base = sum(RARITIES[r["rarity"]]["pas"] for r in inv)
    return int(base * rep_pas_mult(get_rep(uid)))

def set_event(name, h):
    e = (datetime.now() + timedelta(hours=h)).isoformat()
    cur.execute("INSERT OR REPLACE INTO events VALUES (?,?)", (name, e))
    conn.commit()

def ev_mult(name):
    cur.execute("SELECT expires FROM events WHERE name=?", (name,))
    r = cur.fetchone()
    if not r:
        return 1
    try:
        if datetime.fromisoformat(r["expires"]) > datetime.now():
            return 2
    except Exception:
        pass
    return 1

def active_events():
    cur.execute("SELECT name FROM events WHERE expires > ?",
                (datetime.now().isoformat(),))
    return [r["name"] for r in cur.fetchall()]

def clean_market():
    now = datetime.now()
    cur.execute("SELECT * FROM market")
    rows = cur.fetchall()
    changed = False
    for r in rows:
        try:
            delta = (now - datetime.fromisoformat(r["created_at"])).total_seconds()
            if delta > LOT_HOURS * 3600:
                add_card(r["seller_id"], r["card_name"], r["rarity"], "market_return")
                cur.execute("DELETE FROM market WHERE id=?", (r["id"],))
                changed = True
        except Exception:
            pass
    if changed:
        conn.commit()

def add_lot(uid, name, price):
    rar, cd = find_card(name)
    if not cd:
        return False, "Карта не найдена"
    inv = [r for r in get_inv(uid) if r["card_name"] == name]
    if not inv:
        return False, "У тебя нет такой карты"
    del_card(uid, name)
    u = get_user(uid)
    sname = u["username"] or ("id" + str(uid))
    cur.execute("INSERT INTO market (seller_id,seller_name,card_name,rarity,price,created_at) VALUES (?,?,?,?,?,?)",
                (uid, sname, name, rar, price, datetime.now().isoformat()))
    conn.commit()
    return True, "OK"

def get_lots(limit=10):
    cur.execute("SELECT * FROM market ORDER BY id DESC LIMIT ?", (limit,))
    return cur.fetchall()

def get_my_lots(uid):
    cur.execute("SELECT * FROM market WHERE seller_id=? ORDER BY id DESC", (uid,))
    return cur.fetchall()

def buy_lot(uid, lot_id):
    cur.execute("SELECT * FROM market WHERE id=?", (lot_id,))
    lot = cur.fetchone()
    if not lot:
        return False, "Лот не найден"
    if lot["seller_id"] == uid:
        return False, "Нельзя купить свой лот"
    u = get_user(uid)
    if u["balance"] < lot["price"]:
        return False, "Недостаточно монет"
    add_bal(uid, -lot["price"])
    cut = int(lot["price"] * (1 - COMMISSION))
    add_bal(lot["seller_id"], cut)
    add_card(uid, lot["card_name"], lot["rarity"], "market_buy")
    cur.execute("DELETE FROM market WHERE id=?", (lot_id,))
    conn.commit()
    c = get_cnt(lot["seller_id"])
    c["market_sold"] = c.get("market_sold", 0) + 1
    upd(lot["seller_id"], counters=json.dumps(c))
    return True, lot["card_name"]

def add_promo(code, rew, uses):
    try:
        cur.execute("INSERT INTO promo VALUES (?,?,?,0)", (code.upper(), rew, uses))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def use_promo(uid, code):
    code = code.upper()
    cur.execute("SELECT * FROM promo WHERE code=?", (code,))
    p = cur.fetchone()
    if not p:
        return False, "Промокод не найден"
    if p["uses"] >= p["max_uses"]:
        return False, "Промокод закончился"
    cur.execute("SELECT 1 FROM promo_used WHERE user_id=? AND code=?", (uid, code))
    if cur.fetchone():
        return False, "Ты уже использовал этот промокод"
    cur.execute("UPDATE promo SET uses=uses+1 WHERE code=?", (code,))
    cur.execute("INSERT INTO promo_used VALUES (?,?)", (uid, code))
    conn.commit()
    add_bal(uid, p["reward"])
    return True, p["reward"]

def coll_status(uid, rar):
    inv = get_inv(uid)
    owned = set(r["card_name"] for r in inv if r["rarity"] == rar)
    need = set(c[0] for c in CARDS[rar])
    return len(owned & need), len(need)

def claim_coll(uid, rar):
    o, t = coll_status(uid, rar)
    if o < t:
        return 0
    a = get_ach(uid)
    key = "coll_" + rar
    if a.get(key):
        return 0
    a[key] = True
    upd(uid, achievements=json.dumps(a))
    rew = COLLECTIONS[rar]["reward"]
    add_bal(uid, rew)
    return rew

def get_history(uid, limit=10):
    cur.execute("SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))
    return cur.fetchall()

def roll_card(case_key):
    w = CASES[case_key]["w"]
    keys = list(w.keys())
    weights = list(w.values())
    rar = random.choices(keys, weights=weights, k=1)[0]
    return rar, random.choice(CARDS[rar])

def fmt_time(td):
    t = int(td.total_seconds())
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return str(h) + "ч " + str(m) + "м " + str(s) + "с"

def sell_price(uid, rar):
    return int(RARITIES[rar]["sell"] * rep_sell_mult(get_rep(uid)))

def find_card(name):
    for rar in CARDS:
        for cd in CARDS[rar]:
            if cd[0] == name:
                return rar, cd
    return None, None

def card_line(cd, rar, cnt=None):
    e = RARITIES[rar]["e"]
    line = e + " " + cd[1] + " " + cd[0]
    if cnt:
        line += " x" + str(cnt)
    return line

def reply_menu(uid=None):
    rows = [
        [KeyboardButton(text="📦 Кейсы"), KeyboardButton(text="🎒 Коллекция")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="💱 Продать")],
        [KeyboardButton(text="💵 Собрать"), KeyboardButton(text="📅 Бонус")],
        [KeyboardButton(text="🎮 Игры"), KeyboardButton(text="🏪 Рынок")],
        [KeyboardButton(text="📚 Коллекции"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="🎖 Репутация"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📋 Квесты"), KeyboardButton(text="🏅 Достижения")],
        [KeyboardButton(text="⚒ Крафт"), KeyboardButton(text="❓ Помощь")],
    ]
    if uid and is_admin(uid):
        rows.append([KeyboardButton(text="👑 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)

def inline_menu(uid=None):
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
        [InlineKeyboardButton(text="🎖 Репутация", callback_data="rep"),
         InlineKeyboardButton(text="⚒ Крафт", callback_data="craft")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
    ]
    if uid and is_admin(uid):
        rows.append([InlineKeyboardButton(text="👑 Админ", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def cases_menu():
    btns = []
    for k, c in CASES.items():
        t = c["emoji"] + " " + c["name"] + " - " + str(c["price"])
        btns.append([InlineKeyboardButton(text=t, callback_data="case:" + k)])
    btns.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def sell_menu(uid):
    inv = get_inv(uid)
    if not inv:
        return None
    seen = {}
    for r in inv:
        k = (r["card_name"], r["rarity"])
        seen[k] = seen.get(k, 0) + 1
    order = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
    items = sorted(seen.items(), key=lambda x: order[x[0][1]])
    btns = []
    for (name, rar), cnt in items:
        price = sell_price(uid, rar)
        t = RARITIES[rar]["e"] + " " + name + " x" + str(cnt)
        t += " - " + str(price)
        btns.append([InlineKeyboardButton(text=t, callback_data="sell:" + name)])
    btns.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def coll_menu(uid):
    inv = get_inv(uid)
    if not inv:
        return None
    grouped = {}
    for r in inv:
        k = (r["card_name"], r["rarity"])
        grouped[k] = grouped.get(k, 0) + 1
    order = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
    items = sorted(grouped.items(), key=lambda x: order[x[0][1]])
    btns = []
    for (name, rar), cnt in items:
        t = RARITIES[rar]["e"] + " " + name + " x" + str(cnt)
        btns.append([InlineKeyboardButton(text=t, callback_data="ci:" + name)])
    btns.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def craft_menu(uid):
    inv = get_inv(uid)
    btns = []
    for rk in ["common", "rare", "epic"]:
        avail = sum(1 for r in inv if r["rarity"] == rk)
        if avail >= 3:
            nxt = {"common": "rare", "rare": "epic", "epic": "legendary"}[rk]
            t = "3x " + RARITIES[rk]["name"] + " -> 1x "
            t += RARITIES[nxt]["name"]
            btns.append([InlineKeyboardButton(text=t, callback_data="craft:" + rk)])
    btns.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    if len(btns) > 1:
        return InlineKeyboardMarkup(inline_keyboard=btns)
    return None

def games_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Дуэль - /duel 100", callback_data="h:duel")],
        [InlineKeyboardButton(text="Рулетка - /roulette", callback_data="h:roul")],
        [InlineKeyboardButton(text="Кости - /dice 100", callback_data="h:dice")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

def market_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Витрина", callback_data="mkt_browse")],
        [InlineKeyboardButton(text="Мои лоты", callback_data="mkt_my")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

def mkt_browse_menu(lots):
    btns = []
    for lot in lots:
        e = RARITIES[lot["rarity"]]["e"]
        t = e + " " + lot["card_name"] + " - " + str(lot["price"])
        btns.append([InlineKeyboardButton(text=t, callback_data="buy:" + str(lot["id"]))])
    btns.append([InlineKeyboardButton(text="Обновить", callback_data="mkt_browse")])
    btns.append([InlineKeyboardButton(text="Назад", callback_data="market")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def colls_menu(uid):
    btns = []
    for rar, info in COLLECTIONS.items():
        o, t = coll_status(uid, rar)
        e = RARITIES[rar]["e"]
        ach = get_ach(uid)
        mark = " OK" if ach.get("coll_" + rar) else ""
        txt = e + " " + info["name"] + " " + str(o) + "/" + str(t) + mark
        btns.append([InlineKeyboardButton(text=txt, callback_data="cs:" + rar)])
    btns.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика", callback_data="a:stats")],
        [InlineKeyboardButton(text="Рассылка", callback_data="a:bc")],
        [InlineKeyboardButton(text="Выдать монеты", callback_data="a:coins")],
        [InlineKeyboardButton(text="Выдать карту", callback_data="a:card")],
        [InlineKeyboardButton(text="Промокод", callback_data="a:promo")],
        [InlineKeyboardButton(text="Ивент", callback_data="a:event")],
        [InlineKeyboardButton(text="Бан", callback_data="a:ban")],
        [InlineKeyboardButton(text="Разбан", callback_data="a:unban")],
        [InlineKeyboardButton(text="Назад", callback_data="back")],
    ])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(m: Message):
    if is_banned(m.from_user.id):
        await m.answer("Ты забанен.")
        return
    u = get_user(m.from_user.id, m.from_user.username)
    lines = ["Добро пожаловать!", ""]
    lines.append("Баланс: " + str(u["balance"]))
    lines.append("Уровень: " + str(u["level"]))
    lines.append("Репутация: " + str(u["reputation"]))
    lines.append("Звание: " + rank_for(u["reputation"]))
    for e in active_events():
        lines.append("Ивент: " + e)
    lines.append("")
    lines.append("Кнопки меню внизу экрана")
    await m.answer("\n".join(lines),
                   reply_markup=reply_menu(m.from_user.id))

@dp.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Меню", reply_markup=reply_menu(m.from_user.id))

@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("Только для владельца")
        return
    await m.answer("Админ-панель", reply_markup=admin_menu())

@dp.message(Command("cancel"))
async def cmd_cancel(m: Message):
    pending.pop(m.from_user.id, None)
    await m.answer("Отменено")

@dp.message(Command("claim"))
async def cmd_claim(m: Message):
    t = claim_quests(m.from_user.id)
    if t:
        await m.answer("Получено: +" + str(t))
    else:
        await m.answer("Нет выполненных квестов")

@dp.message(Command("promo"))
async def cmd_promo(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("Использование: /promo КОД")
        return
    ok, res = use_promo(uid, parts[1])
    if ok:
        await m.answer("Промокод активирован! +" + str(res))
    else:
        await m.answer(res)

@dp.message(Command("sell_market"))
async def cmd_sell_market(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid):
        return
    text = m.text
    if len(text) <= len("/sell_market "):
        await m.answer("Формат: /sell_market ИмяКарты Цена")
        return
    body = text[len("/sell_market "):].strip()
    parts = body.rsplit(" ", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        await m.answer("Формат: /sell_market ИмяКарты Цена")
        return
    name = parts[0].strip()
    price = int(parts[1])
    if price < 10:
        await m.answer("Минимум 10")
        return
    ok, msg = add_lot(uid, name, price)
    if ok:
        await m.answer("Лот выставлен: " + name + " за " + str(price))
    else:
        await m.answer("Ошибка: " + msg)

@dp.message(Command("market"))
async def cmd_market(m: Message):
    clean_market()
    lots = get_lots(10)
    if not lots:
        await m.answer("Пока лотов нет")
        return
    await m.answer("Витрина:", reply_markup=mkt_browse_menu(lots))

@dp.message(Command("my_lots"))
async def cmd_my_lots(m: Message):
    await show_my_lots(m, m.from_user.id)

@dp.message(Command("find"))
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
    lines = ["Найдено:"]
    for key, cnt in grouped.items():
        name = key[0]
        rar = key[1]
        e = RARITIES[rar]["e"]
        lines.append(e + " " + name + " x" + str(cnt))
    await m.answer("\n".join(lines))

@dp.message(Command("history"))
async def cmd_history(m: Message):
    await show_history(m.from_user.id, m)

@dp.message(Command("stats"))
async def cmd_stats(m: Message):
    await show_stats(m.from_user.id, m)

@dp.message(Command("duel"))
async def cmd_duel(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid):
        return
    if not m.reply_to_message:
        await m.answer("Ответь на сообщение игрока: /duel 100")
        return
    opp = m.reply_to_message.from_user
    if opp.id == uid or opp.is_bot:
        await m.answer("Нельзя дуэлить себя или бота")
        return
    parts = m.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await m.answer("Использование: /duel 100")
        return
    bet = int(parts[1])
    if bet < MIN_BET:
        await m.answer("Минимум " + str(MIN_BET))
        return
    u = get_user(uid)
    o = get_user(opp.id, opp.username)
    if u["balance"] < bet:
        await m.answer("Недостаточно монет")
        return
    if o["balance"] < bet:
        await m.answer("У соперника нет столько")
        return
    if u["last_duel"]:
        last = datetime.fromisoformat(u["last_duel"])
        d = (datetime.now() - last).total_seconds()
        if d < DUEL_CD:
            await m.answer("Кулдаун " + str(int(DUEL_CD - d)) + "с")
            return
    add_bal(uid, -bet)
    add_bal(opp.id, -bet)
    r1, c1 = roll_card("basic")
    r2, c2 = roll_card("basic")
    order = {"common": 0, "rare": 1, "epic": 2, "legendary": 3}
    if order[r1] > order[r2]:
        winner = uid
        wname = m.from_user.first_name
    elif order[r2] > order[r1]:
        winner = opp.id
        wname = opp.first_name
    else:
        if RARITIES[r1]["sell"] >= RARITIES[r2]["sell"]:
            winner = uid
            wname = m.from_user.first_name
        else:
            winner = opp.id
            wname = opp.first_name
    bank = bet * 2
    add_bal(winner, bank)
    upd(uid, last_duel=datetime.now().isoformat())
    if winner == uid:
        await bump(uid, "duel_wins", 1, m)
    lines = ["Дуэль! Банк: " + str(bank)]
    lines.append(m.from_user.first_name + ": " + RARITIES[r1]["e"] + " " + c1[0])
    lines.append(opp.first_name + ": " + RARITIES[r2]["e"] + " " + c2[0])
    lines.append("Победил: " + wname + " (+" + str(bank) + ")")
    await m.answer("\n".join(lines))

@dp.message(Command("roulette"))
async def cmd_roulette(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid):
        return
    parts = m.text.split()
    if len(parts) < 3:
        await m.answer("Формат: /roulette 100 red|black|green")
        return
    if not parts[1].isdigit():
        await m.answer("Ставка должна быть числом")
        return
    bet = int(parts[1])
    color = parts[2].lower()
    if color not in ("red", "black", "green"):
        await m.answer("Цвет: red, black или green")
        return
    if bet < MIN_BET:
        await m.answer("Минимум " + str(MIN_BET))
        return
    u = get_user(uid)
    if u["balance"] < bet:
        await m.answer("Недостаточно монет")
        return
    add_bal(uid, -bet)
    roll = random.choices(["red", "black", "green"], weights=[47, 47, 6], k=1)[0]
    if roll == color:
        mult = 2 if color in ("red", "black") else 14
        win = bet * mult
        add_bal(uid, win)
        await m.answer("Выпало: " + roll + ". Победа +" + str(win))
    else:
        await m.answer("Выпало: " + roll + ". Проигрыш -" + str(bet))

@dp.message(Command("dice"))
async def cmd_dice(m: Message):
    uid = m.from_user.id
    get_user(uid, m.from_user.username)
    if is_banned(uid):
        return
    parts = m.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await m.answer("Формат: /dice 100")
        return
    bet = int(parts[1])
    if bet < MIN_BET:
        await m.answer("Минимум " + str(MIN_BET))
        return
    u = get_user(uid)
    if u["balance"] < bet:
        await m.answer("Недостаточно монет")
        return
    add_bal(uid, -bet)
    my = random.randint(1, 6)
    bt = random.randint(1, 6)
    if my > bt:
        add_bal(uid, bet * 2)
        await m.answer("Ты: " + str(my) + " Бот: " + str(bt) + ". Победа +" + str(bet))
    elif my < bt:
        await m.answer("Ты: " + str(my) + " Бот: " + str(bt) + ". Проигрыш -" + str(bet))
    else:
        add_bal(uid, bet)
        await m.answer("Ты: " + str(my) + " Бот: " + str(bt) + ". Ничья")

@dp.callback_query(F.data == "back")
async def cb_back(c: CallbackQuery):
    await c.message.answer("Меню", reply_markup=inline_menu(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data == "cases")
async def cb_cases(c: CallbackQuery):
    await c.message.answer("Выбери кейс:", reply_markup=cases_menu())
    await c.answer()

@dp.callback_query(F.data == "balance")
async def cb_bal(c: CallbackQuery):
    u = get_user(c.from_user.id, c.from_user.username)
    lines = ["Баланс: " + str(u["balance"])]
    lines.append("Уровень: " + str(u["level"]))
    lines.append("XP: " + str(u["xp"]) + "/" + str(xp_need(u["level"])))
    lines.append("Репутация: " + str(u["reputation"]))
    lines.append("Звание: " + rank_for(u["reputation"]))
    await c.message.answer("\n".join(lines))
    await c.answer()

@dp.callback_query(F.data == "inv")
async def cb_inv(c: CallbackQuery):
    await show_coll(c.from_user.id, c.message)
    await c.answer()

@dp.callback_query(F.data.startswith("ci:"))
async def cb_ci(c: CallbackQuery):
    name = c.data.split(":", 1)[1]
    ok = await render_card(c.message, c.from_user.id, name)
    if ok:
        await c.answer()
    else:
        await c.answer("Карта не найдена", show_alert=True)

@dp.callback_query(F.data == "daily")
async def cb_daily(c: CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)
    if u["last_daily"]:
        d = datetime.now() - datetime.fromisoformat(u["last_daily"])
        if d < timedelta(hours=DAILY_CD):
            left = timedelta(hours=DAILY_CD) - d
            await c.answer("Через " + fmt_time(left), show_alert=True)
            return
        streak = u["daily_streak"] + 1 if d < timedelta(hours=48) else 1
    else:
        streak = 1
    bonus = int(random.randint(300, 700) * (1 + (streak - 1) * 0.1))
    add_bal(uid, bonus)
    upd(uid, last_daily=datetime.now().isoformat(), daily_streak=streak)
    await c.message.answer("Бонус: +" + str(bonus) + " Streak: " + str(streak))
    await c.answer("Получено!")

@dp.callback_query(F.data == "quests")
async def cb_quests(c: CallbackQuery):
    await show_quests(c.message, c.from_user.id)
    await c.answer()

@dp.callback_query(F.data == "top")
async def cb_top(c: CallbackQuery):
    await show_top(c.message)
    await c.answer()

@dp.callback_query(F.data == "stats")
async def cb_stats(c: CallbackQuery):
    await show_stats(c.from_user.id, c.message)
    await c.answer()

@dp.callback_query(F.data == "rep")
async def cb_rep(c: CallbackQuery):
    await show_rep(c.from_user.id, c.message)
    await c.answer()

@dp.callback_query(F.data == "ach")
async def cb_ach(c: CallbackQuery):
    await show_ach(c.from_user.id, c.message)
    await c.answer()

@dp.callback_query(F.data == "craft")
async def cb_craft(c: CallbackQuery):
    menu = craft_menu(c.from_user.id)
    if not menu:
        await c.answer("Нужно 3 карты одной редкости", show_alert=True)
        return
    await c.message.answer("Что крафтим?", reply_markup=menu)
    await c.answer()

@dp.callback_query(F.data.startswith("craft:"))
async def cb_do_craft(c: CallbackQuery):
    uid = c.from_user.id
    src = c.data.split(":")[1]
    inv = [r for r in get_inv(uid) if r["rarity"] == src]
    if len(inv) < 3:
        await c.answer("Недостаточно карт", show_alert=True)
        return
    for row in random.sample(inv, 3):
        del_card(uid, row["card_name"])
    nxt = {"common": "rare", "rare": "epic", "epic": "legendary"}[src]
    card = random.choice(CARDS[nxt])
    add_card(uid, card[0], nxt, "craft")
    txt = "Крафт: " + RARITIES[nxt]["e"] + " " + card[1] + " " + card[0]
    await c.message.answer(txt)
    await c.answer("Готово!")

@dp.callback_query(F.data == "sell")
async def cb_sell_menu(c: CallbackQuery):
    menu = sell_menu(c.from_user.id)
    if not menu:
        await c.answer("Нечего продавать", show_alert=True)
        return
    await c.message.answer("Выбери карту:", reply_markup=menu)
    await c.answer()

@dp.callback_query(F.data.startswith("sell:"))
async def cb_sell(c: CallbackQuery):
    uid = c.from_user.id
    name = c.data.split(":", 1)[1]
    inv = [r for r in get_inv(uid) if r["card_name"] == name]
    if not inv:
        await c.answer("Карта не найдена", show_alert=True)
        return
    rar = inv[0]["rarity"]
    price = sell_price(uid, rar)
    del_card(uid, name)
    add_bal(uid, price)
    await bump(uid, "sold", 1, c.message)
    if rar == "legendary":
        add_rep(uid, RP_LEG)
    prog_quest(uid, "sell", 1)
    await c.answer("Продано за " + str(price), show_alert=True)
    rest = [r for r in get_inv(uid) if r["card_name"] == name]
    if rest:
        await render_card(c.message, uid, name)
    else:
        await show_coll(uid, c.message)

@dp.callback_query(F.data == "collect")
async def cb_collect(c: CallbackQuery):
    await do_collect(c.from_user.id, c.message)
    await c.answer()

@dp.callback_query(F.data.startswith("case:"))
async def cb_case(c: CallbackQuery):
    key = c.data.split(":")[1]
    await open_case(c.from_user.id, c.message, key, c.from_user.username)
    await c.answer()

@dp.callback_query(F.data == "games")
async def cb_games(c: CallbackQuery):
    await c.message.answer("Игры:", reply_markup=games_menu())
    await c.answer()

@dp.callback_query(F.data.startswith("h:"))
async def cb_help(c: CallbackQuery):
    k = c.data.split(":")[1]
    if k == "duel":
        t = "Дуэли. Ответь на сообщение: /duel 100"
    elif k == "roul":
        t = "Рулетка: /roulette 100 red"
    else:
        t = "Кости: /dice 100"
    await c.message.answer(t)
    await c.answer()

@dp.callback_query(F.data == "market")
async def cb_market(c: CallbackQuery):
    await c.message.answer("Рынок:", reply_markup=market_menu())
    await c.answer()

@dp.callback_query(F.data == "mkt_browse")
async def cb_mkt_browse(c: CallbackQuery):
    clean_market()
    lots = get_lots(10)
    if not lots:
        await c.answer("Пока лотов нет", show_alert=True)
        return
    await c.message.answer("Витрина:", reply_markup=mkt_browse_menu(lots))
    await c.answer()

@dp.callback_query(F.data == "mkt_my")
async def cb_mkt_my(c: CallbackQuery):
    await show_my_lots(c.message, c.from_user.id)
    await c.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def cb_buy(c: CallbackQuery):
    uid = c.from_user.id
    lot_id = int(c.data.split(":")[1])
    ok, res = buy_lot(uid, lot_id)
    if ok:
        await c.answer("Куплено: " + res, show_alert=True)
    else:
        await c.answer(res, show_alert=True)

@dp.callback_query(F.data == "collections")
async def cb_colls(c: CallbackQuery):
    await c.message.answer("Коллекции:", reply_markup=colls_menu(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data.startswith("cs:"))
async def cb_cs(c: CallbackQuery):
    rar = c.data.split(":")[1]
    uid = c.from_user.id
    info = COLLECTIONS[rar]
    o, t = coll_status(uid, rar)
    inv = get_inv(uid)
    owned = set(r["card_name"] for r in inv if r["rarity"] == rar)
    lines = [info["name"]]
    lines.append("Прогресс: " + str(o) + "/" + str(t))
    lines.append("Награда: " + str(info["reward"]))
    lines.append("")
    for cd in CARDS[rar]:
        mark = "[x]" if cd[0] in owned else "[ ]"
        lines.append(mark + " " + cd[1] + " " + cd[0])
    a = get_ach(uid)
    if a.get("coll_" + rar):
        lines.append("")
        lines.append("Коллекция собрана!")
    elif o >= t:
        lines.append("")
        lines.append("Награда готова!")
    rows = []
    if o >= t and not a.get("coll_" + rar):
        t2 = "Забрать " + str(info["reward"])
        rows.append([InlineKeyboardButton(text=t2, callback_data="cc:" + rar)])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="collections")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    try:
        await c.message.edit_text("\n".join(lines), reply_markup=kb)
    except Exception:
        await c.message.answer("\n".join(lines), reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("cc:"))
async def cb_cc(c: CallbackQuery):
    rar = c.data.split(":")[1]
    rew = claim_coll(c.from_user.id, rar)
    if rew:
        await c.answer("+" + str(rew), show_alert=True)
    else:
        await c.answer("Уже получено или не собрано", show_alert=True)

@dp.callback_query(F.data == "admin")
async def cb_admin(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Только для владельца", show_alert=True)
        return
    await c.message.answer("Админ-панель", reply_markup=admin_menu())
    await c.answer()

@dp.callback_query(F.data == "a:stats")
async def cb_a_stats(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM inventory")
    cards = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM market")
    lots = cur.fetchone()[0]
    cur.execute("SELECT SUM(balance) FROM users")
    tb = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM bans WHERE until > ?",
                (datetime.now().isoformat(),))
    bans = cur.fetchone()[0]
    lines = ["Статистика:"]
    lines.append("Игроков: " + str(users))
    lines.append("Карт: " + str(cards))
    lines.append("Лотов: " + str(lots))
    lines.append("Монет: " + str(tb))
    lines.append("Забанено: " + str(bans))
    ev = active_events()
    lines.append("Ивенты: " + (", ".join(ev) if ev else "нет"))
    await c.message.answer("\n".join(lines))
    await c.answer()

@dp.callback_query(F.data == "a:bc")
async def cb_a_bc(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "bc"
    await c.message.answer("Отправь текст рассылки")
    await c.answer()

@dp.callback_query(F.data == "a:coins")
async def cb_a_coins(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "coins"
    await c.message.answer("Формат: USER_ID СУММА")
    await c.answer()

@dp.callback_query(F.data == "a:card")
async def cb_a_card(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "card"
    await c.message.answer("Формат: USER_ID ИмяКарты")
    await c.answer()

@dp.callback_query(F.data == "a:promo")
async def cb_a_promo(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "promo"
    await c.message.answer("Формат: КОД НАГРАДА ИСПОЛЬЗОВАНИЙ")
    await c.answer()

@dp.callback_query(F.data == "a:event")
async def cb_a_event(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="x2 монеты", callback_data="ae:x2_money")],
        [InlineKeyboardButton(text="x2 XP", callback_data="ae:x2_xp")],
        [InlineKeyboardButton(text="x2 RP", callback_data="ae:x2_rep")],
        [InlineKeyboardButton(text="Отключить", callback_data="ae:off")],
    ])
    await c.message.answer("Ивент на 24 часа:", reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("ae:"))
async def cb_ae(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    ev = c.data.split(":")[1]
    if ev == "off":
        cur.execute("DELETE FROM events")
        conn.commit()
        await c.answer("Ивенты отключены", show_alert=True)
        return
    set_event(ev, 24)
    await c.answer(ev + " на 24ч", show_alert=True)

@dp.callback_query(F.data == "a:ban")
async def cb_a_ban(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "ban"
    await c.message.answer("Формат: USER_ID ЧАСЫ")
    await c.answer()

@dp.callback_query(F.data == "a:unban")
async def cb_a_unban(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "unban"
    await c.message.answer("USER_ID для разбана")
    await c.answer()

@dp.callback_query(F.data.startswith("mkh:"))
async def cb_mkh(c: CallbackQuery):
    name = c.data.split(":", 1)[1]
    t = "Чтобы выставить " + name + " на рынок:"
    t += "\n\n/sell_market " + name + " 500"
    await c.message.answer(t)
    await c.answer()

@dp.message(F.text == "📦 Кейсы")
async def rb_cases(m: Message):
    await m.answer("Выбери кейс:", reply_markup=cases_menu())

@dp.message(F.text == "🎒 Коллекция")
async def rb_inv(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    await show_coll(m.from_user.id, m)

@dp.message(F.text == "💰 Баланс")
async def rb_bal(m: Message):
    u = get_user(m.from_user.id, m.from_user.username)
    lines = ["Баланс: " + str(u["balance"])]
    lines.append("Уровень: " + str(u["level"]))
    lines.append("XP: " + str(u["xp"]) + "/" + str(xp_need(u["level"])))
    lines.append("Репутация: " + str(u["reputation"]))
    lines.append("Звание: " + rank_for(u["reputation"]))
    await m.answer("\n".join(lines))

@dp.message(F.text == "💱 Продать")
async def rb_sell(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    menu = sell_menu(m.from_user.id)
    if not menu:
        await m.answer("Нечего продавать")
        return
    await m.answer("Выбери карту:", reply_markup=menu)

@dp.message(F.text == "💵 Собрать")
async def rb_collect(m: Message):
    await do_collect(m.from_user.id, m)

@dp.message(F.text == "📅 Бонус")
async def rb_daily(m: Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username)
    if u["last_daily"]:
        d = datetime.now() - datetime.fromisoformat(u["last_daily"])
        if d < timedelta(hours=DAILY_CD):
            left = timedelta(hours=DAILY_CD) - d
            await m.answer("Через " + fmt_time(left))
            return
        streak = u["daily_streak"] + 1 if d < timedelta(hours=48) else 1
    else:
        streak = 1
    bonus = int(random.randint(300, 700) * (1 + (streak - 1) * 0.1))
    add_bal(uid, bonus)
    upd(uid, last_daily=datetime.now().isoformat(), daily_streak=streak)
    await m.answer("Бонус: +" + str(bonus) + " Streak: " + str(streak))

@dp.message(F.text == "🎮 Игры")
async def rb_games(m: Message):
    await m.answer("Игры:", reply_markup=games_menu())

@dp.message(F.text == "🏪 Рынок")
async def rb_market(m: Message):
    await m.answer("Рынок:", reply_markup=market_menu())

@dp.message(F.text == "📚 Коллекции")
async def rb_colls(m: Message):
    await m.answer("Коллекции:", reply_markup=colls_menu(m.from_user.id))

@dp.message(F.text == "🏆 Топ")
async def rb_top(m: Message):
    await show_top(m)

@dp.message(F.text == "🎖 Репутация")
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
    await show_ach(m.from_user.id, m)

@dp.message(F.text == "⚒ Крафт")
async def rb_craft(m: Message):
    menu = craft_menu(m.from_user.id)
    if not menu:
        await m.answer("Нужно 3 карты одной редкости")
        return
    await m.answer("Что крафтим?", reply_markup=menu)

@dp.message(F.text == "❓ Помощь")
async def rb_help(m: Message):
    lines = ["Помощь:"]
    lines.append("Кейсы, Коллекция, Продажа - кнопки меню")
    lines.append("Игры:")
    lines.append("/duel 100 - ответить на сообщение")
    lines.append("/roulette 100 red")
    lines.append("/dice 100")
    lines.append("Рынок:")
    lines.append("/sell_market Имя Цена")
    lines.append("/market - витрина")
    lines.append("/my_lots - мои лоты")
    lines.append("Прочее:")
    lines.append("/find ИМЯ - поиск карты")
    lines.append("/history - последние карты")
    lines.append("/promo КОД")
    lines.append("/claim - забрать награды")
    await m.answer("\n".join(lines))

@dp.message(F.text == "👑 Админ-панель")
async def rb_admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("Только для владельца")
        return
    await m.answer("Админ-панель", reply_markup=admin_menu())

@dp.message()
async def fallback(m: Message):
    uid = m.from_user.id
    if uid not in pending:
        return
    if not is_admin(uid):
        pending.pop(uid, None)
        return
    if not m.text:
        return
    act = pending.pop(uid)
    text = m.text.strip()
    if act == "bc":
        cur.execute("SELECT user_id FROM users")
        users = [r["user_id"] for r in cur.fetchall()]
        ok = 0
        fail = 0
        for u in users:
            try:
                await bot.send_message(u, text)
                ok += 1
            except Exception:
                fail += 1
            await asyncio.sleep(0.05)
        await m.answer("Доставлено: " + str(ok) + " ошибок: " + str(fail))
    elif act == "coins":
        parts = text.split()
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            await m.answer("Формат: USER_ID СУММА")
            return
        t = int(parts[0])
        amt = int(parts[1])
        add_bal(t, amt)
        await m.answer("Выдано " + str(amt) + " юзеру " + str(t))
        try:
            await bot.send_message(t, "Владелец выдал +" + str(amt))
        except Exception:
            pass
    elif act == "card":
        parts = text.rsplit(" ", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            await m.answer("Формат: USER_ID ИмяКарты")
            return
        t = int(parts[0])
        name = parts[1]
        rar, cd = find_card(name)
        if not cd:
            await m.answer("Карта не найдена")
            return
        add_card(t, name, rar, "admin")
        await m.answer("Выдана " + cd[1] + " " + name)
        try:
            await bot.send_message(t, "Владелец выдал карту: " + cd[1] + " " + name)
        except Exception:
            pass
    elif act == "promo":
        parts = text.split()
        if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
            await m.answer("Формат: КОД НАГРАДА ИСПОЛЬЗОВАНИЙ")
            return
        if add_promo(parts[0], int(parts[1]), int(parts[2])):
            await m.answer("Промокод " + parts[0] + " создан")
        else:
            await m.answer("Такой код уже есть")
    elif act == "ban":
        parts = text.split()
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            await m.answer("Формат: USER_ID ЧАСЫ")
            return
        ban_user(int(parts[0]), int(parts[1]))
        await m.answer("Забанен " + parts[0] + " на " + parts[1] + "ч")
    elif act == "unban":
        if not text.isdigit():
            await m.answer("USER_ID должен быть числом")
            return
        unban_user(int(text))
        await m.answer("Разбанен " + text)

async def open_case(uid, message, case_key, username=""):
    case = CASES[case_key]
    u = get_user(uid, username)
    if u["balance"] < case["price"]:
        t = "Нужно " + str(case["price"])
        t += " у тебя " + str(u["balance"])
        await message.answer(t)
        return
    add_bal(uid, -case["price"])
    boosters = get_boosters(uid)
    msg = await message.answer(case["emoji"] + " Открываем...")
    await asyncio.sleep(1)
    await msg.edit_text(case["emoji"] + " Открываем... x")
    await asyncio.sleep(1)
    await msg.edit_text(case["emoji"] + " Открываем... xx")
    await asyncio.sleep(1)
    if boosters.get("guaranteed_rare"):
        rar = random.choices(["rare", "epic", "legendary"],
                             weights=[70, 25, 5], k=1)[0]
        card = random.choice(CARDS[rar])
        boosters.pop("guaranteed_rare")
    else:
        rar, card = roll_card(case_key)
    set_boosters(uid, boosters)
    add_card(uid, card[0], rar, "case")
    add_rep(uid, RP_CASE)
    await give_xp(uid, XP_PER_CASE)
    prog_quest(uid, "case", 1)
    await bump(uid, "cases", 1)
    if rar == "legendary":
        await bump(uid, "legendary", 1)
    new_u = get_user(uid)
    lines = ["Выпала карта!", ""]
    e = RARITIES[rar]["e"]
    lines.append(e + " " + card[1] + " " + card[0])
    lines.append("Редкость: " + RARITIES[rar]["name"])
    lines.append("")
    lines.append(card[2])
    lines.append("")
    lines.append("Баланс: " + str(new_u["balance"]))
    lines.append("XP: " + str(new_u["xp"]) + "/" + str(xp_need(new_u["level"])))
    lines.append("RP: +" + str(RP_CASE))
    try:
        await msg.delete()
    except Exception:
        pass
    await message.answer("\n".join(lines),
                         reply_markup=inline_menu(uid))
    await check_ach(uid, message)

async def do_collect(uid, message):
    u = get_user(uid)
    if not u["last_collect"]:
        upd(uid, last_collect=datetime.now().isoformat())
        rate = pas_rate(uid)
        await message.answer("Доход запущен. " + str(rate) + " в час")
        return
    last = datetime.fromisoformat(u["last_collect"])
    hours = (datetime.now() - last).total_seconds() / 3600
    if hours < COLLECT_CD:
        left = timedelta(hours=COLLECT_CD) - timedelta(hours=hours)
        await message.answer("Сбор через " + fmt_time(left))
        return
    hours = min(hours, 24)
    rate = pas_rate(uid)
    earned = int(rate * hours)
    if earned == 0:
        await message.answer("Нет карт")
        return
    add_bal(uid, earned)
    upd(uid, last_collect=datetime.now().isoformat())
    t = "Собрано +" + str(earned)
    t += " (" + str(rate) + "/час)"
    await message.answer(t)

async def show_coll(uid, message):
    menu = coll_menu(uid)
    if not menu:
        text = "Коллекция пуста"
        try:
            await message.edit_text(text)
        except Exception:
            await message.answer(text)
        return
    inv = get_inv(uid)
    rate = pas_rate(uid)
    lines = ["Коллекция"]
    lines.append("Карт: " + str(len(inv)))
    lines.append("Доход: " + str(rate) + "/час")
    lines.append("")
    lines.append("Нажми на карту:")
    try:
        await message.edit_text("\n".join(lines), reply_markup=menu)
    except Exception:
        await message.answer("\n".join(lines), reply_markup=menu)

async def render_card(message, uid, name):
    rar, cd = find_card(name)
    if not cd:
        return False
    inv = get_inv(uid)
    cnt = sum(1 for r in inv if r["card_name"] == name)
    if cnt == 0:
        return False
    price = sell_price(uid, rar)
    lines = [RARITIES[rar]["e"] + " " + cd[1] + " " + cd[0]]
    lines.append("")
    lines.append("Редкость: " + RARITIES[rar]["name"])
    lines.append("В коллекции: " + str(cnt))
    lines.append("Цена продажи: " + str(price))
    lines.append("Пассив: " + str(RARITIES[rar]["pas"]) + "/час")
    lines.append("")
    lines.append(cd[2])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продать за " + str(price),
                              callback_data="sell:" + name)],
        [InlineKeyboardButton(text="На рынок",
                              callback_data="mkh:" + name)],
        [InlineKeyboardButton(text="К коллекции", callback_data="inv")],
    ])
    text = "\n".join(lines)
    try:
        await message.edit_text(text, reply_markup=kb)
    except Exception:
        await message.answer(text, reply_markup=kb)
    return True

async def show_my_lots(message, uid):
    clean_market()
    lots = get_my_lots(uid)
    if not lots:
        await message.answer("Нет лотов")
        return
    lines = ["Мои лоты:"]
    for lot in lots:
        e = RARITIES[lot["rarity"]]["e"]
        lines.append(e + " " + lot["card_name"] + " - " + str(lot["price"]))
    await message.answer("\n".join(lines))

async def show_top(message):
    cur.execute("SELECT username,user_id,balance,level,reputation FROM users ORDER BY balance DESC LIMIT 10")
    rows = cur.fetchall()
    if not rows:
        await message.answer("Пусто")
        return
    lines = ["Топ-10:"]
    for i, r in enumerate(rows, 1):
        name = r["username"] or ("id" + str(r["user_id"]))
        rep = " RP" + str(r["reputation"]) if r["reputation"] else ""
        line = str(i) + ". " + name + " - " + str(r["balance"])
        line += " (ур." + str(r["level"]) + rep + ")"
        lines.append(line)
    await message.answer("\n".join(lines))

async def show_quests(message, uid):
    d = get_quests(uid)
    lines = ["Ежедневные:"]
    for qid, text, goal, rew, t in QUESTS:
        done = d.get(qid, 0)
        mark = "[x]" if done >= goal else "[ ]"
        line = mark + " " + text + " " + str(done) + "/" + str(goal)
        line += " +" + str(rew)
        lines.append(line)
    lines.append("")
    lines.append("/claim - забрать")
    await message.answer("\n".join(lines))

async def show_ach(uid, message):
    a = get_ach(uid)
    lines = ["Достижения:"]
    for aid, text, rew, key, thr in ACHIEVEMENTS:
        mark = "[x]" if a.get(aid) else "[ ]"
        line = mark + " " + text + " +" + str(rew)
        lines.append(line)
    await message.answer("\n".join(lines))

async def show_rep(uid, message):
    rp = get_rep(uid)
    sm = rep_sell_mult(rp)
    pm = rep_pas_mult(rp)
    nxt = (rp // RP_STEP + 1) * RP_STEP
    lines = ["Репутация: " + str(rp)]
    lines.append("Звание: " + rank_for(rp))
    lines.append("")
    lines.append("Продажа: +" + str(int((sm - 1) * 100)) + "%")
    lines.append("Пассив: +" + str(int((pm - 1) * 100)) + "%")
    lines.append("До бонуса: " + str(nxt - rp))
    await message.answer("\n".join(lines))

async def show_stats(uid, message):
    u = get_user(uid)
    c = get_cnt(uid)
    inv = get_inv(uid)
    uniq = len(set(r["card_name"] for r in inv))
    lines = ["Статистика"]
    lines.append("Ур. " + str(u["level"]) + " RP " + str(u["reputation"]))
    lines.append("Баланс: " + str(u["balance"]))
    lines.append("")
    lines.append("Кейсов: " + str(c.get("cases", 0)))
    lines.append("Продано: " + str(c.get("sold", 0)))
    lines.append("Побед в дуэлях: " + str(c.get("duel_wins", 0)))
    lines.append("Продано на рынке: " + str(c.get("market_sold", 0)))
    line = "Коллекция: " + str(len(inv))
    line += " уникальных: " + str(uniq)
    lines.append(line)
    await message.answer("\n".join(lines))

async def show_history(uid, message):
    rows = get_history(uid, 10)
    if not rows:
        await message.answer("История пуста")
        return
    src_map = {"case": "кейс", "craft": "крафт",
               "market_buy": "рынок", "market_return": "возврат",
               "duel": "дуэль", "admin": "админ"}
    lines = ["Последние 10 карт:"]
    for r in rows:
        e = RARITIES[r["rarity"]]["e"]
        s = src_map.get(r["source"], r["source"])
        lines.append(e + " " + r["card_name"] + " (" + s + ")")
    await message.answer("\n".join(lines))

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())