import telebot
from telebot import types

# Токени ту, ки фиристодӣ
TOKEN = "8595575038:AAHV531OhJlMrIjk_sVy1Rjd_Y88GtAyrlU"
ADMIN_ID = "@YouTubefaizulo"  # Админи бот

bot = telebot.TeleBot(TOKEN)

# 1. Фармони Start бо тугмаҳои премиуми зебо
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    # Матни хушомадгӯӣ бо забони тоҷикӣ
    welcome_text = (
        f"✨ **Салом, {user_name}!** ✨\n\n"
        f"Бисёр хуш омадед ба боти расмии мо! Ин ҷо шумо метавонед аз хизматрасониҳо истифода баред, "
        f"каналҳо ва гурӯҳҳои моро пайгирӣ кунед.\n\n"
        f"Мулки худро бо мо боэътимод ва бехатар хариду фурӯш кунед! 🚀"
    )

    # Сохтани тугмаҳои شیشه‌ای (Inline Keyboards) бо дизайн ва эмодзиҳо
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_channel = types.InlineKeyboardButton("📢 Канали расмӣ", url="https://t.me/Faizuloucshop")
    btn_group = types.InlineKeyboardButton("💬 Гурӯҳи муҳокима", url="https://t.me/faizulochat")
    btn_deals = types.InlineKeyboardButton("🛡 Канали Сделкаҳо", url="https://t.me/sdelkoifaizulo")
    btn_reviews = types.InlineKeyboardButton("⭐ Отзивҳо (Шарҳҳо)", url="https://t.me/otzivfaizulo")
    btn_admin = types.InlineKeyboardButton("👤 Тамос бо Админ", url=f"https://t.me/YouTubefaizulo")
    btn_help = types.InlineKeyboardButton("ℹ️ Маълумот", callback_data="help_info")

    markup.add(btn_channel, btn_group)
    markup.add(btn_deals, btn_reviews)
    markup.add(btn_admin, btn_help)

    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# 2. Коркарди тугмаи "Маълумот"
@bot.callback_query_handler(func=lambda call: call.data == "help_info")
def callback_help(call):
    help_text = (
        "📌 **Маълумот дар бораи бот:**\n\n"
        "• Ин бот барои осон кардани робитаи шумо бо мо сохта шудааст.\n"
        "• Ҳамаи хариду фурӯшҳо тавассути канали сделкаҳо гузаронида мешаванд.\n"
        f"• Админи асосӣ: {ADMIN_ID}\n\n"
        "Агар саволе дошта бошед, бемалол ба админ нависед!"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Ба қафо", callback_data="go_back")
    markup.add(btn_back)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=help_text, parse_mode="Markdown", reply_markup=markup)

# Тугмаи баргашт ба менюи асосӣ
@bot.callback_query_handler(func=lambda call: call.data == "go_back")
def callback_back(call):
    send_welcome(call.message)

# 3. Ҷавоб ба паёмҳои оддии истифодабарандагон бо меҳрубонӣ
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    markup = types.InlineKeyboardMarkup()
    btn_admin = types.InlineKeyboardButton("👤 Навиштан ба Админ", url=f"https://t.me/YouTubefaizulo")
    markup.add(btn_admin)
    
    bot.reply_to(
        message, 
        "Паёми шумо қабул шуд! 📩\nАгар ба шумо кӯмак лозим бошад ё хоҳед сделка кунед, лутфан мустақиман ба админ муроҷиат кунед:", 
        reply_markup=markup
    )

# Оғози кор ва чопи хабар дар консол
print("Бот бо муваффақият ба кор даромад ва омодаи хизмат аст...")
bot.infinity_polling()

