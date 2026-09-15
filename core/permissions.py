from enum import IntEnum


class Role(IntEnum):
    USER = 10
    OPERATOR = 20
    ADMIN = 30
    MANAGER = 40
    OWNER = 50


def has_permission(
    role: Role,
    required_role: Role,
) -> bool:
    return role >= required_role
