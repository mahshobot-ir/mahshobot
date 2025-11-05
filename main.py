import os
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import google.generativeai as genai

# کلیدها (از Secrets در Replit)
GEMINI_KEY = os.environ.get('GEMINI_KEY')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# مراحل مکالمه
PHOTO, DESCRIPTION = range(2)

# محصولات واقعی (لینک‌های واقعی سایتت)
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
        "📸 لطفاً برای شروع عکس صورت یا پوستت را بفرست تا بررسی کنم."
    )
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عکس دریافت شد! ✅\n\n"
                                    "حالا لطفاً مشکل پوستی‌ات رو توضیح بده (مثلاً: جوش، خشکی، لک، چروک...)\n"
                                    "هر چی بیشتر توضیح بدی، جواب دقیق‌تر می‌شه! 🤔")
    
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
        
        problem = "عمومی"
        for key in PRODUCTS.keys():
            if key in user_desc:
                problem = key
                break
        
        product = PRODUCTS.get(problem, PRODUCTS["عمومی"])
        product_text = f"[خرید {product['name']}]({
