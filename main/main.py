import asyncio
import time
import logging
from telethon import TelegramClient
from config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
    NEW_ACCOUNT_USERNAME,
    FORWARD_TO_USERNAME,
    ADMIN_ID,
    logger,
)
from storage import whitelist_ids
from stats import stats, log_stats
from handlers import register_handlers, replied_users

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
ME_ID = None


async def clear_replied_users_periodically():
    """Vaqti-vaqti bilan javob berilgan foydalanuvchilar ro'yxatini tozalaydi."""
    while True:
        await asyncio.sleep(3600)
        replied_users.clear()
        logger.info("Replied_users ro'yxati 1 soatdan so‘ng tozalandi.")


async def main():
    global ME_ID
    try:
        logger.info("Telegramga ulanish boshlanmoqda...")
        await client.start()
        my_self = await client.get_me()

        if not my_self:
            logger.error("XATOLIK: Foydalanuvchi ma'lumotlarini olib bo'lmadi!")
            return

        ME_ID = my_self.id
        username_display = (
            f"@{my_self.username}" if my_self.username else f"ID: {ME_ID}"
        )
        logger.info(
            f"Userbot ishga tushdi ({my_self.first_name} ({username_display}) nomidan)..."
        )
        logger.info(f"Admin ID: {ADMIN_ID}")
        logger.info(f"Yangi akkaunt: {NEW_ACCOUNT_USERNAME}")
        logger.info(f"Forward manzil: {FORWARD_TO_USERNAME}")
        logger.info(f"Oq ro'yxat: {len(whitelist_ids)} ta")

        await register_handlers(client, ME_ID)

        log_stats()

        asyncio.create_task(clear_replied_users_periodically())

        logger.info("Userbot xabarlarni tinglashni boshladi...")
        await client.run_until_disconnected()

    except Exception as e:
        logger.critical(f"Main funksiyasida global xatolik: {e}", exc_info=True)
        stats["errors"] += 1
    finally:
        logger.info("Yakuniy statistika...")
        log_stats()
        if client.is_connected():
            logger.info("Klientni o'chirish...")
            await client.disconnect()
            logger.info("Klient o'chirildi.")
        else:
            logger.info("Klient ulanmagan.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dastur foydalanuvchi tomonidan to'xtatildi.")
    except Exception as e:
        logger.critical(f"Umumiy ishga tushirish xatoligi: {e}", exc_info=True)
    finally:
        logger.info("Dastur yakunlandi.")
