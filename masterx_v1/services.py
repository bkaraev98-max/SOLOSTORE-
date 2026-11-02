try:
    from .database import db
except ImportError:
    from database import db


class MasterXServices:
    """Core business services for MASTER X."""

    def register_user(self, user_id: int, username: str = "", full_name: str = ""):
        db.add_user(
            user_id=user_id,
            username=username,
            full_name=full_name,
        )
        return db.get_user(user_id)

    def get_user_profile(self, user_id: int):
        return db.get_user(user_id)

    def register_guarantor(
        self,
        user_id: int,
        username: str = "",
        full_name: str = "",
    ):
        db.add_guarantor(
            user_id=user_id,
            username=username,
            full_name=full_name,
        )
        return db.get_guarantor(user_id)

    def add_channel(
        self,
        guarantor_user_id: int,
        channel_id: str,
        channel_title: str,
        purpose: str,
        is_active: bool = False,
    ):
        return db.add_channel(
            guarantor_user_id=guarantor_user_id,
            channel_id=channel_id,
            channel_title=channel_title,
            purpose=purpose,
            is_active=is_active,
        )

    def get_channels(self, guarantor_user_id: int):
        return db.get_channels(guarantor_user_id)

    def activate_channel(self, channel_id: int, is_active: bool):
        return db.set_channel_active(channel_id, is_active)

    def add_lot(self, **lot_data):
        required_fields = [
            "name",
            "description",
            "price",
            "category",
            "guarantor_user_id",
            "video_url",
        ]

        missing = [
            field for field in required_fields
            if field not in lot_data or lot_data[field] in (None, "")
        ]

        if missing:
            raise ValueError(
                "Missing lot fields: " + ", ".join(missing)
            )

        return db.add_lot(**lot_data)

    def get_lot(self, lot_id: int):
        return db.get_lot(lot_id)

    def list_lots(self, status: str = "available", limit: int = 50):
        return db.list_lots(status=status, limit=limit)

    def update_lot(self, lot_id: int, **updates):
        return db.update_lot(lot_id, **updates)

    def change_lot_status(self, lot_id: int, status: str):
        allowed_statuses = {
            "available",
            "reserved",
            "sold",
            "inactive",
        }

        if status not in allowed_statuses:
            raise ValueError("Invalid lot status")

        return db.set_lot_status(lot_id, status)

    def create_subscription(self, **subscription_data):
        return db.create_subscription(**subscription_data)

    def get_subscription(self, subscription_id: int):
        return db.get_subscription(subscription_id)

    def get_user_subscriptions(self, user_id: int):
        return db.get_user_subscriptions(user_id)

    def update_subscription(self, subscription_id: int, **updates):
        return db.update_subscription(subscription_id, **updates)

    def record_payment(self, **payment_data):
        return db.add_payment(**payment_data)

    def update_payment(self, payment_id: int, status: str):
        allowed_statuses = {
            "pending",
            "confirmed",
            "rejected",
        }

        if status not in allowed_statuses:
            raise ValueError("Invalid payment status")

        return db.update_payment_status(payment_id, status)

    def record_commission(self, **commission_data):
        return db.add_commission(**commission_data)

    def confirm_commission_paid(self, commission_id: int):
        return db.mark_commission_paid(commission_id)

    def add_bonus(self, **bonus_data):
        return db.add_bonus(**bonus_data)

    def add_ai_credits(self, **transaction_data):
        return db.add_ai_credit_transaction(**transaction_data)

    def get_ai_credit_balance(self, user_id: int):
        return db.get_ai_credit_balance(user_id)

    def accept_rules(self, user_id: int, rules_version: str):
        return db.accept_rules(user_id, rules_version)

    def log(self, actor_id: int, action: str, details: str = ""):
        return db.log_action(
            actor_id=actor_id,
            action=action,
            details=details,
        )


services = MasterXServices()
