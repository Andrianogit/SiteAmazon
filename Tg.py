import json
import logging
import os
from jinja2 import Template
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# Состояния
CATEGORY, TITLE, IMAGE, LINK = range(4)

# Категории товаров
categories = [
    "Cookware", "Appliances", "Storage", "Cleaning",
    "Tableware", "Utensils", "Decor", "Lighting"
]

# Логгирование
logging.basicConfig(level=logging.INFO)

# Загрузка товаров
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        return {cat: [] for cat in categories}

# Сохранение товаров
def save_products(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# Генерация index.html
def generate_index_html():
    products = load_products()
    with open('template.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())
    html_content = template.render(products=products)
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index.html успешно обновлён.")

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[cat] for cat in categories]
    await update.message.reply_text(
        "📦 Choose product category:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY

# Категория
async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text
    if category not in categories:
        await update.message.reply_text("❌ Invalid category. Choose from menu.")
        return CATEGORY
    context.user_data["category"] = category
    await update.message.reply_text("📦 Enter product title:", reply_markup=ReplyKeyboardRemove())
    return TITLE

# Название
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text("🖼 Send image link(s), comma separated:")
    return IMAGE

# Картинки
async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["images"] = [img.strip() for img in update.message.text.split(",")]
    await update.message.reply_text("🔗 Send Amazon affiliate link:")
    return LINK

# Ссылка
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["link"] = update.message.text.strip()

    product = {
        "title": context.user_data["title"],
        "images": context.user_data["images"],
        "link": context.user_data["link"]
    }

    products = load_products()
    cat = context.user_data["category"]
    products.setdefault(cat, []).insert(0, product)
    save_products(products)
    generate_index_html()

    await update.message.reply_text("✅ Product added!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Main
def main():
    app = ApplicationBuilder().token("7772105188:AAGsjeL4YIBWbTDcMtmzYimwawV8ALbhn7g").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_image)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("🤖 Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()

