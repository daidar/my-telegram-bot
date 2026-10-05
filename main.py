import asyncio
import random
import sqlite3
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
)

BOT_TOKEN = "8918809137:AAEPzaMMiBwL8rHSGkHJsiIfwAmnKjF56ds"
OWNER_ID = 1010721326
START_BALANCE = 1000
DAILY_CD = 24
XP_PER_CASE = 10

CASES = {
    "basic": {"name": "Обычный", "emoji": "📦", "price": 100,
              "w": {"common": 65, "rare": 25, "epic": 9, "legendary": 1},
              "group": "main",
              "desc": "Классический кейс для новичков. Базовый набор артистов, отличный для начала коллекции."},
    "premium": {"name": "Премиум", "emoji": "🎁", "price": 500,
                "w": {"common": 30, "rare": 45, "epic": 20, "legendary": 5},
                "group": "main",
                "desc": "Кейс для опытных коллекционеров. Увеличенный шанс на редкие и эпические карты."},
    "vip": {"name": "VIP", "emoji": "💎", "price": 2000,
            "w": {"common": 0, "rare": 50, "epic": 35, "legendary": 15},
            "group": "main",
            "desc": "Элитный кейс. Никаких обычных карт — только редкие и выше. Высокий шанс на топ."},
    "shadow": {"name": "Теневой", "emoji": "🌑", "price": 250,
               "w": {"common": 55, "rare": 30, "epic": 13, "legendary": 2},
               "group": "other",
               "desc": "Тёмная сторона саундклауда. Мрачные артисты и низкие биты."},
    "neon": {"name": "Неон", "emoji": "💡", "price": 350,
             "w": {"common": 50, "rare": 35, "epic": 12, "legendary": 3},
             "group": "other",
             "desc": "Неоновый вайб. Яркие артисты новой волны и модный звук."},
    "dream": {"name": "Сон", "emoji": "💭", "price": 400,
              "w": {"common": 45, "rare": 38, "epic": 15, "legendary": 2},
              "group": "other",
              "desc": "Мечтательный кейс. Сны, меланхолия и красивые мелодии."},
    "nature": {"name": "Природа", "emoji": "🌿", "price": 450,
               "w": {"common": 45, "rare": 38, "epic": 15, "legendary": 2},
               "group": "other",
               "desc": "Природный вайб. Тёплые треки для уютных вечеров."},
    "ghost": {"name": "Призрак", "emoji": "👻", "price": 600,
              "w": {"common": 40, "rare": 40, "epic": 17, "legendary": 3},
              "group": "other",
              "desc": "Призрачный кейс. Тайные исполнители и загадочные звуки."},
    "cyber": {"name": "Кибер", "emoji": "🤖", "price": 700,
              "w": {"common": 35, "rare": 42, "epic": 20, "legendary": 3},
              "group": "other",
              "desc": "Кибер-кейс. Экспериментальный звук и цифровая эстетика."},
    "retro": {"name": "Ретро", "emoji": "📼", "price": 800,
              "w": {"common": 38, "rare": 38, "epic": 20, "legendary": 4},
              "group": "other",
              "desc": "Ретро-кейс. Олдскул и классика саундклауда."},
    "storm": {"name": "Шторм", "emoji": "🌩️", "price": 900,
              "w": {"common": 30, "rare": 42, "epic": 24, "legendary": 4},
              "group": "other",
              "desc": "Штормовой кейс. Мощные биты и агрессивная подача."},
    "gold": {"name": "Золото", "emoji": "🥇", "price": 1000,
             "w": {"common": 20, "rare": 42, "epic": 33, "legendary": 5},
             "group": "other",
             "desc": "Золотой кейс. Сбалансированное разнообразие и хороший шанс на эпик."},
    "frost": {"name": "Мороз", "emoji": "❄️", "price": 1100,
              "w": {"common": 25, "rare": 40, "epic": 30, "legendary": 5},
              "group": "other",
              "desc": "Ледяной кейс. Холодный звук и мрачная атмосфера."},
    "fire": {"name": "Огонь", "emoji": "🔥", "price": 1200,
             "w": {"common": 22, "rare": 38, "epic": 35, "legendary": 5},
             "group": "other",
             "desc": "Огненный кейс. Жаркие треки и мощная энергия."},
    "chaos": {"name": "Хаос", "emoji": "🌀", "price": 1300,
              "w": {"common": 15, "rare": 38, "epic": 40, "legendary": 7},
              "group": "other",
              "desc": "Хаос. Случайные карты, непредсказуемый результат."},
    "order": {"name": "Порядок", "emoji": "⚖️", "price": 1300,
              "w": {"common": 25, "rare": 45, "epic": 25, "legendary": 5},
              "group": "other",
              "desc": "Кейс порядка. Стабильный дроп и предсказуемые шансы."},
    "time": {"name": "Время", "emoji": "⏳", "price": 1400,
             "w": {"common": 18, "rare": 37, "epic": 38, "legendary": 7},
             "group": "other",
             "desc": "Кейс времени. От старых легенд до новых звёзд сцены."},
    "dragon": {"name": "Дракон", "emoji": "🐉", "price": 1500,
               "w": {"common": 10, "rare": 33, "epic": 45, "legendary": 12},
               "group": "other",
               "desc": "Драконий кейс. Мощные артисты и высокий шанс на эпик."},
    "angel": {"name": "Ангел", "emoji": "👼", "price": 1600,
              "w": {"common": 10, "rare": 33, "epic": 45, "legendary": 12},
              "group": "other",
              "desc": "Ангельский кейс. Светлые мелодии и талантливые артисты."},
    "demon": {"name": "Демон", "emoji": "😈", "price": 1600,
              "w": {"common": 10, "rare": 33, "epic": 45, "legendary": 12},
              "group": "other",
              "desc": "Демонический кейс. Тёмные тексты и мощный звук."},
    "space": {"name": "Космос", "emoji": "🚀", "price": 1800,
              "w": {"common": 0, "rare": 40, "epic": 42, "legendary": 18},
              "group": "other",
              "desc": "Космический кейс. Без обычных карт — только редкие и выше."},
    "legend": {"name": "Легенда", "emoji": "🏆", "price": 2500,
               "w": {"common": 0, "rare": 30, "epic": 48, "legendary": 22},
               "group": "other",
               "desc": "Легендарный кейс. Повышенный шанс на топ-карту."},
    "king": {"name": "Король", "emoji": "👑", "price": 3000,
             "w": {"common": 0, "rare": 25, "epic": 48, "legendary": 27},
             "group": "other",
             "desc": "Королевский кейс. Для тех, кто хочет только эпик и легенды."},
    "master": {"name": "Мастер", "emoji": "🎓", "price": 4000,
               "w": {"common": 0, "rare": 20, "epic": 45, "legendary": 35},
               "group": "other",
               "desc": "Мастерский кейс. Свыше 35% шанс на легендарку."},
    "god": {"name": "Бог", "emoji": "⚡", "price": 5000,
            "w": {"common": 0, "rare": 15, "epic": 45, "legendary": 40},
            "group": "other",
            "desc": "Божественный кейс. Максимальный шанс на легендарку — 40%."},
}

