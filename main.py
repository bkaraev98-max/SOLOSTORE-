import telebot
from telebot import types
import re

# Токени нав ва маълумоти ту
TOKEN = "8968261391:AAFuwAUaQjx35OqrtKlNjNdcj6cvLiHEll8"
ADMIN_USERNAME = "@xs_anush19"
CHANNEL_SHOP = "https://t.me/ANUSHuc_SHOP"
CHANNEL_REVIEWS = "https://t.me/zvezdaotviz"
GROUP_CHAT = "https://t.me/chatanush"

bot = telebot.TeleBot(TOKEN)

# Рӯйхати калимаҳои қабеҳ/дашномҳо барои назорати гурӯҳ (метавонӣ зиёд кунӣ)
BAD_WORDS = ["ҷлаб", "кун", "мунҷ", "матти", "harom", "suk", "durto", "pidar", "blyat", "nahuj", "ebal"]

# ---------------------------------------------------------
# 1. ҚИСМИ ЧАТИ ШАХСӢ (PRIVATE CHAT) & START
# ---------------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private':
        return  # Дар группа фармони старт кор накунад, то халал нарасонад
        
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"✨ **Салом, {user_name}! Хуш омадед ба боти расмии мо!** ✨\n\n"
        f"Ман ёвари худкори шумо ҳастам. Шумо метавонед аз хизматрасониҳои зерин истифода баред, "
        f"молатонро интихоб кунед ё ба саволҳои худ ҷавоб гиред. 🚀\n\n"
        f"📌 **Линкҳои расмии мо:**\n"
        f"• Канали дӯкон: {CHANNEL_SHOP}\n"
        f"• Канали отзивҳо: {CHANNEL_REVIEWS}\n"
        f"• Гурӯҳи муҳокима: {GROUP_CHAT}\n\n"
        f"💡 **Лутфан, ягон савол дошта бошед, бемалол пурсед!** Агар ман кӯмак карда натавонам ё мушкиле бошад, владелетс ва админи асосӣ {ADMIN_USERNAME} ба шумо ҳатман кӯмак мекунад!"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_shop = types.InlineKeyboardButton("🛍 Канали дӯкон", url=CHANNEL_SHOP)
    btn_reviews = types.InlineKeyboardButton("⭐ Отзивҳо", url=CHANNEL_REVIEWS)
    btn_group = types.InlineKeyboardButton("💬 Гуруҳи мо", url=GROUP_CHAT)
    btn_admin = types.InlineKeyboardButton("👤 Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    btn_help = types.InlineKeyboardButton("ℹ️ Ёрӣ ва Маълумот", callback_data="help_menu")
    
    markup.add(btn_shop, btn_reviews)
    markup.add(btn_group, btn_admin)
    markup.add(btn_help)

    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "help_menu")
def callback_help(call):
    help_text = (
        "🤖 **Дастурамали истифодаи бот:**\n\n"
        "1. Ин бот ба таври худкор ба саволҳои шумо ҷавоб медиҳад.\n"
        "2. Шумо метавонед саволи худро дар бораи нарх, хариду фурӯш ё хизматрасониҳо нависед.\n"
        f"3. Дар ҳолати зарурӣ мустақиман ба владетс {ADMIN_USERNAME} муроҷиат кунед.\n\n"
        "✨ Ҳамеша дар хизмати шумоем!"
    )
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("◀️ Ба қафо", callback_data="go_back")
    markup.add(btn_back)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=help_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "go_back")
def callback_back(call):
    send_welcome(call.message)


# ---------------------------------------------------------
# 2. ИДОРАКУНИИ ГУРУҲ (GROUP AUTOMATION & MODERATION)
# ---------------------------------------------------------

# А) Истиқболи аъзои нав ба гурӯҳ
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        name = member.first_name
        greeting = (
            f"Ассалому алайкум, **{name}**! Хуш омадед ба гурӯҳи мо! 🎉\n\n"
            f"Қоидаи асосии гурӯҳ: **Дар гурӯҳ дашном ва суханҳои қабеҳ назанед!** ❌\n"
            f"Марҳамат, саволҳои худро диҳед ё ба канали мо муроҷиат кунед: {CHANNEL_SHOP}\n"
            f"Агар ба шумо кӯмак лозим шавад, владелетс {ADMIN_USERNAME} дар хизмат аст!"
        )
        bot.send_message(message.chat.id, greeting, parse_mode="Markdown")

