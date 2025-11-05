import os
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import google.generativeai as genai

# کلیدها
GEMINI_KEY = os.environ.get('GEMINI_KEY')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# مراحل مکالمه
PHOTO, DESCRIPTION = range(2)

# محصولات واقعی
PRODUCTS = {
    "جوش": {"name": "سرم ضدجوش COSRX", "link": "https://mahshobio.ir/cosrx-acne"},
    "خشکی": {"name": "سرم هیالورونیک Ordinary", "link": "https://mahshobio.ir/ordinary-hyaluronic"},
    "لک": {"name": "سرم ضدلک Axis-Y", "link": "https://mahshobio.ir/axis-y-spot"},
    "چروک": {"name": "کرم ضدچروک قوی", "link": "https://mahshobio.ir/anti-wrinkle-cream"},
    "حساسیت": {"name": "کرم تسکین‌دهنده Clinique", "link": "https://mahshobio.ir/clinique-calming"},
    "عمومی": {"name": "کیت مراقبت کامل پوست", "link": "https://mahshobio.ir/skincare-kit"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 🌸\n"
        "به ربات ماه‌شو خوش اومدی!\n"
        "مجموعه ما با بهره‌گیری از هوش مصنوعی بصورت تخصصی وضعیت سلامت پوست و مو شما را آنالیز می‌کنه و مناسب‌ترین محصولات را پیشنهاد میده.\n\n"
        "📸 لطفاً برای شروع **عکس صورت یا پوستت** را بفرست تا بررسی کنم."
    )
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عکس دریافت شد! ✅\n\n"
                                    "حالا لطفاً **مشکل پوستی‌ات** رو توضیح بده (مثلاً: جوش، خشکی، لک، چروک...)\n"
                                    "هر چی بیشتر توضیح بدی، جواب دقیق‌تر می‌شه! 🤔")
    
    # ذخیره عکس
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    context.user_data['photo_bytes'] = photo_bytes
    context.user_data['mime_type'] = 'image/jpeg' if photo_bytes.startswith(b'\xff\xd8\xff') else 'image/png'
    
    return DESCRIPTION

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_desc = update.message.text.strip()
    photo_bytes = context.user_data.get('photo_bytes')
    mime_type = context.user_data.get('mime_type')
    
    if not photo_bytes:
        await update.message.reply_text("عکس گم شده! لطفاً دوباره /start بزن.")
        return ConversationHandler.END
    
    await update.message.reply_text("در حال تحلیل عمیق عکس + توضیحات شما... ⏳")
    
    try:
        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # تشخیص مشکل از توضیح کاربر
        problem = "عمومی"
        for key in PRODUCTS.keys():
            if key in user_desc:
                problem = key
                break
        
        product = PRODUCTS.get(problem, PRODUCTS["عمومی"])
        product_text = f"[خرید {product['name']}]({product['link']}) 🌟" if product.get("link") else product["name"]
        
        prompt = (
            f"عکس پوست + توضیح کاربر: \"{user_desc}\"\n"
            "تحلیل دقیق کن و پاسخ فارسی کوتاه و حرفه‌ای بده:\n\n"
            "1. مشکل چیه؟\n"
            "2. روتین ۳ مرحله (صبح، شب، هفتگی)\n"
            "3. هشدار پزشکی\n"
            "4. محصول پیشنهادی: فقط این رو بنویس: {product_text}\n\n"
            "هر بخش یک پاراگراف با یک خط فاصله. ایموجی جذاب اضافه کن.\n"
            "در آخر: ممنون از استفاده از ربات ماه‌شو! 🌸"
        )
        
        response = model.generate_content([
            prompt,
            {"inline_data": {"mime_type": mime_type, "data": image_base64}}
        ])
        
        await update.message.reply_text(response.text, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("متأسفانه مشکلی پیش اومد 😔\n"
                                        "لطفاً دوباره /start بزن.\n"
                                        "ممنون از استفاده از ربات ماه‌شو! 🌸")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ممنون از استفاده از ربات ماه‌شو! 🌸\nهر وقت خواستی دوباره /start بزن.")
    return ConversationHandler.END

# ربات
app = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

app.add_handler(conv_handler)
app.run_polling()

