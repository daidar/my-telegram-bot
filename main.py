import asyncio, random, sqlite3, os, json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ====================== НАСТРОЙКИ ======================
BOT_TOKEN = "8918809137:AAEPzaMMiBwL8rHSGkHJsiIfwAmnKjF56ds"
START_BALANCE = 1000
DAILY_COOLDOWN_HOURS = 24
XP_PER_CASE = 10
COLLECT_COOLDOWN_HOURS = 1

# Репутация: за каждые RP_STEP репутации +2% к продаже и +5% к пассивному доходу
RP_STEP = 100
RP_PER_CASE = 1
RP_PER_LEGENDARY_SOLD = 5

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

# ====================== КАРТЫ ======================
CARDS = {
    "common": [
        {"name": "mumble", "emoji": "🗣️", "desc": "Трэп и клауд на стыке. Тихий голос, громкие биты."},
        {"name": "Размаха", "emoji": "💥", "desc": "Девушка в новом олдскуле. Голос, который не спутаешь."},
        {"name": "Tuborosho", "emoji": "🥁", "desc": "Саундклауд с пацанским вайбом. Начал с SoundCloud, выстрелил в TikTok."},
        {"name": "mapt0v", "emoji": "🗺️", "desc": "Меланхоличный рэп про любовь и потери. Молодой, но уже культовый."},
        {"name": "dope17", "emoji": "💊", "desc": "Воронежский фрешмен. Грустные мелодии, честные тексты."},
        {"name": "KRISTIEE", "emoji": "✨", "desc": "17-летний фрешмен из Москвы. Смелый поп-звук, яркие образы."},
        {"name": "Locked23", "emoji": "🔒", "desc": "Автор хитов «Мои глаза сияют» и «Татухи». Голос нового поколения."},
        {"name": "юпи", "emoji": "🎸", "desc": "Саундклауд-рэпер и продюсер. Поп-панк, гранж и подростковый бунт."},
        {"name": "euro91", "emoji": "🚗", "desc": "Участник объединения Bouquet. Танцевальный трэп и клубная эстетика."},
        {"name": "fleurnothappy", "emoji": "🥀", "desc": "Меланхоличная новая волна. Цветы, боль и красивые мелодии."},
    ],
    "rare": [
        {"name": "Тёмный Принц", "emoji": "🦇", "desc": "Самый загадочный саундклауд-фрешмен. Мрачные треды и мультижанровость."},
        {"name": "whitek3d", "emoji": "💎", "desc": "15+ млн стримов. Вирусные треки в TikTok и мощные релизы."},
        {"name": "Fortuna 812", "emoji": "🏴", "desc": "Автор хита «ParisLove». Тег archivecore стал квазижанром."},
        {"name": "madk1d", "emoji": "🚀", "desc": "Один из лидеров новой волны. Почти любой трек становится интернет-хитом."},
        {"name": "Урал Гайсин", "emoji": "🎹", "desc": "Продюсер и рэпер из Уфы. «Священная война» — гимн поколения."},
        {"name": "паранойя", "emoji": "🌀", "desc": "Мультижанровый исполнитель из Уфы. Эксперименты со звуком и подачей."},
        {"name": "Anonymous Ember", "emoji": "👤", "desc": "Тайный участник Russia Be Mad. Тёмная эстетика и фиты с Tuborosho."},
        {"name": "tewiq", "emoji": "🎯", "desc": "Автор хита «распять». Мрачный трэп с дисторшном и живыми клавишными."},
        {"name": "королевский XVII", "emoji": "⚔️", "desc": "Мрачный трэп с дисторшном и живой музыкой. Родом из Волгограда."},
        {"name": "KUDOKUSHI", "emoji": "🏯", "desc": "Легенда русского саундклауда. Участник Prescription Gang."},
    ],
    "epic": [
        {"name": "CODE80", "emoji": "👑", "desc": "Главный герой касты «любимые рэперы твоих любимых рэперов»."},
        {"name": "Sagath", "emoji": "⛓️", "desc": "Король хоррор-трэпа. Пулемётный речитатив и страшные сказки."},
        {"name": "Friendly Thug 52 NGG", "emoji": "🃏", "desc": "Один из самых востребованных исполнителей новой волны."},
        {"name": "ICEGERGERT", "emoji": "❄️", "desc": "Прорыв года. «Наследство» завирусилось в TikTok."},
        {"name": "Словетский", "emoji": "📜", "desc": "Один из тех, кто формирует новое звуейчание российской рэп-сцены."},
        {"name": "Aarne", "emoji": "🎛️", "desc": "Продюсер главных хитов новой волны. Создаёт звук для звёзд."},
        {"name": "LILCAK3", "emoji": "🌶️", "desc": "Хит с madk1d. Локальная звезда саундклауд-сцены."},
        {"name": "unki", "emoji": "🌪️", "desc": "Яркий представитель новшей волны андерграунд-рэпа."},
    ],
    "legendary": [
        {"name": "Miyagi & Эндшпиль", "emoji": "🌴", "desc": "«I Got Love» — трек десятилетия. Легенды, выросшие из саундклауда."},
        {"name": "Баста", "emoji": "🎩", "desc": "Легенда сцены. Прошёл путь от андерграунда до стадионов."},
        {"name": "Oxxxymiron", "emoji": "🏛️", "desc": "Горгород. Один из лучших текстовиков русского рэпа."},
        {"name": "Скриптонит", "emoji": "🦅", "desc": "Дом с нормальными явлениями. Голос нового поколения."},
        {"name": "Хаски", "emoji": "🐺", "desc": "Тёмный рэп, сложные тексты. Панелька и философия."},
        {"name": "Noize MC", "emoji": "🎸", "desc": "Рэп с гитарой и острым словом. Не боится говорить правду."},
        {"name": "FACE", "emoji": "🥀", "desc": "Грустный трэп и юность нулевых. Голос поколения Z."},
        {"name": "Элджей", "emoji": "🎧", "desc": "Sayonara, детка. Пионер российского трэпа."},
    ],
}

