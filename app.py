# ============================================================
# ACCESS CONTROL
# ============================================================

def is_master_admin(user_id: int) -> bool:
    return (
        MASTER_ADMIN_ID != 0
        and user_id == MASTER_ADMIN_ID
    )


def is_bot_admin(user_id: int, bot_row) -> bool:
    return (
        bot_row is not None
        and bot_row["admin_id"] is not None
        and user_id == bot_row["admin_id"]
    )


# ============================================================
# TELEGRAM API
# ============================================================

async def telegram_get_me(token: str):
    """
    Check whether token is valid and return bot information.
    """

    url = f"https://api.telegram.org/bot{token}/getMe"

    timeout = ClientTimeout(total=15)

    async with ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:

            if response.status != 200:
                return None, f"HTTP {response.status}"

            data = await response.json()

            if not data.get("ok"):
                return None, data.get("description", "Telegram API error")

            return data["result"], None


async def telegram_get_webhook_info(token: str):
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"

    timeout = ClientTimeout(total=15)

    async with ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:

            if response.status != 200:
                return None, f"HTTP {response.status}"

            data = await response.json()

            if not data.get("ok"):
                return None, data.get("description", "Telegram API error")

            return data["result"], None


async def telegram_set_webhook(token: str, url: str, secret_token: str):
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"

    payload = {
        "url": url,
        "secret_token": secret_token,
        "drop_pending_updates": True,
    }

    timeout = ClientTimeout(total=20)

    async with ClientSession(timeout=timeout) as session:
        async with session.post(api_url, json=payload) as response:

            data = await response.json()

            if response.status != 200:
                return False, data.get(
                    "description",
                    f"HTTP {response.status}"
                )

            return bool(data.get("ok")), data.get(
                "description",
                ""
            )


async def telegram_delete_webhook(token: str):
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook"

    timeout = ClientTimeout(total=20)

    async with ClientSession(timeout=timeout) as session:
        async with session.post(
            api_url,
            json={"drop_pending_updates": True}
        ) as response:

            data = await response.json()

            if response.status != 200:
                return False, data.get(
                    "description",
                    f"HTTP {response.status}"
                )

            return bool(data.get("ok")), data.get(
                "description",
                ""
            )


# ============================================================
# MASTER BOT
# ============================================================

master_router = Router()


def master_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(
        text="➕ Add Bot",
        callback_data="add_bot"
    )

    kb.button(
        text="📋 Bot List",
        callback_data="bot_list"
    )

    kb.button(
        text="🔍 Search",
        callback_data="search_bot"
    )

    kb.button(
        text="🧪 System Test",
        callback_data="system_test"
    )

    kb.adjust(2)

    return kb.as_markup()


def bot_keyboard(bot_id: int, enabled: bool):
    kb = InlineKeyboardBuilder()

    kb.button(
        text="👤 Set Admin",
        callback_data=f"setadmin:{bot_id}"
    )

    if enabled:
        kb.button(
            text="🔴 Disable",
            callback_data=f"disable:{bot_id}"
        )
    else:
        kb.button(
            text="🟢 Enable",
            callback_data=f"enable:{bot_id}"
        )

    kb.button(
        text="🔗 Webhook",
        callback_data=f"webhook:{bot_id}"
    )

    kb.button(
        text="🧪 Test",
        callback_data=f"testbot:{bot_id}"
    )

    kb.button(
        text="🔙 Back",
        callback_data="bot_list"
    )

    kb.adjust(2)

    return kb.as_markup()


def format_bot(bot_row):
    username = (
        f"@{html.escape(bot_row['username'])}"
        if bot_row["username"]
        else "—"
    )

    name = html.escape(
        bot_row["first_name"] or "Unknown"
    )

    status = "🟢 Active" if bot_row["enabled"] else "🔴 Disabled"

    admin = (
        str(bot_row["admin_id"])
        if bot_row["admin_id"]
        else "❌ Not assigned"
    )

    return (
        f"🤖 <b>{name}</b>\n"
        f"👤 Username: {username}\n"
        f"🆔 Bot ID: <code>{bot_row['telegram_id']}</code>\n"
        f"👑 Bot Admin: <code>{admin}</code>\n"
        f"📊 Status: {status}\n"
        f"🗂 Internal ID: <code>{bot_row['id']}</code>"
    )


@master_router.message(CommandStart())
async def start_handler(message: Message):

    if not is_master_admin(message.from_user.id):
        await message.answer(
            "⛔ Access denied."
        )
        return

    await message.answer(
        "👑 <b>MASTER BOT</b>\n\n"
        "🤖 Multi-Bot Management System\n\n"
        "Аз ин ҷо ту ҳамаи ботҳои худро идора карда метавонӣ.",
        reply_markup=master_keyboard()
    )


