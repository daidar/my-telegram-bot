import asyncio, random, sqlite3, os, json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8918809137:AAEPzaMMiBwL8rHSGkHJsiIfwAmnKjF56ds"
START_BALANCE = 1000
DAILY_COOLDOWN_HOURS = 24
XP_PER_CASE = 10

CASES = {
    "basic":   {"name": "Обычный", "emoji": "📦", "price": 100,
                "weights": {"common": 60, "rare": 25, "epic": 12, "legendary": 3}},
    "premium": {"name": "Премиум", "emoji": "🎁", "price": 500,
                "weights": {"common": 25, "rare": 40, "epic": 25, "legendary": 10}},
    "vip":     {"name": "VIP",     "emoji": "💎", "price": 2000,
                "weights": {"common": 0,  "rare": 30, "epic": 45, "legendary": 25}},
}

RARITIES = {
    "common":    {"name": "Обычная",     "emoji": "⚪️", "sell": 30},
    "rare":      {"name": "Редкая",      "emoji": "🔵", "sell": 120},
    "epic":      {"name": "Эпическая",   "emoji": "🟣", "sell": 400},
    "legendary": {"name": "Легендарная", "emoji": "🟡", "sell": 1500},
}

CARDS = {
    "common": [
        {"name": "Sky Rae", "emoji": "🌌", "desc": "Трек «Наследство» — хит 2025."},
        {"name": "Аня Пересильд", "emoji": "🎬", "desc": "Актриса и певица, новая звезда."},
        {"name": "Nextime", "emoji": "⏭️", "desc": "Новая волна поп-музыки."},
        {"name": "Baby Cute", "emoji": "🎀", "desc": "Хип-хоп набирает обороты."},
        {"name": "Hellovercavi", "emoji": "🔥", "desc": "Громкий новичок года."},
        {"name": "Темный Принц", "emoji": "🦇", "desc": "Мрачная эстетика, цепляет."},
        {"name": "Gera Amen", "emoji": "🎙️", "desc": "Быстро дошёл до заметной фигуры."},
        {"name": "mumble", "emoji": "🗣️", "desc": "Трэп и клауд на стыке."},
        {"name": "Tuborosho", "emoji": "🥁", "desc": "Саундклауд с пацанским вайбом."},
        {"name": "Размаха", "emoji": "💥", "desc": "Девушка в новом олдскуле."},
    ],
    "rare": [
        {"name": "VILLIAN", "emoji": "👑", "desc": "Главный фрешмен года."},
        {"name": "madk1d", "emoji": "🚀", "desc": "«КАТЮХА» и стремительный взлёт."},
        {"name": "whitek3d", "emoji": "💎", "desc": "15+ млн стримов."},
        {"name": "doza86", "emoji": "🎲", "desc": "Хлёсткие тексты и фиты."},
        {"name": "LILCAK3", "emoji": "🌶️", "desc": "Хит с madk1d."},
        {"name": "unki", "emoji": "🌀", "desc": "Новая волна андерграунда."},
        {"name": "luvdakash", "emoji": "💸", "desc": "Имя на слуху у новой сцены."},
        {"name": "euro91", "emoji": "🚗", "desc": "Участник Bouquet."},
        {"name": "fleurnothappy", "emoji": "🥀", "desc": "Меланхоличная новая волна."},
        {"name": "Словетский", "emoji": "📜", "desc": "Формирует новое звучание."},
    ],
    "epic": [
        {"name": "Toxi$", "emoji": "📱", "desc": "«Возьми телефон, детка»."},
        {"name": "Дора", "emoji": "🌸", "desc": "Подростковый поп-рок."},
        {"name": "ENZRO", "emoji": "🌙", "desc": "«Ты не бойся ночи» — гимн года."},
        {"name": "Big Baby Tape", "emoji": "📼", "desc": "Задаёт тренды в трэпе."},
        {"name": "Aarne", "emoji": "🎛️", "desc": "Продюсер главных хитов."},
        {"name": "Платина", "emoji": "✨", "desc": "Рэпер нового поколения."},
        {"name": "SALUKI", "emoji": "🐺", "desc": "Уважаемый представитель школы."},
        {"name": "Kizaru", "emoji": "🌊", "desc": "Стабильно в чартах."},
    ],
    "legendary": [
        {"name": "Macan", "emoji": "🏆", "desc": "Артист года, 800 млн стримов."},
        {"name": "Ваня Дмитриенко", "emoji": "⚡", "desc": "Прорыв года."},
        {"name": "Anna Asti", "emoji": "👸", "desc": "Самая прослушиваемая, 280 млн."},
        {"name": "Miyagi & Эндшпиль", "emoji": "🌴", "desc": "«I Got Love» — трек десятилетия."},
        {"name": "Баста", "emoji": "🎩", "desc": "Легенда сцены с 2016 года."},
        {"name": "ICEGERGERT", "emoji": "❄️", "desc": "Прорыв года, TikTok-вирус."},
        {"name": "FRIENDLY THUG 52 NGG", "emoji": "🏴", "desc": "Стабильно в топе чартов."},
        {"name": "Morgenshtern", "emoji": "🃏", "desc": "Скандальный экспериментатор."},
        {"name": "Джиган", "emoji": "💪", "desc": "Хиты живут годами."},
    ],
}

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
    boosters TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    card_name TEXT, rarity TEXT, obtained_at TEXT
);
""")
for col, typ in [("xp","INTEGER DEFAULT 0"),("level","INTEGER DEFAULT 1"),
                 ("daily_streak","INTEGER DEFAULT 0"),("quest_data","TEXT DEFAULT '{}'"),
                 ("quest_date","TEXT"),("boosters","TEXT DEFAULT '{}'")]:
    try: cur.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
    except sqlite3.OperationalError: pass
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
    cur.execute(f"UPDATE users SET {keys} WHERE user_id=?", (*kw.values(), uid))
    conn.commit()

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

# ====================== XP / УРОВНИ ======================
async def give_xp(uid, amount, message: Message = None):
    u = get_user(uid)
    new_xp = u["xp"] + amount
    new_lvl = u["level"]
    leveled = False
    while new_xp >= xp_needed(new_lvl):
        new_xp -= xp_needed(new_lvl)
        new_lvl += 1
        leveled = True
    upd(uid, xp=new_xp, level=new_lvl)
    if leveled and message:
        await message.answer(f"🎉 <b>Уровень {new_lvl}!</b> Продолжай в том же духе!",
                             parse_mode="HTML")

# ====================== КВЕСТЫ ======================
QUEST_TEMPLATES = [
    {"id": "case3",  "text": "Открой 3 кейса",  "goal": 3, "reward": 200, "type": "case"},
    {"id": "sell2",  "text": "Продай 2 карты",  "goal": 2, "reward": 100, "type": "sell"},
    {"id": "case5",  "text": "Открой 5 кейсов", "goal": 5, "reward": 400, "type": "case"},
]

def get_quests(uid):
    u = get_user(uid)
    today = datetime.now().date().isoformat()
    if u["quest_date"] != today:
        data = {q["id"]: 0 for q in QUEST_TEMPLATES}
        upd(uid, quest_date=today, quest_data=json.dumps(data))
        return data, False
    return json.loads(u["quest_data"] or "{}"), True

def progress_quest(uid, qtype, amount=1):
    data, _ = get_quests(uid)
    for q in QUEST_TEMPLATES:
        if q["type"] == qtype and data.get(q["id"], 0) < q["goal"]:
            data[q["id"]] = min(data[q["id"]] + amount, q["goal"])
    upd(uid, quest_data=json.dumps(data))

def claim_quests(uid):
    data, _ = get_quests(uid)
    total = 0
    for q in QUEST_TEMPLATES:
        if data.get(q["id"], 0) >= q["goal"]:
            total += q["reward"]
            data[q["id"]] = 0
    if total > 0:
        add_balance(uid, total)
        upd(uid, quest_data=json.dumps(data))
    return total

# ====================== БУСТЕРЫ ======================
def get_boosters(uid): return json.loads(get_user(uid)["boosters"] or "{}")
def set_boosters(uid, d): upd(uid, boosters=json.dumps(d))

# ====================== ХЕЛПЕРЫ ======================
def roll_card(case_key):
    w = CASES[case_key]["weights"]
    rar = random.choices(list(w.keys()), weights=list(w.values()), k=1)[0]
    return rar, random.choice(CARDS[rar])

def fmt_time(td):
    t = int(td.total_seconds()); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{h}ч {m}м {s}с"

# ====================== КЛАВИАТУРЫ ======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Кейсы", callback_data="cases")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
         InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="📅 Бонус", callback_data="daily"),
         InlineKeyboardButton(text="📋 Квесты", callback_data="quests")],
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

def craft_menu(uid):
    inv = get_inv(uid)
    counts = {}
    for row in inv:
        counts[row["card_name"]] = counts.get(row["card_name"], 0) + 1
    btns = []
    for rar_key in ["common", "rare", "epic"]:
        available = sum(1 for row in inv if row["rarity"] == rar_key)
        if available >= 3:
            rar_next = {"common": "rare", "rare": "epic", "epic": "legendary"}[rar_key]
            btns.append([InlineKeyboardButton(
                text=f"3× {RARITIES[rar_key]['name']} → 1× {RARITIES[rar_next]['name']}",
                callback_data=f"craft:{rar_key}")])
    btns.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns) if len(btns) > 1 else None

# ====================== ХЕНДЛЕРЫ ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(m: Message):
    u = get_user(m.from_user.id, m.from_user.username)
    await m.answer(
        f"🎴 <b>Добро пожаловать!</b>\n\n"
        f"💰 Баланс: <b>{u['balance']}</b>\n"
        f"⭐ Уровень: <b>{u['level']}</b> ({u['xp']}/{xp_needed(u['level'])} XP)",
        reply_markup=main_menu(), parse_mode="HTML")

@dp.message(Command("top"))
async def cmd_top(m: Message): await show_top(m)

@dp.message(Command("quests"))
async def cmd_quests(m: Message): await show_quests(m, m.from_user.id)

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
        f"⭐ Уровень: <b>{u['level']}</b> ({u['xp']}/{xp_needed(u['level'])})",
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
    # Streak logic
    if u["last_daily"]:
        delta = datetime.now() - datetime.fromisoformat(u["last_daily"])
        streak = u["daily_streak"] + 1 if delta < timedelta(hours=48) else 1
    else:
        streak = 1
    base = random.randint(300, 700)
    bonus = int(base * (1 + (streak - 1) * 0.1))
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

@dp.callback_query(F.data.startswith("craft:"))
async def cb_do_craft(c: CallbackQuery):
    uid = c.from_user.id
    src = c.data.split(":")[1]
    inv = [r for r in get_inv(uid) if r["rarity"] == src]
    if len(inv) < 3:
        await c.answer("Недостаточно карт", show_alert=True); return
    # Удаляем 3 случайные
    picked = random.sample(inv, 3)
    for row in picked:
        del_card(uid, row["card_name"])
    next_rar = {"common": "rare", "rare": "epic", "epic": "legendary"}[src]
    new_card = random.choice(CARDS[next_rar])
    add_card(uid, new_card["name"], next_rar)
    await c.message.answer(
        f"⚒️ Крафт успешен!\n\n{RARITIES[next_rar]['emoji']} <b>{new_card['emoji']} {new_card['name']}</b>\n"
        f"<i>{new_card['desc']}</i>", parse_mode="HTML")
    await c.answer("Готово!")

@dp.callback_query(F.data.startswith("case:"))
async def cb_case(c: CallbackQuery):
    await open_case(c.from_user.id, c.message, c.data.split(":")[1],
                   c.from_user.username); await c.answer()

# ====================== ОСНОВНЫЕ ФУНКЦИИ ======================
async def open_case(uid, message: Message, case_key: str, username=""):
    case = CASES[case_key]
    u = get_user(uid, username)
    if u["balance"] < case["price"]:
        await message.answer(f"❌ Нужно {case['price']}💰, у тебя {u['balance']}💰"); return

    add_balance(uid, -case["price"])
    boosters = get_boosters(uid)
    msg = await message.answer(f"{case['emoji']} Открываем...")
    await asyncio.sleep(1)
    await msg.edit_text(f"{case['emoji']} Открываем... 🔄")
    await asyncio.sleep(1)
    await msg.edit_text(f"{case['emoji']} Открываем... ✨")
    await asyncio.sleep(1)

    # Гарантия редкого бустера
    if boosters.get("guaranteed_rare"):
        rar = random.choices(["rare","epic","legendary"], weights=[70,25,5], k=1)[0]
        card = random.choice(CARDS[rar])
        boosters.pop("guaranteed_rare")
    else:
        rar, card = roll_card(case_key)
    set_boosters(uid, boosters)

    # x2 coins бустер
    if boosters.get("x2_coins"):
        add_balance(uid, case["price"])
        boosters.pop("x2_coins")
        set_boosters(uid, boosters)

    add_card(uid, card["name"], rar)
    await give_xp(uid, XP_PER_CASE)
    progress_quest(uid, "case", 1)
    new_u = get_user(uid)

    caption = (f"🎉 <b>Выпала карта!</b>\n\n"
               f"{RARITIES[rar]['emoji']} <b>{card['emoji']} {card['name']}</b>\n"
               f"Редкость: <b>{RARITIES[rar]['name']}</b>\n\n"
               f"📖 <i>{card['desc']}</i>\n\n"
               f"💰 Баланс: <b>{new_u['balance']}</b>\n"
               f"⭐ {new_u['xp']}/{xp_needed(new_u['level'])} XP")
    try: await msg.delete()
    except: pass
    await message.answer(caption, parse_mode="HTML", reply_markup=main_menu())

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
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_top(message: Message):
    cur.execute("SELECT username, user_id, balance, level FROM users ORDER BY balance DESC LIMIT 10")
    rows = cur.fetchall()
    if not rows:
        await message.answer("Пока пусто."); return
    lines = ["🏆 <b>Топ-10 по балансу:</b>\n"]
    for i, r in enumerate(rows, 1):
        name = r["username"] or f"id{r['user_id']}"
        lines.append(f"{i}. {name} — <b>{r['balance']}💰</b> (ур. {r['level']})")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_quests(message: Message, uid: int):
    data, _ = get_quests(uid)
    lines = ["📋 <b>Ежедневные задания:</b>\n"]
    for q in QUEST_TEMPLATES:
        done = data.get(q["id"], 0)
        mark = "✅" if done >= q["goal"] else "⏳"
        lines.append(f"{mark} {q['text']} — {done}/{q['goal']} (+{q['reward']}💰)")
    lines.append("\n💰 /claim — забрать награды за выполненные")
    await message.answer("\n".join(lines), parse_mode="HTML")

@dp.message(Command("claim"))
async def cmd_claim(m: Message):
    total = claim_quests(m.from_user.id)
    if total:
        await m.answer(f"🎁 Получено: <b>+{total}💰</b>", parse_mode="HTML")
    else:
        await m.answer("Нет выполненных квестов 🤷")

# ====================== ЗАПУСК ======================
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())