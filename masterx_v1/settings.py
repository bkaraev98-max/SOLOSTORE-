import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
FOUNDER_ID = int(os.getenv("FOUNDER_ID", "0"))

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "masterx_v1/masterx.db"
)

BOT_NAME = "MASTER X"
BOT_VERSION = "1.0.0"

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN is not configured!")

if FOUNDER_ID == 0:
    print("WARNING: FOUNDER_ID is not configured!")
