try:
    from .database import db
except ImportError:
    from database import db


class LotManager:

    ALLOWED_STATUSES = {
        "available",
        "reserved",
        "sold",
        "inactive",
    }

    REQUIRED_FIELDS = {
        "name",
        "description",
        "price",
        "category",
        "guarantor_user_id",
        "video_url",
    }

    GAME_FIELDS = {
        "level",
        "classic_level",
        "metro_level",
        "collection_level",
        "upgrades",
        "mythic_count",
        "account_age",
        "bindings",
        "full_binding",
        "important_info",
        "extra_info",
    }

    def validate_lot(self, lot_data: dict):
        missing = [
            field
            for field in self.REQUIRED_FIELDS
            if field not in lot_data or lot_data[field] in (None, "")
        ]

        if missing:
            raise ValueError(
                "Missing required fields: " + ", ".join(missing)
            )

        try:
            price = float(lot_data["price"])
        except (TypeError, ValueError):
            raise ValueError("Price must be a number")

        if price < 0:
            raise ValueError("Price cannot be negative")

        if not isinstance(lot_data["name"], str):
            raise ValueError("Lot name must be text")

        return True

    def create_lot(self, **lot_data):
        self.validate_lot(lot_data)

        lot_data.setdefault("status", "available")

        if lot_data["status"] not in self.ALLOWED_STATUSES:
            raise ValueError("Invalid lot status")

        allowed_fields = (
            self.REQUIRED_FIELDS
            | self.GAME_FIELDS
            | {"status", "platform"}
        )

        clean_data = {
            key: value
            for key, value in lot_data.items()
            if key in allowed_fields
        }

        return db.add_lot(**clean_data)

    def get_lot(self, lot_id: int):
        return db.get_lot(lot_id)

    def get_available_lots(self, limit: int = 50):
        return db.list_lots(
            status="available",
            limit=limit,
        )

    def get_lots_by_category(
        self,
        category: str,
        limit: int = 50,
    ):
        return db.list_lots(
            status="available",
            category=category,
            limit=limit,
        )

    def update_lot(self, lot_id: int, **updates):
        if not updates:
            raise ValueError("No updates provided")

        if "status" in updates:
            if updates["status"] not in self.ALLOWED_STATUSES:
                raise ValueError("Invalid lot status")

        if "price" in updates:
            try:
                if float(updates["price"]) < 0:
                    raise ValueError("Price cannot be negative")
            except (TypeError, ValueError):
                raise ValueError("Invalid price")

        return db.update_lot(lot_id, **updates)

    def change_status(self, lot_id: int, status: str):
        if status not in self.ALLOWED_STATUSES:
            raise ValueError("Invalid lot status")

        return db.set_lot_status(lot_id, status)


lot_manager = LotManager()
