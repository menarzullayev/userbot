import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User
from telethon.errors.rpcerrorlist import UserIsBlockedError, ChatWriteForbiddenError # Maxsus xatoliklar uchun
import re
import logging
import os
from dotenv import load_dotenv

# .env faylidan o'zgaruvchilarni yuklash
load_dotenv()

# Logging sozlamalari
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# .env faylidan konfiguratsiyalarni olish
API_ID_STR = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME', 'userbot_default_session')
NEW_ACCOUNT_USERNAME = os.getenv('NEW_ACCOUNT_USERNAME')

# API_ID ni integerga o'tkazish va tekshirish
if API_ID_STR is None:
    logger.error("XATOLIK: .env faylida API_ID topilmadi yoki sozlanmagan.")
    exit(1)
try:
    API_ID = int(API_ID_STR)
except ValueError:
    logger.error(f"XATOLIK: .env faylidagi API_ID ('{API_ID_STR}') yaroqli butun son emas.")
    exit(1)

if not API_HASH:
    logger.error("XATOLIK: .env faylida API_HASH topilmadi yoki sozlanmagan.")
    exit(1)
if not NEW_ACCOUNT_USERNAME:
    logger.error("XATOLIK: .env faylida NEW_ACCOUNT_USERNAME topilmadi yoki sozlanmagan.")
    exit(1)


client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

