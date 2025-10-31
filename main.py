import os
import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# هوش مصنوعی
genai.configure(api_key=os.getenv("GEMINI_KEY_HERE"))
model = genai.GenerativeModel('gemini-1.5-flash')

# محصولات جدید از RSS
def get_latest_products():
    try:
        feed = feedparser.parse("https://mahshobio.ir/feed/?post_type=product")
        products = []
        for entry in feed.entries[:5]:
            title = entry.title
            link = entry.link
            category = "عمومی"
            if any(k in title.lower() for k in ["جوش", "acne"]): category = "جوش"
            elif any(k in title.lower() for k in ["خشکی", "dry"]): category = "خشکی"
            elif any(k in title.lower() for k in ["لک", "spot"]): category = "لک"
            products.append({"title": title, "link": link, "category": category})
        return products
    except:
        return [
            {"title": "سرم ضدجوش COSRX", "link": "https://mahshobio.ir/cosrx-acne", "category": "جوش"},
            {"title": "هیالورونیک Ordinary", "link": "https://mahshobio.ir/ordinary-hyaluronic", "category": "خشکی"}
        ]

async def start(update: Update, context):
    await update.message.reply_text(
        "سلام! عکس پوستت رو بفرست + مشکلت رو بنویس\n"
        "محصولات جدید ماه‌شو رو اتوماتیک پیشنهاد می‌دم!"
    )

async def handle_photo(update: Update, context):
    await update.message.reply_text("در حال تحلیل... ⏳")
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    latest_products = get_latest_products()
    products_text = "\n".join([f"- {p['title']}: {p['category']} ({p['link']})" for p in latest_products])

    try:
        response = model.generate_content([
            f"عکس پوست رو ببین و مشکل رو تشخیص بده.\n"
            f"محصولات جدید: {products_text}\n"
            "پاسخ کوتاه فارسی:\n"
            "1. مشکل چیه؟\n"
            "2. روتین ۳ مرحله\n"
            "3. هشدار پزشکی\n"
            "4. یک محصول مرتبط پیشنهاد بده + لینک کامل\n"
            "لینک: [خرید با ۱۵% تخفیف](لینک)",
            {"inline_data": {"mime_type": "image/jpeg", "data": photo_bytes}}
        ])
        await update.message.reply_text(response.text)
    except:
        await update.message.reply_text("عکس واضح نیست!")

app = Application.builder().token(os.getenv("BOT_TOKEN_HERE")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
