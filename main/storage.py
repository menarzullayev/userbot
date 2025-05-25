import json
import logging
import os
from config import WHITELIST_FILE, logger


def save_whitelist_ids(whitelist_ids: set[int]):
    try:
        with open(WHITELIST_FILE, "w") as f:
            json.dump(list(whitelist_ids), f, indent=4)
        logger.info(f"{len(whitelist_ids)} ta ID oq ro'yxatga saqlandi.")
    except Exception as e:
        logger.error(f"Oq ro'yxatni saqlashda xatolik: {e}")


def load_whitelist_ids() -> set[int]:
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r") as f:
                content = f.read()
                if not content:
                    logger.warning(f"{WHITELIST_FILE} bo'sh, bo'sh ro'yxat qaytarildi.")
                    return set()
                data = json.loads(content)
            logger.info(f"{len(data)} ta ID oq ro'yxatdan yuklandi.")
            return set(data)
        except json.JSONDecodeError:
            logger.error(f"XATOLIK: {WHITELIST_FILE} fayli yaroqsiz JSON formatida.")
            return set()
        except Exception as e:
            logger.error(f"Oq ro'yxatni yuklash xatosi: {e}")
            return set()
    else:
        logger.warning(
            f"{WHITELIST_FILE} topilmadi, bo'sh ro'yxat yaratildi va saqlandi."
        )
        save_whitelist_ids(set())
        return set()


whitelist_ids = load_whitelist_ids()
