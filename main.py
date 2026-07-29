import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Токени боти худро аз BotFather инҷо гузоред
TOKEN = "8171911240:AAHBabUEVQ_bpSNodobCBCyCx3FR1jiBN_E"

# Танзимоти холатҳо (FSM) барои қабули номи суруд аз корбар
class MusicState(StatesGroup):
    waiting_for_prompt = State()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Командаи /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Салом! Хуш омадед ба боти сурудсози мо.\n\n"
        "🎶 Барои эҷод кардани мусиқӣ лутфан тугмаи поёнро пахш кунед ё фармони /create-ро фиристед."
    )
    # Намоиши тугмаи оддӣ
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🎵 Эҷод кардани мусиқӣ")]],
        resize_keyboard=True
    )
    await message.answer("Барои оғоз тугмаро зер кунед:", reply_markup=keyboard)

# Оғози сохтани мусиқӣ
@dp.message(F.text == "🎵 Эҷод кардани мусиқӣ")
@dp.message(Command("create"))
async def start_music_creation(message: types.Message, state: FSMContext):
    await state.set_state(MusicState.waiting_for_prompt)
    await message.answer(
        "✍️ Мавзӯъ, услуб ё матни кӯтоҳи сурудеро, ки хоҳед эҷод кунед, нависед:\n"
        "(Масалан: *Трэк дар бораи мошинҳо ва шаб, услуби рэп*)"
    )

# Қабули дархост ва тавлиди суруд
@dp.message(MusicState.waiting_for_prompt)
async def process_music_prompt(message: types.Message, state: FSMContext):
    user_prompt = message.text
    
    # Хабар медиҳем, ки ҷараёни омодасозӣ рафта истодааст
    waiting_msg = await message.answer("⏳ Мусиқии шумо дар ҳоли эҷод шудан аст... Лутфан чанд лаҳза интизор шавед 🎧")
    
    # Инҷо дар оянда метавонед ботро ба API-и сурудсози AI (монанди Suno ё дигарҳо) пайваст кунед.
    # Ҳоло бошад, барои намуна мо паёми тасдиқӣ ва суруди тестоӣ мефиристем:
    
            await asyncio.sleep(3) # Хунуккунии сунъӣ барои намоиши ҷараён
    
    await bot.delete_message(chat_id=message.chat.id, message_id=waiting_msg.message_id)
    
    await message.answer(
        f"✅ **Мусиқии шумо бо муваффақият омода шуд!**\n\n"
        f"🔍 **Дархости шумо:** *{user_prompt}*\n\n"
        "🎶 *(Дар ин ҷо бот файли аудиоии MP3-ро мефиристад, вақте API-и сурудсоз пайваст карда мешавад)*"
    )
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
