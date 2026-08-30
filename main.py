import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.executor import start_webhook

# Фаъол кардани нишон додани хатогиҳо ва маълумот дар лог
logging.basicConfig(level=logging.INFO)

# Токени боти худро ин ҷо мемонед (ё дар Render ҳамчун Environment Variable бо номи BOT_TOKEN мемонед)
TOKEN = os.getenv("BOT_TOKEN", "8636114621:AAErp00GYBoMPIpsjvReJ8JBnSl4td2haMY")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Гирифтани суроғаи сервер аз муҳити Render ба таври худкор
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else ""

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 10000))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Салом! Боти фурӯши ЮС бомуваффақият ба кор даромад ва 24/7 фаъол аст! 🎮🔥")

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.reply("Ин бот барои фармоиш ва қабули пардохтҳо сохта шудааст. Барои оғоз /start-ро пахш кунед.")

async def on_startup(dispatcher):
    if RENDER_EXTERNAL_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook бомуваффақият пайваст شد: {WEBHOOK_URL}")
    else:
        logging.warning("RENDER_EXTERNAL_URL ёфт нашуд, вале бот омода аст.")

async def on_shutdown(dispatcher):
    await bot.remove_webhook()
    logging.info("Webhook хомӯш карда шуд.")

if __name__ == '__main__':
    if RENDER_EXTERNAL_URL:
        # Кор бо Webhook барои серверҳои абрӣ (Render)
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    else:
        # Агар хоҳед муваққатан дар компютер ё телефон санҷед (Long Polling)
        from aiogram.utils import executor
        executor.start_polling(dp, skip_updates=True)
    
