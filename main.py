import telebot

TOKEN = "8618711572:AAHTpbMmTbTvIyV0mSh838gRxb_sPXTgKWg"
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(
      message.chat.id,
      f"Привет, {message.from_user.first_name}! Добро пожаловать в Solostore.ru"
      " 🎮",
  )


if __name__ == "__main__":
  bot.infinity_polling()
  
