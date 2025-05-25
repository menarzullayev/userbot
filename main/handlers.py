from telethon import events, TelegramClient
from telethon.tl.types import User
from config import (
    ADMIN_ID,
    NEW_ACCOUNT_USERNAME,
    FORWARD_TO_USERNAME,
    logger,
)
from storage import whitelist_ids
from stats import stats
from display import display_name
from commands import handle_commands

replied_users = set()


async def register_handlers(client: TelegramClient, me_id: int):
    """Barcha xabar ishlovchilarini ro'yxatdan o'tkazadi."""

    @client.on(events.NewMessage(incoming=True))
    async def handle_new_message(event):
        sender = await event.get_sender()
        chat_id = event.chat_id

        if not sender:
            logger.info("Noma'lum jo'natuvchidan xabar. Ignor qilinadi.")
            return

        sender_id = sender.id

        if sender_id == me_id:
            return

        if sender_id == ADMIN_ID:
            reply_text = await handle_commands(event)
            if reply_text:
                await client.send_message(
                    chat_id, reply_text, reply_to=event.message.id
                )
                logger.info(
                    f"Admin buyrug'i '{event.raw_text.split()[0]}' {chat_id} da bajarildi."
                )
                return

        if not isinstance(sender, User):
            s_title = getattr(sender, "title", sender.id)
            logger.info(
                f"Foydalanuvchi bo'lmagan jo'natuvchi ({s_title}). Ignor qilinadi."
            )
            return

        if sender.bot:
            logger.info(f"Botdan ({sender_id}) xabar. Ignor qilinadi.")
            return

        if event.is_private:
            if sender_id in whitelist_ids:
                stats["whitelisted_messages"] += 1
                logger.debug(f"ID {sender_id} dan oq ro'yxat xabari.")
                return

            stats["received_messages"] += 1
            stats["unique_users"].add(sender_id)

            try:
                await client.forward_messages(
                    entity=FORWARD_TO_USERNAME, messages=event.message
                )
                stats["forwarded_messages"] += 1
            except Exception as e:
                logger.error(f"Forward qilishda xatolik ({sender_id}): {e}")
                stats["errors"] += 1
                try:
                    await client.send_message(
                        ADMIN_ID, f"Xatolik: Forward qilishda: {e}"
                    )
                except Exception as admin_e:
                    logger.error(f"Adminga xato yuborishda xatolik: {admin_e}")

            user_display_name, parse_mode = await display_name(client, sender)
            if sender_id not in replied_users:
                reply_text = (
                    f"Assalomu alaykum {user_display_name}!\n"
                    f"Hozirda bu yerda faol emasman!\n"
                    f"Iltimos, murojaatingizni yangi sahifamga qoldiring:\n"
                    f"{NEW_ACCOUNT_USERNAME}"
                )
                replied_users.add(sender_id)
            else:
                reply_text = (
                    f"Hurmatli {user_display_name}!\n\n"
                    f"Yangi sahifamga o'ting va murojaatingizni o'sha yerga qoldiring deb aytdim sizga!!!\n"
                    f"{NEW_ACCOUNT_USERNAME}"
                )

            try:
                await client.send_message(
                    entity=chat_id,
                    message=reply_text,
                    parse_mode=parse_mode,
                    reply_to=event.message.id,
                    link_preview=False,
                )
                stats["replied_messages"] += 1
            except Exception as e:
                logger.error(f"Javob yuborishda xatolik ({sender_id}): {e}")
                stats["errors"] += 1
                try:
                    await client.send_message(
                        ADMIN_ID, f"Xatolik: Javob yuborishda: {e}"
                    )
                except Exception as admin_e:
                    logger.error(f"Adminga xato yuborishda xatolik: {admin_e}")

    @client.on(events.NewMessage(chats="me", outgoing=True))
    async def handle_me_commands(event):

        if not event.raw_text or not event.raw_text.startswith("/"):
            return

        logger.info(f"Saved Messages da buyruq qabul qilindi: {event.raw_text}")
        reply_text = await handle_commands(event)
        if reply_text:

            await event.reply(reply_text)

            if ADMIN_ID != me_id:
                try:
                    await client.send_message(
                        ADMIN_ID,
                        f"Saved Messages buyrug'i [{event.raw_text.split()[0]}] natijasi:\n\n{reply_text}",
                    )
                except Exception as e:
                    logger.error(
                        f"Adminga 'Saved Messages' natijasini yuborishda xatolik: {e}"
                    )

            logger.info(
                f"Buyruq '{event.raw_text.split()[0]}' Saved Messages da bajarildi."
            )

    logger.info("Xabar ishlovchilari ro'yxatdan o'tkazildi.")
