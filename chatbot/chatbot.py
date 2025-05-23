import logging
import json
import os
from telegram import Update, Message as TelegramMessage, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Bot tokeningizni shu yerga qo'ying
BOT_TOKEN = "8129388433:AAFq5KJtWuZ_fvQ-bcOFjTdUFuUX731_1N0" # O'ZINGIZNING BOT TOKENINGIZNI KIRITING

# Salomlashilgan foydalanuvchilarni saqlash uchun JSON fayl nomi
GREETED_USERS_FILE = "greeted_users.json"

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Ma'lumotlarni yuklash va saqlash funksiyalari ---
def load_greeted_users():
    if os.path.exists(GREETED_USERS_FILE):
        try:
            with open(GREETED_USERS_FILE, 'r') as f:
                content = f.read()
                if not content:
                    logger.info(f"{GREETED_USERS_FILE} fayli bo'sh.")
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"{GREETED_USERS_FILE} faylida JSON o'qish xatosi. Bo'sh lug'at qaytarilmoqda.")
            return {}
        except Exception as e:
            logger.error(f"{GREETED_USERS_FILE} faylini o'qishda kutilmagan xatolik: {e}")
            return {}
    logger.info(f"{GREETED_USERS_FILE} fayli topilmadi. Bo'sh lug'at yaratilmoqda.")
    return {}

def save_greeted_users(data):
    try:
        with open(GREETED_USERS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"{GREETED_USERS_FILE} fayliga ma'lumotlar saqlandi.")
    except Exception as e:
        logger.error(f"{GREETED_USERS_FILE} fayliga saqlashda xatolik: {e}")

# --- Tugma bosilishlarini qayta ishlash uchun callback funksiyalari ---
async def tanishish_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Tugma bosilganini Telegramga bildirish

    tanishish_text = ("Assalomu alaykum! Mening ismim menarzullayev (Narzullayev Asadbek).\n\n"
                      "Men Full-Stack dasturchiman. Python (Django, FastAPI, DRF, Aiogram) va JavaScript (Vue.js, Nuxt.js) texnologiyalari bilan ishlayman.\n\n"
                      "Agar sizda dasturlash yoki IT sohasiga oid loyihalar, g'oyalar bo'lsa yoki hamkorlik qilmoqchi bo'lsangiz, bemalol murojaat qilishingiz mumkin.\n\n"
                      "Qo'shimcha ma'lumot uchun @NarzullayevPro profilimga yozishingiz mumkin.")
    
    business_connection_id = None
    chat_id_to_reply = None

    if query.message: # Tugma bosilgan xabar mavjudligini tekshirish
        chat_id_to_reply = query.message.chat.id
        if hasattr(query.message, 'business_connection_id'):
            business_connection_id = query.message.business_connection_id
    else: # Agar qandaydir sabab bilan query.message bo'lmasa (juda kam holat)
        chat_id_to_reply = query.from_user.id


    try:
        if chat_id_to_reply:
            await context.bot.send_message(
                chat_id=chat_id_to_reply,
                text=tanishish_text,
                business_connection_id=business_connection_id # Agar None bo'lsa, oddiy xabar kabi yuboriladi
            )
            logger.info(f"TANISHISH_CALLBACK: 'Tanishish' tugmasi uchun javob yuborildi. Chat ID: {chat_id_to_reply}, Biznes ID: {business_connection_id if business_connection_id else 'N/A'}")
        else:
            logger.error("TANISHISH_CALLBACK_ERROR: Javob yuborish uchun chat_id topilmadi.")
    except Exception as e:
        logger.error(f"TANISHISH_CALLBACK_ERROR: 'Tanishish' javobini yuborishda xatolik: {e}")

async def savol_berish_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    savol_berish_text = "Marhamat, savolingizni yoki taklifingizni shu yerda yozishingiz mumkin. Imkon qadar tezroq javob berishga harakat qilaman."
    
    business_connection_id = None
    chat_id_to_reply = None

    if query.message:
        chat_id_to_reply = query.message.chat.id
        if hasattr(query.message, 'business_connection_id'):
            business_connection_id = query.message.business_connection_id
    else:
        chat_id_to_reply = query.from_user.id
            
    try:
        if chat_id_to_reply:
            await context.bot.send_message(
                chat_id=chat_id_to_reply,
                text=savol_berish_text,
                business_connection_id=business_connection_id
            )
            logger.info(f"SAVOL_BERISH_CALLBACK: 'Savol berish' tugmasi uchun javob yuborildi. Chat ID: {chat_id_to_reply}, Biznes ID: {business_connection_id if business_connection_id else 'N/A'}")
        else:
            logger.error("SAVOL_BERISH_CALLBACK_ERROR: Javob yuborish uchun chat_id topilmadi.")
    except Exception as e:
        logger.error(f"SAVOL_BERISH_CALLBACK_ERROR: 'Savol berish' javobini yuborishda xatolik: {e}")

