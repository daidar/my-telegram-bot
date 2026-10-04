import asyncio
import random
import sqlite3
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ====================== НАСТРОЙКИ ======================
BOT_TOKEN = "8918809137:AAEPzaMMiBwL8rHSGkHJsiIfwAmnKjF56ds"   # ← ЗАМЕНИ!
CASE_PRICE = 100
DAILY_BONUS_MIN = 300
DAILY_BONUS_MAX = 700
START_BALANCE = 1000
DAILY_COOLDOWN_HOURS = 24

# ====================== РЕДКОСТИ ======================
RARITIES = {
    "common":    {"name": "Обычная",      "emoji": "⚪️", "chance": 60, "sell": 30},
    "rare":      {"name": "Редкая",       "emoji": "🔵", "chance": 25, "sell": 120},
    "epic":      {"name": "Эпическая",    "emoji": "🟣", "chance": 12, "sell": 400},
    "legendary": {"name": "Легендарная",  "emoji": "🟡", "chance": 3,  "sell": 1500},
}

# ====================== КАРТЫ ======================
CARDS = {
    "common": [
        {"name": "Крестьянин",  "emoji": "🧑‍🌾", "desc": "Простой работяга с поля. Верит в лучшее."},
        {"name": "Стражник",    "emoji": "💂",   "desc": "Охраняет ворота уже 20 лет. Устал."},
        {"name": "Трактирщик",  "emoji": "🍺",   "desc": "Знает все сплетни королевства."},
        {"name": "Путник",      "emoji": "🎒",   "desc": "Идёт куда глаза глядят."},
    ],
    "rare": [
        {"name": "Рыцарь",      "emoji": "⚔️",   "desc": "Честный воин, служит своему лорду."},
        {"name": "Маг-ученик",  "emoji": "🔮",   "desc": "Ещё учится, но уже взрывает вещи."},
        {"name": "Лучница",     "emoji": "🏹",   "desc": "Попадает в яблоко с 300 шагов."},
    ],
    "epic": [
        {"name": "Архимаг",     "emoji": "🧙",   "desc": "Повелевает стихиями. Не любит шутки."},
        {"name": "Паладин",     "emoji": "🛡️",   "desc": "Свет ведёт его клинок."},
        {"name": "Ассасин",     "emoji": "🗡️",   "desc": "Никто не видел его лица."},
    ],
    "legendary": [
        {"name": "Дракон",      "emoji": "🐉",   "desc": "Древний владыка небес. Сжигает всё."},
        {"name": "Король-Лич",  "emoji": "💀",   "desc": "Смерть — лишь начало его пути."},
        {"name": "Титан",       "emoji": "🗿",   "desc": "Один удар — и горы дрожат."},
    ],
}

