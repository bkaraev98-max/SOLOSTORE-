
import logging
from html import escape

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

try:
    from .services import services
    from .settings import FOUNDER_ID, BOT_NAME, BOT_VERSION
except ImportError:
    from services import services
    from settings import FOUNDER_ID, BOT_NAME, BOT_VERSION


logger = logging.getLogger("MASTER_X.HANDLERS")
router = Router(name="master_x_handlers")


# =========================================================
# TEXTS
# =========================================================

WELCOME_TEXT = """
<b>✦ MASTER X ✦</b>

Салом, {name}! 👋

Хуш омадӣ ба <b>MASTER X</b> — платформаи пайвасткунандаи
фурӯшандагон, кафилон ва харидорон.

Дар ин ҷо ту метавонӣ:
▫️ Эълонҳоро тамошо кунӣ
▫️ Маълумоти профилатро бинӣ
▫️ Қоидаҳои платформаро омӯзӣ
▫️ Аз имкониятҳои платформа истифода барӣ

<i>Интихоби худро аз меню анҷом деҳ.</i>
"""

HELP_TEXT = """
<b>📚 ДАСТУРИ MASTER X</b>

Фармонҳои асосӣ:

/start — оғоз кардани бот
/menu — менюи асосӣ
/profile — профили ман
/lots — эълонҳои дастрас
/rules — қоидаҳои платформа
/accept — қабул кардани қоидаҳо
/help — дастур

<b>Маълумоти муҳим:</b>
MASTER X платформаи миёнарав ва низоми бақайдгирии эълонҳо мебошад.

MASTER X худ кафолат намедиҳад ва фурӯшанда ё кафил нест.
Шартҳои хизматрасонии кафилон мустақилона аз ҷониби худи онҳо муайян карда мешаванд.
"""

RULES_TEXT = """
<b>📜 ҚОИДАҲОИ MASTER X</b>

<b>1. Истифодаи платформа</b>
Ҳар як корбар бояд маълумоти дуруст пешниҳод кунад.

<b>2. Эълонҳо</b>
Маълумоти эълон бояд дақиқ ва ба воқеият мувофиқ бошад.

<b>3. Кафилон</b>
Кафилон мустақилона фаъолият мекунанд.
MASTER X кафолати мустақим намедиҳад.

<b>4. Масъулият</b>
Пеш аз ҳар гуна муомила шартҳо, нарх ва маълумоти тарафҳоро бодиққат санҷед.

<b>5. Қоидаҳои умумӣ</b>
Истифодаи платформа маънои риояи қоидаҳои онро дорад.

<i>Барои тасдиқи шиносоӣ бо қоидаҳо тугмаи зерро пахш кун.</i>
"""


# =========================================================
# KEYBOARDS
# =========================================================

def main_keyboard(is_founder: bool = False):
    rows = [
        [
            InlineKeyboardButton(
                text="🛍 Эълонҳо",
                callback_data="menu_lots"
            ),
            InlineKeyboardButton(
                text="👤 Профили ман",
                callback_data="menu_profile"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📜 Қоидаҳо",
                callback_data="menu_rules"
            ),
            InlineKeyboardButton(
                text="ℹ️ Дастур",
                callback_data="menu_help"
            ),
        ],
    ]

    if is_founder:
        rows.append([
            InlineKeyboardButton(
                text="👑 Founder",
                callback_data="menu_founder"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Менюи асосӣ",
                    callback_data="menu_home"
                )
            ]
        ]
    )


def rules_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Қоидаҳоро қабул мекунам",
                    callback_data="accept_rules"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Бозгашт",
                    callback_data="menu_home"
                )
            ]
        ]
    )


def lot_keyboard(lot_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Тафсилоти эълон",
                    callback_data=f"lot_{lot_code}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ба эълонҳо",
                    callback_data="menu_lots"
                )
            ]
        ]
    )


# =========================================================
# HELPERS
# =========================================================

def get_user_name(message: Message) -> str:
    user = message.from_user
    if not user:
        return "Корбар"

    return escape(user.first_name or "Корбар")


def is_founder(user_id: int) -> bool:
    return bool(FOUNDER_ID and user_id == FOUNDER_ID)


def safe_log(user_id: int, action: str, details=None):
    try:
        services.log(
            actor_id=user_id,
            action=action,
            details=details or {}
        )
    except Exception:
        logger.exception("Failed to write audit log")


def register_telegram_user(message: Message):
    user = message.from_user

    if not user:
        return None

    try:
        services.register_user(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name
        )
        return services.get_user_profile(user.id)

    except Exception:
        logger.exception("User registration failed")
        return None