RARITIES = {
    "common": {"name": "Обычная", "e": "⚪️", "sell": 30},
    "rare": {"name": "Редкая", "e": "🔵", "sell": 120},
    "epic": {"name": "Эпическая", "e": "🟣", "sell": 400},
    "legendary": {"name": "Легендарная", "e": "🟡", "sell": 1500},
}

CARDS = {
    "common": [
        ("#вечныйкод", "🕯️", "Загадочный проект из андерграунда. Мрачный клауд и низкие биты. Никто не знает, кто стоит за проектом. Каждый трек — откровение."),
        ("qon", "🌑", "Тёмный звук и глубокие тексты. Молодой исполнитель новой волны. Работает в жанре трэп и клауд-рэп. Один из тех, кого стоит слушать в темноте."),
        ("fillhadro", "❄️", "Холодный саунд из Сибири. Меланхоличные треки о жизни. Голос с хрипотцой и морозной атмосферой. Настоящий андерграунд."),
        ("litk3d", "🔥", "Молодой фрешмен с огненной подачей. Экспериментальный звук и неожиданные ходы. Быстро набирает обороты в узких кругах."),
        ("3umph", "🌊", "Волна нового звука. Мягкие биты и лиричные тексты. Один из восходящих артистов саундклауд-сцены. Слушается на одном дыхании."),
        ("3goth2002", "🦇", "Готическая эстетика и тёмный трэп. Поют о боли и одиночестве. Культовый для узкого круга ценителей мрачного звука."),
        ("trepet", "💔", "Меланхоличный рэпер из тени. Грустные тексты о любви и потерях. Тихий, но цепляющий. Каждый трек — как личный дневник."),
        ("alredytrash", "🗑️", "Андерграунд с самоиронией. Экспериментальный звук и необычные тексты. Не боится быть другим и это подкупает."),
        ("shadex", "🌫️", "Туманный саунд и обволакивающие биты. Атмосферные треки для ночных прогулок. Один из самых недооценённых артистов волны."),
        ("молодой рубль", "💵", "Дерзкий фрешмен из Москвы. Простые тексты о деньгах и жизни. Молодой флоу и свежий звук. Растёт быстро."),
        ("sadfem", "🥀", "Меланхоличный проект. Нежные мелодии и печальные тексты. Для любителей погрустить под хорошую музыку. Тихий и искренний."),
        ("t1k", "⏰", "Быстрый и ритмичный рэп. Электронные биты и модный звук. Новое поколение сцены. Каждый трек — как секундная стрелка."),
        ("lxk3sh", "🎭", "Театральная подача и эксперименты со звуком. Яркие образы и необычные треки. Один из самых креативных молодых артистов."),
        ("void", "🌌", "Космический трэп и философские тексты. Поёт о пустоте и бесконечности. Для тех, кто любит подумать под музыку."),
        ("psycho", "🧠", "Мрачный рэпер с нестандартным подходом. Эксперименты с подачей и звуком. Настоящий андерграунд без компромиссов."),
        ("b3rlin", "🏙️", "Городской рэп о жизни в мегаполисе. Атмосферные биты и честные тексты. Берлин — это состояние души, а не место."),
        ("silent", "🤫", "Тихий и меланхоличный. Работает в жанре lo-fi рэпа. Для тех, кто ценит атмосферу больше громкости. Голос как шёпот."),
        ("lowk3y", "🔑", "Минималистичный звук и глубокие тексты. Новая волна саундклауд-рэпа. Ключ к пониманию современной сцены."),
        ("m1st", "🌫️", "Туманный и загадочный. Экспериментальный рэп с элементами эмбиента. Каждый трек — как путешествие в неизвестность."),
        ("02blade", "⚔️", "Острый флоу и дерзкие тексты. Молодой рэпер из андерграунда. Режет биты как лезвие."),
        ("vlone", "💠", "Модный фрешмен с характерным звуком. Работает на стыке рэпа и электроники. Один из самых стильных на сцене."),
        ("darkmoon", "🌑", "Ночной саунд и мрачные тексты. Для тех, кто слушает музыку в темноте. Луна — его главный вдохновитель."),
        ("fading", "🌠", "Исчезающий звук и меланхоличные мелодии. Атмосферный рэп нового поколения. Всё проходит — и это красиво."),
        ("wasted", "💀", "Мрачный и жёсткий. Тексты о жизни и потерях. Не для всех, но для тех, кто понимает."),
        ("Katanacss", "🗡️", "Дерзкий трэп и агрессивная подача. Каждый трек — удар. Не для слабонервных. Катана наготове."),
    ],
    "rare": [
        ("doza86", "🎲", "Автор хлёстких текстов и запоминающихся треков. Работает в жанре трэп и саундклауд-рэпа. Один из самых активных новых артистов сцены."),
        ("королевский XVII", "⚔️", "Мрачный трэп с дисторшном и живой музыкой. Родом из Волгограда. Культовый в узких кругах андерграунда. Каждый трек как маленькая трагедия."),
        ("unki", "🌪️", "Яркий представитель новейшей волны андерграунд-рэпа. Необычный звук и эксперименты с формой. Один из тех, кто задаёт новые тренды."),
        ("Tuborosho", "🥁", "Саундклауд с пацанским вайбом. Начал с SoundCloud, выстрелил в TikTok. Голос улиц и настоящий андерграунд. Один из самых узнаваемых в своём кругу."),
        ("Anonymous Ember", "👤", "Тайный участник Russia Be Mad. Тёмная эстетика и фиты с Tuborosho. Не показывают лицо и не дают интервью. Настоящая загадка сцены."),
        ("euro91", "🚗", "Участник объединения Bouquet. Танцевальный трэп и клубная эстетика. Молодой и дерзкий. Один из самых перспективных в объединении."),
        ("Fortuna 812", "🏴", "Автор хита ParisLove. Тег archivecore стал квазижанром. Культовый для знатоков андерграунда. Один из тех, кто формирует звук."),
        ("mumble", "🗣️", "Трэп и клауд на стыке. Тихий голос, громкие биты. Один из первых новой волны. Его звук узнаётся с первых секунд."),
        ("Размаха", "💥", "Девушка в новом олдскуле. Голос, который не спутаешь ни с кем. Поёт о жизни без прикрас. Одна из немногих в жанре."),
        ("dope17", "💊", "Воронежский фрешмен. Грустные мелодии, честные тексты. Голос поколения из регионов. Один из самых искренних артистов волны."),
        ("KRISTIEE", "✨", "17-летний фрешмен из Москвы. Смелый поп-звук, яркие образы. Растёт на глазах. Будущее сцены уже здесь."),
        ("Locked23", "🔒", "Автор хитов Татухи и Мои глаза сияют. Голос нового поколения. Лёгкие запоминающиеся мелодии. Один из самых мелодичных артистов."),
        ("юпи", "🎸", "Саундклауд-рэпер и продюсер. Поп-панк, гранж и подростковый бунт. Живой звук и настоящая энергия. Не вписывается в рамки."),
        ("fleurnothappy", "🥀", "Меланхоличная новая волна. Цветы, боль и красивые мелодии. Голос с надрывом. Каждый трек как письмо самому себе."),
        ("mapt0v", "🗺️", "Меланхоличный рэп про любовь и потери. Молодой, но уже культовый. Каждый трек как дневник. Карта его мира — у тебя в наушниках."),
        ("LILCAK3", "🌶️", "Хит с madk1d. Локальная звезда саундклауд-сцены. Растёт быстро и уверенно. Острый как перец."),
        ("Krvvv", "🩸", "Тёмный трэп из тени. Мрачные тексты о жизни. Голос как нож по стеклу. Один из самых атмосферных артистов андерграунда."),
        ("BUSHIDO ZHO", "🗡️", "Московский трэп с японской эстетикой. Дерзкие тексты и мощные биты. Один из лидеров андерграунда. Путь самурая в звуке."),
        ("ssshhhiiittt!", "🎤", "Лоу-фай и пост-панк из Питера. Поют о молодости и боли. Голос как отражение серых дней. Одна из самых нишевых групп волны."),
        ("CMH", "☁️", "Cloud-рэп и меланхолия. Мягкие биты и грустные тексты. Настоящий саундклауд-вайб. Для тихих вечеров."),
        ("BORIS", "🏴", "Мрачный трэп из Москвы. Тёмная эстетика и агрессия. Культовый для андерграунда. Один из тех, кого уважают все."),
        ("Shadow Priest", "🕯️", "Мрачный рэпер из тени. Тёмные тексты и загадочные биты. Для любителей андерграунда. Слушать в темноте."),
        ("Thrill Pill", "💊", "Пионер российского трэпа. Хиты 2017-2019. Знаковая фигура для целого поколения. Его звук повлиял на всю сцену."),
        ("LOVV66", "💔", "Романтичный рэп о девушках. Мягкие биты и искренние тексты. Культ у молодой аудитории. Каждая песня о любви."),
        ("Yung Trappa", "🔫", "Питерский трэп. Легендарный флоу. Повлиял на всю сцену. Один из тех, с кого началась новая волна."),
    ],
    "epic": [
        ("Friendly Thug 52 NGG", "🃏", "Один из самых востребованных исполнителей новой волны. Стабильно в топе чартов. Уникальный голос и стиль. Уважаем всеми."),
        ("ICEGERGERT", "❄️", "Прорыв года. Наследство завирусилось в TikTok. Мощный саунд и узнаваемый голос. Один из лидеров новой волны."),
        ("Словетский", "📜", "Один из тех, кто формирует новое звучание российской рэп-сцены. Уважаемый в андерграунде. Каждый трек как манифест."),
        ("Aarne", "🎛️", "Продюсер главных хитов новой волны. Создаёт звук для звёзд. Один из главных за кулисами сцены. Без него не было бы многих хитов."),
        ("madk1d", "🚀", "Один из лидеров новой волны. Почти любой трек становится интернет-хитом. Голос поколения. Каждый релиз ждут с нетерпением."),
        ("tewiq", "🎯", "Автор хита распять. Мрачный трэп с дисторшном и живыми клавишными. Тёмный и глубокий. Попадает точно в цель."),
        ("Тёмный Принц", "🦇", "Самый загадочный саундклауд-фрешмен. Мрачные треды и мультижанровость. Никто не знает его настоящего имени. Тёмная лошадка сцены."),
        ("whitek3d", "💎", "15+ млн стримов. Вирусные треки в TikTok и мощные релизы. Один из лидеров новой волны. Его звук узнаётся сразу."),
        ("Скрипп", "🎭", "Питерский рэпер. Мрачные тексты. Экспериментирует со звуком и формой. Один из самых интересных артистов андерграунда."),
        ("Кровосток", "🩸", "Легендарная группа. Шокирующие тексты. Культовые в андерграунде с 2000-х. Повлияли на всю российскую сцену."),
        ("Каста", "🏰", "Ростовская группа. Социальные тексты. Легенды российской сцены, на которых выросли многие. Классика жанра."),
        ("Хамиль", "🎩", "Участник Касты. Лиричный рэп. Голос с характером. Уважаем в среде уже больше 15 лет. Мастер слова."),
    ],
    "legendary": [
        ("CODE80", "👑", "Главный герой касты любимые рэперы твоих любимых рэперов. Легенда для прошаренных. Культовый андерграунд, который знают все, кто в теме."),
        ("Sagath", "⛓️", "Король хоррор-трэпа. Пулемётный речитатив и страшные сказки. Тёмный и мощный. Легенда для своего поколения слушателей."),
        ("KUDOKUSHI", "🏯", "Легенда русского саундклауда. Участник Prescription Gang. Западный звук в России. Один из тех, с кого всё началось."),
        ("GONE.Fludd", "🌊", "Питерский рэпер с уникальным звуком. Атмосферные треки. Культовый для целого поколения. Его звук невозможно спутать."),
        ("Boulevard Depo", "🥀", "Питерский рэпер. Меланхоличный трэп. Один из лидеров новой волны. Задал тренды на годы вперёд."),
        ("Mnogoznaal", "🎨", "Коми рэпер. Экспериментальный звук. Философские тексты. Один из главных новаторов сцены. Каждый альбом — событие."),
        ("i61", "📖", "Рэпер с философским подходом. Острые тексты. Культовый для знатоков андерграунда. Один из самых уважаемых в среде."),
        ("Jeembo", "🌌", "Мрачный рэпер. Экспериментальный звук. Уникальная подача и стиль. Один из тех, кто сформировал звук андерграунда."),
        ("Хаски", "🐺", "Тёмный рэп, сложные тексты. Панелька и философия. Культовый артист андерграунда. Один из главных голосов поколения."),
        ("Слава КПСС", "🎭", "Рэпер и баттл-исполнитель. Ироничные и умные тексты. Мастер слова. Один из самых уважаемых в российской рэп-игре."),
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
    ("craft_5", "Скрафти 5 карт", 500, "crafted", 5),
    ("craft_20", "Скрафти 20 карт", 2000, "crafted", 20),
]

def xp_need(lv):
    return int(100 * (1.15 ** (lv - 1)))

conn = sqlite3.connect("bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY, username TEXT,
  balance INTEGER DEFAULT 0, xp INTEGER DEFAULT 0,
  level INTEGER DEFAULT 1, last_daily TEXT,
  daily_streak INTEGER DEFAULT 0,
  quest_data TEXT DEFAULT '{}', quest_date TEXT,
  boosters TEXT DEFAULT '{}', counters TEXT DEFAULT '{}',
  achievements TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
  card_name TEXT, rarity TEXT, obtained_at TEXT
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
CREATE TABLE IF NOT EXISTS card_images (card_name TEXT PRIMARY KEY, file_id TEXT);
""")
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
    u = (datetime.now() + timedelta(hours=h)).isoformat()
    cur.execute("INSERT OR REPLACE INTO bans VALUES (?,?)", (uid, u))
    conn.commit()

def unban_user(uid):
    cur.execute("DELETE FROM bans WHERE user_id=?", (uid,))
    conn.commit()

def get_image(name):
    cur.execute("SELECT file_id FROM card_images WHERE card_name=?", (name,))
    r = cur.fetchone()
    return r["file_id"] if r else None

def set_image(name, file_id):
    cur.execute("INSERT OR REPLACE INTO card_images VALUES (?,?)", (name, file_id))
    conn.commit()

def del_image(name):
    cur.execute("DELETE FROM card_images WHERE card_name=?", (name,))
    conn.commit()

def images_count():
    cur.execute("SELECT COUNT(*) FROM card_images")
    return cur.fetchone()[0]

def create_user(uid, un=""):
    sql = "INSERT OR IGNORE INTO users (user_id,username,balance)"
    sql += " VALUES (?,?,?)"
    cur.execute(sql, (uid, un or "", START_BALANCE))
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
    sql = "UPDATE users SET balance=balance+? WHERE user_id=?"
    cur.execute(sql, (amt, uid))
    conn.commit()

def add_card(uid, name, rar, src="unknown"):
    now = datetime.now().isoformat()
    sql1 = "INSERT INTO inventory (user_id,card_name,rarity,obtained_at)"
    sql1 += " VALUES (?,?,?,?)"
    cur.execute(sql1, (uid, name, rar, now))
    sql2 = "INSERT INTO history (user_id,card_name,rarity,source,created_at)"
    sql2 += " VALUES (?,?,?,?,?)"
    cur.execute(sql2, (uid, name, rar, src, now))
    conn.commit()

def get_inv(uid):
    sql = "SELECT card_name,rarity FROM inventory WHERE user_id=?"
    sql += " ORDER BY id DESC"
    cur.execute(sql, (uid,))
    return cur.fetchall()

def del_card(uid, name):
    sub = "SELECT id FROM inventory WHERE user_id=? AND card_name=?"
    sub += " LIMIT 1"
    cur.execute("DELETE FROM inventory WHERE id=(" + sub + ")",
                (uid, name))
    conn.commit()

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
        if c.get(key, 0) >= thr:
            a[aid] = True
            add_bal(uid, rew)
            unlocked.append((text, rew))
    if unlocked:
        upd(uid, achievements=json.dumps(a))
        if msg:
            for text, rew in unlocked:
                t = "🏅 Достижение: " + text
                t += " (+" + str(rew) + "💰)"
                try:
                    await msg.answer(t)
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
                await msg.answer("🎉 Уровень " + str(lv) + "!")
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
    sql = "SELECT name FROM events WHERE expires > ?"
    cur.execute(sql, (datetime.now().isoformat(),))
    return [r["name"] for r in cur.fetchall()]

def add_promo(code, rew, uses):
    try:
        sql = "INSERT INTO promo VALUES (?,?,?,0)"
        cur.execute(sql, (code.upper(), rew, uses))
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
    sql = "SELECT 1 FROM promo_used WHERE user_id=? AND code=?"
    cur.execute(sql, (uid, code))
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
    sql = "SELECT * FROM history WHERE user_id=?"
    sql += " ORDER BY id DESC LIMIT ?"
    cur.execute(sql, (uid, limit))
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

def find_card(name):
    for rar in CARDS:
        for cd in CARDS[rar]:
            if cd[0] == name:
                return rar, cd
    return None, None

def reply_menu():
    rows = [[
        KeyboardButton(text="📦 Кейсы"),
        KeyboardButton(text="🎒 Коллекция"),
        KeyboardButton(text="💰 Баланс"),
    ]]
    return ReplyKeyboardMarkup(
        keyboard=rows, resize_keyboard=True, is_persistent=True)

def inline_menu(uid=None):
    rows = [
        [InlineKeyboardButton(text="📦 Кейсы",
                              callback_data="cases")],
        [InlineKeyboardButton(text="💰 Баланс",
                              callback_data="balance"),
         InlineKeyboardButton(text="🎒 Коллекция",
                              callback_data="inv")],
        [InlineKeyboardButton(text="📅 Бонус",
                              callback_data="daily"),
         InlineKeyboardButton(text="📋 Квесты",
                              callback_data="quests")],
        [InlineKeyboardButton(text="🏅 Достижения",
                              callback_data="ach"),
         InlineKeyboardButton(text="⚒️ Крафт",
                              callback_data="craft")],
        [InlineKeyboardButton(text="🏆 Топ",
                              callback_data="top")],
    ]
    if uid and is_admin(uid):
        rows.append([InlineKeyboardButton(
            text="👑 Админ", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def cases_menu():
    btns = []
    for k, c in CASES.items():
        if c["group"] != "main":
            continue
        t = c["emoji"] + " " + c["name"]
        t += " — " + str(c["price"]) + "💰"
        btns.append([InlineKeyboardButton(
            text=t, callback_data="case:" + k)])
    total_other = sum(1 for c in CASES.values()
                      if c["group"] == "other")
    t2 = "📂 Другие кейсы (" + str(total_other) + ")"
    btns.append([InlineKeyboardButton(
        text=t2, callback_data="cases_other")])
    btns.append([InlineKeyboardButton(
        text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def cases_other_menu():
    btns = []
    row = []
    for k, c in CASES.items():
        if c["group"] != "other":
            continue
        t = c["emoji"] + " " + c["name"]
        t += " — " + str(c["price"]) + "💰"
        row.append(InlineKeyboardButton(
            text=t, callback_data="case:" + k))
        if len(row) == 2:
            btns.append(row)
            row = []
    if row:
        btns.append(row)
    btns.append([InlineKeyboardButton(
        text="⬅️ Назад", callback_data="cases")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def case_info_menu(key):
    c = CASES[key]
    text = c["emoji"] + " <b>" + c["name"] + "</b>\n\n"
    text += c["desc"] + "\n\n"
    text += "💰 Цена за 1: <b>" + str(c["price"]) + "</b>\n\n"
    text += "<b>Шансы выпадения:</b>\n"
    for rk in ["legendary", "epic", "rare", "common"]:
        w = c["w"].get(rk, 0)
        if w > 0:
            text += RARITIES[rk]["e"] + " "
            text += RARITIES[rk]["name"]
            text += ": <b>" + str(w) + "%</b>\n"
    back = "cases_other" if c["group"] == "other" else "cases"
    p = c["price"]
    btns = [
        [InlineKeyboardButton(
            text="📦 Открыть 1 (" + str(p) + "💰)",
            callback_data="case_open:" + key + ":1")],
        [InlineKeyboardButton(
            text="📦 Открыть 3 (" + str(p*3) + "💰)",
            callback_data="case_open:" + key + ":3")],
        [InlineKeyboardButton(
            text="📦 Открыть 10 (" + str(p*10) + "💰)",
            callback_data="case_open:" + key + ":10")],
        [InlineKeyboardButton(
            text="⬅️ Назад", callback_data=back)],
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=btns)

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
        price = RARITIES[rar]["sell"]
        e = RARITIES[rar]["e"]
        t = e + " " + name + " ×" + str(cnt)
        t += " — " + str(price) + "💰"
        btns.append([InlineKeyboardButton(
            text=t, callback_data="sell:" + name)])
    btns.append([InlineKeyboardButton(
        text="⬅️ Назад", callback_data="back")])
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
        e = RARITIES[rar]["e"]
        t = e + " " + name + " ×" + str(cnt)
        btns.append([InlineKeyboardButton(
            text=t, callback_data="ci:" + name)])
    btns.append([InlineKeyboardButton(
        text="📚 Прогресс коллекций", callback_data="colls")])
    btns.append([InlineKeyboardButton(
        text="⚒️ Крафт", callback_data="craft")])
    btns.append([InlineKeyboardButton(
        text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def colls_menu(uid):
    btns = []
    for rar, info in COLLECTIONS.items():
        o, t = coll_status(uid, rar)
        e = RARITIES[rar]["e"]
        ach = get_ach(uid)
        mark = " ✅" if ach.get("coll_" + rar) else ""
        txt = e + " " + info["name"]
        txt += " " + str(o) + "/" + str(t) + mark
        btns.append([InlineKeyboardButton(
            text=txt, callback_data="cs:" + rar)])
    btns.append([InlineKeyboardButton(
        text="⬅️ Назад в коллекцию", callback_data="inv")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def craft_menu(uid):
    inv = get_inv(uid)
    btns = []
    for rk in ["common", "rare", "epic"]:
        avail = sum(1 for r in inv if r["rarity"] == rk)
        if avail >= 3:
            nxt = {"common": "rare", "rare": "epic",
                   "epic": "legendary"}[rk]
            t = "3× " + RARITIES[rk]["name"]
            t += " → 1× " + RARITIES[nxt]["name"]
            btns.append([InlineKeyboardButton(
                text=t, callback_data="craft:" + rk)])
    btns.append([InlineKeyboardButton(
        text="⬅️ Назад", callback_data="back")])
    if len(btns) > 1:
        return InlineKeyboardMarkup(inline_keyboard=btns)
    return None

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📊 Статистика", callback_data="a:stats")],
        [InlineKeyboardButton(
            text="📢 Рассылка", callback_data="a:bc")],
        [InlineKeyboardButton(
            text="🎁 Выдать монеты", callback_data="a:coins")],
        [InlineKeyboardButton(
            text="🎴 Выдать карту", callback_data="a:card")],
        [InlineKeyboardButton(
            text="📜 Промокод", callback_data="a:promo")],
        [InlineKeyboardButton(
            text="🎬 Ивент", callback_data="a:event")],
        [InlineKeyboardButton(
            text="🖼️ Фото карт", callback_data="a:img")],
        [InlineKeyboardButton(
            text="🚫 Бан", callback_data="a:ban")],
        [InlineKeyboardButton(
            text="✅ Разбан", callback_data="a:unban")],
        [InlineKeyboardButton(
            text="⬅️ Назад", callback_data="back")],
    ])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(m: Message):
    if is_banned(m.from_user.id):
        await m.answer("🚫 Ты забанен.")
        return
    u = get_user(m.from_user.id, m.from_user.username)
    lines = ["🎴 <b>Добро пожаловать!</b>", ""]
    lines.append("💰 Баланс: <b>" + str(u["balance"]) + "</b>")
    lines.append("⭐ Уровень: <b>" + str(u["level"]) + "</b>")
    lines.append("XP: " + str(u["xp"]))
    lines.append("/" + str(xp_need(u["level"])))
    for e in active_events():
        lines.append("🔥 Ивент: " + e)
    lines.append("")
    lines.append("👇 Кнопки внизу экрана")
    await m.answer("\n".join(lines),
                   reply_markup=reply_menu())

@dp.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("Меню:",
                   reply_markup=inline_menu(m.from_user.id))

@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("👑 Только для владельца")
        return
    await m.answer("👑 <b>Админ-панель</b>",
                   reply_markup=admin_menu())

@dp.message(Command("cancel"))
async def cmd_cancel(m: Message):
    pending.pop(m.from_user.id, None)
    await m.answer("Отменено")

@dp.message(Command("claim"))
async def cmd_claim(m: Message):
    t = claim_quests(m.from_user.id)
    if t:
        await m.answer("🎁 +" + str(t) + "💰")
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
        await m.answer("🎁 Промокод активирован! +"
                       + str(res) + "💰")
    else:
        await m.answer("❌ " + res)

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
        await m.answer("🔍 Не найдено")
        return
    grouped = {}
    for r in found:
        key = (r["card_name"], r["rarity"])
        grouped[key] = grouped.get(key, 0) + 1
    lines = ["🔍 <b>Найдено:</b>"]
    for key, cnt in grouped.items():
        name = key[0]
        rar = key[1]
        e = RARITIES[rar]["e"]
        lines.append(e + " " + name + " ×" + str(cnt))
    await m.answer("\n".join(lines))

@dp.message(Command("history"))
async def cmd_history(m: Message):
    await show_history(m.from_user.id, m)

@dp.message(Command("setimage"))
async def cmd_setimage(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("👑 Только для владельца")
        return
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.answer(
            "🖼️ Ответь командой /setimage ИмяАртиста "
            "на сообщение с фото.\n\n"
            "Пример: отправь боту фото madk1d, "
            "ответь на него <code>/setimage madk1d</code>",
            parse_mode="HTML")
        return
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Формат: /setimage ИмяАртиста")
        return
    name = parts[1].strip()
    rar, cd = find_card(name)
    if not cd:
        await m.answer("❌ Карта не найдена: " + name)
        return
    file_id = m.reply_to_message.photo[-1].file_id
    set_image(name, file_id)
    await m.answer("✅ Фото установлено: " + cd[1] + " " + name)

@dp.message(Command("delimage"))
async def cmd_delimage(m: Message):
    if not is_admin(m.from_user.id):
        return
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Формат: /delimage ИмяАртиста")
        return
    name = parts[1].strip()
    del_image(name)
    await m.answer("🗑️ Фото удалено: " + name)

@dp.callback_query(F.data == "back")
async def cb_back(c: CallbackQuery):
    await c.message.answer("Меню:",
                           reply_markup=inline_menu(c.from_user.id))
    await c.answer()

@dp.callback_query(F.data == "cases")
async def cb_cases(c: CallbackQuery):
    await c.message.answer("📦 Выбери кейс:",
                           reply_markup=cases_menu())
    await c.answer()

@dp.callback_query(F.data == "cases_other")
async def cb_cases_other(c: CallbackQuery):
    await c.message.answer("📂 Другие кейсы:",
                           reply_markup=cases_other_menu())
    await c.answer()

@dp.callback_query(F.data.startswith("case_open:"))
async def cb_case_open(c: CallbackQuery):
    parts = c.data.split(":")
    key = parts[1]
    count = int(parts[2])
    await open_case_multi(c.from_user.id, c.message, key, count,
                          c.from_user.username)
    await c.answer()

@dp.callback_query(F.data.startswith("case:"))
async def cb_case(c: CallbackQuery):
    key = c.data.split(":")[1]
    text, kb = case_info_menu(key)
    try:
        await c.message.edit_text(text, reply_markup=kb,
                                  parse_mode="HTML")
    except Exception:
        await c.message.answer(text, reply_markup=kb,
                               parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "balance")
async def cb_bal(c: CallbackQuery):
    u = get_user(c.from_user.id, c.from_user.username)
    lines = ["💰 Баланс: <b>" + str(u["balance"]) + "</b>"]
    lines.append("⭐ Уровень: <b>" + str(u["level"]) + "</b>")
    lines.append("XP: " + str(u["xp"]))
    lines.append("/" + str(xp_need(u["level"])))
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

@dp.callback_query(F.data == "colls")
async def cb_colls(c: CallbackQuery):
    uid = c.from_user.id
    kb = colls_menu(uid)
    try:
        await c.message.edit_text("📚 <b>Коллекции</b>",
                                  reply_markup=kb)
    except Exception:
        await c.message.answer("📚 <b>Коллекции</b>",
                               reply_markup=kb)
    await c.answer()

@dp.callback_query(F.data.startswith("cs:"))
async def cb_cs(c: CallbackQuery):
    rar = c.data.split(":")[1]
    uid = c.from_user.id
    info = COLLECTIONS[rar]
    o, t = coll_status(uid, rar)
    inv = get_inv(uid)
    owned = set(r["card_name"] for r in inv if r["rarity"] == rar)
    lines = [RARITIES[rar]["e"] + " <b>"
             + info["name"] + "</b>"]
    lines.append("Прогресс: <b>" + str(o) + "/" + str(t) + "</b>")
    lines.append("Награда: <b>" + str(info["reward"]) + "💰</b>")
    lines.append("")
    for cd in CARDS[rar]:
        mark = "✅" if cd[0] in owned else "⬜"
        lines.append(mark + " " + cd[1] + " " + cd[0])
    a = get_ach(uid)
    if a.get("coll_" + rar):
        lines.append("")
        lines.append("🏆 Коллекция собрана!")
    elif o >= t:
        lines.append("")
        lines.append("🎁 Награда готова!")
    rows = []
    if o >= t and not a.get("coll_" + rar):
        t2 = "🎁 Забрать " + str(info["reward"]) + "💰"
        rows.append([InlineKeyboardButton(
            text=t2, callback_data="cc:" + rar)])
    rows.append([InlineKeyboardButton(
        text="⬅️ Назад", callback_data="colls")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    text = "\n".join(lines)
    try:
        await c.message.edit_text(text, reply_markup=kb,
                                  parse_mode="HTML")
    except Exception:
        await c.message.answer(text, reply_markup=kb,
                               parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data.startswith("cc:"))
async def cb_cc(c: CallbackQuery):
    rar = c.data.split(":")[1]
    rew = claim_coll(c.from_user.id, rar)
    if rew:
        await c.answer("🎉 +" + str(rew) + "💰", show_alert=True)
    else:
        await c.answer("Уже получено или не собрано",
                       show_alert=True)

@dp.callback_query(F.data == "daily")
async def cb_daily(c: CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)
    if u["last_daily"]:
        d = datetime.now() - datetime.fromisoformat(u["last_daily"])
        if d < timedelta(hours=DAILY_CD):
            left = timedelta(hours=DAILY_CD) - d
            await c.answer("⏳ Через " + fmt_time(left),
                           show_alert=True)
            return
        if d < timedelta(hours=48):
            streak = u["daily_streak"] + 1
        else:
            streak = 1
    else:
        streak = 1
    base = random.randint(300, 700)
    bonus = int(base * (1 + (streak - 1) * 0.1))
    add_bal(uid, bonus)
    upd(uid, last_daily=datetime.now().isoformat(),
        daily_streak=streak)
    t = "🎉 Бонус: <b>+" + str(bonus) + "💰</b>"
    t += "\n🔥 Streak: <b>" + str(streak) + " дней</b>"
    await c.message.answer(t, parse_mode="HTML")
    await c.answer("Получено!")

@dp.callback_query(F.data == "quests")
async def cb_quests(c: CallbackQuery):
    await show_quests(c.message, c.from_user.id)
    await c.answer()

@dp.callback_query(F.data == "top")
async def cb_top(c: CallbackQuery):
    await show_top(c.message)
    await c.answer()

@dp.callback_query(F.data == "ach")
async def cb_ach(c: CallbackQuery):
    await show_ach(c.from_user.id, c.message)
    await c.answer()

@dp.callback_query(F.data == "craft")
async def cb_craft(c: CallbackQuery):
    menu = craft_menu(c.from_user.id)
    if not menu:
        await c.answer("Нужно 3 карты одной редкости",
                       show_alert=True)
        return
    await c.message.answer("⚒️ Что крафтим?", reply_markup=menu)
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
    nxt = {"common": "rare", "rare": "epic",
           "epic": "legendary"}[src]
    card = random.choice(CARDS[nxt])
    add_card(uid, card[0], nxt, "craft")
    await bump(uid, "crafted", 1, c.message)
    t = "⚒️ Крафт: "
    t += RARITIES[nxt]["e"] + " " + card[1] + " " + card[0]
    img = get_image(card[0])
    if img:
        try:
            await c.message.answer_photo(photo=img, caption=t)
            await c.answer("Готово!")
            return
        except Exception:
            pass
    await c.message.answer(t)
    await c.answer("Готово!")

@dp.callback_query(F.data.startswith("sell:"))
async def cb_sell(c: CallbackQuery):
    uid = c.from_user.id
    name = c.data.split(":", 1)[1]
    inv = [r for r in get_inv(uid) if r["card_name"] == name]
    if not inv:
        await c.answer("Карта не найдена", show_alert=True)
        return
    rar = inv[0]["rarity"]
    price = RARITIES[rar]["sell"]
    del_card(uid, name)
    add_bal(uid, price)
    await bump(uid, "sold", 1, c.message)
    prog_quest(uid, "sell", 1)
    await c.answer("✅ Продано за " + str(price) + "💰",
                   show_alert=True)
    rest = [r for r in get_inv(uid) if r["card_name"] == name]
    if rest:
        await render_card(c.message, uid, name)
    else:
        await show_coll(uid, c.message)

@dp.callback_query(F.data == "admin")
async def cb_admin(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        await c.answer("Только для владельца", show_alert=True)
        return
    await c.message.answer("👑 <b>Админ-панель</b>",
                           reply_markup=admin_menu())
    await c.answer()

@dp.callback_query(F.data == "a:stats")
async def cb_a_stats(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM inventory")
    cards = cur.fetchone()[0]
    cur.execute("SELECT SUM(balance) FROM users")
    tb = cur.fetchone()[0] or 0
    sql = "SELECT COUNT(*) FROM bans WHERE until > ?"
    cur.execute(sql, (datetime.now().isoformat(),))
    bans = cur.fetchone()[0]
    lines = ["📊 <b>Статистика</b>", ""]
    lines.append("👥 Игроков: <b>" + str(users) + "</b>")
    lines.append("🎴 Карт: <b>" + str(cards) + "</b>")
    lines.append("💰 Монет: <b>" + str(tb) + "</b>")
    lines.append("🚫 Забанено: <b>" + str(bans) + "</b>")
    lines.append("🖼️ Фото карт: <b>"
                 + str(images_count()) + "/72</b>")
    ev = active_events()
    lines.append("🔥 Ивенты: " + (", ".join(ev) if ev else "нет"))
    await c.message.answer("\n".join(lines), parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "a:bc")
async def cb_a_bc(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "bc"
    await c.message.answer("📢 Отправь текст рассылки")
    await c.answer()

@dp.callback_query(F.data == "a:coins")
async def cb_a_coins(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "coins"
    await c.message.answer("🎁 Формат: USER_ID СУММА")
    await c.answer()

@dp.callback_query(F.data == "a:card")
async def cb_a_card(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "card"
    await c.message.answer("🎴 Формат: USER_ID ИмяКарты")
    await c.answer()

@dp.callback_query(F.data == "a:promo")
async def cb_a_promo(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "promo"
    await c.message.answer("📜 Формат: КОД НАГРАДА ИСПОЛЬЗОВАНИЙ")
    await c.answer()

@dp.callback_query(F.data == "a:event")
async def cb_a_event(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💰 x2 монеты", callback_data="ae:x2_money")],
        [InlineKeyboardButton(
            text="⭐ x2 XP", callback_data="ae:x2_xp")],
        [InlineKeyboardButton(
            text="❌ Отключить", callback_data="ae:off")],
    ])
    await c.message.answer("🎬 Ивент на 24 часа:", reply_markup=kb)
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
    await c.answer("✅ " + ev + " на 24ч", show_alert=True)

@dp.callback_query(F.data == "a:img")
async def cb_a_img(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    await c.message.answer(
        "🖼️ <b>Как добавить фото карты</b>\n\n"
        "1. Отправь боту фото артиста\n"
        "2. В ответ на это сообщение отправь:\n"
        "   <code>/setimage ИмяАртиста</code>\n\n"
        "Пример:\n"
        "  <code>/setimage madk1d</code>\n\n"
        "Удалить фото:\n"
        "  <code>/delimage ИмяАртиста</code>\n\n"
        "Прогресс: <b>" + str(images_count()) + "/72</b>",
        parse_mode="HTML")
    await c.answer()

@dp.callback_query(F.data == "a:ban")
async def cb_a_ban(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "ban"
    await c.message.answer("🚫 Формат: USER_ID ЧАСЫ")
    await c.answer()

@dp.callback_query(F.data == "a:unban")
async def cb_a_unban(c: CallbackQuery):
    if not is_admin(c.from_user.id):
        return
    pending[c.from_user.id] = "unban"
    await c.message.answer("✅ USER_ID для разбана")
    await c.answer()

@dp.message(F.text == "📦 Кейсы")
async def rb_cases(m: Message):
    await m.answer("📦 Выбери кейс:", reply_markup=cases_menu())

@dp.message(F.text == "🎒 Коллекция")
async def rb_inv(m: Message):
    get_user(m.from_user.id, m.from_user.username)
    await show_coll(m.from_user.id, m)

@dp.message(F.text == "💰 Баланс")
async def rb_bal(m: Message):
    u = get_user(m.from_user.id, m.from_user.username)
    lines = ["💰 Баланс: <b>" + str(u["balance"]) + "</b>"]
    lines.append("⭐ Уровень: <b>" + str(u["level"]) + "</b>")
    lines.append("XP: " + str(u["xp"]))
    lines.append("/" + str(xp_need(u["level"])))
    await m.answer("\n".join(lines), parse_mode="HTML")

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
        t = "✅ Доставлено: " + str(ok)
        t += " ошибок: " + str(fail)
        await m.answer(t)
    elif act == "coins":
        parts = text.split()
        ok = len(parts) == 2 and parts[0].isdigit()
        ok = ok and parts[1].isdigit()
        if not ok:
            await m.answer("Формат: USER_ID СУММА")
            return
        t = int(parts[0])
        amt = int(parts[1])
        add_bal(t, amt)
        await m.answer("✅ +" + str(amt) + " юзеру " + str(t))
        try:
            await bot.send_message(t, "🎁 +" + str(amt))
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
        await m.answer("✅ Выдана " + cd[1] + " " + name)
        try:
            await bot.send_message(
                t, "🎁 Карта: " + cd[1] + " " + name)
        except Exception:
            pass
    elif act == "promo":
        parts = text.split()
        ok = len(parts) == 3
        ok = ok and parts[1].isdigit() and parts[2].isdigit()
        if not ok:
            await m.answer("Формат: КОД НАГРАДА ИСПОЛЬЗОВАНИЙ")
            return
        if add_promo(parts[0], int(parts[1]), int(parts[2])):
            await m.answer("✅ Промокод " + parts[0])
        else:
            await m.answer("Такой код уже есть")
    elif act == "ban":
        parts = text.split()
        ok = len(parts) == 2
        ok = ok and parts[0].isdigit() and parts[1].isdigit()
        if not ok:
            await m.answer("Формат: USER_ID ЧАСЫ")
            return
        ban_user(int(parts[0]), int(parts[1]))
        t = "🚫 Забанен " + parts[0]
        t += " на " + parts[1] + "ч"
        await m.answer(t)
    elif act == "unban":
        if not text.isdigit():
            await m.answer("USER_ID должен быть числом")
            return
        unban_user(int(text))
        await m.answer("✅ Разбанен " + text)

async def open_case_multi(uid, message, case_key, count, username=""):
    case = CASES[case_key]
    total = case["price"] * count
    u = get_user(uid, username)
    if u["balance"] < total:
        t = "❌ Нужно " + str(total) + "💰"
        t += " у тебя " + str(u["balance"]) + "💰"
        await message.answer(t)
        return
    add_bal(uid, -total)
    boosters = get_boosters(uid)
    results = []
    for _ in range(count):
        if boosters.get("guaranteed_rare"):
            rar = random.choices(["rare", "epic", "legendary"],
                                 weights=[70, 25, 5], k=1)[0]
            card = random.choice(CARDS[rar])
            boosters.pop("guaranteed_rare")
        else:
            rar, card = roll_card(case_key)
        add_card(uid, card[0], rar, "case")
        results.append((rar, card))
    set_boosters(uid, boosters)
    await give_xp(uid, XP_PER_CASE * count)
    for _ in range(count):
        prog_quest(uid, "case", 1)
    await bump(uid, "cases", count)
    leg = sum(1 for r, _ in results if r == "legendary")
    if leg:
        await bump(uid, "legendary", leg)
    new_u = get_user(uid)

    if count == 1:
        rar, card = results[0]
        e = RARITIES[rar]["e"]
        caption = "🎉 <b>Выпала карта!</b>\n\n"
        caption += e + " <b>" + card[1] + " " + card[0] + "</b>\n"
        caption += "Редкость: <b>"
        caption += RARITIES[rar]["name"] + "</b>\n\n"
        caption += "📖 <i>" + card[2] + "</i>\n\n"
        caption += "💰 Баланс: <b>"
        caption += str(new_u["balance"]) + "</b>\n"
        caption += "⭐ XP: " + str(new_u["xp"])
        caption += "/" + str(xp_need(new_u["level"]))
        img = get_image(card[0])
        if img:
            try:
                await message.answer_photo(
                    photo=img, caption=caption,
                    reply_markup=inline_menu(uid),
                    parse_mode="HTML")
                await check_ach(uid, message)
                return
            except Exception:
                pass
        await message.answer(caption,
                             reply_markup=inline_menu(uid),
                             parse_mode="HTML")
    else:
        order = {"legendary": 0, "epic": 1, "rare": 2, "common": 3}
        sorted_res = sorted(results, key=lambda x: order[x[0]])
        lines = ["🎉 <b>Открыто "
                 + str(count) + " кейс(ов) "
                 + case["emoji"] + "</b>", ""]
        for i, (rar, card) in enumerate(sorted_res, 1):
            e = RARITIES[rar]["e"]
            lines.append(str(i) + ". " + e + " "
                         + card[1] + " " + card[0])
        lines.append("")
        if leg:
            lines.append("🟡 Легендарных: <b>"
                         + str(leg) + "</b>")
        ep = sum(1 for r, _ in results if r == "epic")
        rar_c = sum(1 for r, _ in results if r == "rare")
        com = sum(1 for r, _ in results if r == "common")
        if ep:
            lines.append("🟣 Эпических: <b>" + str(ep) + "</b>")
        if rar_c:
            lines.append("🔵 Редких: <b>" + str(rar_c) + "</b>")
        if com:
            lines.append("⚪ Обычных: <b>" + str(com) + "</b>")
        lines.append("")
        lines.append("💰 Баланс: <b>"
                     + str(new_u["balance"]) + "</b>")
        lines.append("⭐ XP: " + str(new_u["xp"]))
        lines.append("/" + str(xp_need(new_u["level"])))
        # Альбом с фото (если есть хотя бы одно)
        media = []
        for rar, card in sorted_res:
            img = get_image(card[0])
            if img:
                media.append(InputMediaPhoto(media=img))
        if media and len(media) > 1:
            try:
                await message.answer_media_group(media=media[:10])
            except Exception:
                pass
        elif media and len(media) == 1:
            try:
                await message.answer_photo(photo=media[0].media)
            except Exception:
                pass
        await message.answer("\n".join(lines),
                             reply_markup=inline_menu(uid),
                             parse_mode="HTML")

    await check_ach(uid, message)

async def show_coll(uid, message):
    menu = coll_menu(uid)
    if not menu:
        text = "🎒 <b>Коллекция пуста</b>"
        try:
            await message.edit_text(text, parse_mode="HTML")
        except Exception:
            await message.answer(text, parse_mode="HTML")
        return
    inv = get_inv(uid)
    lines = ["🎒 <b>Коллекция</b>"]
    lines.append("Карт: <b>" + str(len(inv)) + "</b>")
    lines.append("")
    lines.append("Нажми на карту:")
    text = "\n".join(lines)
    try:
        await message.edit_text(text, reply_markup=menu,
                                parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=menu,
                             parse_mode="HTML")

async def render_card(message, uid, name):
    rar, cd = find_card(name)
    if not cd:
        return False
    inv = get_inv(uid)
    cnt = sum(1 for r in inv if r["card_name"] == name)
    if cnt == 0:
        return False
    price = RARITIES[rar]["sell"]
    e = RARITIES[rar]["e"]
    lines = [e + " <b>" + cd[1] + " " + cd[0] + "</b>"]
    lines.append("")
    lines.append("Редкость: <b>"
                 + RARITIES[rar]["name"] + "</b>")
    lines.append("В коллекции: <b>" + str(cnt) + "</b>")
    lines.append("💰 Цена: <b>" + str(price) + "</b>")
    lines.append("")
    lines.append("📖 <i>" + cd[2] + "</i>")
    t1 = "💱 Продать за " + str(price) + "💰"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t1,
                              callback_data="sell:" + name)],
        [InlineKeyboardButton(text="🎒 К коллекции",
                              callback_data="inv")],
    ])
    text = "\n".join(lines)
    img = get_image(name)
    if img:
        try:
            await message.answer_photo(photo=img, caption=text,
                                       reply_markup=kb,
                                       parse_mode="HTML")
            return True
        except Exception:
            pass
    try:
        await message.edit_text(text, reply_markup=kb,
                                parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=kb,
                             parse_mode="HTML")
    return True

async def show_top(message):
    sql = "SELECT username,user_id,balance,level FROM users"
    sql += " ORDER BY balance DESC LIMIT 10"
    cur.execute(sql)
    rows = cur.fetchall()
    if not rows:
        await message.answer("Пусто")
        return
    lines = ["🏆 <b>Топ-10:</b>", ""]
    for i, r in enumerate(rows, 1):
        name = r["username"] or ("id" + str(r["user_id"]))
        line = str(i) + ". " + name
        line += " — <b>" + str(r["balance"]) + "💰</b>"
        line += " (ур. " + str(r["level"]) + ")"
        lines.append(line)
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_quests(message, uid):
    d = get_quests(uid)
    lines = ["📋 <b>Ежедневные:</b>", ""]
    for qid, text, goal, rew, t in QUESTS:
        done = d.get(qid, 0)
        mark = "✅" if done >= goal else "⏳"
        line = mark + " " + text
        line += " — " + str(done) + "/" + str(goal)
        line += " (+" + str(rew) + "💰)"
        lines.append(line)
    lines.append("")
    lines.append("💰 /claim — забрать награды")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_ach(uid, message):
    a = get_ach(uid)
    lines = ["🏅 <b>Достижения:</b>", ""]
    for aid, text, rew, key, thr in ACHIEVEMENTS:
        mark = "✅" if a.get(aid) else "🔒"
        line = mark + " " + text
        line += " (+" + str(rew) + "💰)"
        lines.append(line)
    await message.answer("\n".join(lines), parse_mode="HTML")

async def show_history(uid, message):
    rows = get_history(uid, 10)
    if not rows:
        await message.answer("📜 История пуста")
        return
    src_map = {"case": "кейс", "craft": "крафт",
               "admin": "админ"}
    lines = ["📜 <b>Последние 10 карт:</b>", ""]
    for r in rows:
        e = RARITIES[r["rarity"]]["e"]
        s = src_map.get(r["source"], r["source"])
        lines.append(e + " " + r["card_name"] + " (" + s + ")")
    await message.answer("\n".join(lines), parse_mode="HTML")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())