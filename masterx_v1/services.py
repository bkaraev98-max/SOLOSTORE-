
try:
    from .database import db
except ImportError:
    from database import db


class MasterXServices:
    """Core business services for MASTER X."""

    def register_user(
        self,
        user_id: int,
        username: str = "",
        full_name: str = ""
    ):
        db.add_user(
            user_id=user_id,
            username=username,
            full_name=full_name
        )
        return db.get_user(user_id)

    def get_user_profile(self, user_id: int):
        return db.get_user(user_id)

    def register_guarantor(
        self,
        user_id: int,
        username: str = "",
        full_name: str = "",
        display_name: str = ""
    ):
        db.add_guarantor(
            user_id=user_id,
            username=username,
            full_name=full_name,
            display_name=display_name
        )
        return db.get_guarantor(user_id)

    def add_channel(
        self,
        guarantor_user_id: int,
        channel_id: str,
        channel_title: str,
        purpose: str,
        is_active: bool = False
    ):
        # Ensure the guarantor exists.
        if not db.get_guarantor(guarantor_user_id):
            raise ValueError("Guarantor is not registered")

        result = db.add_channel(
            channel_id=channel_id,
            title=channel_title,
            purpose=purpose,
            added_by=guarantor_user_id
        )

        if is_active:
            db.set_channel_active(channel_id, True)

        return result

    def get_channels(self, guarantor_user_id: int = None):
        # The current database schema does not link channels
        # to individual guarantors.
        return db.get_channels(active_only=True)

    def activate_channel(self, channel_id: str, is_active: bool):
        return db.set_channel_active(channel_id, is_active)

    def add_lot(self, **lot_data):
        required_fields = [
            "title",
            "description",
            "price",
            "category",
            "platform",
            "guarantor_user_id"
        ]

        missing = [
            field for field in required_fields
            if field not in lot_data
            or lot_data[field] in (None, "")
        ]

        if missing:
            raise ValueError(
                "Missing lot fields: " + ", ".join(missing)
            )

        return db.add_lot(lot_data)

    def get_lot(self, lot_code: str):
        return db.get_lot(lot_code)

    def list_lots(
        self,
        status: str = "available",
        category: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        return db.list_lots(
            status=status,
            category=category,
            limit=limit,
            offset=offset
        )

    def update_lot(self, lot_code: str, **updates):
        return db.update_lot(lot_code, updates)

    def change_lot_status(self, lot_code: str, status: str):
        allowed_statuses = {
            "available",
            "reserved",
            "sold",
            "inactive"
        }

        if status not in allowed_statuses:
            raise ValueError("Invalid lot status")

        return db.set_lot_status(lot_code, status)

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

    def update_payment(
        self,
        payment_id: int,
        status: str,
        confirmed_by: int = None
    ):
        allowed_statuses = {
            "pending",
            "confirmed",
            "rejected"
        }

        if status not in allowed_statuses:
            raise ValueError("Invalid payment status")

        return db.update_payment_status(
            payment_id,
            status,
            confirmed_by=confirmed_by
        )

    def record_commission(self, **commission_data):
        return db.add_commission(**commission_data)

    def confirm_commission_paid(
        self,
        commission_id: int,
        paid_by: int = None
    ):
        return db.mark_commission_paid(
            commission_id,
            paid_by=paid_by
        )

    def add_bonus(self, **bonus_data):
        return db.add_bonus(**bonus_data)

    def add_ai_credits(self, **transaction_data):
        return db.add_ai_credit_transaction(**transaction_data)

    def get_ai_credit_balance(self, user_id: int):
        return db.get_ai_credit_balance(user_id)

    def accept_rules(self, user_id: int, rules_version: str):
        return db.accept_rules(user_id, rules_version)

    def log(self, actor_id: int, action: str, details=None):
        return db.log_action(
            actor_user_id=actor_id,
            action=action,
            details=details or {}
        )


services = MasterXServices()
            