# Достижения: id, текст, награда, тип счётчика
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
]
ACHIEVEMENT_THRESHOLDS = {
    "first_case": 1, "first_legendary": 1, "cases_10": 10, "cases_100": 100,
    "sell_10": 10, "sell_100": 100, "level_10": 10, "level_25": 25, "rp_500": 500,
}

# Звания по репутации
RAN}KS = [
    (0,    { "🌱 Новичок"),
   typ (100, }")
 "🎤 Андерграунд"),
       (500,  "🔥 Легенда except саундклауда"),
    (2000, "👑 Икона сцены"),
]

def rank_for(rp):
    r = RANKS[0][1]
    for threshold, name in RANKS:
        if rp >= threshold:
            r = name
    return r

def xp_needed(level): return int(100 * (1.15 ** (level - 1)))

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
    last_collect TEXT
);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    card_name TEXT, rarity TEXT, obtained_at TEXT
);
""")
# На случай старой базы: добавляем колонки, если их нет
for col, typ in [("counters","TEXT DEFAULT '{}'"), ("achievements","TEXT DEFAULT '{}'"),
                 ("reputation","INTEGER DEFAULT 0"), ("last_collect","TEXT")]:
    try: cur.execute(f"ALTER TABLE users ADD COLUMN {col sqlite3.OperationalError: pass
conn.commit()

# ====================== ПОЛЬЗОВАТЕЛИ ======================
def create_user(uid, un=""):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?,?,?)",
                (uid, un or "", START_BALANCE)); conn.commit()

def get_user(uid, un=""):
    create_user(uid, un)
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def upd(uid, **kw):
    keys = ", ".join(f"{k}=?" for k in kw)
    cur.execute(f"UPDATE users SET {keys} WHERE user_id=?", (*kw.values(), uid)); conn.commit()

def add_balance(uid, amt):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid)); conn.commit()

def add_card(uid, name, rar):
    cur.execute("INSERT INTO inventory (user_id,card_name,rarity,obtained_at) VALUES (?,?,?,?)",
                (uid, name, rar, datetime.now().isoformat())); conn.commit()

def get_inv(uid):
    cur.execute("SELECT card_name,rarity FROM inventory WHERE user_id=? ORDER BY id DESC", (uid,))
    return cur.fetchall()

def del_card(uid, name):
    cur.execute("DELETE FROM inventory WHERE id=(SELECT id FROM inventory WHERE user_id=? AND card_name=? LIMIT 1)",
                (uid, name)); conn.commit()

def count_card(uid, name):
    cur.execute("SELECT COUNT(*) FROM inventory WHERE user_id=? AND card_name=?", (uid, name))
    return cur.fetchone()[0]

# ====================== РЕПУТАЦИЯ ======================
def get_rep(uid): return get_user(uid)["reputation"] or 0

def add_rep(uid, amount):
    cur.execute("UPDATE users SET reputation=reputation+? WHERE user_id=?", (amount, uid)); conn.commit()

def rep_sell_multiplier(rp): return 1 + 0.02 * (rp // RP_STEP)
def rep_passive_multiplier(rp): return 1 + 0.05 * (rp // RP_STEP)

# ====================== СЧЁТЧИКИ И АЧИВКИ ======================
def get_counters(uid): return json.loads(get_user(uid)["counters"] or "{}")
def get_achievements(uid): return json.loads(get_user(uid)["achievements"] or "{}")

async def bump_counter(uid, key, amount=1, message: Message = None):
    c = get_counters(uid)
    c[key] = c.get(key, 0) + amount
    upd(uid, counters=json.dumps(c))
    await check_achievements(uid, message)

async def check_achievements(uid, message: Message = None):
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
                await message.answer(f"🏅 <b>Достижение!</b>\n{a['text']}\n+{a['reward']}💰",
                                     parse_mode="HTML")
    return unlocked

# ====================== XP / УРОВНИ ======================
async def give_xp(uid, amount, message: Message = None):
    u = get_user(uid)
    new_xp = u["xp"] + amount
    new_lvl = u["level"]
    leveled = False
    while new_xp >= xp_needed(new_lvl):
        new_xp -= xp_needed(new_lvl); new_lvl += 1; leveled = True
    upd(uid, xp=new_xp, level=new_lvl)
    if leveled:
        if message:
            await message.answer(f"🎉 <b>Уровень {new_lvl}!</b> Продолжай!", parse_mode="HTML")
        c = get_counters(uid)
        c["level"] = new_lvl
        upd(uid, counters=json.dumps(c))
        await check_achievements(uid, message)

# ====================== КВЕСТЫ ======================
QUEST_TEMPLATES = [
    {"id": "case3", "text": "Открой 3 кейса", "goal": 3, "reward": 200, "type": "case"},
    {"id": "sell2", "text": "Продай 2 карты", "goal": 2, "reward": 100, "type": "sell"},
    {"id": "case5", "text": "Открой 5 кейсов","goal": 5, "reward": 400, "type": "case"},
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

# ====================== БУСТЕРЫ ======================
def get_boosters(uid): return json.loads(get_user(uid)["boosters"] or "{}")
def set_boosters(uid, d): upd(uid, boosters=json.dumps(d))

# ====================== ПАССИВНЫЙ ДОХОД ======================
def calc_passive_rate(uid):
    inv = get_inv(uid)
    base = sum(RARITIES[r["rarity"]]["passive"] for r in inv)
    return int(base * rep_passive_multiplier(get_rep(uid)))

# ====================== ХЕЛПЕРЫ ======================
def roll_card(case_key):
    w = CASES[case_key]["weights"]
    rar = random.choices(list(w.keys()), weights=list(w.values()), k=1)[0]
    return rar, random.choice(CARDS[rar])

def fmt_time(td):
    t = int(td.total_seconds()); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{h}ч {m}м {s}с"

def sell_price(uid, rar):
    base = RARITIES[rar]["sell"]
    return int(base * rep_sell_multiplier(get_rep(uid)))

# ====================== КЛАВИАТУРЫ ======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Кейсы", callback_data="cases")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="💱 Продать", callback_data="sell"),
         InlineKeyboardButton(text="💵 Собрать", callback_data="collect")],
        [InlineKeyboardButton(text="📅 Бонус", callback_data="daily"),
         InlineKeyboardButton(text="📋 Квесты", callback_data="quests")],
        [InlineKeyboardButton(text="🏅 Достижения", callback_data="ach"),
         InlineKeyboardButton(text="🎖️ Репутация", callback_data="rep")],
        [InlineKeyboardButton(text="🏆 Топ", callback_data="top"),
         InlineKeyboardButton(text="⚒️ Крафт", callback_data="craft")],
    ])

def cases_menu():
    btns = []
    for k, c in CASES.items():
        btns.append([InlineKeyboardButton(
            text=f"{c['emoji']} {c['name']} — {c['price']}💰", callback_data=f"case:{k}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def sell_menu(uid):
    inv = get_inv(uid)
    if not inv: return None
    seen = {}
    for row in inv:
        key = (row["card_name"], row["rarity"])
        seen[key] = seen.get(key, 0) " + 1
    order = {"legendary": 0rare, "epic": 1,", "rare": 2, "common":  "3}
    btns = []
    for (epname, rar), cnt in sorted(seen.items(), key=lambda x: order[x[0][1]]):
        price = sell_price(uid, rar)
        btns.append([InlineKeyboardButton(
            text=f"{RARITIES[rar]['emoji']} {name} ×{cnt} — {price}💰",
            callback_data=f"sell:{name}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def craft_menu(uid):
    inv = get_inv(uid)
    btns = []
    for rar_key in ["common",ic"]:
        available = sum(1 for row in inv if row["rarity"] == rar_key)
        if available >= 3:
            rar_next = {"common": "rare", "rare": "epic", "epic": "legendary"}[rar_key]
            btns.append([InlineKeyboardButton(
                text=f"3× {RARITIES[rar_key]['name']} → 1× {RARITIES[rar_next]['name']}",
                callback_data=f"craft:{rar_key}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns) if len(btns) > 1 else None

# ====================== БОТ ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(m: Message):
    u = get_user(m.from_user.id, m.from_user.username)
    await m.answer(
        f"🎴 <b>Добро пожаловать!</b>\n\n"
        f"💰 Баланс: <b>{u['balance']}</b>\n"
        f"⭐ Уровень: <b>{u['level']}</b> ({u['xp']}/{xp_needed(u['level'])} XP)\n"
        f"🎖️ Репутация: <b>{u['reputation']}</b> — {rank_for(u['reputation'])}",
        reply_markup=main_menu(), parse_mode="HTML")

@dp.message(Command("top"))
async def cmd_top(m: Message): await show_top(m)

@dp.message(Command("quests"))
async def cmd_quests(m: Message): await show_quests(m, m.from_user.id)

@dp.message(Command("claim"))
async def cmd_claim(m: Message):
    total = claim_quests(m.from_user.id)
    await m.answer(f"🎁 +{total}💰" if total else "Нет выполненных квестов 🤷")

@dp.message(Command("sell"))
async def cmd_sell(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    menu = sell_menu(m.from_user.id)
    if not menu:
        await m.answer("🎒 Нечего продавать."); return
    await m.answer("💱 Выбери карту:", reply_markup=menu)

@dp.message(Command("collect"))
async def cmd_collect(m: Message):
    await do_collect(m.from_user.id, m)

@dp.message(Command("rep"))
async def cmd_rep(m: Message):
    await show_rep(m.from_user.id, m)

@dp.callback_query(F.data == "back")
async def cb_back(c: CallbackQuery):
    await c.message.answer("Главное меню 👇", reply_markup=main_menu()); await c.answer()

@dp.callback_query(F.data == "cases")
async def cb_cases(c: CallbackQuery):
    await c.message.answer("Выбери кейс:", reply_markup=cases_menu()); await c.answer()

@dp.callback_query(F.data == "balance")
async def cb_bal(c: CallbackQuery):
    u = get_user(c.from_user.id, c.from_user.username)
    await c.message.answer(
        f"💰 Баланс: <b>{u['balance']}</b>\n"
        f"⭐ Уровень: <b>{u['level']}</b>\n"
        f"XP: {u['xp']}/{xp_needed(u['level'])}\n"
        f"🎖️ Репутация: <b>{u['reputation']}</b> — {rank_for(u['reputation'])}",
        parse_mode="HTML"); await c.answer()

@dp.callback_query(F.data == "inv")
async def cb_inv(c: CallbackQuery):
    await show_inv(c.from_user.id, c.message); await c.answer()

@dp.callback_query(F.data == "daily")
async def cb_daily(c: CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)
    if u["last_daily"]:
        delta = datetime.now() - datetime.fromisoformat(u["last_daily"])
        if delta < timedelta(hours=DAILY_COOLDOWN_HOURS):
            await c.answer(f"Через {fmt_time(timedelta(hours=DAILY_COOLDOWN_HOURS)-delta)}", show_alert=True)
            return
        streak = u["daily_streak"] + 1 if delta < timedelta(hours=48) else 1
    else:
        streak = 1
    bonus = int(random.randint(300, 700) * (1 + (streak - 1) * 0.1))
    add_balance(uid, bonus)
    upd(uid, last_daily=datetime.now().isoformat(), daily_streak=streak)
    await c.message.answer(f"🎉 Бонус: <b>+{bonus}💰</b>\n🔥 Streak: <b>{streak} дней</b>",
                           parse_mode="HTML"); await c.answer("Получено!")

@dp.callback_query(F.data == "quests")
async def cb_quests(c: CallbackQuery):
    await show_quests(c.message, c.from_user.id); await c.answer()

@dp.callback_query(F.data == "top")
async def cb_top(c: CallbackQuery):
    await show_top(c.message); await c.answer()

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
        await c.answer("🎒 Нечего продавать.", show_alert=True); return
    await c.message.answer("💱 Выбери карту:", reply_markup=menu); await c.answer()

@dp.callback_query(F.data.startswith("sell:"))
async def cb_sell(c: CallbackQuery):
    uid = c.from_user.id
    name = c.data.split(":", 1)[1]
    inv = [r for r in get_inv(uid) if r["card_name"] == name]
    if not inv:
        await c.answer("Карта не найдена", show_alert=True); return
    rar = inv[0]["rarity"]
    price = sell_price(uid, rar)
    del_card(uid, name); add_balance(uid, price)
    await bump_counter(uid, "sold", 1, c.message)
    if rar == "legendary":
        add_rep(uid, RP_PER_LEGENDARY_SOLD)
    progress_quest(uid, "sell", 1)
    await c.answer(f"✅ Продано за {price}💰", show_alert=True)
    menu = sell_menu(uid)
    if menu:
        try: await c.message.edit_reply_markup(reply_markup=menu)
        except: pass
    else:
        try: await c.message.edit_text("🎒 Инвентарь пуст.")
        except: pass

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
    uid = c.from_user.id
    src = c.data.split(":")[1]
    inv = [r for r in get_inv(uid) if r["rarity"] == src]
    if len(inv) < 3:
        await c.answer("Недостаточно карт", show_alert=True); return
    for row in random.sample(inv, 3): del_card(uid, row["card_name"])
    nxt = {"common":"rare","rare":"epic","epic":"legendary"}[src]
    card = random.choice(CARDS[nxt]); add_card(uid, card["name"], nxt)
    await c.message.answer(
        f"⚒️ Крафт успешен!\n\n{RARITIES[nxt]['emoji']} <b>{card['emoji']} {card['name']}</b>\n"
        f"<i>{card['desc']}</i>", parse_mode="HTML")
    await c.answer("Готово!")

@dp.callback_query(F.data.startswith("case:"))
async def cb_case(c: CallbackQuery):
    await open_case(c.from_user.id, c.message, c.data.split(":")[1], c.from_user.username)
    await c.answer()

# ====================== ФУНКЦИИ ======================
async def open_case(uid, message: Message, case_key: str, username=""):
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
        rar = random.choices(["rare","epic","legendary"], weights=[70,25,5], k=1)[0]
        card = random.choice(CARDS[rar]); boosters.pop("guaranteed_rare")
    else:
        rar, card = roll_card(case_key)
    set_boosters(uid, boosters)

    if boosters.get("x2_coins"):
        add_balance(uid, case["price"]); boosters.pop("x2_coins"); set_boosters(uid, boosters)

    add_card(uid, card["name"], rar)
    add_rep(uid, RP_PER_CASE)
    await give_xp(uid, XP_PER_CASE)
    progress_quest(uid, "case", 1)

    await bump_counter(uid, "cases", 1)
    if rar == "legendary":
        await bump_counter(uid, "legendary", 1)

    new_u = get_user(uid)
    caption = (f"🎉 <b>Выпала карта!</b>\n\n"
               f"{RARITIES[rar]['emoji']} <b>{card['emoji']} {card['name']}</b>\n"
               f"Редкость: <b>{RARITIES[rar]['name']}</b>\n\n"
               f"📖 <i>{card['desc']}</i>\n\n"
               f"💰 Баланс: <b>{new_u['balance']}</b>\n"
               f"⭐ {new_u['xp']}/{xp_needed(new_u['level'])} XP\n"
               f"🎖️ +{RP_PER_CASE} RP")
    try: await msg.delete()
    except: pass
    await message.answer(caption, parse_mode="HTML", reply_markup=main_menu())
    await check_achievements(uid, message)

async def do_collect(uid, message: Message):
    u = get_user(uid)
    if not u["last_collect"]:
        upd(uid, last_collect=datetime.now().isoformat())
        rate = calc_passive_rate(uid)
        await message.answer(
            f"💵 Пассивный доход запущен!\n"
            f"Твои карты приносят <b>{rate}💰/час</b>.\n"
            f"Возвращайся через час.", parse_mode="HTML")
        return
    last = datetime.fromisoformat(u["last_collect"])
    hours = (datetime.now() - last).total_seconds() / 3600
    if hours < COLLECT_COOLDOWN_HOURS:
        rem = timedelta(hours=COLLECT_COOLDOWN_HOURS) - timedelta(hours=hours)
        await message.answer(f"⏳ Следующий сбор через: <b>{fmt_time(rem)}</b>", parse_mode="HTML")
        return
    hours = min(hours, 24)
    rate = calc_passive_rate(uid)
    earned = int(rate * hours)
    if earned == 0:
        await message.answer("💸 У тебя нет карт — нечего собирать.")
        return
    add_balance(uid, earned)
    upd(uid, last_collect=datetime.now().isoformat())
    await message.answer(
        f"💵 <b>Собрано: +{earned}💰</b>\n"
        f"Ставка: {rate}💰/час\n"
        f"Прошло: {hours:.1f} ч", parse_mode="HTML")

async def show_inv(uid, message: Message):
    inv = get_inv(uid)
    if not inv:
        await message.answer("🎒 Инвентарь пуст."); return
    grouped = {}
    for r in inv:
        key = (r["card_name"], r["rarity"])
        grouped[key] = grouped.get(key, 0) + 1
    lines = [f"🎒 <b>Инвентарь</b> ({len(inv)})\n"]
    order = {"legendary":0, "epic":1, "rare":2, "common":3}
    for (name, rar), cnt in sorted(grouped.items(), key=lambda x: order[x[0][1]]):
        lines.append(f"{RARITIES[rar]['emoji']} <b>{name}</b> ×{cnt}")
    rate = calc_passive_rate(uid)
    lines.append(f"\n💵 Доход: <b>{rate}💰/час</b>")
    lines.append("💱 /sell — продать карты")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_top(message: Message):
    cur.execute("SELECT username, user_id, balance, level, reputation FROM users ORDER BY balance DESC LIMIT 10")
    rows = cur.fetchall()
    if not rows:
        await message.answer("Пока пусто."); return
    lines = ["🏆 <b>Топ-10 по балансу:</b>\n"]
    for i, r in enumerate(rows, 1):
        name = r["username"] or f"id{r['user_id']}"
        rep = f" 🎖️{r['reputation']}" if r["reputation"] else ""
        lines.append(f"{i}. {name} — <b>{r['balance']}💰</b> (ур. {r['level']}{rep})")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_quests(message: Message, uid: int):
    data = get_quests(uid)
    lines = ["📋 <b>Ежедневные задания:</b>\n"]
    for q in QUEST_TEMPLATES:
        done = data.get(q["id"], 0)
        mark = "✅" if done >= q["goal"] else "⏳"
        lines.append(f"{mark} {q['text']} — {done}/{q['goal']} (+{q['reward']}💰)")
    lines.append("\n💰 /claim — забрать награды")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_achievements(uid: int, message: Message):
    ach = get_achievements(uid)
    lines = ["🏅 <b>Достижения:</b>\n"]
    for a in ACHIEVEMENTS:
        mark = "✅" if ach.get(a["id"]) else "🔒"
        lines.append(f"{mark} {a['text']} (+{a['reward']}💰)")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_rep(uid: int, message: Message):
    rp = get_rep(uid)
    sell_mult = rep_sell_multiplier(rp)
    pass_mult = rep_passive_multiplier(rp)
    next_step = (rp // RP_STEP + 1) * RP_STEP
    lines = [
        f"🎖️ <b>Репутация:</b> {rp} RP",
        f"🏅 <b>Звание:</b> {rank_for(rp)}\n",
        f"💱 Бонус к продаже: <b>+{(sell_mult-1)*100:.0f}%</b>",
        f"💵 Бонус к пассиву: <b>+{(pass_mult-1)*100:.0f}%</b>\n",
        f"📈 До следующего бонуса: <b>{next_step - rp} RP</b>",
        f"(каждые {RP_STEP} RP дают +2% к продаже и +5% к доходу)\n",
        f"💡 +{RP_PER_CASE} RP за кейс",
        f"💡 +{RP_PER_LEGENDARY_SOLD} RP за продажу легендарки",
    ]
    await message.answer("\n".join(lines), parse_mode="HTML")

# ====================== ЗАПУСК ======================
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())