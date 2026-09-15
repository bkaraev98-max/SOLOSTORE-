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
            f"<b>@{html.escape(info.user


def master_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(
        text="➕ Add Bot",
        callback_data="add_bot"
    )

    kb.button(
        text="📋 Bot List",
        callback_data="bot_list"
    )

    kb.button(
        text="🔍 Search",
        callback_data="search_bot"
    )

    kb.button(
        text="🧪 System Test",
        callback_data="system_test"
    )

    kb.adjust(2)

    return kb.as_markup()


def bot_keyboard(bot_id: int, enabled: bool):
    kb = InlineKeyboardBuilder()

    kb.button(
        text="👤 Set Admin",
        callback_data=f"setadmin:{bot_id}"
    )

    if enabled:
        kb.button(
            text="🔴 Disable",
            callback_data=f"disable:{bot_id}"
        )
    else:
        kb.button(
            text="🟢 Enable",
            callback_data=f"enable:{bot_id}"
        )

    kb.button(
        text="🔗 Webhook",
        callback_data=f"webhook:{bot_id}"
    )

    kb.button(
        text="🧪 Test",
        callback_data=f"testbot:{bot_id}"
    )

    kb.button(
        text="🔙 Back",
        callback_data="bot_list"
    )

    kb.adjust(2)

    return kb.as_markup()


def format_bot(bot_row):
    username = (
        f"@{html.escape(bot_row['username'])}"
        if bot_row["username"]
        else "—"
    )

    name = html.escape(
        bot_row["first_name"] or "Unknown"
    )

    status = "🟢 Active" if bot_row["enabled"] else "🔴 Disabled"

    admin = (
        str(bot_row["admin_id"])
        if bot_row["admin_id"]
        else "❌ Not assigned"
    )

    return (
        f"🤖 <b>{name}</b>\n"
        f"👤 Username: {username}\n"
        f"🆔 Bot ID: <code>{bot_row['telegram_id']}</code>\n"
        f"👑 Bot Admin: <code>{admin}</code>\n"
        f"📊 Status: {status}\n"
        f"🗂 Internal ID: <code>{bot_row['id']}</code>"
    )


@master_router.message(CommandStart())
async def start_handler(message: Message):

    if not is_master_admin(message.from_user.id):
        await message.answer(
            "⛔ Access denied."
        )
        return

    await message.answer(
        "👑 <b>MASTER BOT</b>\n\n"
        "🤖 Multi-Bot Management System\n\n"
        "Аз ин ҷо ту ҳамаи ботҳои худро идора карда метавонӣ.",
        reply_markup=master_keyboard()
    )


@master_router.message(Command("panel"))
async def panel_handler(message: Message):

    if not is_master_admin(message.from_user.id):
        return

    await message.answer(
        "👑 <b>MASTER PANEL</b>",
        reply_markup=master_keyboard()
    )


# ============================================================
# ADD BOT
# ============================================================

waiting_for_token = set()
waiting_for_admin = {}


@master_router.callback_query(F.data == "add_bot")
async def add_bot_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    waiting_for_token.add(callback.from_user.id)

    await callback.message.answer(
        "➕ <b>Add Bot</b>\n\n"
        "Token-и боти Telegram-ро фирист.\n\n"
        "Мисол:\n"
        "<code>123456:ABC...</code>\n\n"
        "⚠️ Token-ро танҳо ба Master Bot фирист."
    )

    await callback.answer()


@master_router.message()
async def text_router(message: Message):

    if not is_master_admin(message.from_user.id):
        return

    user_id = message.from_user.id
    text = (message.text or "").strip()

    # ----------------------------------------
    # ADD BOT TOKEN
    # ----------------------------------------

    if user_id in waiting_for_token:

        waiting_for_token.discard(user_id)

        if not text:
            await message.answer(
                "❌ Token холӣ аст."
            )
            return

        await message.answer(
            "⏳ Token санҷида мешавад..."
        )

        bot_info, error = await telegram_get_me(text)

        if error:
            await message.answer(
                "❌ <b>Token invalid</b>\n\n"
                f"Telegram: <code>{html.escape(error)}</code>\n\n"
                "Token-ро аз BotFather санҷ."
            )
            return

        try:
            bot_id = db_add_bot(
                token=text,
                telegram_id=bot_info["id"],
                username=bot_info.get("username"),
                first_name=bot_info.get("first_name"),
            )

        except sqlite3.IntegrityError:
            await message.answer(
                "⚠️ Ин бот аллакай ба система илова шудааст."
            )
            return

        row = db_get_bot(bot_id)

        await message.answer(
            "✅ <b>Bot successfully added!</b>\n\n"
            + format_bot(row),
            reply_markup=bot_keyboard(
                bot_id,
                bool(row["enabled"])
            )
        )

        return

    # ----------------------------------------
    # SET ADMIN
    # ----------------------------------------

    if user_id in waiting_for_admin:

        bot_id = waiting_for_admin.pop(user_id)

        try:
            admin_id = int(text)
        except ValueError:
            await message.answer(
                "❌ Admin ID бояд рақам бошад.\n"
                "Мисол: <code>123456789</code>"
            )
            return

        row = db_get_bot(bot_id)

        if row is None:
            await message.answer(
                "❌ Bot ёфт нашуд."
            )
            return

        db_set_admin(bot_id, admin_id)

        row = db_get_bot(bot_id)

        await message.answer(
            "✅ <b>Bot Admin assigned.</b>\n\n"
            + format_bot(row),
            reply_markup=bot_keyboard(
                bot_id,
                bool(row["enabled"])
            )
        )

        return


