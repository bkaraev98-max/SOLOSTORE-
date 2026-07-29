import telebot
from telebot import types

# Токени нави боти шумо
TOKEN = "8908899314:AAGd1VONMYnsLj3KetU4vLPEhXLWtLnkdcQ"
bot = telebot.TeleBot(TOKEN)

# Каналҳои шумо
CHANNEL_METRO = "@metrosolostore"
CHANNEL_ACCOUNT = "@solostoretj"

# Базаи вақтии хотираи бот барои баланс ва молҳо
users_balance = {}  
items_list = [
    {"id": 1, "name": "Аккаунти Metro Royale (60 Левел)", "price": 150, "desc": "Лоббии бой, лути қиммат"},
    {"id": 2, "name": "Вагон / 10 Миллион Баланс", "price": 80, "desc": "Интиқоли фаврӣ"}
]

# Санҷиши обуна ба ҳарду канал
def check_subscriptions(user_id):
    try:
        m1 = bot.get_chat_member(CHANNEL_METRO, user_id)
        m2 = bot.get_chat_member(CHANNEL_ACCOUNT, user_id)
        
        sub1 = m1.status in ['member', 'administrator', 'creator']
        sub2 = m2.status in ['member', 'administrator', 'creator']
        
        return sub1 and sub2
    except:
        return False

# Кнопкаҳои асосии бот
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 Молҳо ва Аккаунтҳо", "💰 Баланси ман")
    markup.row("📥 Пур кардани баланс", "📞 Тамос бо Админ")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Санҷиши ҳатмии обуна
    if not check_subscriptions(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Канали Metro Royale", url="https://t.me/metrosolostore"))
        markup.add(types.InlineKeyboardButton("📢 Канали Аккаунт Фурӯш", url="https://t.me/solostoretj"))
        markup.add(types.InlineKeyboardButton("💬 Гурӯҳи SOLOSTORE.TJ", url="https://t.me/SOLOSTORE_TJ")) # Линки гурӯҳ
        markup.add(types.InlineKeyboardButton("🔄 Санҷиши обуна", callback_data="check_sub"))
        
        bot.send_message(
            message.chat.id,
            "❌ **Барои истифода аз бот, лутфан аввал ба каналҳо ва гурӯҳи мо обуна шавед!**",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    user_name = message.from_user.first_name
    bot.send_message(
        message.chat.id, 
        f"Салом, {user_name}! 👋\nХуш омадед ба боти расмии **SOLOSTORE.TJ** 🎮",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "Ташаккур, шумо ба ҳамаи манбаъҳо обуна шудед! ✅")
        bot.send_message(call.id, "Бот ҳозир пурра фаъол шуд! Фармони /start-ро занед.", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "Шумо ҳанӯз ба ҳамаи каналҳо обуна нашудаед! ❌", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "🛒 Молҳо ва Аккаунтҳо")
def show_items(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Лутфан аввал ба каналҳо обуна шавед!")
        return
        
    for item in items_list:
        text = f"🔥 *{item['name']}*\n💵 Нарх: {item['price']} сомонӣ\n📝 Тавсиф: {item['desc']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Харидани мол", callback_data=f"buy_{item['id']}"))
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💰 Баланси ман")
def check_balance(message):
    user_id = message.from_user.id
    balance = users_balance.get(user_id, 0)
    bot.send_message(message.chat.id, f"💳 Баланси кунунии шумо: *{balance} сомонӣ*", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📥 Пур кардани баланс")
def top_up(message):
    bot.send_message(message.chat.id, "Барои пур кардани баланс ба гурӯҳи **SOLOSTORE.TJ** муроҷиат кунед ва скриншоти пардохтро фиристед.")

@bot.message_handler(func=lambda message: message.text == "📞 Тамос бо Админ")
def contact_admin(message):
    bot.send_message(message.chat.id, "Барои тамос бо админ ба гурӯҳи **SOLOSTORE.TJ** нависед.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_item(call):
    user_id = call.from_user.id
    item_id = int(call.data.split('_')[1])
    item = next((i for i in items_list if i['id'] == item_id), None)
    if not item:
        return
    
    current_balance = users_balance.get(user_id, 0)
    if current_balance >= item['price']:
        users_balance[user_id] = current_balance - item['price']
        bot.answer_callback_query(call.id, "Харид бомуваффақият анҷом ёфт! ✅")
        bot.send_message(call.id, f"🎉 Шумо моли *{item['name']}*-ро бо муваффақият харидед!")
    else:
        bot.answer_callback_query(call.id, "Баланси шумо барои харид кофӣ нест! ❌", show_alert=True)

print("Бот бо токени нав ва шартҳои SOLOSTORE ба кор даромад...")
bot.infinity_polling()
        
