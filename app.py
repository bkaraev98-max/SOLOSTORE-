import asyncio
import logging
import os
import sqlite3
from contextlib import suppress

from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = os.getenv("MASTER_BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PORT = int(os.getenv("PORT", "10000"))
DB = "database.db"

conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row

conn.execute("""
CREATE TABLE IF NOT EXISTS bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    telegram_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    name TEXT,
    owner_id INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1
)
""")
conn.commit()

router = Router()

waiting_token = set()
waiting_owner = {}
tasks = {}


def master(uid):
    return uid == ADMIN_ID


def get_bot(bot_id):
    return conn.execute(
        "SELECT * FROM bots WHERE id = ?",
        (bot_id,),
    ).fetchone()


async def get_me(token):
    bot = Bot(token)

    try:
        return await bot.get_me(), None
    except Exception as e:
        return None, str(e)
    finally:
        await bot.session.close()


def menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Add Bot",
                    callback_data="add",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 Bot List",
                    callback_data="list",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧪 System Test",
                    callback_data="sys",
                )
            ],
        ]
    )


def bot_menu(bot_id, enabled):
    return InlineKeyboardMarkup(
        inline_keyboard=[
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
            [
                InlineKeyboardButton(
                    text="🔴 Disable" if enabled else "🟢 Enable",
                    callback_data=(
                        f"disable:{bot_id}"
                        if enabled
                        else f"enable:{bot_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="list",
                )
            ],
        ]
    )


@router.message(CommandStart())
async def start(message: Message):
    if not master(message.from_user.id):
        await message.answer("⛔ Access denied.")
        return

    await message.answer(
        "👑 Master Control Panel",
        reply_markup=menu(),
    )


@router.callback_query(F.data == "add")
async def add(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    waiting_token.add(callback.from_user.id)

    await callback.message.answer(
        "➕ Token-и BotFather-ро фиристед."
    )

    await callback.answer()


@router.callback_query(F.data == "list")
async def listing(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    rows = conn.execute(
        "SELECT * FROM bots ORDER BY id DESC"
    ).fetchall()

    if not rows:
        await callback.message.answer(
            "🤖 Ягон bot илова нашудааст.",
            reply_markup=menu(),
        )
    else:
        buttons = []

        for row in rows:
            if row["username"]:
                name = f"@{row['username']}"
            else:
                name = row["name"] or f"Bot {row['id']}"

            status = "🟢" if row["enabled"] else "🔴"

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{status} {name}",
                        callback_data=f"bot:{row['id']}",
                    )
                ]
            )

        await callback.message.answer(
            "🤖 Managed Bots",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=buttons
            ),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("bot:"))
async def details(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(callback.data.split(":")[1])
    row = get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Not found",
            show_alert=True,
        )
        return

    username = (
        f"@{row['username']}"
        if row["username"]
        else "—"
    )

    owner = (
        str(row["owner_id"])
        if row["owner_id"]
        else "Not assigned"
    )

    text = (
        "🤖 <b>BOT DETAILS</b>\n\n"
        f"ID: <code>{row['id']}</code>\n"
        f"Name: <b>{row['name'] or '—'}</b>\n"
        f"Username: <b>{username}</b>\n"
        f"Telegram ID: <code>{row['telegram_id']}</code>\n"
        f"Owner: <code>{owner}</code>\n"
        f"Status: "
        f"{'🟢 Enabled' if row['enabled'] else '🔴 Disabled'}\n"
        "Token: 🔐 Hidden"
    )

    await callback.message.answer(
        text,
        reply_markup=bot_menu(
            bot_id,
            bool(row["enabled"]),
        ),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("owner:"))
