import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
STEAM_REGION = os.getenv("STEAM_REGION", "JP")
TOP_N = int(os.getenv("TOP_N", "50"))
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))

LOG_DIR = "logs"
LOG_PATH = "logs/app.log"
