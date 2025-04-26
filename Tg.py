import json
import logging
import os
from jinja2 import Template
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# Состояния
TITLE, IMAGE, LINK = range(3)

# Логгинг
logging.basicConfig(level=logging.INFO)

# Загрузка товаров
def load_products():
    try:
        with open("products.json", "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Сохранение товаров
def save_products(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# Генерация index.html из template.html
def generate_index_html():
    try:
        with open('products.json', 'r', encoding='utf-8-sig') as f:
            products = json.load(f)
    except FileNotFoundError:
        products = []

    # Загружаем внешний шаблон
    with open('template.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    template = Template(template_content)

    html_content = template.render(products=products)

    os.makedirs("public", exist_ok=True)
    with open(os.path.join("public", "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ index.html успешно обновлён.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📦 Введи название товара:")
    return TITLE

# Получение названия
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["title"] = update.message.text
    await update.message.reply_text("🖼 Отправь ссылку на изображение (или несколько через запятую):")
    return IMAGE

# Получение изображений
async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    image_links = update.message.text.strip().split(",")
    context.user_data["images"] = [img.strip() for img in image_links]
    await update.message.reply_text("🔗 Отправь партнёрскую ссылку на товар:")
    return LINK

# Получение ссылки
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["link"] = update.message.text

    # Создание нового товара
    new_product = {
        "title": context.user_data["title"],
        "images": context.user_data["images"],
        "link": context.user_data["link"],
    }

    products = load_products()
    products.insert(0, new_product)
    save_products(products)
    generate_index_html()

    await update.message.reply_text("✅ Товар добавлен!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Добавление отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Запуск бота
def main():
    app = ApplicationBuilder().token("7772105188:AAGsjeL4YIBWbTDcMtmzYimwawV8ALbhn7g").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_image)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("🤖 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
