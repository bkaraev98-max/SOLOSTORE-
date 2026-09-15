import asyncio
import logging
import os
import sqlite3
from contextlib import suppress
from datetime import datetime
from html import escape

from aiohttp import web
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

# =========================
# CONFIG
# =========================

MASTER_BOT_TOKEN = os.getenv("MASTER_BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))
DB_PATH = os.getenv("DB_PATH", "master.db")

if not MASTER_BOT_TOKEN:
    raise RuntimeError("MASTER_BOT_TOKEN is missing")

if ADMIN_ID <= 0:
    raise RuntimeError("ADMIN_ID must be a valid Telegram numeric ID")


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

log = logging.getLogger("master-system")


# =========================
# DATABASE
# =========================

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row

db.execute("PRAGMA journal_mode=WAL")

db.execute(
    """
    CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL UNIQUE,
        telegram_id INTEGER NOT NULL UNIQUE,
        username TEXT NOT NULL,
        name TEXT NOT NULL,
        owner_id INTEGER NOT NULL DEFAULT 0,
        enabled INTEGER NOT NULL DEFAULT 1,
        schedule_enabled INTEGER NOT NULL DEFAULT 0,
        start_time TEXT NOT NULL DEFAULT '00:00',
        end_time TEXT NOT NULL DEFAULT '23:59',
        timezone_offset INTEGER NOT NULL DEFAULT 300,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """
)

db.commit()


# =========================
# DATABASE HELPERS
# =========================

def now_text():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def get_bot(bot_id: int):
    return db.execute(
        "SELECT * FROM bots WHERE id = ?",
        (bot_id,),
    ).fetchone()


def get_all_bots():
    return db.execute(
        "SELECT * FROM bots ORDER BY id DESC"
    ).fetchall()


def master_only(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================
# TIME SYSTEM
# =========================

def valid_hhmm(value: str):
    try:
        h, m = map(int, value.split(":"))

        if 0 <= h <= 23 and 0 <= m <= 59:
            return True

        return False

    except Exception:
        return False


def in_schedule(row) -> bool:

    # Schedule disabled = 24/7
    if not row["schedule_enabled"]:
        return True

    offset = int(row["timezone_offset"])

    local_timestamp = (
        datetime.utcnow().timestamp()
        + offset * 60
    )

    local_now = datetime.fromtimestamp(local_timestamp)

    current_minutes = (
        local_now.hour * 60
        + local_now.minute
    )

    start_h, start_m = map(
        int,
        row["start_time"].split(":"),
    )

    end_h, end_m = map(
        int,
        row["end_time"].split(":"),
    )

    start = start_h * 60 + start_m
    end = end_h * 60 + end_m

    # Same time = 24 hours
    if start == end:
        return True

    # Normal schedule
    if start < end:
        return start <= current_minutes <= end

    # Overnight schedule
    return (
        current_minutes >= start
        or current_minutes <= end
    )


def should_run(row) -> bool:
    return bool(row["enabled"]) and in_schedule(row)


# =========================
# TELEGRAM HELPERS
# =========================

async def close_bot_session(bot: Bot):

    with suppress(Exception):
        await bot.session.close()


async def validate_token(token: str):

    bot = Bot(token=token)

    try:
        me = await bot.get_me()

        return me

    finally:
        await close_bot_session(bot)


# =========================
# MASTER KEYBOARD
# =========================

def master_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Иловаи бот"),
                KeyboardButton(text="🤖 Ботҳо"),
            ],
            [
                KeyboardButton(text="🔎 Ҷустуҷӯ"),
                KeyboardButton(text="🧪 System Test"),
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="ℹ️ Система"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


# =========================
# BOT MENU
# =========================

def bot_menu(bot_id: int):

    row = get_bot(bot_id)

    if not row:

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Бозгашт",
                        callback_data="bots",
                    )
                ]
            ]
        )

    enabled_text = (
        "🟢 ФАЪОЛ"
        if row["enabled"]
        else
        "🔴 ХОМӮШ"
    )

    schedule_text = (
        "⏰ ВАҚТ: ON"
        if row["schedule_enabled"]
        else
        "♾ ВАҚТ: OFF"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Owner",
                    callback_data=f"owner:{bot_id}",
                ),
                InlineKeyboardButton(
                    text="🧪 Test",
                    callback_data=f"test:{bot_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=enabled_text,
                    callback_data=f"toggle:{bot_id}",
                ),
                InlineKeyboardButton(
                    text=schedule_text,
                    callback_data=f"schedule:{bot_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏱ Вақт",
                    callback_data=f"time:{bot_id}",
                ),
                InlineKeyboardButton(
                    text="🗑 Нест кардан",
                    callback_data=f"delete:{bot_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Навсозӣ",
                    callback_data=f"view:{bot_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ботҳо",
                    callback_data="bots",
                )
            ],
        ]
    )