async def owner(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(callback.data.split(":")[1])

    if get_bot(bot_id) is None:
        await callback.answer(
            "Not found",
            show_alert=True,
        )
        return

    waiting_owner[callback.from_user.id] = bot_id

    await callback.message.answer(
        "👤 Telegram ID-и Owner-ро фиристед."
    )

    await callback.answer()


@router.callback_query(F.data.startswith("enable:"))
async def enable(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(callback.data.split(":")[1])
    row = get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Not found",
            show_alert=True,
        )
        return

    conn.execute(
        "UPDATE bots SET enabled = 1 WHERE id = ?",
        (bot_id,),
    )
    conn.commit()

    await start_managed(bot_id)

    await callback.message.answer(
        "🟢 Bot enabled."
    )

    await callback.answer()


@router.callback_query(F.data.startswith("disable:"))
async def disable(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(callback.data.split(":")[1])
    row = get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Not found",
            show_alert=True,
        )
        return

    conn.execute(
        "UPDATE bots SET enabled = 0 WHERE id = ?",
        (bot_id,),
    )
    conn.commit()

    await stop_managed(bot_id)

    await callback.message.answer(
        "🔴 Bot disabled."
    )

    await callback.answer()


@router.callback_query(F.data.startswith("test:"))
async def test(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    bot_id = int(callback.data.split(":")[1])
    row = get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Not found",
            show_alert=True,
        )
        return

    info, error = await get_me(row["token"])

    if error:
        await callback.message.answer(
            "❌ Test failed:\n"
            f"<code>{error}</code>"
        )
    else:
        running = (
            bot_id in tasks
            and not tasks[bot_id].done()
        )

        await callback.message.answer(
            "✅ <b>TEST PASSED</b>\n\n"
            f"Name: <b>{info.first_name or '—'}</b>\n"
            f"Username: <b>@{info.username or '—'}</b>\n"
            f"Telegram ID: <code>{info.id}</code>\n"
            f"Polling: "
            f"{'🟢 Running' if running else '🔴 Stopped'}"
        )

    await callback.answer()


@router.callback_query(F.data == "sys")
async def system(callback: CallbackQuery):
    if not master(callback.from_user.id):
        await callback.answer(
            "Access denied",
            show_alert=True,
        )
        return

    total = conn.execute(
        "SELECT COUNT(*) FROM bots"
    ).fetchone()[0]

    running = sum(
        not task.done()
        for task in tasks.values()
    )

    await callback.message.answer(
        "🧪 <b>SYSTEM TEST</b>\n\n"
        "Database: ✅\n"
        "Master Bot: ✅\n"
        f"Saved bots: <b>{total}</b>\n"
        f"Running bots: <b>{running}</b>"
    )

    await callback.answer()


@router.message()
async def text(message: Message):
    user_id = message.from_user.id

    if not master(user_id):
        await message.answer(
            "⛔ Access denied."
        )
        return

    value = (message.text or "").strip()

    if user_id in waiting_token:
        waiting_token.remove(user_id)

        info, error = await get_me(value)

        if error:
            await message.answer(
                "❌ Invalid token:\n"
                f"<code>{error}</code>"
            )
            return

        try:
            cursor = conn.execute(
                """
                INSERT INTO bots (
                    token,
                    telegram_id,
                    username,
                    name
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    value,
                    info.id,
                    info.username,
                    info.first_name,
                ),
            )

            conn.commit()

        except sqlite3.IntegrityError:
            await message.answer(
                "⚠️ Ин bot аллакай илова шудааст."
            )
            return

        bot_id = cursor.lastrowid

        await message.answer(
            "✅ <b>BOT ADDED</b>\n\n"
            f"Name: <b>{info.first_name or '—'}</b>\n"
            f"Username: <b>@{info.username or '—'}</b>\n"
            f"Telegram ID: <code>{info.id}</code>\n"
            f"Internal ID: <code>{bot_id}</code>"
        )

        await start_managed(bot_id)
        return

    if user_id in waiting_owner:
        bot_id = waiting_owner.pop(user_id)

        try:
            owner_id = int(value)
        except ValueError:
            await message.answer(
                "❌ ID бояд рақам бошад."
            )
            return

        conn.execute(
            """
            UPDATE bots
            SET owner_id = ?
            WHERE id = ?
            """,
            (
                owner_id,
                bot_id,
            ),
        )

        conn.commit()

        await message.answer(
            "✅ Owner assigned."
        )
        return

    await message.answer(
        "👑 Master Panel",
        reply_markup=menu(),
    )


def managed_router(bot_id):
    managed = Router()

    @managed.message(CommandStart())
    async def managed_start(message: Message):
        row = get_bot(bot_id)

        if row is None:
            return

        if not row["enabled"]:
            await message.answer(
                "🔴 Bot disabled."
            )
            return

        if (
            row["owner_id"]
            and message.from_user.id == row["owner_id"]
        ):
            await message.answer(
                "👑 <b>Owner Panel</b>\n\n"
                "Шумо Owner-и ҳамин bot ҳастед."
            )
        else:
            await message.answer(
                "🤖 Bot is online."
            )

    return managed


async def worker(bot_id):
    row = get_bot(bot_id)

    if row is None:
        return

    bot = Bot(row["token"])

    try:
        await bot.get_me()

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        dispatcher = Dispatcher()
        dispatcher.include_router(
            managed_router(bot_id)
        )

        await dispatcher.start_polling(
            bot,
            handle_signals=False,
        )

    except asyncio.CancelledError:
        raise

    except Exception:
        log.exception(
            "Managed bot %s stopped because of an error",
            bot_id,
        )

    finally:
        await bot.session.close()


async def start_managed(bot_id):
    task = tasks.get(bot_id)

    if task and not task.done():
        return

    tasks[bot_id] = asyncio.create_task(
        worker(bot_id)
    )


async def stop_managed(bot_id):
    task = tasks.get(bot_id)

    if task:
        task.cancel()

        with suppress(
            asyncio.CancelledError,
            Exception,
        ):
            await task

        tasks.pop(
            bot_id,
            None,
        )


async def health(request):
    total = conn.execute(
        "SELECT COUNT(*) FROM bots"
    ).fetchone()[0]

    running = sum(
        not task.done()
        for task in tasks.values()
    )

    return web.json_response(
        {
            "ok": True,
            "saved_bots": total,
            "running_bots": running,
        }
    )


async def main():
    if not TOKEN:
        raise RuntimeError(
            "MASTER_BOT_TOKEN is missing"
        )

    if ADMIN_ID == 0:
        raise RuntimeError(
            "ADMIN_ID is missing"
        )

    master_bot = Bot(TOKEN)

    info = await master_bot.get_me()

    log.info(
        "Master Bot: @%s (%s)",
        info.username,
        info.id,
    )

    app = web.Application()

    app.router.add_get(
        "/",
        health,
    )

    app.router.add_get(
        "/health",
        health,
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT,
    )

    await site.start()

    rows = conn.execute(
        "SELECT id FROM bots WHERE enabled = 1"
    ).fetchall()

    for row in rows:
        await start_managed(
            row["id"]
        )

    dispatcher = Dispatcher()

    dispatcher.include_router(
        router
    )

    try:
        await master_bot.delete_webhook(
            drop_pending_updates=True
        )

        await dispatcher.start_polling(
            master_bot,
            handle_signals=False,
        )

    finally:
        for bot_id in list(tasks):
            await stop_managed(bot_id)

        await runner.cleanup()
        await master_bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