# ====================== БАЗА ДАННЫХ ======================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY,
    username  TEXT,
    balance   INTEGER DEFAULT 0,
    last_daily TEXT
);
CREATE TABLE IF NOT EXISTS inventory (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    card_name  TEXT,
    rarity     TEXT,
    obtained_at TEXT
);
""")
conn.commit()


def get_user(user_id: int, username: str = ""):
    create_user(user_id, username)
    cur.execute("SELECT user_id, username, balance, last_daily FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()


def create_user(user_id: int, username: str = ""):
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, ?)",
        (user_id, username or "", START_BALANCE),
    )
    conn.commit()


def add_balance(user_id: int, amount: int):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()


def add_card(user_id: int, card_name: str, rarity: str):
    cur.execute(
        "INSERT INTO inventory (user_id, card_name, rarity, obtained_at) VALUES (?, ?, ?, ?)",
        (user_id, card_name, rarity, datetime.now().isoformat()),
    )
    conn.commit()


def get_inventory(user_id: int):
    cur.execute("SELECT card_name, rarity FROM inventory WHERE user_id=? ORDER BY id DESC", (user_id,))
    return cur.fetchall()


def remove_card(user_id: int, card_name: str):
    cur.execute(
        "DELETE FROM inventory WHERE id = (SELECT id FROM inventory WHERE user_id=? AND card_name=? LIMIT 1)",
        (user_id, card_name),
    )
    conn.commit()


# ====================== ЛОГИКА ======================
def roll_card():
    rarities = list(RARITIES.keys())
    weights = [RARITIES[r]["chance"] for r in rarities]
    rarity = random.choices(rarities, weights=weights, k=1)[0]
    card = random.choice(CARDS[rarity])
    return rarity, card


def check_daily(user_id: int):
    row = get_user(user_id)
    if not row or not row[3]:
        return True, None
    last = datetime.fromisoformat(row[3])
    now = datetime.now()
    delta = now - last
    if delta >= timedelta(hours=DAILY_COOLDOWN_HOURS):
        return True, None
    remaining = timedelta(hours=DAILY_COOLDOWN_HOURS) - delta
    return False, remaining


def set_daily_now(user_id: int):
    cur.execute("UPDATE users SET last_daily=? WHERE user_id=?", (datetime.now().isoformat(), user_id))
    conn.commit()


def format_time(td: timedelta) -> str:
    total = int(td.total_seconds())
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}ч {m}м {s}с"


# ====================== КЛАВИАТУРЫ ======================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎁 Открыть кейс ({CASE_PRICE}💰)", callback_data="open_case")],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"),
        ],
        [InlineKeyboardButton(text="📅 Ежедневный бонус", callback_data="daily")],
    ])


def sell_menu(user_id: int):
    inv = get_inventory(user_id)
    if not inv:
        return None
    seen = {}
    for name, rar in inv:
        if name not in seen:
            seen[name] = {"rarity": rar, "count": 0}
        seen[name]["count"] += 1
    buttons = []
    for name, data in seen.items():
        rar = RARITIES[data["rarity"]]
        price = rar["sell"]
        buttons.append([InlineKeyboardButton(
            text=f"{rar['emoji']} {name} ×{data['count']} — {price}💰",
            callback_data=f"sell:{name}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ====================== БОТ ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    text = (
        "🎴 <b>Добро пожаловать в Кейс-Бота!</b>\n\n"
        "Открывай кейсы, собирай карты разной редкости и продавай их за монеты.\n\n"
        f"💰 Твой баланс: <b>{user[2]}</b>\n\n"
        "Используй меню ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    await message.answer(f"💰 Баланс: <b>{user[2]}</b>", parse_mode="HTML")


@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    get_user(message.from_user.id, message.from_user.username)
    ok, remaining = check_daily(message.from_user.id)
    if not ok:
        await message.answer(f"⏳ Бонус уже получен.\nСледующий через: <b>{format_time(remaining)}</b>", parse_mode="HTML")
        return
    bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
    add_balance(message.from_user.id, bonus)
    set_daily_now(message.from_user.id)
    await message.answer(f"🎉 Ты получил ежедневный бонус: <b>+{bonus}💰</b>", parse_mode="HTML")


@dp.message(Command("case"))
async def cmd_case(message: Message):
    await open_case(message.from_user.id, message)


@dp.message(Command("inventory"))
async def cmd_inventory(message: Message):
    get_user(message.from_user.id, message.from_user.username)
    await show_inventory(message.from_user.id, message)


@dp.message(Command("sell"))
async def cmd_sell(message: Message):
    get_user(message.from_user.id, message.from_user.username)
    menu = sell_menu(message.from_user.id)
    if not menu:
        await message.answer("🎒 У тебя нет карт для продажи.")
        return
    await message.answer("💱 Выбери карту для продажи:", reply_markup=menu)


@dp.callback_query(F.data == "open_case")
async def cb_open_case(call: CallbackQuery):
    await open_case(call.from_user.id, call.message, call.from_user.username)
    await call.answer()


@dp.callback_query(F.data == "balance")
async def cb_balance(call: CallbackQuery):
    user = get_user(call.from_user.id, call.from_user.username)
    await call.message.answer(f"💰 Баланс: <b>{user[2]}</b>", parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "daily")
async def cb_daily(call: CallbackQuery):
    get_user(call.from_user.id, call.from_user.username)
    ok, remaining = check_daily(call.from_user.id)
    if not ok:
        await call.answer(f"Через {format_time(remaining)}", show_alert=True)
        return
    bonus = random.randint(DAILY_BONUS_MIN, DAILY_BONUS_MAX)
    add_balance(call.from_user.id, bonus)
    set_daily_now(call.from_user.id)
    await call.message.answer(f"🎉 Ежедневный бонус: <b>+{bonus}💰</b>", parse_mode="HTML")
    await call.answer("Получено!")


@dp.callback_query(F.data == "inventory")
async def cb_inventory(call: CallbackQuery):
    get_user(call.from_user.id, call.from_user.username)
    await show_inventory(call.from_user.id, call.message)
    await call.answer()


@dp.callback_query(F.data == "back")
async def cb_back(call: CallbackQuery):
    await call.message.answer("Главное меню 👇", reply_markup=main_menu())
    await call.answer()


@dp.callback_query(F.data.startswith("sell:"))
async def cb_sell(call: CallbackQuery):
    get_user(call.from_user.id, call.from_user.username)
    card_name = call.data.split(":", 1)[1]
    inv = get_inventory(call.from_user.id)
    rarity = None
    for name, rar in inv:
        if name == card_name:
            rarity = rar
            break
    if not rarity:
        await call.answer("Карта не найдена", show_alert=True)
        return
    price = RARITIES[rarity]["sell"]
    remove_card(call.from_user.id, card_name)
    add_balance(call.from_user.id, price)
    await call.answer(f"Продано за {price}💰", show_alert=True)
    menu = sell_menu(call.from_user.id)
    if menu:
        try:
            await call.message.edit_reply_markup(reply_markup=menu)
        except Exception:
            pass
    else:
        try:
            await call.message.edit_text("🎒 Инвентарь пуст.")
        except Exception:
            pass


# ====================== ОБЩИЕ ФУНКЦИИ ======================
async def open_case(user_id: int, message: Message, username: str = ""):
    user = get_user(user_id, username)
    if user[2] < CASE_PRICE:
        await message.answer(f"❌ Недостаточно монет. Нужно {CASE_PRICE}💰, у тебя {user[2]}💰")
        return

    add_balance(user_id, -CASE_PRICE)
    msg = await message.answer("🎁 Открываем кейс...")
    await asyncio.sleep(1)
    await msg.edit_text("🎁 Открываем кейс... 🔄")
    await asyncio.sleep(1)
    await msg.edit_text("🎁 Открываем кейс... ✨")
    await asyncio.sleep(1)

    rarity, card = roll_card()
    rar_info = RARITIES[rarity]
    add_card(user_id, card["name"], rarity)
    new_user = get_user(user_id)

    text = (
        f"🎉 <b>Выпала карта!</b>\n\n"
        f"{rar_info['emoji']} <b>{card['emoji']} {card['name']}</b>\n"
        f"Редкость: <b>{rar_info['name']}</b>\n\n"
        f"📖 <i>{card['desc']}</i>\n\n"
        f"💰 Баланс: <b>{new_user[2]}</b>"
    )
    await msg.edit_text(text, parse_mode="HTML", reply_markup=main_menu())


async def show_inventory(user_id: int, message: Message):
    inv = get_inventory(user_id)
    if not inv:
        await message.answer("🎒 Инвентарь пуст. Открой кейс командой /case")
        return
    grouped = {}
    for name, rar in inv:
        grouped[(name, rar)] = grouped.get((name, rar), 0) + 1
    lines = [f"🎒 <b>Инвентарь</b> (всего: {len(inv)})\n"]
    order = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
    for (name, rar), count in sorted(grouped.items(), key=lambda x: order[x[0][1]]):
        info = RARITIES[rar]
        lines.append(f"{info['emoji']} <b>{name}</b> ×{count}  <i>({info['name']})</i>")
    lines.append("\n💱 /sell — продать карты")
    await message.answer("\n".join(lines), parse_mode="HTML")


# ====================== ЗАПУСК ======================
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())