def escape_markdown_v2_for_display(text: str) -> str:
    # MarkdownV2 uchun maxsus belgilarni ekranlash
    # Ushbu ro'yxat Telegram hujjatlaridan olingan va kengaytirilgan bo'lishi mumkin
    escape_chars = r'([_*\[\]()~`>#\+\-=|{}\.!])' # \ belgisi o'zi ham maxsus
    return re.sub(escape_chars, r'\\\1', text)

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    sender_event_obj = await event.get_sender()
    
    # Faqat shaxsiy chatlar, bot bo'lmagan foydalanuvchilardan kelgan va o'zimiz yozmagan xabarlarga javob beramiz
    if event.is_private and sender_event_obj and not sender_event_obj.bot and not event.message.out:
        chat_id = event.chat_id
        greeting_part = "" 
        parse_mode_to_use = None # Agar markdown ishlatilmasa None bo'ladi

        # Foydalanuvchi kontaktlarda mavjudligini tekshirish
        if sender_event_obj.contact:
            logger.info(f"Foydalanuvchi {sender_event_obj.id} kontaktda mavjud.")
            chosen_username_for_contact = None
            if sender_event_obj.username:
                chosen_username_for_contact = sender_event_obj.username
                logger.info(f"Kontakt uchun asosiy username ishlatildi: @{chosen_username_for_contact}")
            elif hasattr(sender_event_obj, 'usernames') and sender_event_obj.usernames: # Ba'zi user obyektlarida bu atribut bo'lmasligi mumkin
                active_usernames = [u.username for u in sender_event_obj.usernames if u.active and u.username]
                if active_usernames:
                    chosen_username_for_contact = active_usernames[0]
                    logger.info(f"Kontakt uchun birinchi aktiv username (ro'yxatdan) ishlatildi: @{chosen_username_for_contact}")
                else: 
                    first_available_username_from_list = [u.username for u in sender_event_obj.usernames if u.username]
                    if first_available_username_from_list:
                        chosen_username_for_contact = first_available_username_from_list[0]
                        logger.info(f"Kontakt uchun birinchi username (ro'yxatdan, aktivligi noma'lum) ishlatildi: @{chosen_username_for_contact}")
            
            if chosen_username_for_contact:
                # Oddiy @username mention uchun Markdown kerak emas, Telegram o'zi handle qiladi.
                # Lekin agar formatlashni to'liq nazorat qilmoqchi bo'lsak, 'md' ishlatishimiz mumkin.
                # Bu yerda oddiy matn sifatida qo'yamiz, chunki @username o'zi link bo'ladi.
                greeting_part = f"Assalomu alaykum @{chosen_username_for_contact}!"
                # parse_mode_to_use = 'md' # Agar boshqa MD formatlash kerak bo'lsa
            else:
                greeting_part = "Assalomu alaykum!"
                logger.info("Kontakt uchun umumiy salomlashish (username topilmadi).")
        
        else: # Foydalanuvchi kontaktlarda emas
            logger.info(f"Foydalanuvchi {sender_event_obj.id} kontaktda emas. Public ism-familiya olinadi.")
            
            public_first_name = ""
            public_last_name = ""
            
            try:
                logger.info(f"Foydalanuvchi {sender_event_obj.id} uchun to'liq (public) ma'lumot so'ralmoqda...")
                # GetFullUserRequest natijasi UserFull obyektini qaytaradi
                full_user_data = await client(GetFullUserRequest(id=sender_event_obj.id))
                logger.debug(f"DEBUG: GetFullUserRequest natijasi (raw) for {sender_event_obj.id}: {full_user_data}")

                actual_user_profile = None
                # UserFull.full_user atributi User obyektini saqlaydi (Telethon v1.20+ da UserFull.user)
                # Telethonning turli versiyalari uchun moslashuvchanlik:
                potential_user_attr_names = ['user', 'full_user'] 
                for attr_name in potential_user_attr_names:
                    if hasattr(full_user_data, attr_name) and isinstance(getattr(full_user_data, attr_name), User):
                        if getattr(full_user_data, attr_name).id == sender_event_obj.id:
                            actual_user_profile = getattr(full_user_data, attr_name)
                            break
                
                # Agar yuqoridagi usul bilan topilmasa, .users ro'yxatidan qidiramiz
                if not actual_user_profile and hasattr(full_user_data, 'users'):
                    for u in full_user_data.users:
                        if isinstance(u, User) and u.id == sender_event_obj.id:
                            actual_user_profile = u
                            break
                
                if actual_user_profile:
                    public_first_name = actual_user_profile.first_name if actual_user_profile.first_name else ""
                    public_last_name = actual_user_profile.last_name if actual_user_profile.last_name else ""
                    logger.info(f"GetFullUserRequest (kontakt emas): Ism='{public_first_name}', Familiya='{public_last_name}'")
                else:
                    logger.warning("GetFullUserRequest (kontakt emas) dan User obyekti olinmadi yoki ID mos kelmadi. event.get_sender() dagi ismdan foydalaniladi.")
                    public_first_name = sender_event_obj.first_name if sender_event_obj.first_name else ""
                    public_last_name = sender_event_obj.last_name if sender_event_obj.last_name else ""
            except Exception as e:
                logger.error(f"Foydalanuvchi {sender_event_obj.id} (kontakt emas) uchun to'liq ma'lumot olishda xatolik: {e}. event.get_sender() dagi ismdan foydalaniladi.", exc_info=True)
                public_first_name = sender_event_obj.first_name if sender_event_obj.first_name else ""
                public_last_name = sender_event_obj.last_name if sender_event_obj.last_name else ""

            display_name_non_contact = public_first_name.strip()
            if public_last_name.strip():
                display_name_non_contact = f"{public_first_name.strip()} {public_last_name.strip()}"
            
            if not display_name_non_contact.strip(): # Agar ism-familiya umuman topilmasa
                display_name_non_contact = f"Foydalanuvchi ({sender_event_obj.id})" # Fallback
            
            escaped_display_name_non_contact = escape_markdown_v2_for_display(display_name_non_contact)
            markdown_mention_non_contact = f"[{escaped_display_name_non_contact}](tg://user?id={sender_event_obj.id})"
            greeting_part = f"Assalomu alaykum {markdown_mention_non_contact}!"
            parse_mode_to_use = 'md' 
            logger.info(f"Kontaktda bo'lmagan foydalanuvchi uchun display_name: '{display_name_non_contact}' (mention bilan)")

        
        # Xabar tanasi
        message_body = (
            f"\nHozirda bu yerda faol emasman!\n"
            f"\nIltimos, murojaatingizni yangi sahifamga qoldiring:\n"
            f"{NEW_ACCOUNT_USERNAME}\n" # Bu yerda @username o'zi link bo'ladi
        )
        reply_text = f"{greeting_part}{message_body}"
        
        sender_display_name_log = sender_event_obj.username if sender_event_obj.username else f"ID: {sender_event_obj.id}"
        
        logger.info(f"Yangi xabar keldi (qayta ishlash uchun): Kimdan: {sender_display_name_log}, Chat ID: {chat_id}, Xabar: '{event.message.text}'")
        logger.debug(f"DEBUG: Yuborilayotgan matn: '{reply_text}', parse_mode='{parse_mode_to_use}'")

        try:
            logger.info(f"{sender_display_name_log} ga javob yuborilmoqda...")
            await client.send_message(
                entity=chat_id,
                message=reply_text,
                parse_mode=parse_mode_to_use,
                reply_to=event.message.id,
                link_preview=False # NEW_ACCOUNT_USERNAME uchun alohida preview kerak emas
            )
            logger.info(f"{sender_display_name_log} ga javob muvaffaqiyatli yuborildi.")
        
        except (UserIsBlockedError, ChatWriteForbiddenError) as e:
            logger.warning(f"{sender_display_name_log} ga xabar yuborishda ruxsat bilan bog'liq xatolik: {type(e).__name__} - {e}")
        except Exception as e:
            # Boshqa kutilmagan xatoliklar (masalan, tarmoq muammolari, FloodWaitError - garchi Telethon buni o'zi hal qilsa ham)
            logger.error(f"Xatolik yuz berdi ({sender_display_name_log} ga yuborishda): {type(e).__name__} - {e}", exc_info=True)
            
    elif event.is_private and (not sender_event_obj or (sender_event_obj and sender_event_obj.bot)):
        sender_info = "Noma'lum jo'natuvchi"
        if sender_event_obj and sender_event_obj.bot:
            sender_info = f"Bot ({sender_event_obj.username if sender_event_obj.username else sender_event_obj.id})"
        logger.info(f"Shaxsiy chatda {sender_info}dan kelgan xabarga javob berilmadi (e'tiborga olinmadi).")

