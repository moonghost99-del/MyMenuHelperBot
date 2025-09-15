import logging
import random
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- НАСТРОЙКА ЛОГГИРОВАНИЯ ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- НОВАЯ СТРУКТУРА МЕНЮ ПО КАТЕГОРИЯМ ---
menu = {
    "Пиццы": [
        {"name": "4 мяса", "ingredients": ["соус чесночный", "филе куриное запеченное", "салями", "ветчина", "балык", "помидоры", "шампиньоны", "сыр твердый", "моцарелла"]},
        {"name": "4 сыра", "ingredients": ["сметана", "сыр твердый", "моцарелла", "дор блю", "пармезан"]},
        {"name": "Гавайская", "ingredients": ["соус чесночный", "филе куриное запеченное", "балык", "ананас", "помидор", "перец болгарский", "сыр твердый", "моцарелла"]},
        {"name": "Цезарь", "ingredients": ["соус цезарь", "филе куриное запеченное", "помидоры", "пекинка", "сыр твердый", "моцарелла", "пармезан"]},
        {"name": "Мексиканская", "ingredients": ["соус томатный", "ветчина", "охотничьи колбаски", "перец острый", "помидоры", "перец болгарский", "сыр твердый", "моцарелла"]},
        {"name": "Верона", "ingredients": ["соус томатный", "филе куриное запеченное", "салями", "помидоры", "перец болгарский", "сыр твердый", "моцарелла"]},
        {"name": "Куриная", "ingredients": ["соус чесночный", "филе куриное запеченное", "шампиньоны", "помидоры", "перец болгарский", "сыр твердый", "моцарелла"]},
        {"name": "Пеперони", "ingredients": ["соус томатный", "салями", "помидоры", "перец болгарский", "сыр твердый", "моцарелла"]},
        {"name": "Грибная", "ingredients": ["соус чесночный", "помидоры", "шампиньоны", "вешенки", "сыр твердый", "моцарелла"]},
        {"name": "Маргарита", "ingredients": ["соус томатный", "помидоры", "моцарелла", "итальянские травы"]},
        {"name": "Карбонара", "ingredients": ["соус чесночный", "балык", "охотничьи колбаски", "шампиньоны", "помидоры", "сыр твердый", "моцарелла"]},
        {"name": "ЛАВ пицца", "ingredients": ["соус томатный", "филе куриное запеченное", "охотничьи колбаски", "ветчина", "шампиньоны", "помидоры", "огурцы соленые", "сыр твердый", "моцарелла"]},
        {"name": "По-деревенски", "ingredients": ["соус чесночный", "соус томатный", "охотничьи колбаски", "бекон", "картофель запеченный", "огурцы соленые", "лук красный", "помидоры", "шампиньоны", "окорок", "моцарелла"]},
        {"name": "Охота", "ingredients": ["соус томатный", "охотничьи колбаски", "салями", "перец болгарский", "шампиньоны", "сыр твердый", "моцарелла"]},
        {"name": "Сырный цыпленок", "ingredients": ["соус томатный", "филе куриное запеченное", "перец болгарский", "огурцы соленые", "лук красный", "сыр твердый", "моцарелла"]},
    ],
    "Пироги": [
        {"name": "Мясной", "ingredients": ["соус чесночный", "соус барбекю", "курино-свиной фарш", "окорок", "бекон", "лук", "огурец соленый", "шампиньоны", "помидор", "сыр твёрдый", "моцарелла", "кинза"]},
        {"name": "Сырный", "ingredients": ["сметана", "сыр сулугуни", "сыр адыгейский", "кинза", "сыр твёрдый", "творог"]},
        {"name": "Картофельно-грибной", "ingredients": ["сметана", "картофель", "шампиньоны", "сыр твёрдый", "петрушка"]},
        {"name": "Яблочно-банановый", "ingredients": ["яблоко", "банан", "ананас", "соус шоколадно-сметанный", "сыр твёрдый", "моцарелла"]},
    ],
    "Кальцоне": [
        {"name": "С лососем и креветкой", "ingredients": ["соус цезарь", "лосось", "креветка", "помидор", "пекинская капуста", "сыр твёрдый", "моцарелла"]},
        {"name": "ЛАВ", "ingredients": ["соус чесночный", "соус барбекю", "курино-свиной фарш", "огурец соленый", "моцарелла", "твёрдый сыр"]},
        {"name": "Мясной", "ingredients": ["соус томатный", "филе куриное", "ветчина", "шампиньоны", "помидоры", "сыр твёрдый", "моцарелла"]},
        {"name": "Сырный", "ingredients": ["сметана", "сыр твёрдый", "моцарелла", "помидоры"]},
        {"name": "Грибной", "ingredients": ["соус чесночный", "вешенки", "шампиньоны", "помидоры", "сыр твёрдый", "моцарелла"]},
        {"name": "Фруктово-шоколадный", "ingredients": ["соус шоколадный", "банан", "клубника", "моцарелла"]},
    ],
    "Шаурма": [
        {"name": "Шаурма с курицей", "ingredients": ["мясо", "огурец свежий", "помидор", "капуста пекинская", "морковь по корейски", "соус чесночный и томатный"]},
        {"name": "Шаурма со свининой", "ingredients": ["мясо", "огурец свежий", "помидор", "капуста пекинская", "морковь по корейски", "соус чесночный и томатный"]},
    ],
    "Закуски": [
        {"name": "Крылья Баффало (острые)", "description": "230г - 250руб"},
        {"name": "Крылья в панировке", "description": "230г - 250руб"},
        {"name": "Стрипсы", "description": "200г - 250руб"},
        {"name": "Пельмени во фритюре", "description": "190г - 220руб"},
        {"name": "Картофель Фри", "description": "150г - 170руб"},
        {"name": "Картофельные шарики", "description": "150г - 170руб"},
        {"name": "Картофель по деревенски", "description": "170г - 170руб"},
        {"name": "Наггетсы", "description": "10 штук - 230руб"},
        {"name": "Луковые кольца", "description": "15 штук - 200руб"},
        {"name": "Креветка в панировке", "description": "6 штук + соус тартар - 320руб"},
    ],
    "Добавки": [
        {"name": "Сыр", "description": "80руб"},
        {"name": "Филе куриное", "description": "60руб"},
        {"name": "Охотничьи колбаски", "description": "60руб"},
        {"name": "Ветчина", "description": "60руб"},
        {"name": "Салями", "description": "60руб"},
        {"name": "Балык", "description": "60руб"},
        {"name": "Бекон", "description": "60руб"},
        {"name": "Кукуруза", "description": "30руб"},
        {"name": "Перец болгарский", "description": "30руб"},
        {"name": "Шампиньоны", "description": "30руб"},
        {"name": "Маслины", "description": "30руб"},
        {"name": "Помидоры", "description": "30руб"},
        {"name": "Ананас", "description": "40руб"},
        {"name": "Огурец соленый", "description": "30руб"},
        {"name": "Халапеньо", "description": "30руб"},
        {"name": "Лук", "description": "20руб"},
        {"name": "Зелень", "description": "20руб"},
    ],
    "Соусы": [
        {"name": "Кетчуп", "description": "40руб"},
        {"name": "Соус Чесночный", "description": "40руб"},
        {"name": "Соус Сырный", "description": "40руб"},
        {"name": "Соус Кисло-сладкий", "description": "40руб"},
        {"name": "Соус Терияки", "description": "40руб"},
        {"name": "Соус Барбекю", "description": "40руб"},
        {"name": "Соус Грибной", "description": "40руб"},
        {"name": "Соус Тартар", "description": "40руб"},
    ]
}
# Категории, подходящие для тестов на знание состава
TRAINABLE_CATEGORIES = ["Пиццы", "Пироги", "Кальцоне", "Шаурма"]
ALL_INGREDIENTS = sorted(list(set(ing for cat in TRAINABLE_CATEGORIES for item in menu[cat] for ing in item['ingredients'])))

