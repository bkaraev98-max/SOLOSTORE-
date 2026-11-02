from datetime import datetime, timezone

try:
    from .database import db
except ImportError:
    from database import db


class SubscriptionManager:

    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"

    def now(self):
        return datetime.now(timezone.utc)

    def parse_time(self, value):
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(value)

    def create_subscription(
        self,
        user_id: int,
        plan_name: str,
        duration_seconds: int,
        is_vip_pluss: bool = False,
    ):
        if duration_seconds <= 0:
            raise ValueError("Duration must be positive")

        now = self.now()

        return db.create_subscription(
            user_id=user_id,
            plan_name=plan_name,
            status=self.PAUSED,
            remaining_seconds=duration_seconds,
            is_vip_pluss=is_vip_pluss,
            started_at=None,
            expires_at=None,
            created_at=now.isoformat(),
        )

    def start_subscription(self, subscription_id: int):
        subscription = db.get_subscription(subscription_id)

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription["status"] == self.EXPIRED:
            raise ValueError("Subscription has expired")

        now = self.now()
        remaining = int(subscription["remaining_seconds"])

        if remaining <= 0:
            self.expire_subscription(subscription_id)
            return False

        expires_at = (
            now.timestamp() + remaining
        )

        return db.update_subscription(
            subscription_id,
            status=self.ACTIVE,
            started_at=now.isoformat(),
            expires_at=datetime.fromtimestamp(
                expires_at,
                tz=timezone.utc,
            ).isoformat(),
        )

    def pause_subscription(self, subscription_id: int):
        subscription = db.get_subscription(subscription_id)

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription["status"] != self.ACTIVE:
            return False

        if subscription.get("is_vip_pluss"):
            return False

        expires_at = self.parse_time(
            subscription.get("expires_at")
        )

        if not expires_at:
            raise ValueError("Expiration time missing")

        remaining = max(
            0,
            int((expires_at - self.now()).total_seconds()),
        )

        if remaining <= 0:
            self.expire_subscription(subscription_id)
            return False

        return db.update_subscription(
            subscription_id,
            status=self.PAUSED,
            remaining_seconds=remaining,
            started_at=None,
            expires_at=None,
        )

    def expire_subscription(self, subscription_id: int):
        return db.update_subscription(
            subscription_id,
            status=self.EXPIRED,
            remaining_seconds=0,
        )

    def get_remaining_seconds(self, subscription_id: int):
        subscription = db.get_subscription(subscription_id)

        if not subscription:
            return 0

        if subscription["status"] == self.PAUSED:
            return max(
                0,
                int(subscription["remaining_seconds"]),
            )

        if subscription["status"] == self.EXPIRED:
            return 0

        expires_at = self.parse_time(
            subscription.get("expires_at")
        )

        if not expires_at:
            return 0

        remaining = max(
            0,
            int((expires_at - self.now()).total_seconds()),
        )

        if remaining == 0:
            self.expire_subscription(subscription_id)

        return remaining

    def switch_subscription(
        self,
        old_subscription_id: int | None,
        new_subscription_id: int,
    ):
        if old_subscription_id == new_subscription_id:
            return True

        if old_subscription_id is not None:
            self.pause_subscription(old_subscription_id)

        new_subscription = db.get_subscription(
            new_subscription_id
        )

        if not new_subscription:
            raise ValueError("New subscription not found")

        return self.start_subscription(new_subscription_id)


subscription_manager = SubscriptionManager()