async def main():
    try:
        logger.info("Telegramga ulanish boshlanmoqda...")
        logger.info("Agar birinchi marta ulanayotgan bo'lsangiz (yangi sessiya uchun),")
        logger.info("Telefon raqamingiz, Telegram kodi va agar mavjud bo'lsa 2FA parolingiz so'raladi.")
        
        # Klientni ishga tushirish va login qilish
        # `client.start()` o'rniga `client.connect()` va `client.is_user_authorized()` / `client.sign_in()`
        # kabi bosqichma-bosqich yondashuv ham mumkin, lekin `start()` o'zi bularni boshqaradi.
        await client.start() 

        my_self = await client.get_me()
        if my_self:
            username_display = f"@{my_self.username}" if my_self.username else f"ID: {my_self.id}"
            logger.info(f"Userbot ishga tushdi ({my_self.first_name} ({username_display}) nomidan) va yangi xabarlarni kutmoqda...")
            logger.info(f"Bu akkauntga ({username_display}) kelgan shaxsiy xabarlarga avtomatik javob beriladi.")
            logger.info(f"Yangi akkaunt manzili: {NEW_ACCOUNT_USERNAME}")
        else:
            logger.error("XATOLIK: Foydalanuvchi ma'lumotlarini olib bo'lmadi! Sessiya bilan muammo bo'lishi mumkin.")
            return # Agar o'zimiz haqimizda ma'lumot ololmasak, davom etishdan ma'no yo'q

        # Xabarlarni qabul qilish uchun doimiy ishlash
        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Main funksiyasida global xatolik: {type(e).__name__} - {e}", exc_info=True)
    finally:
        # Asosiy `main` funksiya tugaganda yoki xatolik bilan yakunlanganda klientni o'chiramiz
        if client.is_connected():
            logger.info("Klientni asosiy funksiya yakunida o'chirish...")
            await client.disconnect()
            logger.info("Klient muvaffaqiyatli o'chirildi.")
        else:
            logger.info("Klient ulanmagan yoki allaqachon o'chirilgan edi (main's finally).")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dastur foydalanuvchi tomonidan to'xtatildi (KeyboardInterrupt).")
        # Bu yerda klient allaqachon `main` ning `finally` blokida o'chirilgan bo'lishi kerak,
        # lekin har ehtimolga qarshi yana tekshirish mumkin.
    except Exception as e:
        logger.error(f"Dasturning umumiy ishga tushirishida kutilmagan xatolik: {type(e).__name__} - {e}", exc_info=True)
    finally:
        # Agar `asyncio.run(main())` xatolik bilan tugasa ham, bu blok ishlaydi.
        # Klient `main` ning `finally` blokida o'chirilishi kerak.
        # Bu yerdagi `finally` asosan dasturning toza yakunlanganini loglash uchun.
        logger.info("Dastur o'z ishini yakunladi.")