def format_lot(lot: dict) -> str:
    title = escape(str(lot.get("title") or "Бе ном"))
    code = escape(str(lot.get("lot_code") or "—"))
    description = escape(str(lot.get("description") or "Маълумот нест"))
    category = escape(str(lot.get("category") or "—"))
    platform = escape(str(lot.get("platform") or "—"))
    price = escape(str(lot.get("price") or "—"))
    status = escape(str(lot.get("status") or "available"))

    return (
        "<b>🛍 МАЪЛУМОТИ ЭЪЛОН</b>\n\n"
        f"<b>📌 Ном:</b> {title}\n"
        f"<b>🆔 Lot ID:</b> <code>{code}</code>\n"
        f"<b>📂 Категория:</b> {category}\n"
        f"<b>🎮 Платформа:</b> {platform}\n"
        f"<b>💰 Нарх:</b> {price}\n"
        f"<b>📊 Ҳолат:</b> {status}\n\n"
        f"<b>📝 Тавсиф:</b>\n{description}\n\n"
        "<i>Пеш аз муомила маълумоти эълонро бодиққат санҷед.</i>"
    )


# =========================================================
# START AND MENU COMMANDS
# =========================================================

@router.message(CommandStart())
async def start_handler(message: Message):
    register_telegram_user(message)

    name = get_user_name(message)
    founder = is_founder(message.from_user.id)

    safe_log(
        message.from_user.id,
        "user_started_bot"
    )

    await message.answer(
        WELCOME_TEXT.format(name=name),
        reply_markup=main_keyboard(founder),
        parse_mode=ParseMode.HTML
    )


@router.message(Command("menu"))
async def menu_handler(message: Message):
    await message.answer(
        "<b>✦ MASTER X — МЕНЮ</b>\n\n"
        "Лутфан, бахши лозимаро интихоб кун:",
        reply_markup=main_keyboard(
            is_founder(message.from_user.id)
        ),
        parse_mode=ParseMode.HTML
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        HELP_TEXT,
        reply_markup=back_keyboard(),
        parse_mode=ParseMode.HTML
    )


# =========================================================
# PROFILE
# =========================================================

async def show_profile(message: Message):
    user_id = message.from_user.id

    try:
        profile = services.get_user_profile(user_id)

        if not profile:
            profile = register_telegram_user(message)

        if not profile:
            await message.answer(
                "⚠️ Профилро ҳоло гирифтан имкон надорад.",
                reply_markup=back_keyboard()
            )
            return

        username = profile.get("username") or "Нест"
        full_name = profile.get("full_name") or "Нест"
        status = "Фаъол" if profile.get("is_active", True) else "Ғайрифаъол"

        text = (
            "<b>👤 ПРОФИЛИ ШУМО</b>\n\n"
            f"<b>🆔 Telegram ID:</b> <code>{user_id}</code>\n"
            f"<b>📛 Ном:</b> {escape(str(full_name))}\n"
            f"<b>🔗 Username:</b> @{escape(str(username)) if username != 'Нест' else 'Нест'}\n"
            f"<b>📊 Ҳолат:</b> {status}\n\n"
            "<i>Ин маълумот аз профили сабтшуда гирифта шудааст.</i>"
        )

        await message.answer(
            text,
            reply_markup=back_keyboard(),
            parse_mode=ParseMode.HTML
        )

    except Exception:
        logger.exception("Profile display failed")
        await message.answer(
            "❌ Ҳангоми гирифтани профил хатогӣ рух дод.",
            reply_markup=back_keyboard()
        )


@router.message(Command("profile"))
async def profile_command(message: Message):
    await show_profile(message)


# =========================================================
# LOTS
# =========================================================

async def show_lots(message: Message):
    try:
        lots = services.list_lots(
            status="available",
            limit=10,
            offset=0
        )

        if not lots:
            await message.answer(
                "<b>🛍 ЭЪЛОНҲО</b>\n\n"
                "Ҳоло эълони дастрас вуҷуд надорад.\n"
                "<i>Баъдтар боз санҷед.</i>",
                reply_markup=back_keyboard(),
                parse_mode=ParseMode.HTML
            )
            return

        await message.answer(
            "<b>🛍 ЭЪЛОНҲОИ ДАСТРАС</b>\n\n"
            "<i>Рӯйхати эълонҳои фаъол:</i>",
            parse_mode=ParseMode.HTML
        )

        for lot in lots:
            code = str(lot.get("lot_code") or "")
            text = format_lot(lot)

            if code:
                await message.answer(
                    text,
                    reply_markup=lot_keyboard(code),
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.answer(
                    text,
                    parse_mode=ParseMode.HTML
                )

    except Exception:
        logger.exception("Lots list failed")
        await message.answer(
            "❌ Ҳангоми гирифтани эълонҳо хатогӣ рух дод.",
            reply_markup=back_keyboard()
        )


@router.message(Command("lots"))
async def lots_command(message: Message):
    await show_lots(message)


@router.message(Command("lot"))
async def lot_command(message: Message):
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "Намунаи истифода:\n"
            "<code>/lot LOT-001</code>",
            parse_mode=ParseMode.HTML
        )
        return

    lot_code = parts[1].strip()

    await show_single_lot(message, lot_code)