@master_router.message(Command("panel"))
async def panel_handler(message: Message):

    if not is_master_admin(message.from_user.id):
        return

    await message.answer(
        "👑 <b>MASTER PANEL</b>",
        reply_markup=master_keyboard()
    )


# ============================================================
# ADD BOT
# ============================================================

waiting_for_token = set()
waiting_for_admin = {}


@master_router.callback_query(F.data == "add_bot")
async def add_bot_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    waiting_for_token.add(callback.from_user.id)

    await callback.message.answer(
        "➕ <b>Add Bot</b>\n\n"
        "Token-и боти Telegram-ро фирист.\n\n"
        "Мисол:\n"
        "<code>123456:ABC...</code>\n\n"
        "⚠️ Token-ро танҳо ба Master Bot фирист."
    )

    await callback.answer()


@master_router.message()
async def text_router(message: Message):

    if not is_master_admin(message.from_user.id):
        return

    user_id = message.from_user.id
    text = (message.text or "").strip()

    # ----------------------------------------
    # ADD BOT TOKEN
    # ----------------------------------------

    if user_id in waiting_for_token:

        waiting_for_token.discard(user_id)

        if not text:
            await message.answer(
                "❌ Token холӣ аст."
            )
            return

        await message.answer(
            "⏳ Token санҷида мешавад..."
        )

        bot_info, error = await telegram_get_me(text)

        if error:
            await message.answer(
                "❌ <b>Token invalid</b>\n\n"
                f"Telegram: <code>{html.escape(error)}</code>\n\n"
                "Token-ро аз BotFather санҷ."
            )
            return

        try:
            bot_id = db_add_bot(
                token=text,
                telegram_id=bot_info["id"],
                username=bot_info.get("username"),
                first_name=bot_info.get("first_name"),
            )

        except sqlite3.IntegrityError:
            await message.answer(
                "⚠️ Ин бот аллакай ба система илова шудааст."
            )
            return

        row = db_get_bot(bot_id)

        await message.answer(
            "✅ <b>Bot successfully added!</b>\n\n"
            + format_bot(row),
            reply_markup=bot_keyboard(
                bot_id,
                bool(row["enabled"])
            )
        )

        return

    # ----------------------------------------
    # SET ADMIN
    # ----------------------------------------

    if user_id in waiting_for_admin:

        bot_id = waiting_for_admin.pop(user_id)

        try:
            admin_id = int(text)
        except ValueError:
            await message.answer(
                "❌ Admin ID бояд рақам бошад.\n"
                "Мисол: <code>123456789</code>"
            )
            return

        row = db_get_bot(bot_id)

        if row is None:
            await message.answer(
                "❌ Bot ёфт нашуд."
            )
            return

        db_set_admin(bot_id, admin_id)

        row = db_get_bot(bot_id)

        await message.answer(
            "✅ <b>Bot Admin assigned.</b>\n\n"
            + format_bot(row),
            reply_markup=bot_keyboard(
                bot_id,
                bool(row["enabled"])
            )
        )

        return


# ============================================================
# BOT LIST
# ============================================================

@master_router.callback_query(F.data == "bot_list")
async def bot_list_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bots = db_get_all_bots()

    if not bots:
        await callback.message.answer(
            "📋 <b>Bot List</b>\n\n"
            "Ҳоло ягон бот илова нашудааст."
        )

        await callback.answer()
        return

    kb = InlineKeyboardBuilder()

    text = "📋 <b>MANAGED BOTS</b>\n\n"

    for row in bots:

        username = (
            f"@{row['username']}"
            if row["username"]
            else str(row["telegram_id"])
        )

        status = "🟢" if row["enabled"] else "🔴"

        text += (
            f"{status} <b>{html.escape(username)}</b> "
            f"— ID {row['id']}\n"
        )

        kb.button(
            text=f"{status} {username}",
            callback_data=f"bot:{row['id']}"
        )

    kb.button(
        text="🔙 Main Menu",
        callback_data="main_menu"
    )

    kb.adjust(1)

    await callback.message.answer(
        text,
        reply_markup=kb.as_markup()
    )

    await callback.answer()


# ============================================================
# BOT DETAILS
# ============================================================

@master_router.callback_query(F.data.startswith("bot:"))
async def bot_details_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    await callback.message.answer(
        format_bot(row),
        reply_markup=bot_keyboard(
            bot_id,
            bool(row["enabled"])
        )
    )

    await callback.answer()


