
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
        "description",
        "price",
        "category",
        "platform",
        "guarantor_user_id",
    }

    OPTIONAL_FIELDS = {
        "title",
        "name",
        "video_url",
        "status",
        "lot_code",
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

    ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS | GAME_FIELDS

    def validate_lot(self, lot_data: dict) -> bool:
        if not isinstance(lot_data, dict):
            raise ValueError("Lot data must be a dictionary")

        data = dict(lot_data)

        # Дастгирии name ҳамчун номи кӯҳна
        if not data.get("title") and data.get("name"):
            data["title"] = data["name"]

        missing = [
            field
            for field in self.REQUIRED_FIELDS
            if data.get(field) in (None, "")
        ]

        if not data.get("title"):
            missing.append("title")

        if missing:
            raise ValueError(
                "Missing required fields: " + ", ".join(missing)
            )

        if not isinstance(data["title"], str):
            raise ValueError("Lot title must be text")

        if not isinstance(data["description"], str):
            raise ValueError("Description must be text")

        try:
            price = float(data["price"])
        except (TypeError, ValueError):
            raise ValueError("Price must be a number")

        if price < 0:
            raise ValueError("Price cannot be negative")

        try:
            guarantor_id = int(data["guarantor_user_id"])
        except (TypeError, ValueError):
            raise ValueError("Invalid guarantor_user_id")

        if guarantor_id <= 0:
            raise ValueError("Invalid guarantor_user_id")

        status = data.get("status", "available")
        if status not in self.ALLOWED_STATUSES:
            raise ValueError("Invalid lot status")

        return True

    def _normalize_data(self, lot_data: dict) -> dict:
        data = dict(lot_data)

        if not data.get("title") and data.get("name"):
            data["title"] = data["name"]

        data.pop("name", None)

        clean_data = {
            key: value
            for key, value in data.items()
            if key in self.ALLOWED_FIELDS
        }

        clean_data["price"] = float(clean_data["price"])
        clean_data["guarantor_user_id"] = int(
            clean_data["guarantor_user_id"]
        )
        clean_data.setdefault("status", "available")

        return clean_data

    def create_lot(self, **lot_data):
        self.validate_lot(lot_data)
        clean_data = self._normalize_data(lot_data)

        # database.py: add_lot(data)
        return db.add_lot(clean_data)

    def get_lot(self, lot_code: str):
        if not lot_code:
            raise ValueError("Lot code is required")

        # database.py ҷустуҷӯро бо lot_code анҷом медиҳад
        return db.get_lot(str(lot_code))

    def get_available_lots(self, limit: int = 50):
        if limit < 1:
            raise ValueError("Limit must be greater than zero")

        return db.list_lots(
            status="available",
            limit=limit,
            offset=0,
        )

    def get_lots_by_category(
        self,
        category: str,
        limit: int = 50,
    ):
        if not category:
            raise ValueError("Category is required")

        if limit < 1:
            raise ValueError("Limit must be greater than zero")

        return db.list_lots(
            status="available",
            category=category,
            limit=limit,
            offset=0,
        )

    def update_lot(self, lot_code: str, **updates):
        if not lot_code:
            raise ValueError("Lot code is required")

        if not updates:
            raise ValueError("No updates provided")

        data = dict(updates)

        if "name" in data and "title" not in data:
            data["title"] = data.pop("name")
        else:
            data.pop("name", None)

        allowed_update_fields = self.ALLOWED_FIELDS - {
            "guarantor_user_id",
            "lot_code",
        }

        unknown = set(data) - allowed_update_fields
        if unknown:
            raise ValueError(
                "Unsupported fields: " + ", ".join(sorted(unknown))
            )

        if "status" in data:
            if data["status"] not in self.ALLOWED_STATUSES:
                raise ValueError("Invalid lot status")

        if "price" in data:
            try:
                price = float(data["price"])
            except (TypeError, ValueError):
                raise ValueError("Invalid price")

            if price < 0:
                raise ValueError("Price cannot be negative")

            data["price"] = price

        if "title" in data:
            if not isinstance(data["title"], str) or not data["title"].strip():
                raise ValueError("Invalid lot title")

        # database.py: update_lot(lot_code, data)
        return db.update_lot(str(lot_code), data)

    def change_status(self, lot_code: str, status: str):
        if status not in self.ALLOWED_STATUSES:
            raise ValueError("Invalid lot status")

        return db.set_lot_status(str(lot_code), status)


lot_manager = LotManager()
        
