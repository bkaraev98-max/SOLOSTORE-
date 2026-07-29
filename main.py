import telebot
from telebot import types

# Токени нав
TOKEN = "8934022770:AAEstorPqKu75e1FvaiZ__PUR2W3mh8Q5HU"
ADMIN_USERNAME = "@xs_anush19"
CHANNEL_SHOP = "https://t.me/ANUSHuc_SHOP"
CHANNEL_REVIEWS = "https://t.me/zvezdaotviz"
GROUP_CHAT = "https://t.me/chatanush"

# Истифодаи объекти нав барои пешгирии муноқиша (Conflict 409)
bot = telebot.TeleBot(TOKEN)

# Рӯйхати дақиқи ҳақоратҳо ва суханҳои қабеҳе, ки бояд манъ шаванд
FORBIDDEN_PHRASES = [
    "очата мегом", "мегомта", "сука", "сука", "да даҳат мегом", 
    "кси апа", "кси хоҳар", "хоҳарта гом", "ҷлаб", "кун", "мунҷ", 
    "harom", "suk", "durto", "pidar", "blyat", "nahuj", "ebal", "блять"
]

# ---------------------------------------------------------
# 1. СТАРТ ВА МЕНЮИ АСОСӢ (ДАР ЧАТИ ШАХСӢ)
# ---------------------------------------------------------
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type != 'private':
        return
        
    user_firstname = message.from_user.first_name
    
    greeting_text = (
        f"🌟 **Салом, ҳурматли {user_firstname}!** 🌟\n\n"
        f"Хуш омадед ба маркази хизматрасонии мо! Ман ёвари худкори шумо ҳастам. "
        f"Ҳамаи маҳсулот ва маълумоти лозимиро дар ин ҷо пайдо карда метавонед.\n\n"
        f"📌 **Платформаҳои расмии мо:**\n"
        f"• Канали дӯкон: {CHANNEL_SHOP}\n"
        f"• Канали отзивҳо: {CHANNEL_REVIEWS}\n"
        f"• Гурӯҳи муҳокима: {GROUP_CHAT}\n\n"
        f"💡 *Агар саволе дошта бошед, ки ман ҷавоб дода наметавонам, мустақиман ба владетс {ADMIN_USERNAME} муроҷиат кунед!*"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    b_shop = types.InlineKeyboardButton("🛍 Канали Дӯкон", url=CHANNEL_SHOP)
    b_rev = types.InlineKeyboardButton("⭐ Отзивҳо", url=CHANNEL_REVIEWS)
    b_grp = types.InlineKeyboardButton("💬 Гурӯҳи Чат", url=GROUP_CHAT)
    b_adm = types.InlineKeyboardButton("👑 Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    b_info = types.InlineKeyboardButton("ℹ️ Маълумоти бештар", callback_data="extra_info")
    
    markup.add(b_shop, b_rev)
    markup.add(b_grp, b_adm)
    markup.add(b_info)

    bot.send_message(message.chat.id, greeting_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "extra_info")
def extra_info_callback(call):
    info_text = (
        "📖 **Маълумотномаи бот:**\n\n"
        "• Ин система ба таври худкор ва 24/7 фаъолият мекунад.\n"
        "• Шумо метавонед маҳсулоти худро интихоб кунед ва назарҳоро хонед.\n"
        f"• Сарвар ва масъули асосӣ: {ADMIN_USERNAME}\n\n"
        "Марҳамат, саволҳои худро нависед!"
    )
    markup = types.InlineKeyboardMarkup()
    b_back = types.InlineKeyboardButton("◀️ Баргаштан", callback_data="back_to_home")
    markup.add(b_back)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                text=info_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_home")
def back_home_callback(call):
    start_command(call.message)


# ---------------------------------------------------------
# 2. МОДЕРАТОР ВА ИДОРАКУНИИ ГУРУҲ
# ---------------------------------------------------------

# Истиқболи аъзои нав ба гурӯҳ
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_comer(message):
    for new_user in message.new_chat_members:
        name = new_user.first_name
        msg = (
            f"👋 Салом, **{name}**! Хуш омадед ба гурӯҳи мо! 🎉\n\n"
            f"⚠️ **Қоидаи асосӣ:** Лутфан дар гурӯҳ дашном ва суханҳои қабеҳ (аз ҷумла суханҳои паст) назанед! Дар сурати риоя накардан паём нест карда мешавад.\n"
            f"🛒 Канали мо: {CHANNEL_SHOP}\n"
            f"👑 Владелетс: {ADMIN_USERNAME}"
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# Назорати матнҳои гурӯҳ (Мониторинги дашномҳои сахт ва номи Ануш)
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def group_super_vision(message):
    if not message.text:
        return
        
    txt_lower = message.text.lower()
    
    # 1. Санҷиши дашномҳо ва суханҳои қабеҳи воридшуда
    for bad in FORBIDDEN_PHRASES:
        if bad in txt_lower:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(
                    message.chat.id, 
                    f"🚫 **{message.from_user.first_name}**, истифодаи суханҳои қабеҳ ва дашном дар ин гурӯҳ қатъиян манъ аст! Паёми шумо тоза карда шуд."
                )
            except Exception:
                pass
            return

    # 2. Агар касе номи "Ануш"-ро гирифт
    if "ануш" in txt_lower:
        alert_msg = f"✨ Диққат! Касе номи **Ануш**-ро гирифт! Владелетси мо ва сарвари ин корҳо: {ADMIN_USERNAME} 👑"
        bot.reply_to(message, alert_msg, parse_mode="Markdown")
        return

    # 3. Ҷавоби худкори умумӣ ба саволҳо дар гурӯҳ
    if any(k in txt_lower for k in ["савол", "нарх", "чихел", "кумак", "помощь", "?"]):
        ans_grp = (
            f"💬 Саволи шумо қабул шуд! Агар роҳбарон ё иштирокчиён ҷавоб дода натавонанд, "
            f"лутфан мустақиман ба владетс {ADMIN_USERNAME} муроҷиат кунед ё ба ин канал нигаред: {CHANNEL_SHOP}"
        )
        bot.reply_to(message, ans_grp, parse_mode="Markdown")


# ---------------------------------------------------------
# 3. ҶАВОБИ ХУДКОР ДАР ЛИЧКА (PRIVATE CHAT)
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def private_auto_reply(message):
    content = message.text.lower()
    
    if "нарх" in content or "товар" in content or "китоб" in content:
        reply = f"📦 Маълумот дар бораи молҳо ва нархҳо дар канали дӯкон ҷойгир аст: {CHANNEL_SHOP}\n\nБарои харид ба владетс {ADMIN_USERNAME} нависед!"
    elif "отзив" in content or "отзыв" in content or "назар" in content:
        reply = f"⭐ Шарҳ ва отзивҳои мизоҷонро инҷо тамошо кунед: {CHANNEL_REVIEWS}"
    elif "салом" in content or "хайр" in content:
        reply = f"Салому алайкум! Чӣ тавр ба шумо кӯмак расонам? Барои маълумоти пурра ба владелетс {ADMIN_USERNAME} нависед."
    else:
        reply = (
            f"🤖 Паёми шумо қабул шуд. Ман дархости шуморо қабул кардам, лекин барои тафсилоти бештар "
            f"беҳтар аст мустақиман ба владетс ва админи асосӣ {ADMIN_USERNAME} муроҷиат кунед!"
        )

    markup = types.InlineKeyboardMarkup()
    b_admin = types.InlineKeyboardButton("👤 Навиштан ба Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    markup.add(b_admin)

    bot.reply_to(message, reply, reply_markup=markup, parse_mode="Markdown")


# Оғози бот бо тоза кардани дархостҳои куҳна (пешгирии хатои 409)
print("Бот бо токени нав ва муҳофизати пурқувват ба кор даромад...")
bot.infinity_polling(skip_pending=True)
