import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("8636114621:AAErp00GYBoMPIpsjvReJ8JBnSl4td2haM", "")
ADMIN_ID = int(os.getenv("@pubgertjk3", "123456789")) # ID-и соҳиби бот ё фурӯшанда
PROFIT_MARGIN = 2.0 # 2 сомонӣ фойда барои соҳиби бот

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Базаи оддии хотира барои нигоҳ доштани баланси корбарон
user_balances = {}

class BuyState(StatesGroup):
    waiting_for_pubg_id = State()
    waiting_for_withdrawal_amount = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Баланси ман", callback_data="balance")
    builder.button(text="🛒 Харидани UC", callback_data="buy_uc")
    builder.button(text="💸 Вивест (Бароваrтани пул)", callback_data="withdraw")
    builder.adjust(1)
    
    await message.answer(
        "Салом! Хуш омадед ба боти фурӯши ЮС. 🎮🔥\n"
        "Аз тугмаҳои зерин истифода баред:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "balance")
async def show_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = user_balances.get(user_id, 0.0)
    await callback.message.answer(f"💳 Баланси ҷории шумо: {balance} сомонӣ")
    await callback.answer()

@dp.callback_query(F.data == "buy_uc")
async def buy_uc_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Иلطфао PUBG ID-и худро фиристед то харид оғоз шавад:")
    await state.set_state(BuyState.waiting_for_pubg_id)
    await callback.answer()

@dp.message(BuyState.waiting_for_pubg_id)
async def process_pubg_id(message: types.Message, state: FSMContext):
    pubg_id = message.text
    user_id = message.from_user.id
    
    # Масоили ҳисоб ва ҷудо кардани 2 сомонӣ фойда
    # Ин ҷо нархи аслӣ ва фоида ҳисоб карда мешавад
    base_price = 50.0  # Масалан нархи аслии UC
    total_price = base_price + PROFIT_MARGIN # 52 сомонӣ бо ҳисоби 2 сомонӣ фойдаи соҳиби бот
    
    # Хабар додан ба соҳиби бот/фурӯшанда
    await bot.send_message(
        ADMIN_ID,
        f"🚨 **Фармоиши нави UC!**\n"
        f"👤 Харидор: @{message.from_user.username or message.from_user.first_name} (ID: {user_id})\n"
        f"🎯 PUBG ID: `{pubg_id}`\n"
        f"💵 Маблағи умумӣ: {total_price} сомонӣ (Аз ҷумла {PROFIT_MARGIN} с. фоида)"
    )
    
    await message.answer(f"Фармоиши шумо қабул шуд! Нархи умумӣ: {total_price} сомонӣ (бо назардошти хизматрасонӣ). Ба زӯдӣ UC ба ID-и шумо интиқол дода мешавад.")
    await state.clear()

@dp.callback_query(F.data == "withdraw")
async def withdraw_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Маблағеро, ки мехоҳед вивест (баровард) кунед, нависед:")
    await state.set_state(BuyState.waiting_for_withdrawal_amount)
    await callback.answer()

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