async def show_single_lot(message: Message, lot_code: str):
    try:
        lot = services.get_lot(lot_code)

        if not lot:
            await message.answer(
                "❌ Эълон ёфт нашуд.",
                reply_markup=back_keyboard()
            )
            return

        await message.answer(
            format_lot(lot),
            reply_markup=back_keyboard(),
            parse_mode=ParseMode.HTML
        )

    except Exception:
        logger.exception("Single lot display failed")
        await message.answer(
            "❌ Ҳангоми кушодани эълон хатогӣ рух дод.",
            reply_markup=back_keyboard()
        )


# =========================================================
# RULES
# =========================================================

@router.message(Command("rules"))
async def rules_command(message: Message):
    await message.answer(
        RULES_TEXT,
        reply_markup=rules_keyboard(),
        parse_mode=ParseMode.HTML
    )


@router.message(Command("accept"))
async def accept_rules_command(message: Message):
    await accept_user_rules(message)


async def accept_user_rules(message: Message):
    try:
        result = services.accept_rules(
            user_id=message.from_user.id,
            rules_version="1.0"
        )

        safe_log(
            message.from_user.id,
            "rules_accepted",
            {"rules_version": "1.0"}
        )

        await message.answer(
            "<b>✅ Қоидаҳо қабул шуданд.</b>\n\n"
            "Ташаккур барои шиносоӣ бо қоидаҳои MASTER X.",
            reply_markup=main_keyboard(
                is_founder(message.from_user.id)
            ),
            parse_mode=ParseMode.HTML
        )

    except Exception:
        logger.exception("Rules acceptance failed")
        await message.answer(
            "❌ Қабули қоидаҳо муваффақ нашуд. Баъдтар кӯшиш кунед.",
            reply_markup=back_keyboard()
        )


# =========================================================
# CALLBACKS — MAIN MENU
# =========================================================

@router.callback_query(F.data == "menu_home")
async def callback_home(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "<b>✦ MASTER X — МЕНЮИ АСОСӢ</b>\n\n"
        "Бахши лозимаро интихоб кун:",
        reply_markup=main_keyboard(
            is_founder(callback.from_user.id)
        ),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "menu_lots")
async def callback_lots(callback: CallbackQuery):
    await callback.answer()
    await show_lots(callback.message)


@router.callback_query(F.data == "menu_profile")
async def callback_profile(callback: CallbackQuery):
    await callback.answer()
    await show_profile(callback.message)


@router.callback_query(F.data == "menu_rules")
async def callback_rules(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        RULES_TEXT,
        reply_markup=rules_keyboard(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "menu_help")
async def callback_help(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        HELP_TEXT,
        reply_markup=back_keyboard(),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "accept_rules")
async def callback_accept_rules(callback: CallbackQuery):
    await callback.answer()
    await accept_user_rules(callback.message)


@router.callback_query(F.data.startswith("lot_"))
async def callback_single_lot(callback: CallbackQuery):
    await callback.answer()

    lot_code = callback.data.removeprefix("lot_")
    await show_single_lot(callback.message, lot_code)


# =========================================================
# FOUNDER MENU
# =========================================================

@router.callback_query(F.data == "menu_founder")
async def callback_founder(callback: CallbackQuery):
    if not is_founder(callback.from_user.id):
        await callback.answer(
            "⛔ Дастрасӣ иҷозат дода нашуд.",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.answer(
        "<b>👑 MASTER X — FOUNDER PANEL</b>\n\n"
        "Хуш омадед ба бахши идоракунӣ.\n\n"
        "Дар версияи ҳозира ин бахш менюи асосии Founder мебошад.\n"
        "Идоракунии каналҳо, обунаҳо, пардохтҳо ва ҳисоботҳо "
        "бояд бо модулҳои махсус пайваст карда шавад.",
        reply_markup=back_keyboard(),
        parse_mode=ParseMode.HTML
    )


# =========================================================
# UNKNOWN COMMAND / MESSAGE
# =========================================================

@router.message()
async def unknown_message_handler(message: Message):
    if not message.text:
        await message.answer(
            "Лутфан, аз менюи бот истифода бар.",
            reply_markup=main_keyboard(
                is_founder(message.from_user.id)
            )
        )
        return

    await message.answer(
        "🤔 Ман ин фармонро нашинохтам.\n\n"
        "Барои дидани имкониятҳо /menu ё /help-ро пахш кун.",
        reply_markup=main_keyboard(
            is_founder(message.from_user.id)
        )
            )
    
