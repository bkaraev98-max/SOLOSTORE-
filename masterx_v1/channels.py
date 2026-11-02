try:
    from .database import db
except ImportError:
    from database import db


class ChannelManager:

    ALLOWED_PURPOSES = {
        "lots",
        "subscriptions",
        "bonuses",
        "payments",
        "rules",
        "other",
    }

    def add_channel(
        self,
        guarantor_user_id: int,
        channel_id: str,
        channel_title: str,
        purpose: str,
    ):
        if purpose not in self.ALLOWED_PURPOSES:
            raise ValueError("Invalid channel purpose")

        if not channel_id:
            raise ValueError("Channel ID is required")

        return db.add_channel(
            guarantor_user_id=guarantor_user_id,
            channel_id=channel_id,
            channel_title=channel_title,
            purpose=purpose,
            is_active=False,
        )

    def get_channels(self, guarantor_user_id: int):
        return db.get_channels(guarantor_user_id)

    def activate_channel(self, channel_id: int):
        return db.set_channel_active(channel_id, True)

    def deactivate_channel(self, channel_id: int):
        return db.set_channel_active(channel_id, False)

    async def check_bot_permissions(self, bot, channel_id: str):
        try:
            bot_info = await bot.get_me()

            member = await bot.get_chat_member(
                chat_id=channel_id,
                user_id=bot_info.id,
            )

            return member.status in {"administrator", "creator"}

        except Exception:
            return False

    async def authorize_channel(
        self,
        bot,
        channel_id: str,
        founder_approved: bool,
    ):
        if not founder_approved:
            return False

        has_permission = await self.check_bot_permissions(
            bot,
            channel_id,
        )

        if not has_permission:
            return False

        return True


channel_manager = ChannelManager()
