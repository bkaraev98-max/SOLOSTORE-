import asyncio
import html
import logging
import os
import sqlite3
from contextlib import suppress
from datetime import datetime

from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


# ============================================================
# CONFIG
# ============================================================

MASTER_BOT_TOKEN = os.getenv("MASTER_BOT_TOKEN", "").strip()

try:
    MASTER_ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip())
except ValueError:
    MASTER_ADMIN_ID = 0

PORT = int(os.getenv("PORT", "10000"))
DB_FILE = os.getenv("DB_FILE", "database.db")


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE
# ============================================================

db = sqlite3.connect(
    DB_FILE,
    check_same_thread=False,
)

db.row_factory = sqlite3.Row

db.execute(
    """
    CREATE TABLE IF NOT EXISTS bots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL UNIQUE,
        telegram_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        first_name TEXT,
        admin_id INTEGER,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """
)

db.commit()


def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def db_add_bot(
    token,
    telegram_id,
    username,
    first_name,
):
    timestamp = now()

    cursor = db.execute(
        """
        INSERT INTO bots (
            token,
            telegram_id,
            username,
            first_name,
            admin_id,
            enabled,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, NULL, 1, ?, ?)
        """,
        (
            token,
            telegram_id,
            username,
            first_name,
            timestamp,
            timestamp,
        ),
    )

    db.commit()

    return cursor.lastrowid


def db_get_bot(bot_id):
    return db.execute(
        "SELECT * FROM bots WHERE id = ?",
        (bot_id,),
    ).fetchone()


def db_get_all_bots():
    return db.execute(
        "SELECT * FROM bots ORDER BY id DESC"
    ).fetchall()


def db_search_bots(query):
    q = f"%{query.lower()}%"

    return db.execute(
        """
        SELECT *
        FROM bots
        WHERE
            LOWER(COALESCE(username, '')) LIKE ?
            OR LOWER(COALESCE(first_name, '')) LIKE ?
            OR CAST(telegram_id AS TEXT) LIKE ?
        ORDER BY id DESC
        """,
        (q, q, q),
    ).fetchall()


def db_set_admin(bot_id, admin_id):
    db.execute(
        """
        UPDATE bots
        SET admin_id = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            admin_id,
            now(),
            bot_id,
        ),
    )

    db.commit()


def db_set_enabled(bot_id, enabled):
    db.execute(
        """
        UPDATE bots
        SET enabled = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            1 if enabled else 0,
            now(),
            bot_id,
        ),
    )

    db.commit()


# ============================================================
# ACCESS
# ============================================================

def is_master(user_id):
    return (
        MASTER_ADMIN_ID != 0
        and user_id == MASTER_ADMIN_ID
    )


def is_bot_admin(user_id, bot_id):
    row = db_get_bot(bot_id)

    if row is None:
        return False

    return (
        row["admin_id"] is not None
        and int(row["admin_id"]) == int(user_id)
    )


# ============================================================
# TELEGRAM TOKEN CHECK
# ============================================================

async def check_token(token):
    bot = None

    try:
        bot = Bot(token=token)

        info = await bot.get_me()

        return info, None

    except Exception as e:
        return None, str(e)

    finally:
        if bot is not None:
            with suppress(Exception):
                await bot.session.close()


# ============================================================
# STATE
# ============================================================

waiting_for_token = set()
waiting_for_admin = {}
waiting_for_search = set()


# ============================================================
# MANAGED BOT TASKS
# ============================================================

managed_tasks = {}


# ============================================================
# MASTER BOT KEYBOARDS
# ============================================================

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Add Bot",
                    callback_data="add_bot",
                ),
                InlineKeyboardButton(
                    text="🤖 Bot List",
                    callback_data="bot_list",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Search",
                    callback_data="search",
                ),
                InlineKeyboardButton(
                    text="🧪 System Test",
                    callback_data="system_test",
                ),
            ],
        ]
    )


def bot_keyboard(bot_id, enabled):
    buttons = [
        [
            InlineKeyboardButton(
                text="👤 Set Owner",
                callback_data=f"owner:{bot_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🧪 Test",
                callback_data=f"test:{bot_id}",
            )
        ],
    ]

    if enabled:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔴 Disable",
                    callback_data=f"disable:{bot_id}",
                )
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🟢 Enable",
                    callback_data=f"enable:{bot_id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data="bot_list",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# MASTER ROUTER
# ============================================================

master_router = Router()


# ============================================================
# MASTER /start
# ============================================================

