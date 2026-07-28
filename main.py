import telebot

TOKEN = "8171911240:AAHBabUEVQ_bpSNodobCBCyCx3FR1jiBN_E"
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
  
