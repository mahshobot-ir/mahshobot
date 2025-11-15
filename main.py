import os
import base64
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import google.generativeai as genai

GEMINI_KEY = os.getenv('GEMINI_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not GEMINI_KEY or not BOT_TOKEN:
    raise ValueError("❌ لطفاً متغیرهای محیطی GEMINI_KEY و BOT_TOKEN را تنظیم کن.")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

PHOTO, DESCRIPTION = range(2)

PRODUCTS = {
    "جوش": {"name": "سرم ضدجوش", "link": "https://mahshobio.ir/product-category/skincare/%d8%b6%d8%af-%d8%ac%d9%88%d8%b4/"},
    "خشکی": {"name": "سرم هیالورونیک", "link": "https://mahshobio.ir/product-category/skincare/moisturizer/"},
    "لک": {"name": "سرم ضدلک", "link": "https://mahshobio.ir/product-category/skincare/%d8%b6%d8%af-%d9%84%da%a9/"},
    "چروک": {"name": "کرم ضدچروک قوی", "link": "https://mahshobio.ir/product-category/skincare/%d8%b6%d8%af-%da%86%d8%b1%d9%88%da%a9/"},
    "منافذ": {"name": "سرم نیاسینامید", "link": "https://mahshobio.ir/product-category/skincare/%d8%b1%d9%81%d8%b9-%d9%85%d9%86%d8%a7%d9%81%d8%b0-%d8%a8%d8%a7%d8%b2/"},
    "لایه": {"name": "سرم لایه بردار", "link": "https://mahshobio.ir/product-category/skincare/%d9%84%d8%a7%db%8c%d9%87-%d8%a8%d8%b1%d8%af%d8%a7%d8%b1/"},
    "ترمیم": {"name": "سرم بوستر", "link": "https://mahshobio.ir/product-category/skincare/%d8%aa%d8%b1%d9%85%db%8c%d9%85-%da%a9%d9%86%d9%86%d8%af%d9%87/"},
    "چشم": {"name": "سرم دور چشم", "link": "https://mahshobio.ir/product-category/skincare/%d8%af%d9%88%d8%b1-%da%86%d8%b4%d9%85/"},
    "تونر": {"name": "تونر", "link": "https://https://mahshobio.ir/product-category/skincare/%d8%aa%d9%88%d9%86%d8%b1/"},
    "آفتاب": {"name": "ضد آفتاب", "link": "https://mahshobio.ir/product-category/skincare/%d8%b6%d8%af-%d8%a2%d9%81%d8%aa%d8%a7%d8%a8/"},
    "شوینده": {"name": "شوینده", "link": "https://mahshobio.ir/product-category/skincare/%d8%b4%d9%88%db%8c%d9%86%d8%af%d9%87-%d8%b5%d9%88%d8%b1%d8%aa/"},
    "مرطوب": {"name": "مرطوب کننده", "link": "https://mahshobio.ir/product-category/skincare/%da%a9%d8%b1%d9%85-%d9%85%d8%b1%d8%b7%d9%88%d8%a8-%da%a9%d9%86%d9%86%d8%af%d9%87/"},
    "عمومی": {"name": "کیت مراقبت کامل پوست", "link": "https://mahshobio.ir/product/some-by-mi-retinol-kit/"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 🌸\n"
        "به ربات ماه‌شو خوش اومدی!\n"
        "مجموعه ما با بهره‌گیری از هوش مصنوعی وضعیت پوست شما را آنالیز کرده و بهترین محصولات را پیشنهاد می‌دهد.\n\n"
        "📸 لطفاً عکس صورت یا پوستت را بفرست."
    )
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    context.user_data['photo_bytes'] = photo_bytes
    context.user_data['mime_type'] = 'image/jpeg' if photo_bytes.startswith(b'\xff\xd8\xff') else 'image/png'

    await update.message.reply_text("عکس دریافت شد ✅\nحالا لطفاً مشکل پوستی‌ات را توضیح بده (مثلاً: جوش، خشکی، لک، چروک...)")
    return DESCRIPTION

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_desc = update.message.text.strip()
    photo_bytes = context.user_data.get('photo_bytes')
    mime_type = context.user_data.get('mime_type')

    if not photo_bytes:
        await update.message.reply_text("❗عکس گم شده، لطفاً دوباره /start بزن.")
        return ConversationHandler.END

    await update.message.reply_text("در حال تحلیل عکس و توضیحات شما... ⏳")

    try:
        desc_norm = re.sub(r'[يی]', 'ی', re.sub(r'[كک]', 'ک', user_desc))
        problem = next((k for k in PRODUCTS if k in desc_norm), "عمومی")
        product = PRODUCTS[problem]
        product_text = f"[{product['name']}]({product['link']}) 🌟"

        image_base64 = base64.b64encode(photo_bytes).decode('utf-8')

        prompt = (
            f"عکس پوست + توضیح کاربر: \"{user_desc}\"\n"
            "تحلیل دقیق کن و پاسخ فارسی کوتاه و حرفه‌ای بده:\n\n"
            "1. مشکل چیه؟\n"
            "2. روتین سه مرحله‌ای (صبح، شب، هفتگی)\n"
            "3. هشدار پزشکی\n"
            f"4. محصول پیشنهادی: {product_text}\n\n"
            "هر بخش جدا و ایموجی‌دار بنویس.\n"
            "در آخر بنویس: ممنون از استفاده از ربات ماه‌شو 🌸"
        )

        response = model.generate_content([
            prompt,
            {"inline_data": {"mime_type": mime_type, "data": image_base64}}
        ])

        text = getattr(response, "text", None) or response.candidates[0].content.parts[0].text
        await update.message.reply_text(text)

    except Exception as e:
        print("Error:", e)
        await update.message.reply_text("متأسفانه مشکلی پیش اومد 😔\nلطفاً دوباره /start بزن.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("با موفقیت لغو شد 🌸\nهر وقت خواستی دوباره /start بزن.")
    return ConversationHandler.END

app = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_received)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

app.add_handler(conv_handler)
app.run_polling()