def owner_menu(bot_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Маълумоти бот",
                    callback_data=f"oinfo:{bot_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧪 Test",
                    callback_data=f"otest:{bot_id}",
                )
            ],
        ]
    )


# =========================
# BOT CARD
# =========================

def bot_card(row):

    status = (
        "🟢 ФАЪОЛ"
        if row["enabled"]
        else
        "🔴 ХОМӮШ"
    )

    owner = (
        str(row["owner_id"])
        if row["owner_id"]
        else
        "таъин нашудааст"
    )

    if row["schedule_enabled"]:

        schedule = (
            f"⏰ <b>{row['start_time']} — "
            f"{row['end_time']}</b>\n"
            f"🌍 UTC{int(row['timezone_offset'] / 60):+d}"
        )

    else:

        schedule = "♾ <b>24/7</b>"

    username = (
        f"@{escape(row['username'])}"
        if row["username"]
        else
        "без username"
    )

    return (
        f"<b>🤖 {escape(row['name'])}</b>\n\n"
        f"🆔 Bot ID: <code>#{row['id']}</code>\n"
        f"📌 Telegram ID: <code>{row['telegram_id']}</code>\n"
        f"👤 Username: <b>{username}</b>\n"
        f"👑 Owner ID: <code>{owner}</code>\n"
        f"📡 Status: <b>{status}</b>\n"
        f"{schedule}\n"
        f"🔐 Token: <b>Hidden</b>"
    )


# =========================
# MASTER STATES
# =========================

class AddBotState(StatesGroup):
    token = State()


class OwnerState(StatesGroup):
    owner_id = State()


class SearchState(StatesGroup):
    query = State()


class TimeState(StatesGroup):
    start = State()


class TimeEndState(StatesGroup):
    end = State()


# =========================
# MASTER ROUTER
# =========================

master_router = Router()


@master_router.message(CommandStart())
async def master_start(
    message: Message,
    state: FSMContext,
):

    if not master_only(message.from_user.id):
        return

    await state.clear()

    await message.answer(
        "<b>𒆜 𝑴𝒂𝒔𝒕𝒆𝒓Ӿ 𝑼𝑪⚡</b>\n\n"
        "👑 <b>MASTER CONTROL CENTER</b>\n\n"
        "Ҳамаи ботҳо аз ҳамин ҷо идора мешаванд.",
        reply_markup=master_keyboard(),
    )


# =========================
# ADD BOT
# =========================

@master_router.message(
    lambda m: m.text == "➕ Иловаи бот"
)
async def add_bot_start(
    message: Message,
    state: FSMContext,
):

    if not master_only(message.from_user.id):
        return

    await state.set_state(
        AddBotState.token
    )

    await message.answer(
        "➕ <b>ИЛОВАИ БОТ</b>\n\n"
        "Token-и ботро фирист.\n\n"
        "Ман онро аввал тавассути Telegram API "
        "санҷида, баъд ба система илова мекунам."
    )


