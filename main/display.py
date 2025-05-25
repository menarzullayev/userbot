import logging
from telethon.tl.types import Username, User
from utils import escape_markdown
from config import logger


async def display_name(client, sender_obj: User) -> tuple[str, str | None]:
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
            name = f"[{escape_markdown('foydalanuvchi')}](tg://user?id={user_id})"
            return name, "md"
    else:
        display = (first_name + " " + last_name).strip() or "Foydalanuvchi"
        name = f"[{escape_markdown(display)}](tg://user?id={user_id})"
        return name, "md"
