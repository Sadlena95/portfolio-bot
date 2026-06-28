import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY") or None

_google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_APPLICATION_CREDENTIALS = os.path.expanduser(_google_creds) if _google_creds else None
GOOGLE_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
