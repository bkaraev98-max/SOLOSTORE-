import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import MASTER_BOT_TOKEN
from core.database import Database
from bots.master import router as master_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting MasterX Manager...")

    database = Database()
    database.initialize()

    bot = Bot(
        token=MASTER_BOT_TOKEN
    )

    dispatcher = Dispatcher()

    dispatcher.include_router(
        master_router
    )

    try:
        # Агар webhook-и кӯҳна вуҷуд дошта бошад,
        # онро тоза мекунем, то polling conflict накунад.
        await bot.delete_webhook(
            drop_pending_updates=True
        )

        logger.info("Webhook cleared.")
        logger.info("MasterX Manager is running.")

        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )

    except Exception:
        logger.exception(
            "MasterX Manager stopped because of an error."
        )
        raise

    finally:
        await bot.session.close()
        logger.info("Bot session closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MasterX Manager stopped manually.")