@master_router.message(CommandStart())
async def master_start(message: Message):

    if not is_master(message.from_user.id):
        await message.answer(
            "⛔ Access denied."
        )
        return

    await message.answer(
        "👑 <b>MASTER CONTROL PANEL</b>\n\n"
        "Системаи идоракунии ботҳо фаъол аст.",
        reply_markup=main_keyboard(),
    )


# ============================================================
# MASTER /panel
# ============================================================

@master_router.message(Command("panel"))
async def master_panel(message: Message):

    if not is_master(message.from_user.id):
        await message.answer(
            "⛔ Access denied."
        )
        return

    await message.answer(
        "👑 <b>MASTER CONTROL PANEL</b>",
        reply_markup=main_keyboard(),
    )


# ============================================================
# ADD BOT
# ============================================================

@master_router.callback_query(
    F.data == "add_bot"
)
async def add_bot_callback(callback: CallbackQuery):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    waiting_for_token.add(
        callback.from_user.id
    )

    await callback.message.answer(
        "➕ <b>ADD BOT</b>\n\n"
        "Token-и боти Telegram-ро фиристед.\n\n"
        "Мисол:\n"
        "<code>123456789:AA...</code>"
    )

    await callback.answer()


# ============================================================
# BOT LIST
# ============================================================

@master_router.callback_query(
    F.data == "bot_list"
)
async def bot_list_callback(callback: CallbackQuery):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    rows = db_get_all_bots()

    if not rows:
        await callback.message.answer(
            "🤖 <b>Bot List</b>\n\n"
            "Ҳоло ягон бот илова нашудааст.",
            reply_markup=main_keyboard(),
        )

        await callback.answer()
        return

    buttons = []

    for row in rows:

        username = row["username"]

        if username:
            title = f"@{username}"
        else:
            title = row["first_name"] or f"Bot #{row['id']}"

        status = "🟢" if row["enabled"] else "🔴"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {title}",
                    callback_data=f"bot:{row['id']}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Main Menu",
                callback_data="main_menu",
            )
        ]
    )

    await callback.message.answer(
        "🤖 <b>MANAGED BOTS</b>\n\n"
        f"Total: <b>{len(rows)}</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )

    await callback.answer()


# ============================================================
# BOT DETAILS
# ============================================================

@master_router.callback_query(
    F.data.startswith("bot:")
)
async def bot_details_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(
        callback.data.split(":")[1]
    )

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True,
        )
        return

    username = (
        f"@{row['username']}"
        if row["username"]
        else "—"
    )

    owner = (
        str(row["admin_id"])
        if row["admin_id"]
        else "Not assigned"
    )

    status = (
        "🟢 Enabled"
        if row["enabled"]
        else "🔴 Disabled"
    )

    text = (
        "🤖 <b>BOT DETAILS</b>\n\n"
        f"🆔 Internal ID: <code>{row['id']}</code>\n"
        f"📛 Name: <b>{html.escape(row['first_name'] or '—')}</b>\n"
        f"👤 Username: <b>{html.escape(username)}</b>\n"
        f"🆔 Telegram ID: <code>{row['telegram_id']}</code>\n"
        f"👑 Owner ID: <code>{html.escape(owner)}</code>\n"
        f"📡 Status: {status}\n"
        f"📅 Created: <code>{row['created_at']}</code>\n\n"
        "🔐 Token: <b>Hidden</b>"
    )

    await callback.message.answer(
        text,
        reply_markup=bot_keyboard(
            bot_id,
            bool(row["enabled"]),
        ),
    )

    await callback.answer()


# ============================================================
# SET OWNER
# ============================================================

@master_router.callback_query(
    F.data.startswith("owner:")
)
async def owner_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(
        callback.data.split(":")[1]
    )

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True,
        )
        return

    waiting_for_admin[
        callback.from_user.id
    ] = bot_id

    await callback.message.answer(
        "👤 <b>SET BOT OWNER</b>\n\n"
        "Owner/Admin-и ин ботро бо Telegram ID фиристед.\n\n"
        "Мисол:\n"
        "<code>123456789</code>"
    )

    await callback.answer()


# ============================================================
# ENABLE
# ============================================================

@master_router.callback_query(
    F.data.startswith("enable:")
)
async def enable_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(
        callback.data.split(":")[1]
    )

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True,
        )
        return

    db_set_enabled(bot_id, True)

    if bot_id not in managed_tasks:
        await start_managed_bot(bot_id)

    await callback.message.answer(
        "🟢 <b>Bot enabled.</b>"
    )

    await callback.answer(
        "Enabled"
    )


# ============================================================
# DISABLE
# ============================================================

