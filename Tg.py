import json
import logging
import os
from datetime import datetime
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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Состояния
CATEGORY, TITLE, IMAGE, LINK = range(4)  # Удалено DESIGNER_NOTE

# Категории товаров
categories = ["bags", "skirts", "pants", "accessories", "shoes", "dresses", "tops", "cardigans"]

# Пути к файлам
BASE_DIR = "C:\\Users\\user\\Desktop\\Sitee\\SiteAmazon"
PRODUCTS_JSON_PATH = os.path.join(BASE_DIR, "products.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "template.html")
SITEMAP_TEMPLATE_PATH = os.path.join(BASE_DIR, "sitemap.xml")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
INDEX_PATH = os.path.join(PUBLIC_DIR, "index.html")
SITEMAP_PATH = os.path.join(PUBLIC_DIR, "sitemap.xml")

# Загрузка товаров
def load_products():
    try:
        with open(PRODUCTS_JSON_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Файл products.json не найден. Создаю пустую структуру.")
        return {category: [] for category in categories}

# Сохранение товаров
def save_products(products):
    with open(PRODUCTS_JSON_PATH, "w", encoding="utf-8-sig") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

# Генерация index.html из template.html
def generate_index_html():
    products = load_products()
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template_content = f.read()
    template = Template(template_content)
    html_content = template.render(products=products)
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info("✅ index.html успешно обновлён.")

# Генерация sitemap.xml
def generate_sitemap_xml():
    products = load_products()
    lastmod = datetime.now().strftime('%Y-%m-%d')

    with open(SITEMAP_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        sitemap_template_content = f.read()
    sitemap_template = Template(sitemap_template_content)

    sitemap_content = sitemap_template.render(products=products, lastmod=lastmod)

    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    logger.info("✅ sitemap.xml успешно обновлён.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📦 Выберите категорию товара:\n" + "\n".join(categories))
    return CATEGORY

# Получение категории
async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    category = update.message.text.strip().lower()
    if category in categories:
        context.user_data["category"] = category
        await update.message.reply_text("📦 Введи название товара:")
        return TITLE
    else:
        await update.message.reply_text("❌ Неверная категория. Пожалуйста, выберите одну из следующих категорий:\n" + "\n".join(categories))
        return CATEGORY

# Получение названия
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуй снова:")
        return TITLE
    context.user_data["title"] = title
    await update.message.reply_text("🖼 Отправь ссылку на изображение (или несколько через запятую):")
    return IMAGE

# Получение изображений
async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    image_links = update.message.text.strip().split(",")
    image_links = [img.strip() for img in image_links if img.strip()]
    if not image_links:
        await update.message.reply_text("❌ Необходимо указать хотя бы одну ссылку на изображение. Попробуй снова:")
        return IMAGE
    context.user_data["images"] = image_links
    await update.message.reply_text("🔗 Отправь партнёрскую ссылку на товар:")
    return LINK

# Получение ссылки
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    link = update.message.text.strip()
    if not link.startswith("http"):
        await update.message.reply_text("❌ Ссылка должна начинаться с http или https. Попробуй снова:")
        return LINK
    context.user_data["link"] = link

    # Создание нового товара (без designer_note)
    new_product = {
        "title": context.user_data["title"],
        "images": context.user_data["images"],
        "link": context.user_data["link"],
        "category": context.user_data["category"]
    }

    products = load_products()
    category = context.user_data["category"]
    products[category].insert(0, new_product)
    save_products(products)
    generate_index_html()
    generate_sitemap_xml()

    await update.message.reply_text("✅ Товар добавлен!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Добавление отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Произошла ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Произошла ошибка. Попробуй снова позже.")

# Запуск бота
def main():
    app = ApplicationBuilder().token("7772105188:AAGsjeL4YIBWbTDcMtmzYimwawV8ALbhn7g").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_image)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    logger.info("🤖 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
