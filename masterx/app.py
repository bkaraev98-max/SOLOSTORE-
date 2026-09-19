import datetime
import os
import sqlite3
import telebot
from flask import Flask, request
from telebot import types

# ==========================================
# 👑 MASTER X AUTO-APPROVE VENDOR BOT
# ==========================================
TOKEN = os.getenv("TOKEN", "8953447600:AAE5WupEUGhW4jkW59jJi2DaVYZLLrO6fQc")
ADMIN_USERNAME = (
    "админсайт"  # Номи аккаунти ту (бе аломати @ ё бо @ фарқ надорад)
)
ADMIN_IDS = [7811559530]  # Telegram ID-и ту (барои хабарҳои фоида ва заказ)

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)
DB_NAME = "master_x_auto.db"

user_states = {}


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            seller_status TEXT DEFAULT 'NONE'
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            title TEXT,
            price TEXT,
            description TEXT,
            status TEXT DEFAULT 'ACTIVE'
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER,
            seller_id INTEGER,
            buyer_id INTEGER,
            buyer_name TEXT,
            price TEXT,
            sold_at TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


def main_menu(seller_status):
  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton(
          "🛍 Дидани Лотҳои Бозор (Харид)", callback_data="market_browse"
      )
  )

  if seller_status == "APPROVED":
    markup.add(
        types.InlineKeyboardButton(
            "📦 Кабинети Фурӯшанда", callback_data="seller_panel"
        )
    )
  else:
    markup.add(
        types.InlineKeyboardButton(
            "📝 Фурӯшанда шудан (Бо калима)", callback_data="apply_seller"
        )
    )

  return markup