# ============================================================
# SET ADMIN
# ============================================================

@master_router.callback_query(F.data.startswith("setadmin:"))
async def set_admin_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    waiting_for_admin[callback.from_user.id] = bot_id

    await callback.message.answer(
        f"👤 <b>Set Admin</b>\n\n"
        f"Bot: {html.escape(row['first_name'] or 'Unknown')}\n\n"
        "Telegram ID-и соҳиби ин ботро фирист.\n\n"
        "Мисол:\n"
        "<code>123456789</code>"
    )

    await callback.answer()


# ============================================================
# ENABLE / DISABLE
# ============================================================

@master_router.callback_query(F.data.startswith("enable:"))
async def enable_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    db_set_enabled(bot_id, True)

    row = db_get_bot(bot_id)

    await callback.message.answer(
        "🟢 <b>Bot enabled</b>\n\n"
        + format_bot(row),
        reply_markup=bot_keyboard(bot_id, True)
    )

    await callback.answer("Enabled")


@master_router.callback_query(F.data.startswith("disable:"))
async def disable_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    db_set_enabled(bot_id, False)

    row = db_get_bot(bot_id)

    await callback.message.answer(
        "🔴 <b>Bot disabled</b>\n\n"
        + format_bot(row),
        reply_markup=bot_keyboard(bot_id, False)
    )

    await callback.answer("Disabled")


# ============================================================
# WEBHOOK
# ============================================================

@master_router.callback_query(F.data.startswith("webhook:"))
async def webhook_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    info, error = await telegram_get_webhook_info(
        row["token"]
    )

    if error:
        await callback.message.answer(
            "❌ Webhook check failed:\n"
            f"<code>{html.escape(error)}</code>"
        )

        await callback.answer()
        return

    webhook_url = info.get("url") or "Not configured"

    pending = info.get("pending_update_count", 0)

    last_error = info.get("last_error_message")

    text = (
        "🔗 <b>WEBHOOK INFO</b>\n\n"
        f"URL:\n<code>{html.escape(webhook_url)}</code>\n\n"
        f"Pending updates: <code>{pending}</code>\n"
    )

    if last_error:
        text += (
            "\n⚠️ Last error:\n"
            f"<code>{html.escape(last_error)}</code>"
        )

    if BASE_URL:
        expected_url = (
            f"{BASE_URL}"
            f"{WEBHOOK_PATH_PREFIX}"
            f"/{bot_id}/"
            f"{row['webhook_secret']}"
        )

        text += (
            "\n\nExpected URL:\n"
            f"<code>{html.escape(expected_url)}</code>"
        )

    await callback.message.answer(text)

    await callback.answer()


# ============================================================
# TEST BOT
# ============================================================

@master_router.callback_query(F.data.startswith("testbot:"))
async def test_bot_callback(callback: CallbackQuery):

    if not is_master_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    bot_id = int(callback.data.split(":")[1])

    row = db_get_bot(bot_id)

    if row is None:
        await callback.answer(
            "Bot not found",
            show_alert=True
        )
        return

    await callback.message.answer(
        "🧪 <b>Testing bot...</b>"
    )

    bot_info, error = await telegram_get_me(
        row["token"]
    )

    if error:
        await callback.message.answer(
            "❌ Bot test failed:\n"
            f"<code>{html.escape(error)}</code>"
        )
        await callback.answer()
        return

    webhook_info, webhook_error = (
        await telegram_get_

@dp.message(BuyState.waiting_for_withdrawal_amount)
async def process_withdrawal(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        current_balance = user_balances.get(user_id, 0.0)
        
        if current_balance < amount:
            await message.answer("❌ Маблағи баланси шумо кофӣ нест!")
        else:
            user_balances[user_id] = current_balance - amount
            await message.answer(f"✅ Дархости вивести {amount} сомонӣ бомуваффақият фиристода шуд. Ба زӯдӣ ба ҳамёни شما гузаронида мешавад.")
            await bot.send_message(ADMIN_ID, f"💸 **Дархости вивест аз @{message.from_user.username}**\nМаблағ: {amount} сомонӣ")
    except ValueError:
        await message.answer("Иلطфао фақат рақам нависед.")
    await state.clear()

async def on_startup(bot: Bot):
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        await bot.set_webhook(webhook_url)
        logging.info(f"Webhook пайваст шуд: {webhook_url}")

def main():
    dp.startup.register(on_startup)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path="/webhook")
    
    setup_application(app, dp, bot=bot)
    
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
