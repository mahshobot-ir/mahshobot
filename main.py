import os
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai
import io

# کلیدها (از .env یا Secrets در Replit)
GEMINI_KEY = os.environ.get('GEMINI_KEY')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def start(update: Update, context):
    await update.message.reply_text("سلام! عکس پوست بفرست + مشکل بنویس. محصولات جدید پیشنهاد می‌دم!")

async def handle_photo(update: Update, context):
    await update.message.reply_text("در حال تحلیل... ⏳")
    
    try:
        # دانلود فایل
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # تبدیل به base64
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # mime_type dynamic (از bytes چک کن)
        mime_type = 'image/jpeg' if photo_bytes.startswith(b'\xff\xd8\xff') else 'image/png'
        
        response = model.generate_content([
            "عکس پوست رو ببین و مشکل رو تشخیص بده.\n"
            "پاسخ فارسی کوتاه:\n"
            "1. مشکل چیه؟ (جوش، خشکی، لک)\n"
            "2. روتین ۳ مرحله (صبح، شب، هفتگی)\n"
            "3. هشدار: این مشاوره پزشکی نیست، دکتر مشورت کن.\n"
            "4. یک محصول مرتبط از mahshobio.ir پیشنهاد بده + لینک: [خرید با ۱۵% تخفیف](لینک کامل)",
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_base64
                }
            }
        ])
        
        await update.message.reply_text(response.text)
        
    except Exception as e:
        # لاگ ارور برای دیباگ
        print(f"Error: {e}")  # در Replit console چک کن
        await update.message.reply_text(f"عکس مشکل داره (ارور: {str(e)[:50]}...). عکس واضح‌تر بفرست یا DM بزن.")

# ربات
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
