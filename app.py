import asyncio
import logging
import os
import sqlite3
import sys
import traceback
from contextlib import suppress
from datetime import datetime

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


# ============================================================
# STARTUP DIAGNOSTICS
# ============================================================

print("=" * 60, flush=True)
print("🚀 MASTER UC SYSTEM STARTING...", flush=True)
print(f"🐍 Python: {sys.version}", flush=True)
print("=" * 60, flush=True)


# ============================================================
# CONFIG
# ============================================================

MASTER_BOT_TOKEN = os.getenv("MASTER_BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()
PORT_RAW = os.getenv("PORT", "10000").strip()
DB_PATH = os.getenv("DB_PATH", "master.db")


print("🔍 Checking environment...", flush=True)

if not MASTER_BOT_TOKEN:
    print("❌ MASTER_BOT_TOKEN IS MISSING", flush=True)
    raise RuntimeError(
        "MASTER_BOT_TOKEN environment variable is missing"
    )

print("✅ MASTER_BOT_TOKEN: FOUND", flush=True)

if not ADMIN_ID_RAW:
    print("❌ ADMIN_ID IS MISSING", flush=True)
    raise RuntimeError(
        "ADMIN_ID environment variable is missing"
    )

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    print("❌ ADMIN_ID IS NOT NUMERIC", flush=True)
    raise RuntimeError(
        "ADMIN_ID must contain a Telegram numeric ID"
    )

print("✅ ADMIN_ID: VALID", flush=True)

try:
    PORT = int(PORT_RAW)
except ValueError:
    print("⚠️ Invalid PORT. Using 10000.", flush=True)
    PORT = 10000

print(f"🌐 PORT: {PORT}", flush=True)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

log = logging.getLogger("master-uc")


# ============================================================
# DATABASE
# ============================================================

print("💾 Opening database...", flush=True)

db = sqlite3.connect(
    DB_PATH,
    check_same_thread=False,
)

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

print("✅ DATABASE: OK", flush=True)


# ============================================================
# HELPERS
# ============================================================

def now_text():
    return datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def get_bot(bot_id: int):
    return db.execute(
        "SELECT * FROM bots WHERE id = ?",
        (bot_id,),
    ).fetchone()


def get_all_bots():
    return db.execute(
        "SELECT * FROM bots ORDER BY id DESC"
    ).fetchall()


def is_master(user_id: int):
    return user_id == ADMIN_ID


# ============================================================
# TIME SYSTEM
# ============================================================

def valid_hhmm(value: str):

    try:
        h, m = map(
            int,
            value.split(":"),
        )

        return (
            0 <= h <= 23
            and
            0 <= m <= 59
        )

    except Exception:
        return False


def in_schedule(row):

    if not row["schedule_enabled"]:
        return True

    offset = int(
        row["timezone_offset"]
    )

    local_timestamp = (
        datetime.utcnow().timestamp()
        +
        offset * 60
    )

    local_now = datetime.fromtimestamp(
        local_timestamp
    )

    current = (
        local_now.hour * 60
        +
        local_now.minute
    )

    sh, sm = map(
        int,
        row["start_time"].split(":"),
    )

    eh, em = map(
        int,
        row["end_time"].split(":"),
    )

    start = sh * 60 + sm
    end = eh * 60 + em

    if start == end:
        return True

    if start < end:
        return (
            start <= current <= end
        )

    return (
        current >= start
        or
        current <= end
    )


def should_run(row):

    return (
        bool(row["enabled"])
        and
        in_schedule(row)
    )


# ============================================================
# TELEGRAM TOKEN CHECK
# ============================================================

async def validate_token(token: str):

    bot = Bot(token=token)

    try:

        return await bot.get_me()

    finally:

        with suppress(Exception):
            await bot.session.close()


# ============================================================
# MASTER KEYBOARD
# ============================================================

def master_keyboard():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Иловаи бот"
                ),
                KeyboardButton(
                    text="🤖 Ботҳо"
                ),
            ],
            [
                KeyboardButton(
                    text="🔎 Ҷустуҷӯ"
                ),
                KeyboardButton(
                    text="🧪 System Test"
                ),
            ],
            [
                KeyboardButton(
                    text="📊 Статистика"
                ),
                KeyboardButton(
                    text="ℹ️ Система"
                ),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


# ============================================================
# BOT CARD
# ============================================================

def bot_card(row):

    status = (
        "🟢 ФАЪОЛ"
        if row["enabled"]
        else
        "🔴 ХОМӮШ"
    )

    schedule = (
        f"⏰ {row['start_time']} → "
        f"{row['end_time']} UTC+5"
        if row["schedule_enabled"]
        else
        "♾ 24/7"
    )

    owner = (
        str(row["owner_id"])
        if row["owner_id"]
        else
        "таъин нашудааст"
    )

    username = (
        f"@{row['username']}"
        if row["username"]
        else
        "no_username"
    )

    return (
        f"<b>🤖 {row['name']}</b>\n\n"
        f"🆔 Internal ID: <code>#{row['id']}</code>\n"
        f"📌 Telegram ID: <code>{row['telegram_id']}</code>\n"
        f"👤 Username: <b>{username}</b>\n"
        f"👑 Owner: <code>{owner}</code>\n"
        f"📡 Status: <b>{status}</b>\n"
        f"{schedule}\n"
        f"🔐 Token: <b>HIDDEN</b>"
    )


# ============================================================
# BOT MENU
# ============================================================

def bot_menu(bot_id: int):

    row = get_bot(bot_id)

    if not row:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Ботҳо",
                        callback_data="bots",
                    )
                ]
            ]
        )

    status = (
        "🟢 ФАЪОЛ"
        if row["enabled"]
        else
        "🔴 ХОМӮШ"
    )

    schedule = (
        "⏰ ВАҚТ: ON"
        if row["schedule_enabled"]
        else
        "♾ 24/7"
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
                    text=status,
                    callback_data=f"toggle:{bot_id}",
                ),
                InlineKeyboardButton(
                    text=schedule,
                    callback_data=f"schedule:{bot_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏰ Вақт",
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


# ============================================================
# STATES
# ============================================================

class AddBotState(StatesGroup):
    token = State()


class OwnerState(StatesGroup):
    owner = State()


class SearchState(StatesGroup):
    query = State()


class TimeStartState(StatesGroup):
    start = State()


class TimeEndState(StatesGroup):
    end = State()


# ============================================================
# MASTER ROUTER
# ============================================================

master_router = Router()


# ============================================================
# /START
# ============================================================

@master_router.message(CommandStart())
async def master_start(
    message: Message,
    state: FSMContext,
):

    if not is_master(
        message.from_user.id
    ):
        return

    await state.clear()

    await message.answer(
        "<b>𒆜 𝑴𝒂𝒔𝒕𝒆𝒓Ӿ 𝑼𝑪⚡</b>\n\n"
        "👑 <b>MASTER CONTROL CENTER</b>\n\n"
        "🤖 Bot Management\n"
        "👤 Owner Management\n"
        "⏰ Per-Bot Schedule\n"
        "🧪 System Diagnostics\n\n"
        "🚀 Ҳама чиз аз ҳамин ҷо идора мешавад.",
        reply_markup=master_keyboard(),
    )


# ============================================================
# ADD BOT
# ============================================================

@master_router.message(
    lambda m: m.text == "➕ Иловаи бот"
)
async def add_bot(
    message: Message,
    state: FSMContext,
):

    if not is_master(
        message.from_user.id
    ):
        return

    await state.set_state(
        AddBotState.token
    )

    await message.answer(
        "➕ <b>ADD BOT</b>\n\n"
        "Token-и ботро фирист.\n\n"
        "🔐 Token дар интерфейс нишон дода намешавад."
    )


@master_router.message(
    AddBotState.token
)
async def receive_token(
    message: Message,
    state: FSMContext,
):

    if not is_master(
        message.from_user.id
    ):
        return

    token = (
        message.text or ""
    ).strip()

    if not token:

        await message.answer(
            "❌ Token холӣ аст."
        )

        return

    await message.answer(
        "🔄 Token санҷида мешавад..."
    )

    try:

        me = await validate_token(
            token
        )

    except Exception as e:

        log.exception(
            "TOKEN VALIDATION ERROR"
        )

        await message.answer(
            "❌ <b>Token нодуруст аст.</b>\n\n"
            "Telegram API token-ро қабул накард."
        )

        return

    exists = db.execute(
        """
        SELECT id
        FROM bots
        WHERE telegram_id = ?
        """,
        (me.id,),
    ).fetchone()

    if exists:

        await state.clear()

        await message.answer(
            "⚠️ <b>Ин бот аллакай ҳаст.</b>\n\n"
            f"🤖 {me.first_name}\n"
            f"👤 @{me.username or 'no_username'}",
            reply_markup=master_keyboard(),
        )

        return

    ts = now_text()

    db.execute(
        """
        INSERT INTO bots (
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
            '00:00', '23:59',
            300, ?, ?
        )
        """,
        (
            token,
            me.id,
            me.username or "",
            me.first_name or "Unknown",
            ts,
            ts,
        ),
    )

    db.commit()

    row = db.execute(
        """
        SELECT *
        FROM bots
        WHERE telegram_id = ?
        """,
        (me.id,),
    ).fetchone()

    await state.clear()

    await message.answer(
        "✅ <b>BOT ADDED SUCCESSFULLY</b>\n\n"
        f"🤖 {row['name']}\n"
        f"👤 @{row['username'] or 'no_username'}\n"
        f"🆔 Telegram ID: <code>{row['telegram_id']}</code>\n"
        f"🔑 Internal ID: <code>#{row['id']}</code>\n\n"
        "♾ Default: 24/7\n"
        "👤 Owner: not assigned",
        reply_markup=master_keyboard(),
    )


# ============================================================
# BOT LIST
# ============================================================

@master_router.message(
    lambda m: m.text == "🤖 Ботҳо"
)
async def list_bots(
    message: Message,
):

    if not is_master(
        message.from_user.id
    ):
        return

    rows = get_all_bots()

    if not rows:

        await message.answer(
            "🤖 Ҳоло ягон бот нест."
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

        clock = (
            "⏰"
            if row["schedule_enabled"]
            else
            "♾"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} {clock} "
                        f"#{row['id']} "
                        f"{row['name'][:25]}"
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


# ============================================================
# VIEW
# ============================================================

@master_router.callback_query(
    lambda c: c.data.startswith("view:")
)
async def view_bot(
    call: CallbackQuery,
):

    if not is_master(
        call.from_user.id
    ):
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

    await call.answer()

    await call.message.edit_text(
        bot_card(row),
        reply_markup=bot_menu(bot_id),
    )


# ============================================================
# BACK TO BOTS
# ============================================================

@master_router.callback_query(
    lambda c: c.data == "bots"
)
async def back_bots(
    call: CallbackQuery,
):

    if not is_master(
        call.from_user.id
    ):
        return

    rows = get_all_bots()

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

    await call.answer()

    await call.message.edit_text(
        "<b>🤖 BOT MANAGEMENT</b>\n\n"
        "Ботро интихоб кун:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )


# ============================================================
# ENABLE / DISABLE
# ============================================================

@master_router.callback_query(
    lambda c: c.data.startswith("toggle:")
)
async def toggle_bot(
    call: CallbackQuery,
):

    if not is_master(
        call.from_user.id
    ):
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

    new_status = (
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
            new_status,
            now_text(),
            bot_id,
        ),
    )

    db.commit()

    await call.answer(
        "Status updated"
    )

    row = get_bot(bot_id)

    await call.message.edit_text(
        bot_card(row),
        reply_markup=bot_menu(bot_id),
    )


# ============================================================
# SCHEDULE ON / OFF
# ============================================================

@master_router.callback_query(
    lambda c: c.data.startswith("schedule:")
)
async def toggle_schedule(
    call: CallbackQuery,
):

    if not is_master(
        call.from_user.id
    ):
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

    value = (
        0
        if row["schedule_enabled"]
        else
        1
    )

    db.execute(
        """
        UPDATE bots
        SET schedule_enabled = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            value,
            now_text(),
            bot_id,
        ),
    )

    db.commit()

    await call.answer(
        "Schedule updated"
    )

    row = get_bot(bot_id)

    await call.message.edit_text(
        bot_card(row),
        reply_markup=bot_menu(bot_id),
    )


# ============================================================
# OWNER
# ============================================================

@master_router.callback_query(
    lambda c: c.data.startswith("owner:")
)
async def owner_start(
    call: CallbackQuery,
    state: FSMContext,
):

    if not is_master(
        call.from_user.id
    ):
        return

    bot_id = int(
        call.data.split(":")[1]
    )

    if not get_bot(bot_id):

        await call.answer(
            "Бот ёфт нашуд",
            show_alert=True,
        )

        return

    await state.update_data(
        bot_id=bot_id
    )

    await state.set_state(
        OwnerState.owner
    )

    await call.answer()

    await call.message.answer(
        f"👤 <b>OWNER — BOT #{bot_id}</b>\n\n"
        "Telegram numeric ID-ро фирист.\n\n"
        "Барои хориҷ кардани Owner:\n"
        "<code>0</code>"
    )


@master_router.message(
    OwnerState.owner
)
async def owner_save(
    message: Message,
    state: FSMContext,
):

    if not is_master(
     
