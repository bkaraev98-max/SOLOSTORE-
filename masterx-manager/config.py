import os


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is not configured."
        )

    return value


MASTER_BOT_TOKEN = get_required_env("MASTER_BOT_TOKEN")

ADMIN_ID = int(get_required_env("ADMIN_ID"))

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "masterx.db",
)

APP_HOST = os.getenv(
    "APP_HOST",
    "0.0.0.0",
)

APP_PORT = int(
    os.getenv(
        "PORT",
        "8080",
    )
)
