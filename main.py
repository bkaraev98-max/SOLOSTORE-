import telebot
from telebot import types
import re

# Токени нав ва маълумоти пурраи шумо
TOKEN = "8956371122:AAGMV0Wob4Q-AKwNqXXSnrRBHbLeKqQiIHg"
ADMIN_USERNAME = "@xs_anush19"
CHANNEL_SHOP = "https://t.me/ANUSHuc_SHOP"
CHANNEL_REVIEWS = "https://t.me/zvezdaotviz"
GROUP_CHAT = "https://t.me/chatanush"

# Сохтани объекти бот бо муҳофизат аз хатои 409
bot = telebot.TeleBot(TOKEN)

# Рӯйхати мушаххаси ҳақоратҳо ва дашномҳое, ки бояд сахт манъ карда шаванд
FORBIDDEN_PATTERNS = [
    "очата мегом", "мегомта", "сука", "да даҳат мегом", 
    "кси апа", "кси хоҳар", "хоҳарта гом", "ҷлаб", "кун", 
    "мунҷ", "harom", "suk", "durto", "pidar", "blyat", 
    "nahuj", "ebal", "блять", "сука", "ебать", "хуй", "пидор"
]

# ---------------------------------------------------------
# 1. МЕНЮИ АСОСӢ ВА СТАРТ (ЧАТИ ШАХСӢ)
# ---------------------------------------------------------
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.type != 'private':
        return
        
    name = message.from_user.first_name
    text = (
        f"👑 **Салом, ҳурматли {name}!** Хуш омадед ба пуриқтидортарин системаи ёвари мо.\n\n"
        f"Ман инҷо ҳастам то ба шумо дар ҳама масъалаҳо кӯмак расонам, молу маҳсулот ва "
        f"каналҳои моро муаррифӣ кунам. 🚀\n\n"
        f"📌 **Платформаҳои расмии мо:**\n"
        f"• Канали дӯкон: {CHANNEL_SHOP}\n"
        f"• Канали отзивҳо: {CHANNEL_REVIEWS}\n"
        f"• Гурӯҳи муҳокима: {GROUP_CHAT}\n\n"
        f"💡 *Агар саволе дошта бошед ё ягон мушкил барояд, бевосита ба владелетс {ADMIN_USERNAME} муроҷиат кунед!*"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("🛍 Канали Дӯкон", url=CHANNEL_SHOP)
    b2 = types.InlineKeyboardButton("⭐ Отзивҳо", url=CHANNEL_REVIEWS)
    b3 = types.InlineKeyboardButton("💬 Гурӯҳи Чат", url=GROUP_CHAT)
    b4 = types.InlineKeyboardButton("👑 Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}")
    b5 = types.InlineKeyboardButton("ℹ️ Маълумоти бештар", callback_data="btn_info")
    
    markup.add(b1, b2)
    markup.add(b3, b4)
    markup.add(b5)

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "btn_info")
def info_callback(call):
    info_text = (
        "⚙️ **Маълумоти махсус дар бораи система:**\n\n"
        "• Ин бот ба таври худкор ва бефосила кор мекунад.\n"
        "• Тамоми қоидаҳо дар гурӯҳ ва личка зери назорати қатъӣ ҳастанд.\n"
        f"• Сарвари асосӣ ва масъул: {ADMIN_USERNAME}\n\n"
        "Марҳамат, метавонед саволҳои худро нависед!"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Баргаштан", callback_data="btn_back"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=info_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "btn_back")
def back_callback(call):
    start_handler(call.message)


# ---------------------------------------------------------
# 2. МОДЕРАТОР ВА МУҲОФИЗАТИ ПУРҚУВВАТИ ГУРУҲ
# ---------------------------------------------------------

# Истиқболи гарм ва ҳушдор ба одамони нав дар гурӯҳ
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_user(message):
    for user in message.new_chat_members:
        fullname = user.first_name
        msg = (
            f"Ассалому алайкум, **{fullname}**! Хуш омадед ба гурӯҳи мо! 🎉\n\n"
            f"⚠️ **Қоидаи қатъӣ:** Дар гурӯҳ навиштани дашном, суханҳои қабеҳ ва ҳар гуна ҳақоратҳо (аз ҷумла оилагӣ) **ҚАТЪИЯН МАНЪ АСТ!** Паёмҳои номатлуб бечунучаро нест карда мешаванд.\n\n"
            f"🛒 Канали расмиамон: {CHANNEL_SHOP}\n"
            f"👑 Владелетс ва админ: {ADMIN_USERNAME}"
        )
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# Санҷиши паёмҳо дар гурӯҳ (Ҳақоратҳо ва номи Ануш)
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def group_security_system(message):
    if not message.text:
        return
        
    text_clean = message.text.lower()
    
    # 1. Санҷиши дашномҳо ва ҳақоратҳои феҳристшуда
    for bad_word in FORBIDDEN_PATTERNS:
        if bad_word in text_clean:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                warning = bot.send_message(
                    message.chat.id,
                    f"🚫 **{message.from_user.first_name}**, дар ин гурӯҳ гуфтани ин гуна суханҳои қабеҳ ва ҳақоратҳо манъ аст! Паёми шумо тоза карда шуд."
                )
            except Exception:
                pass
            return

    # 2. Аксуламал ба номи "Ануш"
    if "ануш" in text_clean:
        alert = f"✨ Диққат! Касе номи **Ануш**-ро гирифт! Владелетс ва сарвари ин корҳо: {ADMIN_USERNAME} 👑"
        bot.reply_to(message, alert, parse_mode="Markdown")
        return

    # 3. Ҷавоби худкори интеллектуалӣ ба саволҳо
    if any(q in text_clean for q in ["савол", "нарх", "чихел", "кумак", "помощь", "помогите", "?"]):
        reply_group = (
            f"💬 Паём ва саволи шумо қабул шуд! Агар касе аз иштирокчиён кӯмак карда натавонад, "
            f"лутфан бевосита ба владелетс {ADMIN_USERNAME} муроҷиат кунед ё ба канали мо нигаред: {CHANNEL_SHOP}"
        )
        bot.reply_to(message, reply_group, parse_mode="Markdown")


# ---------------------------------------------------------
# 3. ҶАВОБИ ХУДКОР ДАР ЧАТИ ШАХСӢ (AI STYLE)
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def private_ai_handler(message):
    txt = message.text.lower()
    
    if "нарх" in txt or "цена" in txt or "товар" in txt or "китоб" in txt:
        response = f"📦 Маълумот оид ба молҳо ва нархҳо дар канали расмии мо мавҷуд аст: {CHANNEL_SHOP}\n\nБарои харид мустақиман ба владелетс {ADMIN_USERNAME} нависед!"
    elif "отзив" in txt or "отзыв" in txt or "назар" in txt:
        response = f"⭐ Шарҳ ва отзивҳои мизоҷони моро инҷо хонед: {CHANNEL_REVIEWS}"
    elif "салом" in txt or "ассалому" in txt:
        response = f"Салому алайкум! Чӣ тавр ба шумо кӯмак расонам? Барои маълумоти пурра ба владелетс {ADMIN_USERNAME} муроҷиат кунед."
    else:
        response = (
            f"🤖 Паёми шумо қабул шуд! Агар ба шумо кӯмаки махсус лозим бошад ё хоҳед маълумоти пурра гиред, "
            f"лутфан бевосита ба владелетс ва админи асосӣ {ADMIN_USERNAME} нависед! Агар кӯмак карда натавонам ҳам, ӯ ҳатман кӯмак мекунад."
        )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👤 Навиштан ба Владелетс", url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))

    bot.reply_to(message, response, reply_markup=markup, parse_mode="Markdown")


# Оғози бот бо тоза кардани дархостҳои куҳна (пешгирии ҳама гуна хатогиҳои 409)
print("Системаи бот бо муваффақият фаъол шуд ва муҳофизати гурӯҳ ба кор даромад...")
bot.infinity_polling(skip_pending=True)
