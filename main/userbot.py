import asyncio
import json
import logging
import os
import re
import time

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import Username, User

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL,
    handlers=[logging.FileHandler("userbot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

API_ID_STR = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_default_session")
NEW_ACCOUNT_USERNAME = os.getenv("NEW_ACCOUNT_USERNAME")
FORWARD_TO_USERNAME = os.getenv("FORWARD_TO_USERNAME", NEW_ACCOUNT_USERNAME)
WHITELIST_IDS_STR = os.getenv("WHITELIST_IDS", "")

ADMIN_ID = 7334856708
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
if not FORWARD_TO_USERNAME:
    logger.warning("DIQQAT: FORWARD_TO_USERNAME ishlatilmagan.")
    FORWARD_TO_USERNAME = NEW_ACCOUNT_USERNAME


def load_whitelist_ids():
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r") as f:
                data = json.load(f)
            return {int(uid) for uid in data}
        except Exception as e:
            logger.error(f"Whitelistsni yuklash xatosi: {e}")
            return set()
    else:
        if WHITELIST_IDS_STR:
            try:
                ids = {
                    int(uid.strip())
                    for uid in WHITELIST_IDS_STR.split(",")
                    if uid.strip()
                }
                with open(WHITELIST_FILE, "w") as f:
                    json.dump(list(ids), f)
                return ids
            except ValueError:
                logger.error("XATOLIK: WHITELIST_IDS noto'g'ri.")
                return set()
        else:
            return set()


def save_whitelist_ids():
    try:
        with open(WHITELIST_FILE, "w") as f:
            json.dump(list(whitelist_ids), f)
    except Exception as e:
        logger.error(f"Whitelistsni saqlashda xatolik: {e}")


whitelist_ids = load_whitelist_ids()
logger.info(f"Oq ro'yxat: {len(whitelist_ids)} ta.")

replied_users = set()
stats = {
    "start_time": time.time(),
    "received_messages": 0,
    "replied_messages": 0,
    "forwarded_messages": 0,
    "whitelisted_messages": 0,
    "unique_users": set(),
    "errors": 0,
}

MD_ESCAPE_CHARS = r"([_\*\[\]\(\)~`>#+\-=|{}!])"


def escape_foydalanuvchi(text: str) -> str:
    return re.sub(MD_ESCAPE_CHARS, r"\\\1", text)


client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
ME_ID = None


async def display_name(sender_obj: User):
    user_id = sender_obj.id
    try:
        entity = await client.get_entity(user_id)
    except Exception as e:
        logger.error(
            f"[ERROR] ID {user_id}: get_entity xatosi ({e}), fallback ishlatilmoqda."
        )
        entity = sender_obj

    is_contact = getattr(entity, "contact", False)
    first_name = getattr(entity, "first_name", "") or ""
    last_name = getattr(entity, "last_name", "") or ""

    raw = []
    if getattr(entity, "username", None):
        raw.append(entity.username)
    if hasattr(entity, "usernames"):
        try:
            for uu in entity.usernames:
                raw.append(uu)
        except Exception as e:
            logger.debug(f"[DEBUG] entity.usernames iteratsiya xatosi: {e}")

    username_candidates = []
    for cand in raw:
        if isinstance(cand, Username):
            if getattr(cand, "username", None):
                username_candidates.append(cand.username)
        elif isinstance(cand, str):
            username_candidates.append(cand)
    chosen_username = username_candidates[0] if username_candidates else None

    if is_contact:
        if chosen_username:
            return f"@{chosen_username}", None
        else:
            name = f"[{escape_foydalanuvchi('foydalanuvchi')}](tg://user?id={user_id})"
            return name, "md"
    else:
        display = (first_name + " " + last_name).strip() or "Foydalanuvchi"
        name = f"[{display}](tg://user?id={user_id})"
        return name, "md"


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    global ME_ID
    sender = await event.get_sender()
    chat_id = event.chat_id
    text = event.raw_text or ""
    sender_id = sender.id if sender else None

    if sender_id == ADMIN_ID:
        if text.startswith("/addwhitelist "):
            parts = text.split()
            if len(parts) == 2:
                try:
                    uid = int(parts[1])
                    if uid not in whitelist_ids:
                        whitelist_ids.add(uid)
                        save_whitelist_ids()
                        reply = f"ID {uid} oq ro'yxatga qo'shildi."
                    else:
                        reply = f"ID {uid} allaqachon oq ro'yxatda."
                except ValueError:
                    reply = "Xato: Iltimos, to'g'ri ID kiriting."
            else:
                reply = "Foydalanish: /addwhitelist <user_id>"
            await client.send_message(chat_id, reply)
            await client.send_message("me", reply)
            return

        elif text.startswith("/removewhitelist "):
            parts = text.split()
            if len(parts) == 2:
                try:
                    uid = int(parts[1])
                    if uid in whitelist_ids:
                        whitelist_ids.remove(uid)
                        save_whitelist_ids()
                        reply = f"ID {uid} oq ro'yxatdan olib tashlandi."
                    else:
                        reply = f"ID {uid} oq ro'yxatda yo'q."
                except ValueError:
                    reply = "Xato: Iltimos, to'g'ri ID kiriting."
            else:
                reply = "Foydalanish: /removewhitelist <user_id>"
            await client.send_message(chat_id, reply)
            await client.send_message("me", reply)
            return

        elif text.startswith("/stats"):
            up_time = time.time() - stats["start_time"]
            up_time_str = time.strftime("%H:%M:%S", time.gmtime(up_time))
            stats_text = (
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
            await client.send_message(chat_id, stats_text)
            await client.send_message("me", stats_text)
            return

        elif text.startswith("/help"):
            help_text = (
                "Admin buyruqlari:\n"
                "/addwhitelist <user_id> – Oq ro'yxatga foydalanuvchi qo'shish\n"
                "/removewhitelist <user_id> – Oq ro'yxatdan foydalanuvchini olib tashlash\n"
                "/stats – Bot statistikasi\n"
                "/help – Bu yordam xabari"
            )
            await client.send_message("me", help_text)
            await client.send_message(chat_id, help_text)
            return

    if event.is_private and sender and not sender.bot and not event.message.out:
        if sender_id in whitelist_ids:
            stats["whitelisted_messages"] += 1
            return

        stats["received_messages"] += 1
        stats["unique_users"].add(sender_id)

        try:
            await client.forward_messages(
                entity=FORWARD_TO_USERNAME, messages=event.message
            )
            stats["forwarded_messages"] += 1
        except Exception as e:
            logger.error(f"Forward qilishda xatolik: {e}")
            stats["errors"] += 1
            error_text = f"Xatolik: Forward qilishda: {e}"
            await client.send_message(ADMIN_ID, error_text)
            await client.send_message("me", error_text)

        display_name, parse_mode_to_use = await display_name(sender)
        if sender_id not in replied_users:
            reply_text = (
                f"Assalomu alaykum {display_name}!\n"
                f"Hozirda bu yerda faol emasman!\n"
                f"Iltimos, murojaatingizni yangi sahifamga qoldiring:\n"
                f"{NEW_ACCOUNT_USERNAME}"
            )
            replied_users.add(sender_id)
        else:
            reply_text = (
                f"Hurmatli {display_name}!\n\n"
                f"Yangi sahifamga o'ting va murojaatingizni o'sha yerga qoldiring deb aytdim sizga!!!\n"
                f"{NEW_ACCOUNT_USERNAME}"
            )

        try:
            await client.send_message(
                entity=chat_id,
                message=reply_text,
                parse_mode=parse_mode_to_use,
                reply_to=event.message.id,
                link_preview=False,
            )
            stats["replied_messages"] += 1
        except Exception as e:
            logger.error(f"Javob yuborishda xatolik: {e}")
            stats["errors"] += 1
            error_text = f"Xatolik: Javob yuborishda: {e}"
            await client.send_message(ADMIN_ID, error_text)
            await client.send_message("me", error_text)

    elif event.is_private and (not sender or sender.bot):
        logger.info("Bot yoki noma'lum jo'natuvchidan xabar. Ignor qilinadi.")


def log_stats():
    up_time = time.time() - stats["start_time"]
    up_time_str = time.strftime("%H:%M:%S", time.gmtime(up_time))
    logger.info("--- STATISTIKA ---")
    logger.info(f"Ishlagan vaqti: {up_time_str}")
    logger.info(
        f"Qabul qilingan xabarlar (oq ro'yxatdan tashqari): {stats['received_messages']}"
    )
    logger.info(f"Oq ro'yxatdagi xabarlar: {stats['whitelisted_messages']}")
    logger.info(f"Yuborilgan javoblar: {stats['replied_messages']}")
    logger.info(f"Forward qilingan xabarlar: {stats['forwarded_messages']}")
    logger.info(
        f"Unikal foydalanuvchilar (oq ro'yxatdan tashqari): {len(stats['unique_users'])}"
    )
    logger.info(f"Xatoliklar soni: {stats['errors']}")
    logger.info("--------------------")


async def clear_replied_users_periodically():
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
        if my_self:
            ME_ID = my_self.id
            username_display = (
                f"@{my_self.username}" if my_self.username else f"ID: {my_self.id}"
            )
            logger.info(
                f"Userbot ishga tushdi ({my_self.first_name} ({username_display}) nomidan)..."
            )
            logger.info(f"Yangi akkaunt: {NEW_ACCOUNT_USERNAME}")
            logger.info(f"Forward manzil: {FORWARD_TO_USERNAME}")
            logger.info(f"Oq ro'yxat: {len(whitelist_ids)} ta")
        else:
            logger.error("XATOLIK: Foydalanuvchi ma'lumotlarini olib bo'lmadi!")
            return

        log_stats()
        asyncio.create_task(clear_replied_users_periodically())
        await client.run_until_disconnected()
    except Exception as e:
        logger.critical(f"Main fonctionsida global xatolik: {e}", exc_info=True)
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
        logger.info("Dastur to'xtatildi.")
    except Exception as e:
        logger.critical(f"Umumiy ishga tushirish xatoligi: {e}", exc_info=True)
    finally:
        logger.info("Dastur yakunlandi.")