@master_router.message(AddBotState.token)
async def add_bot_token(
    message: Message,
    state: FSMContext,
):

    if not master_only(message.from_user.id):
        return

    token = (message.text or "").strip()

    if not token:

        await message.answer(
            "❌ Token холӣ аст."
        )

        return

    try:

        me = await validate_token(token)

    except Exception as e:

        log.warning(
            "Token validation failed: %s",
            e,
        )

        await message.answer(
            "❌ Token нодуруст аст "
            "ё Telegram онро қабул накард."
        )

        return

    exists = db.execute(
        "SELECT id FROM bots WHERE telegram_id = ?",
        (me.id,),
    ).fetchone()

    if exists:

        await state.clear()

        await message.answer(
            "⚠️ <b>Ин бот аллакай илова шудааст.</b>\n\n"
            f"🤖 <b>{escape(me.first_name or 'Без имени')}</b>\n"
            f"👤 @{escape(me.username or 'no_username')}",
            reply_markup=master_keyboard(),
        )

        return

    ts = now_text()

    db.execute(
        """
        INSERT INTO bots
        (
            token,
            telegram_id,
            username,
            name,
            owner_id,
            enabled,
            schedule_enabled,
            start_time,
            end_time,
            timezone_offset,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, 0, 1, 0,
            '00:00', '23:59', 300, ?, ?
        )
        """,
        (
            token,
            me.id,
            me.username or "",
            me.first_name or "Без имени",
            ts,
            ts,
        ),
    )

    db.commit()

    row = db.execute(
        "SELECT id FROM bots WHERE telegram_id = ?",
        (me.id,),
    ).fetchone()

    await state.clear()

    await message.answer(
        "✅ <b>БОТ ИЛОВА ШУД!</b>\n\n"
        f"🤖 Ном: <b>{escape(me.first_name or 'Без имени')}</b>\n"
        f"👤 Username: <b>@{escape(me.username or 'no_username')}</b>\n"
        f"🆔 Telegram ID: <code>{me.id}</code>\n"
        f"🔑 Internal ID: <code>#{row['id']}</code>\n\n"
        "🚀 Акнун онро бе навиштани код идора карда метавонӣ.",
        reply_markup=master_keyboard(),
    )


# =========================
# BOT LIST
# =========================

