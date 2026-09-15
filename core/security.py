from config import ADMIN_ID


def is_master_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False

    return user_id == ADMIN_ID


def require_master_admin(user_id: int | None) -> None:
    if not is_master_admin(user_id):
        raise PermissionError("Access denied.")