# --- Asosiy xabar ishlovchisi ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"START: Yangi update qabul qilindi: {update}")

    message_to_process: TelegramMessage | None = None
    update_type_info = ""

    if update.business_message:
        message_to_process = update.business_message
        update_type_info = "BIZNES_XABARI (update.business_message)"
        logger.info(f"UPDATE_TYPE: {update_type_info} aniqlandi.")
    elif update.message:
        message_to_process = update.message
        update_type_info = "ODDIY_XABAR (update.message)"
        logger.info(f"UPDATE_TYPE: {update_type_info} aniqlandi.")
    else:
        logger.info("UPDATE_TYPE: Update tarkibida qayta ishlanadigan xabar topilmadi. To'xtatildi.")
        return

    if not message_to_process:
        logger.info("Qayta ishlanadigan xabar topilmadi (None). To'xtatildi")
        return

    logger.info(f"MESSAGE_OBJECT ({update_type_info}): Xabar obyekti: {message_to_process}")
    
    business_connection_id_value = None
    if hasattr(message_to_process, 'business_connection_id'):
        business_connection_id_value = message_to_process.business_connection_id
        logger.info(f"BUSINESS_ID_CHECK: Xabarda business_connection_id {'mavjud (' + str(business_connection_id_value) + ')' if business_connection_id_value is not None else ('mavjud, lekin None' if business_connection_id_value is None else 'YOQ')}")

    else:
        logger.info("BUSINESS_ID_CHECK: Xabarda business_connection_id atributi YO'Q.")

    # Bu yerda ReplyKeyboard tugmalarini tekshirish logikasi olib tashlandi,
    # chunki endi InlineKeyboard va CallbackQueryHandler ishlatiladi.

    # --- Birinchi marta yozgan foydalanuvchiga javob va InlineKeyboard yuborish ---
    if business_connection_id_value:
        actual_business_connection_id = business_connection_id_value
        
        if not message_to_process.chat or not message_to_process.from_user:
            logger.error("Xatolik: Xabarda 'chat' yoki 'from_user' ma'lumoti yetarli emas.")
            return

        user_chat_id = message_to_process.chat.id
        
        if not message_to_process.from_user.is_bot:
            user_first_name = message_to_process.from_user.first_name
            logger.info(f"USER_INFO: Biznes xabari foydalanuvchi '{user_first_name}' (ID: {user_chat_id}) dan keldi, business_connection_id: {actual_business_connection_id}")

            greeted_users_db = load_greeted_users()
            
            if actual_business_connection_id not in greeted_users_db:
                greeted_users_db[actual_business_connection_id] = []
            
            greeted_list_for_biz = greeted_users_db[actual_business_connection_id]

            if user_chat_id not in greeted_list_for_biz:
                logger.info(f"GREET_LOGIC: Foydalanuvchi (ID: {user_chat_id}) business_id '{actual_business_connection_id}' uchun hali salomlashilmagan. Salom va InlineKeyboard yuboriladi.")
                greeting_text = f"Assalomu alaykum {user_first_name}!"
                
                keyboard = [
                    [InlineKeyboardButton("👋 Tanishish", callback_data='tanishish_pressed')],
                    [InlineKeyboardButton("❓ Savol berish", callback_data='savol_berish_pressed')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await context.bot.send_message(
                        chat_id=user_chat_id,
                        text=greeting_text,
                        business_connection_id=actual_business_connection_id,
                        reply_markup=reply_markup # INLINE KEYBOARD QO'SHILDI
                    )
                    logger.info(f"SUCCESS_SEND_GREETING: '{user_first_name}' (ID: {user_chat_id}) ga '{actual_business_connection_id}' orqali salom xabari va InlineKeyboard muvaffaqiyatli yuborildi.")
                    
                    greeted_list_for_biz.append(user_chat_id)
                    greeted_users_db[actual_business_connection_id] = greeted_list_for_biz
                    save_greeted_users(greeted_users_db)
                except Exception as e:
                    logger.error(f"ERROR_SEND_GREETING: Salom xabari/InlineKeyboard yuborishda xatolik (Foydalanuvchi ID: {user_chat_id}, Biznes ID: {actual_business_connection_id}): {e}")
            else:
                logger.info(f"GREET_LOGIC: Foydalanuvchi (ID: {user_chat_id}) business_id '{actual_business_connection_id}' uchun allaqachon salomlashilgan (boshqa xabar yozdi).")
        else:
            logger.info(f"BIZNES_MSG_TYPE: Biznes xabari bot '{message_to_process.from_user.username}' (ID: {message_to_process.from_user.id}) dan keldi. E'tibor berilmaydi.")
    
    elif update_type_info == "ODDIY_XABAR (update.message)":
        logger.info("NOT_BUSINESS_MSG: Bu oddiy xabar (biznes ulanishisiz). Biznes logikasi qo'llanilmaydi.")
    
    logger.info(f"END_HANDLE_MESSAGE: Xabarni qayta ishlash umumiy tugadi (Xabar IDsi: {message_to_process.message_id if message_to_process else 'N/A'}).")

# --- main funksiyasi ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Matnli xabarlar uchun ishlovchi
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Inline tugma bosilishlari uchun CallbackQueryHandler'lar
    application.add_handler(CallbackQueryHandler(tanishish_button_callback, pattern='^tanishish_pressed$'))
    application.add_handler(CallbackQueryHandler(savol_berish_button_callback, pattern='^savol_berish_pressed$'))

    # Avvalgi /testkeyboard buyrug'i uchun ishlovchini olib tashladim,
    # chunki asosiy muammo aniqlandi va bu endi kerak emas.
    # Agar kerak bo'lsa, qayta qo'shishingiz mumkin.
    
    logger.info("Bot ishga tushirilmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()