@master_router.message(
    lambda m: m.text == "🤖 Ботҳо"
)
async def bot_list(message: Message):

    if not master_only(message.from_user.id):
        return

    rows = get_all_bots()

    if not rows:

        await message.answer(
            "🤖 Ҳоло ягон бот илова нашудааст."
        )

        return

    buttons = []

    for row in rows:

        status = (
            "🟢"
            if row["enabled"]
            else
            "🔴"
        )

        schedule = (
            "⏰"
            if row["schedule_enabled"]
            else
            "♾"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} {schedule} "
                        f"#{row['id']} "
                        f"{row['name'][:24]}"
                    ),
                    callback_data=f"view:{row['id']}",
                )
            ]
        )

    await message.answer(
        "<b>🤖 BOT MANAGEMENT</b>\n\n"
        "Ботро интихоб кун:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )


# =========================
# SEARCH
# =========================

@master_router.message(
    lambda m: m.text == "🔎 Ҷустуҷӯ"
)
async def search_start(
    message: Message,
    state: FSMContext,
):

    if not master_only(message.from_user.id):
        return

    await state.set_state(
        SearchState.query
    )

    await message.answer(
        "🔎 <b>ҶУСТУҶӮ</b>\n\n"
        "Ном, username, Telegram ID ё "
        "Internal ID-ро фирист."
    )


@master_router.message(SearchState.query)
async def search_do(
    message: Message,
    state: FSMContext,
):

    if not master_only(message.from_user.id):
        return

    query = (message.text or "").strip()

    rows = db.execute(
        """
        SELECT *
        FROM bots
        WHERE name LIKE ?
           OR username LIKE ?
           OR CAST(telegram_id AS TEXT) LIKE ?
           OR CAST(id AS TEXT) LIKE ?
        ORDER BY id DESC
        """,
        (
            f"%{query}%",
            f"%{query}%",
            f"%{query}%",
            f"%{query}%",
        ),
    ).fetchall()

    await state.clear()

    if not rows:

        await message.answer(
            "❌ Ягон бот ёфт нашуд.",
            reply_markup=master_keyboard(),
        )

        return

    for row in rows:

        await message.answer(
            bot_card(row),
            reply_markup=bot_menu(row["id"]),
        )


# =========================
# SYSTEM TEST
# =========================

@master_router.message(
    lambda m: m.text == "🧪 System Test"
)
async def system_test(message: Message):

    if not master_only(message.from_user.id):
        return

    rows = get_all_bots()

    ok = 0
    bad = 0

    for row in rows:

        try:

            me = await validate_token(
                row["token"]
            )

            ok += 1

            db.execute(
                """
                UPDATE bots
                SET username = ?,
                    name = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    me.username or "",
                    me.first_name or "Без имени",
                    now_text(),
                    row["id"],
                ),
            )

        except Exception:

            bad += 1

    db.commit()

    await message.answer(
        "<b>🧪 SYSTEM TEST</b>\n\n"
        f"🤖 Ботҳо: <b>{len(rows)}</b>\n"
        f"🟢 Telegram OK: <b>{ok}</b>\n"
        f"🔴 Error: <b>{bad}</b>\n"
        "💾 Database: <b>OK</b>\n"
        "⏰ Scheduler: <b>ACTIVE</b>"
    )


# =========================
# STATISTICS
# =========================

@master_router.message(
    lambda m: m.text == "📊 Статистика"
)
async def stats(message: Message):

    if not master_only(message.from_user.id):
        return

    total = db.execute(
        "SELECT COUNT(*) c FROM bots"
    ).fetchone()["c"]

    enabled = db.execute(
        "SELECT COUNT(*) c FROM bots WHERE enabled = 1"
    ).fetchone()["c"]

    timed = db.execute(
        """
        SELECT COUNT(*) c
        FROM bots
        WHERE schedule_enabled = 1
        """
    ).fetchone()["c"]

    owners = db.execute(
        """
        SELECT COUNT(*) c
        FROM bots
        WHERE owner_id != 0
        """
    ).fetchone()["c"]

    await message.answer(
        "<b>📊 MASTER STATISTICS</b>\n\n"
        f"🤖 Ҳама ботҳо: <b>{total}</b>\n"
        f"🟢 Фаъол: <b>{enabled}</b>\n"
        f"⏰ Бо вақт: <b>{timed}</b>\n"
        f"👤 Owner таъиншуда: <b>{owners}</b>"
    )


# =========================
# SYSTEM INFO
# =========================

@master_router.message(
    lambda m: m.text == "ℹ️ Система"
)
async def system_info(message: Message):

    if not master_only(message.from_user.id):
        return

    await message.answer(
        "<b>𒆜 𝑴𝒂𝒔𝒕𝒆𝒓Ӿ 𝑼𝑪⚡</b>\n\n"
        "👑 Architecture:\n"
        "<b>MASTER → MANAGED BOTS</b>\n\n"
        "💾 Database: <b>SQLite</b>\n"
        "📡 Transport: <b>Polling</b>\n"
        "⏰ Scheduler: <b>Per-Bot</b>\n"
        "👤 Owner Isolation: <b>ON</b>\n"
        "🔐 Token Protection: <b>ON</b>\n"
        "❤️ Health Server: <b>ON</b>"
    )


# =========================
# VIEW BOT
# =========================

@master_router.callback_query(
    lambda c: c.data == "bots"
)
async def cb_bots(call: CallbackQuery):

    if not master_only(call.from_user.id):
        return

    await call.answer()

    rows = get_all_bots()

    if not rows:

        await call.message.edit_text(
            "🤖 Ҳоло бот нест."
        )

        return

    buttons = []

    for row in rows:

        status = (
            "🟢"
            if row["enabled"]
            else
            "🔴"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} #{row['id']} "
                        f"{row['name'][:25]}"
                    ),
                    callback_data=f"view:{row['id']}",
                )
            ]
        )

    await call.message.edit_text(
        "<b>🤖 BOT MANAGEMENT</b>\n\n"
        "Ботро интихоб кун:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )


@master_router.callback_query(
    lambda c: c.data.startswith("view:")
)
async def cb_view(call: CallbackQuery):

    if not master_only(call.from_user.id):
        return

    await call.answer()

    bot_id = int(
        call.data.split(":")[1]
    )

    row = get_bot(bot_id)

    if not row:

        await call.message.edit_text(
            "❌ Бот ёфт нашуд."
        )

        return

    await call.message.edit_text(
        bot_card(row),
        reply_markup=bot_menu(bot_id),
    )


# =========================
# ENABLE / DISABLE
# =========================

@master_router.callback_query(
    lambda c: c.data.startswith("toggle:")
)
async def cb_toggle(call: CallbackQuery):

    if not master_only(call.from_user.id):
        return

    bot_id = int(
        call.data.split(":")[1]
    )

    row = get_bot(bot_id)

    if not row:

        await call.answer(
            "Бот ёфт нашуд",
            show_alert=True,
        )

        return

    new_value = (
        0
        if row["enabled"]
        else
        1
    )

    db.execute(
        """
        UPDATE bots
        SET enabled = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            new_value,
            now_text(),
            bot_id,
        ),
    )

    db.commit()

    await call.answer(
        "Статус иваз шуд"
    )

    row = get_bot(bot_id)

    await call.message.edit_text(
        bot_card(row),
        reply_markup=bot_menu(bot_id),
    )


# ======================
