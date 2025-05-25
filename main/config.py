import logging
import os
import sys
import io
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except (AttributeError, io.UnsupportedOperation):
    print(
        "Warning: Could not reconfigure stdout/stderr to UTF-8 (maybe not running in a TTY or unsupported buffer)."
    )
    pass


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL,
    handlers=[
        logging.FileHandler("userbot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


API_ID_STR = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_default_session")
NEW_ACCOUNT_USERNAME = os.getenv("NEW_ACCOUNT_USERNAME")
FORWARD_TO_USERNAME = os.getenv("FORWARD_TO_USERNAME", NEW_ACCOUNT_USERNAME)
ADMIN_ID_STR = os.getenv("ADMIN_ID")

WHITELIST_FILE = "whitelist_ids.json"

if not API_ID_STR:
    logger.error("XATOLIK: API_ID topilmadi.")
    exit(1)
try:
    API_ID = int(API_ID_STR)
except ValueError:
    logger.error(f"XATOLIK: API_ID ('{API_ID_STR}') yaroqli emas.")
    exit(1)

if not API_HASH:
    logger.error("XATOLIK: API_HASH topilmadi.")
    exit(1)
if not NEW_ACCOUNT_USERNAME:
    logger.error("XATOLIK: NEW_ACCOUNT_USERNAME topilmadi.")
    exit(1)
if not ADMIN_ID_STR:
    logger.error("XATOLIK: ADMIN_ID topilmadi.")
    exit(1)
try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    logger.error(f"XATOLIK: ADMIN_ID ('{ADMIN_ID_STR}') yaroqli emas.")
    exit(1)

logger.info("Konfiguratsiya yuklandi.")
