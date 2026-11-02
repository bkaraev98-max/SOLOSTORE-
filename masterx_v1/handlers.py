
"""
MASTER X — Version 1.0
Telegram command and callback handlers.
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

try:
    from .settings import FOUNDER_ID, BOT_NAME, BOT_VERSION
    from .database import db
except ImportError:
    from settings import FOUNDER_ID, BOT_NAME, BOT_VERSION
    from database import db


router = Router(name="masterx_handlers")


# -------------------------------------------------
# KEYBOARDS
# -------------------------------------------------

def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 MASTER MARKET",
                    callback_data="menu_market"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Профили ман",
                    callback_data="menu_profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Қоидаҳо",
                    callback_data="menu_rules"
                )
            ]
        ]
    )


def founder_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📡 Идоракунии каналҳо",
                    callback_data="admin_channels"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Идоракунии лотҳо",
                    callback_data="admin_lots"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Корбарон ва кафилон",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Пардохтҳо",
                    callback_data="admin_payments"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Обунаҳо",
                    callback_data="admin_subscriptions"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Танзимот",
                    callback_data="admin_settings"
                )
            ]
        ]
    )


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def is_founder(user_id):
    return bool(FOUNDER_ID) and user_id == FOUNDER_ID


def register_user(user):
    db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )


# -------------------------------------------------
# START
# -------------------------------------------------

@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user

    if not user:
        return

    register_user(user)

    if is_founder(user.id):
        await message.answer(
            f"👑 Хуш омадед, Founder!\n\n"
            f"✦ {BOT_NAME}\n"
            f"Версия: {BOT_VERSION}\n\n"
            "Панели идоракунӣ:",
            reply_markup=founder_menu_keyboard()
        )
        return

    await message.answer(
        f"✦ Хуш омадед ба {BOT_NAME}!\n\n"
        "Платформаи пайвасткунандаи харидорон "
        "ва фурӯшандагон.\n\n"
        "Аз меню истифода баред:",
        reply_markup=main_menu_keyboard()
    )


# -------------------------------------------------
# FOUNDER COMMAND
# -------------------------------------------------

@router.message(Command("admin"))
async def admin_handler(message: Message):
    user = message.from_user

    if not user or not is_founder(user.id):
        await message.answer(
            "⛔ Шумо иҷозати ворид шудан надоред."
        )
        return

    await message.answer(
        "👑 MASTER X — FOUNDER PANEL",
        reply_markup=founder_menu_keyboard()
    )


# -------------------------------------------------
# HELP COMMAND
# -------------------------------------------------

@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "✦ MASTER X — Кӯмак\n\n"
        "/start — Оғози бот\n"
        "/help — Кӯмак\n"
        "/admin — Панели Founder"
    )


# -------------------------------------------------
# USER PROFILE
# -------------------------------------------------

@router.callback_query(F.data == "menu_profile")
async def profile_handler(callback: CallbackQuery):
    user = callback.from_user
    profile = db.get_user(user.id)

    if not profile:
        await callback.answer(
            "Профил ёфт нашуд.",
            show_alert=True
        )
        return

    text = (
        "👤 ПРОФИЛИ ШУМО\n\n"
        f"🆔 ID: {profile['user_id']}\n"
        f"👤 Ном: {profile['full_name'] or 'Номаълум'}\n"
        f"📛 Username: @{profile['username'] or 'нест'}\n"
        f"🔰 Вазифа: {profile['role']}\n"
    )

    await callback.message.answer(text)
    await callback.answer()


# -------------------------------------------------
# MARKET
# -------------------------------------------------

@router.callback_query(F.data == "menu_market")
async def market_handler(callback: CallbackQuery):
    lots = db.list_lots(
        status="available",
        limit=10
    )

    if not lots:
        await callback.message.answer(
            "🛒 Ҳоло ягон лоти дастрас нест."
        )
        await callback.answer()
        return

    for lot in lots:
        text = (
            f"✦ MASTER MARKET ✦\n\n"
            f"🎮 {lot['title']}\n"
            f"📝 {lot['description']}\n\n"
            f"📂 Категория: {lot['category']}\n"
            f"🎯 Платформа: {lot['platform']}\n"
            f"💰 Нарх: {lot['price']} {lot['currency']}\n"
            f"🆔 ID: {lot['lot_code']}\n"
        )

        if lot.get("video_url"):
            text += f"\n🎬 Видео: {lot['video_url']}"

        await callback.message.answer(text)

    await callback.answer()


# -------------------------------------------------
# RULES
# -------------------------------------------------

@router.callback_query(F.data == "menu_rules")
async def rules_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📋 MASTER X — ҚОИДАҲО\n\n"
        "1. MASTER X платформаи миёнарав мебошад.\n"
        "2. MASTER X кафил нест ва гарантия намедиҳад.\n"
        "3. Кафилон мустақилона фаъолият мекунанд.\n"
        "4. Пеш аз харид маълумоти лотро санҷед.\n"
        "5. Шартҳои харидро пешакӣ омӯзед."
    )

    await callback.answer()


# -------------------------------------------------
# FOUNDER CALLBACKS
# -------------------------------------------------

@router.callback_query(F.data.startswith("admin_"))
async def founder_callback_handler(callback: CallbackQuery):
    if not is_founder(callback.from_user.id):
        await callback.answer(
            "⛔ Дастрасӣ манъ аст.",
            show_alert=True
        )
        return

    sections = {
        "admin_stats": "📊 Қисми статистика ҳоло омода карда мешавад.",
        "admin_channels": "📡 Қисми идоракунии каналҳо.",
        "admin_lots": "🎮 Қисми идоракунии лотҳо.",
        "admin_users": "👥 Қисми корбарон ва кафилон.",
        "admin_payments": "💳 Қисми пардохтҳо.",
        "admin_subscriptions": "📦 Қисми обунаҳо.",
        "admin_settings": "⚙️ Қисми танзимот."
    }

    text = sections.get(
        callback.data,
        "Қисм ёфт нашуд."
    )

    await callback.message.answer(text)
    await callback.answer()


# -------------------------------------------------
# UNKNOWN COMMAND
# -------------------------------------------------

@router.message()
async def unknown_handler(message: Message):
    await message.answer(
        "Фармон фаҳмо нест.\n"
        "Барои дидани меню /start-ро пахш кунед."
              )
  
