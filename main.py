import telebot
from telebot import types

TOKEN = "8470175020:AAGQKuU7Sx2x57ySrVc1vuCMyuQkIH2Qglg"
ADMIN_USERNAME = "@xs_anush19"
CHANNEL_SHOP = "https://t.me/ANUSHuc_SHOP"
CHANNEL_REVIEWS = "https://t.me/zvezdaotviz"
GROUP_CHAT = "https://t.me/chatanush"

bot = telebot.TeleBot(TOKEN)

FORBIDDEN_WORDS = [
    "очата мегом", "мегомта", "сука", "да даҳат мегом", 
    "кси апа", "кси хоҳар", "хоҳарта гом", "ҷлаб", "кун", 
    "мунҷ", "harom", "suk", "durto", "pidar", "blyat", 
    "nahuj", "ebal", "блять", "ебать", "хуй", "пидор"
]

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return
    name = message.from_user.first_name
    text = (
        f"Салом, ҳурматли {name}!\n\n"
        f"Хуш омадед ба маркази хизматрасонии мо. Ман ёвари худкори шумо ҳастам.\n\n"
        f"Платформаҳои расмии мо:\n"
        f"• Канали дӯкон: {CHANNEL_SHOP}\n"
        f"• Канали отзивҳо: {CHANNEL_REVIEWS}\n"
        f"• Гурӯҳи муҳокима: {GROUP_CHAT}\n\n"
        f"Агар саволе дошта бошед, ба владелетс {ADMIN_USERNAME} муроҷиат кунед!"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Канали Дӯкон", url=CHANNEL_SHOP),
        types.InlineKeyboardButton("Отзивҳо", url=CHANNEL_REVIEWS),
        types.InlineKeyboardButton("Гурӯҳи Чат", url=GROUP_CHAT),
        types.InlineKeyboardButton("Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(content_types=['new_chat_members'])
def new_member(message):
    for user in message.new_chat_members:
        bot.send_message(
            message.chat.id,
            f"Салом, {user.first_name}! Хуш омадед ба гурӯҳи мо.\n"
            f"Қоида: Дар гурӯҳ навиштани дашном ва суханҳои қабеҳ қатъиян манъ аст!\n"
            f"Админ: {ADMIN_USERNAME}"
        )

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def group_handler(message):
    if not message.text:
        return
    txt = message.text.lower()
    
    for word in FORBIDDEN_WORDS:
        if word in txt:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"{message.from_user.first_name}, истифодаи суханҳои қабеҳ манъ аст!")
            except:
                pass
            return

    if "ануш" in txt:
        bot.reply_to(message, f"Диққат! Касе номи Ануш-ро гирифт! Владелетс: {ADMIN_USERNAME}")
        return

@bot.message_handler(func=lambda msg: msg.chat.type == 'private')
def private_handler(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Навиштан ба Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
    bot.reply_to(message, f"Паёми шумо қабул шуд! Барои маълумоти пурра ба владелетс {ADMIN_USERNAME} нависед.", reply_markup=markup)

print("Бот ба кор оғоз кард...")
bot.infinity_polling(skip_pending=True)
