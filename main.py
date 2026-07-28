"8618711572:AAHYOHM0f4nG-r0VZp3PsuaUI7m5N63Z8ow"
import telebot
from telebot import types

TOKEN = "8618711572:AAHYOHM0f4nG-r0VZp3PsuaUI7m5N63Z8ow"
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
  user_name = message.from_user.first_name

  markup = types.InlineKeyboardMarkup(row_width=2)
  item1 = types.InlineKeyboardButton("🛒 Аккаунты PUBG", callback_data="accounts")
  item2 = types.InlineKeyboardButton("💼 Metro Royale", callback_data="metro")
  item3 = types.InlineKeyboardButton("🤝 Продать нам", callback_data="sell")
  # Юзернейми худро ба ҷои '@pubgertjk3' нависед
  item4 = types.InlineKeyboardButton(
      "📞 Связь с админом", url="https://t.me/pubgertjk3"
  )

  
TOKEN = "8618711572:AAHYOHM0f4nG-r0VZp3PsuaUI7m5N63Z8ow"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Салом! Бот кор карда истодааст!")

bot.infinity_polling()
 {user_name}! Добро пожаловать в официальный магазин"
      " Solostore.ru 🎮🔥\n\nЗдесь вы можете безопасно купить аккаунты, лут и"
      " редкие вещи PUBG Mobile (Metro Royale), а также продать свои.\n\nВыберите"
      " нужный раздел в меню ниже:"
  )

  bot.send_message(
      message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup
  )


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
  if call.data == "accounts":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "🛒 Аккаунты PUBG Mobile:\n\nВ данный момент доступные аккаунты:\n1."
        " Аккаунт с прокачанными скинами — Цена: ...\n2. Монарх / Завоеватель"
        " — Цена: ...\n\nДля покупки напишите администратору.",
    )
  elif call.data == "metro":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "💼 Metro Royale (Вещи и валюта):\n\nЗдесь вы можете приобрести игровую"
        " валюту, сталкерское снаряжение и дорогие стволы. Уточняйте наличие у"
        " админа!",
    )
  elif call.data == "sell":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "🤝 Продажа нам:\n\nХотите продать свой аккаунт или вещи? Скиньте"
        " скриншоты и описание нашему администратору, мы оценим и купим!",
    )


if __name__ == "__main__":
  print("Бот Solostore.ru успешно запущен и работает...")
  bot.infinity_polling()
