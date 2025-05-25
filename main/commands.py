from telethon.events import NewMessage
from storage import whitelist_ids, save_whitelist_ids
from stats import get_stats_text
from config import logger


async def handle_commands(event: NewMessage.Event) -> str | None:

    text = event.raw_text or ""
    reply = ""

    if text.startswith("/add "):
        parts = text.split()
        if len(parts) == 2:
            try:
                uid = int(parts[1])
                if uid not in whitelist_ids:
                    whitelist_ids.add(uid)
                    save_whitelist_ids(whitelist_ids)
                    reply = f"ID {uid} oq ro'yxatga qo'shildi."
                else:
                    reply = f"ID {uid} allaqachon oq ro'yxatda."
            except ValueError:
                reply = "Xato: Iltimos, to'g'ri ID kiriting."
        else:
            reply = "Foydalanish: /add <user_id>"

    elif text.startswith("/remove "):
        parts = text.split()
        if len(parts) == 2:
            try:
                uid = int(parts[1])
                if uid in whitelist_ids:
                    whitelist_ids.remove(uid)
                    save_whitelist_ids(whitelist_ids)
                    reply = f"ID {uid} oq ro'yxatdan olib tashlandi."
                else:
                    reply = f"ID {uid} oq ro'yxatda yo'q."
            except ValueError:
                reply = "Xato: Iltimos, to'g'ri ID kiriting."
        else:
            reply = "Foydalanish: /remove <user_id>"

    elif text.startswith("/list"):
        if not whitelist_ids:
            reply = "Oq ro'yxat bo'sh."
        else:
            reply = "Oq ro'yxatdagi IDlar:\n" + "\n".join(
                [str(uid) for uid in whitelist_ids]
            )

    elif text.startswith("/stats"):
        reply = get_stats_text()

    elif text.startswith("/help"):
        reply = (
            "Buyruqlar:\n"
            "/add <user_id> – Oq ro'yxatga qo'shish\n"
            "/remove <user_id> – Oq ro'yxatdan olib tashlash\n"
            "/list – Oq ro'yxatni ko'rish\n"
            "/stats – Statistika\n"
            "/help – Yordam"
        )

    return reply