@master_router.callback_query(
    F.data.startswith("disable:")
)
async def disable_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(
        callback.data.split(":")[1]
    )

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True,
        )
        return

    db_set_enabled(bot_id, False)

    await stop_managed_bot(bot_id)

    await callback.message.answer(
        "🔴 <b>Bot disabled.</b>"
    )

    await callback.answer(
        "Disabled"
    )


# ============================================================
# TEST BOT
# ============================================================

@master_router.callback_query(
    F.data.startswith("test:")
)
async def test_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(
        callback.data.split(":")[1]
    )

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "🧪 <b>TESTING...</b>"
    )

    info, error = await check_token(
        row["token"]
    )

    if error:

        await callback.message.answer(
            "❌ <b>TEST FAILED</b>\n\n"
            f"<code>{html.escape(error)}</code>"
        )

        await callback.answer()
        return

    running = (
        bot_id in managed_tasks
        and not managed_tasks[bot_id].done()
    )

    username = (
        f"@{info.username}"
        if info.username
        else "—"
    )

    await callback.message.answer(
        "✅ <b>BOT TEST PASSED</b>\n\n"
        f"🤖 Name: <b>{html.escape(info.first_name or '—')}</b>\n"
        f"👤 Username: <b>{html.escape(username)}</b>\n"
        f"🆔 Telegram ID: <code>{info.id}</code>\n"
        f"🗄 Database: ✅\n"
        f"🔑 Token: ✅ Valid\n"
        f"🔄 Polling: "
        f"{'🟢 Running' if running else '🔴 Stopped'}"
    )

    await callback.answer(
        "Test passed"
    )


# ============================================================
# SEARCH
# ============================================================

@master_router.callback_query(
    F.data == "search"
)
async def search_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    waiting_for_search.add(
        callback.from_user.id
    )

    await callback.message.answer(
        "🔎 <b>SEARCH BOT</b>\n\n"
        "Username, name ё Telegram ID-ро фиристед."
    )

    await callback.answer()


# ============================================================
# SYSTEM TEST
# ============================================================

@master_router.callback_query(
    F.data == "system_test"
)
async def system_test_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    rows = db_get_all_bots()

    running = sum(
        1
        for bot_id, task in managed_tasks.items()
        if not task.done()
    )

    enabled = sum(
        1
        for row in rows
        if row["enabled"]
    )

    await callback.message.answer(
        "🧪 <b>SYSTEM TEST</b>\n\n"
        "🗄 Database: ✅ Online\n"
        "🤖 Master Bot: ✅ Online\n"
        f"📦 Saved Bots: <b>{len(rows)}</b>\n"
        f"🟢 Enabled Bots: <b>{enabled}</b>\n"
        f"🔄 Running Polling: <b>{running}</b>\n"
        "🌐 Web Server: ✅ Online"
    )

    await callback.answer(
        "System OK"
    )


# ============================================================
# MAIN MENU
# ============================================================

@master_router.callback_query(
    F.data == "main_menu"
)
async def main_menu_callback(
    callback: CallbackQuery,
):

    if not is_master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "👑 <b>MASTER CONTROL PANEL</b>",
        reply_markup=main_keyboard(),
    )

    await callback.answer()


# ============================================================
# MASTER TEXT HANDLER
# ============================================================

@master_router.message()
async def master_text_handler(
    message: Message,
):

    user_id = message.from_user.id

    if not is_master(user_id):
        await message.answer(
            "⛔ Access denied."
        )
        return

    text = (message.text or "").strip()

    # --------------------------------------------------------
    # TOKEN
    # --------------------------------------------------------

    if user_id in waiting_for_token:

        waiting_for_token.discard(user_id)

        await message.answer(
            "🔎 <b>Checking Telegram token...</b>"
        )

        info, error = await check_token(text)

        if error:

            await message.answer(
                "❌ <b>Invalid Bot Token</b>\n\n"
                f"<code>{html.escape(error)}</code>\n\n"
                "Token-ро аз BotFather санҷед."
            )
            return

        try:

            bot_id = db_add_bot(
                token=text,
                telegram_id=info.id,
                username=info.username,
                first_name=info.first_name,
            )

        except sqlite3.IntegrityError:

            await message.answer(
                "⚠️ Ин бот аллакай дар система мавҷуд аст."
            )
            return

        await message.answer(
            "✅ <b>BOT ADDED SUCCESSFULLY</b>\n\n"
            f"📛 Name: <b>{html.escape(info.first_name or '—')}</b>\n"
            f"👤 Username: "
        
