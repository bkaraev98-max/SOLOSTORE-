import random
import string
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Токени боти худро аз @BotFather гирифта инҷо монед
API_TOKEN = "8171911240:AAHBabUEVQ_bpSNodobCBCyCx3FR1jiBN_E"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Функция барои сохтани калиди тасодуфӣ мисли ZOLO-1DTrial-XTUlshcNgq9i
def generate_zolo_key(days: int):
    # Муайян кардани намуди муҳлат дар ключ
    if days == 7:
        duration_str = "7DTrial"
    elif days == 60:
        duration_str = "60DTrial"
    else:
        duration_str = f"{days}DTrial"
        
    # Сохтани қисми тасодуфии ключ (харфҳо ва рақамҳо)
    letters_and_digits = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(letters_and_digits) for _ in range(16))
    
    # Муттаҳид кардани қисмҳо ба формати лозима
    key = f"ZOLO-{duration_str}-{random_part}"
    return key

# Менюи асосӣ бо тугмаҳо
def get_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔑 Гирифтани ключи 7 рӯза", callback_data="get_7d"),
        InlineKeyboardButton("🔑 Гирифтани ключи 60 рӯза", callback_data="get_60d")
    )
    return keyboard

# Фармони /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = (
        f"Салом, **{message.from_user.first_name}**! 👋\n\n"
        "Ин боти ройгони тавлиди ключҳои **Zolocheat** аст.\n"
        "Барои гирифтани ключ тугмаи лозимиро зер пахш кунед:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

# Коркарди тугмаҳо (Callback queries)
@dp.callback_query_handler(lambda c: c.data in ['get_7d', 'get_60d'])
async def process_key_generation(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    # Муайян кардани рӯзҳо вобаста ба тугмаи пахшшуда
    if callback_query.data == 'get_7d':
        days = 7
    elif callback_query.data == 'get_60d':
        days = 60
    else:
        days = 7

    # Тавлиди ключ
    new_key = generate_zolo_key(days)
    
    # Фиристодани ключ ба корбар
    response_text = (
        f"✅ **Ключи шумо омода аст!**\n\n"
        f"`{new_key}`\n\n"
        f"Мӯҳлат: **{days} рӯз**\n"
        f"⚠️ *Эзоҳ: Ин ключҳо ройгон ва тасодуфӣ тавлид шудаанд.*"
    )
    
    await bot.send_message(
        callback_query.from_user.id, 
        response_text, 
        parse_mode="Markdown", 
        reply_markup=get_main_menu()
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
        
