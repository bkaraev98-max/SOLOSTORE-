from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.database import Database
from core.security import is_master_admin


router = Router()

db = Database()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    user = message.from_user

    if user is None:
        return

    db.upsert_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    if not is_master_admin(user.id):
        await message.answer(
            "⛔ Дастрасӣ иҷозат дода нашуд."
        )
        return

    db.add_audit_log(
        actor_telegram_id=user.id,
        action="MASTER_START",
    )

    await message.answer(
        "𒆜 𝑴𝒂𝒔𝒕𝒆𝒓𝑿 𝑴𝒂𝒏𝒂𝒈𝒆𝒓 ⚡\n\n"
        "👑 Master Panel фаъол аст.\n\n"
        "Системаро аз ҳамин ҷо идора мекунем."
    )


@router.message()
async def master_message_handler(message: Message) -> None:
    user = message.from_user

    if user is None:
        return

    if not is_master_admin(user.id):
        return

    await message.answer(
        "⚙️ Функсияи идоракунӣ ҳоло дар марҳилаи сохтан аст."
    )