@bot.message_handler(commands=["start"])
def send_welcome(message):
  uid = message.from_user.id
  if uid in user_states:
    del user_states[uid]

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT seller_status FROM users WHERE user_id = ?", (uid,))
  row = cursor.fetchone()

  if not row:
    cursor.execute(
        "INSERT INTO users (user_id, username, first_name, seller_status)"
        " VALUES (?, ?, ?, 'NONE')",
        (
            uid,
            message.from_user.username or "NoUsername",
            message.from_user.first_name,
        ),
    )
    conn.commit()
    status = "NONE"
  else:
    status = row[0]
  conn.close()

  text = (
      "👑 **MASTER X SECURE MARKETPLACE** 👑\n"
      "━━━━━━━━━━━━━━━━━━━━━\n"
      "Боти худкори хариду фурӯш. Барои фурӯшанда шудан тугмаро зер кунед."
  )
  bot.send_message(
      message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu(status)
  )


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  uid = call.from_user.id

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT seller_status FROM users WHERE user_id = ?", (uid,))
  row = cursor.fetchone()
  status = row[0] if row else "NONE"
  conn.close()

  if call.data == "back_to_main":
    if uid in user_states:
      del user_states[uid]
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "👑 **MASTER X SECURE MARKETPLACE** 👑\nМенюи асосӣ:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=main_menu(status),
    )

  # Дархост барои фурӯшанда шудан (пурсидани калима)
  elif call.data == "apply_seller":
    bot.answer_callback_query(call.id)
    user_states[uid] = {"step": "waiting_secret_word"}
    bot.send_message(
        call.message.chat.id,
        "🔑 Лутфан калимаи махсусро нависед (масалан: `@админсайт`):",
    )

  elif call.data == "seller_panel" and status == "APPROVED":
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "➕ Илова кардани лоти нав", callback_data="start_add_lot"
        ),
        types.InlineKeyboardButton(
            "📋 Лотҳои ман", callback_data="seller_my_lots"
        ),
        types.InlineKeyboardButton(
            "📊 Статистикаи ман", callback_data="seller_stats"
        ),
        types.InlineKeyboardButton(
            "🔙 Бозгашт", callback_data="back_to_main"
        ),
    )
    bot.edit_message_text(
        "📦 **Кабинети Фурӯшанда**\nЯкеро интихоб кунед:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data == "start_add_lot" and status == "APPROVED":
    bot.answer_callback_query(call.id)
    user_states[uid] = {"step": "waiting_title"}
    bot.send_message(
        call.message.chat.id,
        "1️⃣ Лутфан номи лот ё миқдори UC-ро нависед (масалан: `60 UC`):",
    )

  elif call.data == "seller_my_lots" and status == "APPROVED":
    bot.answer_callback_query(call.id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, price FROM vendor_lots WHERE seller_id = ?", (uid,)
    )
    lots = cursor.fetchall()
    conn.close()

    text = "📋 **Лотҳои шумо:**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    if lots:
      for l in lots:
        text += f"🔹 **{l[1]}** — Нарх: `{l[2]}`\n"
        markup.add(
            types.InlineKeyboardButton(
                f"🗑 Нест кардан: {l[1]}", callback_data=f"del_l_{l[0]}"
            )
        )
    else:
      text += "Шумо ягон лот надоред."

    markup.add(
        types.InlineKeyboardButton(
            "🔙 Бозгашт", callback_data="seller_panel"
        )
    )
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data.startswith("del_l_"):
    lot_id = int(call.data.split("_")[2])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM vendor_lots WHERE id = ? AND seller_id = ?", (lot_id, uid)
    )
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ Лот нест шуд!", show_alert=True)

  elif call.data == "seller_stats" and status == "APPROVED":
    bot.answer_callback_query(call.id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*), SUM(price) FROM vendor_orders WHERE seller_id = ?",
        (uid,),
    )
    row = cursor.fetchone()
    conn.close()
    total_sales = row[0] if row[0] else 0
    total_money = row[1] if row[1] else "0"

    text = (
        "📊 **Статистикаи фурӯшҳои шумо:**\n\n"
        f"🛒 Шумораи заказҳо: `{total_sales}` адад\n"
        f"💵 Маблағи умумӣ: `{total_money}`"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔙 Бозгашт", callback_data="seller_panel"
        )
    )
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data == "market_browse":
    bot.answer_callback_query(call.id)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, price, description FROM vendor_lots WHERE status ="
        " 'ACTIVE' ORDER BY id DESC LIMIT 10"
    )
    lots = cursor.fetchall()
    conn.close()

    text = "🛍 **Бозори фаъол:**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    if lots:
      for l in lots:
        text += f"🎮 **{l[1]}**\n💰 Нарх: `{l[2]}`\n📝 {l[3]}\n──────────────\n"
        markup.add(
            types.InlineKeyboardButton(
                f"🛒 Харидан: {l[1]} ({l[2]})", callback_data=f"buy_item_{l[0]}"
            )
        )
    else:
      text += "Ҳоло дар бозор ягон лот нест."

    markup.add(
        types.InlineKeyboardButton(
            "🔙 Бозгашт", callback_data="back_to_main"
        )
    )
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup,
    )

  elif call.data.startswith("buy_item_"):
    lot_id = int(call.data.split("_")[2])
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT seller_id, title, price FROM vendor_lots WHERE id = ?", (lot_id,)
    )
    lot = cursor.fetchone()
    conn.close()

    if not lot:
      bot.answer_callback_query(call.id, "❌ Ин лот нест!", show_alert=True)
      return

    seller_id, title, price = lot
    buyer = call.from_user
    buyer_name = (
        f"@{buyer.username}" if buyer.username else buyer.first_name
    )

    # Вақти дақиқи харид бо соат ва рӯз
    sold_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vendor_orders (lot_id, seller_id, buyer_id, buyer_name,"
        " price, sold_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lot_id, seller_id, buyer.id, buyer_name, price, sold_time),
    )
    conn.commit()
    conn.close()

    # Огоҳ кардани фурӯшанда
    try:
      bot.send_message(
          seller_id,
          f"⚡ **ЗАКАЗИ НАВ!**\n\nЛот: **{title}**\nНарх: **{price}**\nХаридор:"
          f" {buyer_name}\nВақт: `{sold_time}`",
          parse_mode="Markdown",
      )
    except:
      pass

    # 🔥 БА АДМИН (ТУ) ХАБАР ДОДАН ДАР БОРАИ ЗАКАЗ ВА ФОИДА БО ВАҚТ
    for admin_id in ADMIN_IDS:
      try:
        bot.send_message(
            admin_id,
            f"📢 **МАЪЛУМОТ БАРОИ АДМИН (ФУРӮШ)**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 Вақт: `{sold_time}`\n"
            f"🎮 Лот: **{title}**\n"
            f"💰 Нарх / Фоида: **{price}**\n"
            f"👤 Фурӯшанда ID: `{seller_id}`\n"
            f"🛒 Харидор: {buyer_name} (ID: `{buyer.id}`)",
            parse_mode="Markdown",
        )
      except:
        pass

    bot.answer_callback_query(
        call.id,
        "✅ Закази шумо фиристода шуд! Фурӯшанда огоҳ шуд.",
        show_alert=True,
    )


