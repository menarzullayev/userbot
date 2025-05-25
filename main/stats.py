import time
import logging
from config import logger

stats = {
    "start_time": time.time(),
    "received_messages": 0,
    "replied_messages": 0,
    "forwarded_messages": 0,
    "whitelisted_messages": 0,
    "unique_users": set(),
    "errors": 0,
}

def get_stats_text() -> str:
    """Statistika matnini qaytaradi."""
    up_time = time.time() - stats["start_time"]
    up_time_str = time.strftime("%H:%M:%S", time.gmtime(up_time))
    return (
        "--- STATISTIKA ---\n"
        f"Ishlagan vaqti: {up_time_str}\n"
        f"Qabul qilingan xabarlar (oq ro'yxatdan tashqari): {stats['received_messages']}\n"
        f"Oq ro'yxatdagi xabarlar: {stats['whitelisted_messages']}\n"
        f"Yuborilgan javoblar: {stats['replied_messages']}\n"
        f"Forward qilingan xabarlar: {stats['forwarded_messages']}\n"
        f"Unikal foydalanuvchilar (oq ro'yxatdan tashqari): {len(stats['unique_users'])}\n"
        f"Xatoliklar soni: {stats['errors']}\n"
        "--------------------"
    )

def log_stats():
    """Statistikani logga yozadi."""
    logger.info(get_stats_text())