# --- Веб-сервер для "пробуждения" ---
app = Flask(__name__)
@app.route('/')
def index():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- УПРАВЛЕНИЕ МЕНЮ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🤔 Угадать блюдо (тест)", callback_data='mode_guess')],
        [InlineKeyboardButton("✅ Собрать блюдо по названию", callback_data='mode_build')],
        [InlineKeyboardButton("📖 Справочник по меню", callback_data='mode_info')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text('👋 Привет! Выбери режим:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('👋 Привет! Выбери режим:', reply_markup=reply_markup)

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    mode = query.data.split('_')[1] # guess, build, info

    categories = menu.keys()
    if mode in ['guess', 'build']:
        categories = TRAINABLE_CATEGORIES
    
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"start_{mode}_{cat}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите категорию для тренировки:", reply_markup=reply_markup)

# --- РЕЖИМЫ ТРЕНИРОВКИ ---
async def start_training_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, mode, category = query.data.split('_')
    
    if mode == 'guess':
        # Логика для "Угадать блюдо"
        items = menu[category]
        correct_item = random.choice(items)
        context.user_data['correct_item_name'] = correct_item['name']
        context.user_data['category'] = category

        other_items = [item for item in items if item['name'] != correct_item['name']]
        wrong_options = random.sample(other_items, min(2, len(other_items)))
        options = [correct_item] + wrong_options
        random.shuffle(options)

        keyboard = [[InlineKeyboardButton(item['name'], callback_data=f"check_guess_{item['name']}")] for item in options]
        reply_markup = InlineKeyboardMarkup(keyboard)
        ingredients_text = ", ".join(correct_item['ingredients'])
        await query.edit_message_text(f"Из категории '{category}', какому блюду принадлежит состав?\n\n*Состав:* {ingredients_text}", reply_markup=reply_markup)

    elif mode == 'info':
        # Логика для "Справочника"
        items = menu[category]
        response_text = f"📖 *{category.upper()}*\n\n"
        for item in items:
            description = ", ".join(item['ingredients']) if 'ingredients' in item else item.get('description', '')
            response_text += f"*{item['name']}*\n_{description}_\n\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Выбрать другую категорию", callback_data=f'mode_info')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')

async def check_guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    selected_name = query.data.split('check_guess_')[-1]
    correct_name = context.user_data.get('correct_item_name')
    category = context.user_data.get('category')
    
    if selected_name == correct_name:
        text = f"✅ Правильно! Это '{correct_name}'."
    else:
        text = f"❌ Неверно. Это был '{correct_name}'."

    keyboard = [
        [InlineKeyboardButton("➡️ Следующий вопрос", callback_data=f'start_guess_{category}')],
        [InlineKeyboardButton("⬅️ Выбрать категорию", callback_data='mode_guess')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

# (Остальные режимы, например "Собрать блюдо", можно добавить по аналогии для полноты)
# ...

# --- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ---
def main() -> None:
    TOKEN = "8208724950:AAG2JJ3in3_f79efQRodGvwGFvCnOLJks5M"
    if TOKEN == "8208724950:AAG2JJ3in3_f79efQRodGvwGFvCnOLJks5M":
        print("8208724950:AAG2JJ3in3_f79efQRodGvwGFvCnOLJks5M")
        return

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(select_category, pattern='^mode_'))
    application.add_handler(CallbackQueryHandler(start_training_mode, pattern='^start_'))
    application.add_handler(CallbackQueryHandler(check_guess_answer, pattern='^check_guess_'))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()