# ==========================================
# 💬 ДИАЛОГҲО ВА КАЛИМАИ МАХСУС
# ==========================================
@bot.message_handler(
    func=lambda message: message.from_user.id in user_states
    and "step" in user_states[message.from_user.id]
)
def process_dialogs(message):
  uid = message.from_user.id
  state = user_states[uid]["step"]
  text_input = message.text.strip()

  # 1. Санҷиши калимаи махсус барои автоматӣ фурӯшанда шудан
  if state == "waiting_secret_word":
    # Тоза кардани аломати @ аз аввали калима агар бошад
    clean_input = text_input.replace("@", "").lower()
    clean_admin = ADMIN_USERNAME.replace("@", "").lower()

    if clean_input == clean_admin:
      conn = sqlite3.connect(DB_NAME)
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE users SET seller_status = 'APPROVED' WHERE user_id = ?",
          (uid,),
      )
      conn.commit()
      conn.close()

      del user_states[uid]
      bot.send_message(
          message.chat.id,
          "🎉 **Табрик мекунем!** Калима дуруст аст. Акнун шумо ҳуқуқи"
          " фурӯшандагӣ гирифтед!",
          parse_mode="Markdown",
          reply_markup=main_menu("APPROVED"),
      )
    else:
      bot.send_message(
          message.chat.id,
          "❌ Калимаи махсус хато аст! Аз нав кӯшиш кунед ё тугмаи бозгаштро"
          " пахш кунед:",
      )

  # 2. Қадамҳои сохтани лот
  elif state == "waiting_title":
    user_states[uid]["title"] = text_input
    user_states[uid]["step"] = "waiting_price"
    bot.send_message(
        message.chat.id,
        "2️⃣ Нарх чанд сомонӣ аст? (Фурӯшанда менависад, масалан: `10 сомонӣ`):",
    )

  elif state == "waiting_price":
    user_states[uid]["price"] = text_input
    user_states[uid]["step"] = "waiting_desc"
    bot.send_message(
        message.chat.id,
        "3️⃣ Маълумот ё ID-и худро нависед (тавсиф):",
    )

  elif state == "waiting_desc":
    title = user_states[uid]["title"]
    price = user_states[uid]["price"]
    desc = text_input

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vendor_lots (seller_id, title, price, description) VALUES"
        " (?, ?, ?, ?)",
        (uid, title, price, desc),
    )
    conn.commit()
    conn.close()

    del user_states[uid]
    bot.send_message(
        message.chat.id,
        f"✅ **Лоти шумо бомуваффақият илова шуд!**\n\n🔹 Мол: {title}\n💰 Нарх:"
        f" {price}\n📝 Тавсиф: {desc}",
        parse_mode="Markdown",
        reply_markup=main_menu("APPROVED"),
    )


# ==========================================
# 🌐 FLASK WEBHOOK БАРОИ 24/7
# ==========================================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
  if request.headers.get("content-type") == "application/json":
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200
  else:
    return "Forbidden", 403


@app.route("/")
def index():
  return "Master X Auto Bot is running 24/7!"


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

