import telebot
from telebot import types

# Токени ту
TOKEN = "8956371122:AAGMV0Wob4Q-AKwNqXXSnrRBHbLeKqQiIHg"
ADMIN_USERNAME = "@xs_anush19"
CHANNEL_SHOP = "https://t.me/ANUSHuc_SHOP"
CHANNEL_REVIEWS = "https://t.me/zvezdaotviz"
GROUP_CHAT = "https://t.me/chatanush"

bot = telebot.TeleBot(TOKEN)

FORBIDDEN_PATTERNS = [
    "очата мегом", "мегомта", "сука", "да даҳат мегом", 
    "кси апа", "кси хоҳар", "хоҳарта гом", "ҷлаб", "кун", 
    "мунҷ", "harom", "suk", "durto", "pidar", "blyat", 
    "nahuj", "ebal", "блять", "сука", "ебать", "хуй", "пидор"
]

@bot.message_handler(commands=['start'])
def start_handler(message):
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
        f"Агар саволе дошта бошед, мустақиман ба владелетс {ADMIN_USERNAME} муроҷиат кунед!"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("Канали Дӯкон", url=CHANNEL_SHOP)
    b2 = types.InlineKeyboardButton("Отзивҳо", url=CHANNEL_REVIEWS)
    b3 = types.InlineKeyboardButton("Гурӯҳи Чат", url=GROUP_CHAT)
    b4 = types.InlineKeyboardButton("Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    markup.add(b1, b2)
    markup.add(b3, b4)

    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_user(message):
    for user in message.new_chat_members:
        fullname = user.first_name
        msg = (
            f"Салом, {fullname}! Хуш омадед ба гурӯҳи мо!\n\n"
            f"Қоидаи қатъӣ: Дар гурӯҳ навиштани дашном ва суханҳои қабеҳ манъ аст!\n\n"
            f"Канали расмиамон: {CHANNEL_SHOP}\n"
            f"Админ: {ADMIN_USERNAME}"
        )
        bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def group_security_system(message):
    if not message.text:
        return
        
    text_clean = message.text.lower()
    
    for bad_word in FORBIDDEN_PATTERNS:
        if bad_word in text_clean:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(
                    message.chat.id,
                    f"{message.from_user.first_name}, истифодаи суханҳои қабеҳ дар ин гурӯҳ манъ аст!"
                )
            except Exception:
                pass
            return

    if "ануш" in text_clean:
        alert = f"Диққат! Касе номи Ануш-ро гирифт! Владелетс: {ADMIN_USERNAME}"
        bot.reply_to(message, alert)
        return

@bot.message_handler(func=lambda message: message.chat.type == 'private')
def private_ai_handler(message):
    txt = message.text.lower()
    
    if "нарх" in txt or "цена" in txt or "товар" in txt:
        response = f"Маълумот оид ба молҳо дар канали расмии мо мавҷуд аст: {CHANNEL_SHOP}\n\nБарои харид ба {ADMIN_USERNAME} нависед!"
    else:
        response = f"Паёми шумо қабул шуд! Барои маълумоти пурра ба владелетс {ADMIN_USERNAME} муроҷиат кунед."

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Навиштан ба Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))

    bot.reply_to(message, response, reply_markup=markup)

print("Бот бомуваффақият ба кор даромад...")
bot.infinity_polling(skip_pending=True)
    