# ============================================================
# BOT LIST
# ============================================================

@master_router.callback_query(F.data == "bot_list")
async def bot_list_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bots = db_get_all_bots()

    if not bots:
        await callback.message.answer(
            "📋 <b>Bot List</b>\n\n"
            "Ҳоло ягон бот илова нашудааст."
        )

        await callback.answer()
        return

    kb = InlineKeyboardBuilder()

    text = "📋 <b>MANAGED BOTS</b>\n\n"

    for row in bots:

        username = (
            f"@{row['username']}"
            if row["username"]
            else str(row["telegram_id"])
        )

        status = "🟢" if row["enabled"] else "🔴"

        text += (
            f"{status} <b>{html.escape(username)}</b> "
            f"— ID {row['id']}\n"
        )

        kb.button(
            text=f"{status} {username}",
            callback_data=f"bot:{row['id']}"
        )

    kb.button(
        text="🔙 Main Menu",
        callback_data="main_menu"
    )

    kb.adjust(1)

    await callback.message.answer(
        text,
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# BOT DETAILS
# ============================================================

@master_router.callback_query(F.data.startswith("bot:"))
async def bot_details_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    await callback.message.answer(
        format_bot(row),
        reply_markup=bot_keyboard(
            bot_id,
            bool(row["enabled"])
        )
    )

    await callback.answer()


# ============================================================
# SET ADMIN
# ============================================================

@master_router.callback_query(F.data.startswith("setadmin:"))
async def set_admin_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    waiting_for_admin[callback.from_user.id] = bot_id

    await callback.message.answer(
        f"👤 <b>Set Admin</b>\n\n"
        f"Bot: {html.escape(row['first_name'] or 'Unknown')}\n\n"
        "Telegram ID-и соҳиби ин ботро фирист.\n\n"
        "Мисол:\n"
        "<code>123456789</code>"
    )

    await callback.answer()


# ============================================================
# ENABLE / DISABLE
# ============================================================

@master_router.callback_query(F.data.startswith("enable:"))
async def enable_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    db_set_enabled(bot_id, True)

    row = db_get_bot(bot_id)

    await callback.message.answer(
        "🟢 <b>Bot enabled</b>\n\n"
        + format_bot(row),
        reply_markup=bot_keyboard(bot_id, True)
    )

    await callback.answer("Enabled")


@master_router.callback_query(F.data.startswith("disable:"))
async def disable_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    db_set_enabled(bot_id, False)

    row = db_get_bot(bot_id)

    await callback.message.answer(
        "🔴 <b>Bot disabled</b>\n\n"
        + format_bot(row),
        reply_markup=bot_keyboard(bot_id, False)
    )

    await callback.answer("Disabled")


# ============================================================
# WEBHOOK
# ============================================================

@master_router.callback_query(F.data.startswith("webhook:"))
async def webhook_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    info, error = await telegram_get_webhook_info(
        row["token"]
    )

    if error:
        await callback.message.answer(
            "❌ Webhook check failed:\n"
            f"<code>{html.escape(error)}</code>"
        )

        await callback.answer()
        return

    webhook_url = info.get("url") or "Not configured"

    pending = info.get("pending_update_count", 0)

    last_error = info.get("last_error_message")

    text = (
        "🔗 <b>WEBHOOK INFO</b>\n\n"
        f"URL:\n<code>{html.escape(webhook_url)}</code>\n\n"
        f"Pending updates: <code>{pending}</code>\n"
    )

    if last_error:
        text += (
            "\n⚠️ Last error:\n"
            f"<code>{html.escape(last_error)}</code>"
        )

    if BASE_URL:
        expected_url = (
            f"{BASE_URL}"
            f"{WEBHOOK_PATH_PREFIX}"
            f"/{bot_id}/"
            f"{row['webhook_secret']}"
        )

        text += (
            "\n\nExpected URL:\n"
            f"<code>{html.escape(expected_url)}</code>"
        )

    await callback.message.answer(text)

    await callback.answer()


# ============================================================
# TEST BOT
# ============================================================

@master_router.callback_query(F.data.startswith("testbot:"))
async def test_bot_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    await callback.message.answer(
        "🧪 <b>Testing bot...</b>"
    )

    bot_info, error = await telegram_get_me(
        row["token"]
    )

    if error:
        await callback.message.answer(
            "❌ Bot test failed:\n"
            f"<code>{html.escape(error)}</code>"
        )
        await callback.answer()
        return

    webhook_info, webhook_error = (
        await telegram_get_

@dp.message(BuyState.waiting_for_withdrawal_amount)
async def process_withdrawal(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        current_balance = user_balances.get(user_id, 0.0)
        
        if current_balance < amount:
            await message.answer("❌ Маблағи баланси шумо кофӣ нест!")
        else:
            user_balances[user_id] = current_balance - amount
            await message.answer(f"✅ Дархости вивести {amount} сомонӣ бомуваффақият фиристода шуд. Ба زӯдӣ ба ҳамёни شما гузаронида мешавад.")
            await bot.send_message(ADMIN_ID, f"💸 **Дархости вивест аз @{message.from_user.username}**\nМаблағ: {amount} сомонӣ")
    except ValueError:
        await message.answer("Иلطфао фақат рақам нависед.")
    await state.clear()

async def on_startup(bot: Bot):
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook пайваст шуд: {webhook_url}")

def main():
    dp.startup.register(on_startup)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path="/webhook")
    
    setup_application(app, dp, bot=bot)
    
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