# Б) Назорати дохили гурӯҳ (Санҷиши дашномҳо ва калимаи "Ануш")
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def group_message_handler(message):
    if not message.text:
        return
        
    text_lower = message.text.lower()
    
    # 1. Санҷиш барои суханҳои қабеҳ (Дашномҳо)
    for word in BAD_WORDS:
        if word in text_lower:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                warning_msg = bot.send_message(
                    message.chat.id, 
                    f"⚠️ **{message.from_user.first_name}**, илтимос дар гурӯҳ дашном ва суханҳои қабеҳ назанед! Инқоидаи гурӯҳ аст."
                )
                # Баъди 5 сония огоҳиро тоза мекунад
                # (барои пешгирии мушкилот метавон монд ё хориҷ кард)
            except Exception:
                pass
            return

    # 2. Агар касе калимаи "Ануш"-ро нависад
    if "ануш" in text_lower:
        alert_text = f"📢 Диққат! Яке аз иштирокчиён номи **Ануш**-ро гирифт! Владелетс ва сарвари инҷо: {ADMIN_USERNAME} 👑"
        bot.reply_to(message, alert_text, parse_mode="Markdown")
        return

    # 3. Ҷавоби худкори интеллектуалӣ ба дигар саволҳо дар гурӯҳ
    if "?" in message.text or "савол" in text_lower or "нарх" in text_lower or "канал" in text_lower:
        reply_text = (
            f"💬 Саволи шумо қабул шуд! Агар касе аз иштирокчиён ҷавоб дода натавонад, "
            f"лутфан мустақиман ба владетс {ADMIN_USERNAME} нависед ё ба канали расмии мо нигаред: {CHANNEL_SHOP}"
        )
        bot.reply_to(message, reply_text, parse_mode="Markdown")


# ---------------------------------------------------------
# 3.ҶАВОБИ ХУДКОР ДАР ЛИЧКА (AI-STYLE FALLBACK)
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def private_smart_responder(message):
    user_text = message.text.lower()
    
    # Таҳлили оддии саволҳои маъмул ва ҷавоби худкор
    if "нарх" in user_text or "цена" in user_text or "китоб" in user_text or "товар" in user_text:
        ans = f"📦 Ҳамаи молу хизматрасониҳо ва нархҳои онҳо дар канали расмии мо намоиш дода шудаанд: {CHANNEL_SHOP}\n\nБарои харид ё саволҳои мушаххас ба владелетс {ADMIN_USERNAME} нависед!"
    elif "отзив" in user_text or "отзыв" in user_text or "назар" in user_text or "бовар" in user_text:
        ans = f"⭐ Шумо метавонед баҳои дигарон ва отзивҳои мизоҷонро дар ин канал бинед: {CHANNEL_REVIEWS}"
    elif "салом" in user_text or "хайр" in user_text or "ассалому" in user_text:
        ans = f"Салому алайкум! Чӣ тавр ба шумо кӯмак расонам? Агар саволи муҳим дошта бошед, мустақиман ба владетс {ADMIN_USERNAME} муроҷиат кунед."
    else:
        ans = (
            f"🤖 Паёми шумо қабул шуд! Ман кӯшиш кардам ба саволи шумо ҷавоб диҳам, аммо барои маълумоти пурра "
            f"беҳтар аст ба владелетс ва админи асосӣ муроҷиат кунед: {ADMIN_USERNAME}\ инчунин канали моро фаромӯш накунед: {CHANNEL_SHOP}"
        )

    markup = types.InlineKeyboardMarkup()
    btn_admin = types.InlineKeyboardButton("👤 Навиштан ба Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    markup.add(btn_admin)

    bot.reply_to(message, ans, reply_markup=markup, parse_mode="Markdown")


# Оғози кор ва чопи ҳолат дар консол
print("Бот бо қувваи пурра ва системаи муҳофизати гурӯҳ ба кор даромад...")
bot.infinity_polling()
                                   
