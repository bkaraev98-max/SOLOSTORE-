import logging
import telebot
from telebot import types

# ==========================
# SOLOSTORE.TJ BOT
# ==========================

TOKEN = "8171911240:AAHBabUEVQ_bpSNodobCBCyCx3FR1jiBN_E"

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s"
)

ADMIN = "@pubgertjk3"

UC_CHANNEL = "https://t.me/soloucstore"
METRO_CHANNEL = "https://t.me/metrosolostore"
ACCOUNT_CHANNEL = "https://t.me/solostoretj"
GROUP = "https://t.me/solostoretj"


def home_menu():
  markup = types.InlineKeyboardMarkup(row_width=1)

  markup.add(
      types.InlineKeyboardButton("💎 BUY UC", callback_data="uc"),
      types.InlineKeyboardButton("⚔️ METRO ROYALE", callback_data="metro"),
      types.InlineKeyboardButton("🛒 BUY ACCOUNT", url=ACCOUNT_CHANNEL),
      types.InlineKeyboardButton("💰 SELL ACCOUNT", callback_data="sell"),
      types.InlineKeyboardButton("👥 SOLOSTORE.TJ", url=GROUP),
      types.InlineKeyboardButton("👑 OWNER", url="https://t.me/pubgertjk3"),
  )

  return markup


def back():
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("⬅️ BACK", callback_data="home"))
  return markup


WELCOME = """
🎮 *Добро пожаловать в SOLOSTORE.TJ*

🔥 Лучший магазин PUBG Mobile

━━━━━━━━━━━━━━━

💎 Пополнение UC

⚔️ METRO ROYALE

🛒 Покупка аккаунтов

💰 Продажа аккаунтов

🛡 Гарантия безопасности

⚡ Быстро
⚡ Надёжно
⚡ Без обмана

━━━━━━━━━━━━━━━

👇 Выберите нужный раздел.
"""


@bot.message_handler(commands=["start"])
def start(message):
  bot.send_message(message.chat.id, WELCOME, reply_markup=home_menu())


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
  if call.data == "home":
    bot.edit_message_text(
        WELCOME,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=home_menu(),
    )

  elif call.data == "uc":
    text = """
💎 *ПОКУПКА UC*

━━━━━━━━━━━━━━━

✅ Моментальное пополнение

✅ Любое количество UC

✅ Гарантия безопасности

✅ Лучшие цены

━━━━━━━━━━━━━━━

👇 Выберите действие.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton("💎 UC CHANNEL", url=UC_CHANNEL),
        types.InlineKeyboardButton(
            "👑 НАПИСАТЬ ВЛАДЕЛЬЦУ", url="https://t.me/pubgertjk3"
        ),
        types.InlineKeyboardButton("⬅️ BACK", callback_data="home"),
    )

    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id, reply_markup=markup
    )

  elif call.data == "metro":
    text = """
⚔️ *METRO ROYALE*

━━━━━━━━━━━━━━━

🔥 Сопровождение

💰 Фарм валюты

🎒 Лучший лут

🛡 Безопасная игра

━━━━━━━━━━━━━━━

👇 Выберите действие.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "⚔️ METRO ROYALE CHANNEL", url=METRO_CHANNEL
        ),
        types.InlineKeyboardButton("👑 ЗАКАЗАТЬ", url="https://t.me/pubgertjk3"),
        types.InlineKeyboardButton("⬅️ BACK", callback_data="home"),
    )

    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id, reply_markup=markup
    )

  elif call.data == "sell":
    text = """
💰 *ПРОДАЖА АККАУНТА*

━━━━━━━━━━━━━━━

Хотите быстро продать аккаунт PUBG Mobile?

📸 Отправьте:

• Скриншоты

• Описание

• Желаемую цену

━━━━━━━━━━━━━━━

👇 Напишите владельцу.
"""

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "👑 НАПИСАТЬ ВЛАДЕЛЬЦУ", url="https://t.me/pubgertjk3"
        ),
        types.InlineKeyboardButton("⬅️ BACK", callback_data="home"),
    )

    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id, reply_markup=markup
    )

  bot.answer_callback_query(call.id)


print("===================================")
print("      SOLOSTORE.TJ BOT ONLINE")
print("===================================")

bot.infinity_polling(skip_pending=True)
    
