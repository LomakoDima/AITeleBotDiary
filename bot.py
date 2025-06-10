import telebot
from telebot import types
from logic import init_db, add_task, get_tasks, clear_tasks
from ai_logic import process_natural_language, setup_ai
from datetime import datetime
from dotenv import load_dotenv
import re
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация
init_db()
setup_ai(OPENAI_API_KEY)

user_states = {}


def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ Добавить задачу", "📋 Мои задачи")
    keyboard.row("🤖 Умное добавление", "🗑️ Очистить все")
    keyboard.row("ℹ️ Помощь")
    return keyboard


def cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("❌ Отмена")
    return keyboard


@bot.message_handler(commands=['start'])
def start_command(message):
    user_name = message.from_user.first_name
    welcome_text = f"Привет, {user_name}! 👋\n\n"
    welcome_text += "Я умный бот-ежедневник с поддержкой ИИ! 🤖\n"
    welcome_text += "Я могу понимать естественный язык и автоматически создавать задачи.\n\n"
    welcome_text += "Попробуйте написать что-то вроде:\n"
    welcome_text += "• 'Напомни встретиться с Иваном завтра в 14:00'\n"
    welcome_text += "• 'Позвони врачу на следующей неделе'\n"
    welcome_text += "• 'Купить продукты вечером'\n\n"
    welcome_text += "Выберите действие из меню:"

    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = "🤖 Как пользоваться умным ботом:\n\n"
    help_text += "➕ Добавить задачу - классическое добавление с указанием времени\n"
    help_text += "🤖 Умное добавление - опишите задачу естественным языком\n"
    help_text += "📋 Мои задачи - посмотреть все ваши задачи\n"
    help_text += "🗑️ Очистить все - удалить все задачи\n"
    help_text += "ℹ️ Помощь - показать это сообщение\n\n"
    help_text += "🧠 Примеры умного добавления:\n"
    help_text += "• 'Встреча с клиентом завтра в 15:30'\n"
    help_text += "• 'Купить молоко по дороге домой'\n"
    help_text += "• 'Позвонить маме в выходные'\n"
    help_text += "• 'Подготовить презентацию к понедельнику'\n"
    help_text += "• 'Записаться к стоматологу через неделю'\n\n"
    help_text += "ИИ автоматически определит описание задачи и время!"

    bot.send_message(message.chat.id, help_text, reply_markup=main_keyboard())


@bot.message_handler(
    func=lambda message: message.text in ["➕ Добавить задачу", "📋 Мои задачи", "🤖 Умное добавление", "🗑️ Очистить все",
                                          "ℹ️ Помощь"])
def handle_menu_buttons(message):
    user_id = message.from_user.id

    if message.text == "➕ Добавить задачу":
        user_states[user_id] = "waiting_task_description"
        bot.send_message(message.chat.id,
                         "📝 Введите описание задачи:",
                         reply_markup=cancel_keyboard())

    elif message.text == "🤖 Умное добавление":
        user_states[user_id] = "waiting_ai_input"
        bot.send_message(message.chat.id,
                         "🧠 Опишите задачу естественным языком!\n\n"
                         "Примеры:\n"
                         "• 'Встреча с Петром завтра в 10 утра'\n"
                         "• 'Купить продукты вечером'\n"
                         "• 'Позвонить в банк на следующей неделе'\n"
                         "• 'Подготовить отчет к пятнице'\n\n"
                         "Напишите свою задачу:",
                         reply_markup=cancel_keyboard())

    elif message.text == "📋 Мои задачи":
        show_tasks(message)

    elif message.text == "🗑️ Очистить все":
        confirm_clear(message)

    elif message.text == "ℹ️ Помощь":
        help_command(message)


def show_tasks(message):
    user_id = message.from_user.id
    tasks = get_tasks(user_id)

    if not tasks:
        bot.send_message(message.chat.id,
                         "📭 У вас пока нет задач.\n"
                         "Попробуйте умное добавление! 🤖",
                         reply_markup=main_keyboard())
        return

    tasks_text = "📋 Ваши задачи:\n\n"
    for i, (description, time) in enumerate(tasks, 1):
        tasks_text += f"{i}. 🕐 {time} - {description}\n"

    bot.send_message(message.chat.id, tasks_text, reply_markup=main_keyboard())


def confirm_clear(message):
    user_id = message.from_user.id
    tasks = get_tasks(user_id)

    if not tasks:
        bot.send_message(message.chat.id,
                         "📭 У вас нет задач для удаления.",
                         reply_markup=main_keyboard())
        return

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("✅ Да, удалить все", callback_data="confirm_clear"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_clear")
    )

    bot.send_message(message.chat.id,
                     f"🗑️ Вы уверены, что хотите удалить все {len(tasks)} задач(и)?",
                     reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id

    if call.data == "confirm_clear":
        clear_tasks(user_id)
        bot.edit_message_text(
            "✅ Все задачи удалены!",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(call.message.chat.id,
                         "Можете добавить новые задачи с помощью ИИ! 🤖",
                         reply_markup=main_keyboard())

    elif call.data == "cancel_clear":
        bot.edit_message_text(
            "❌ Удаление отменено.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.send_message(call.message.chat.id,
                         "Ваши задачи сохранены.",
                         reply_markup=main_keyboard())


@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def handle_cancel(message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]

    bot.send_message(message.chat.id,
                     "❌ Операция отменена.",
                     reply_markup=main_keyboard())


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if user_id not in user_states:
        # Если пользователь просто пишет текст без выбора режима,
        # попробуем обработать его как умный ввод
        process_ai_input(message)
        return

    state = user_states[user_id]

    if state == "waiting_ai_input":
        process_ai_input(message)

    elif state == "waiting_task_description":
        user_states[user_id] = {
            'state': 'waiting_task_time',
            'description': message.text
        }
        bot.send_message(message.chat.id,
                         "🕐 Введите время для задачи (например: 14:30, утром, вечером):",
                         reply_markup=cancel_keyboard())

    elif isinstance(state, dict) and state['state'] == 'waiting_task_time':
        time_text = message.text.strip()

        if validate_time(time_text):
            description = state['description']
            add_task(user_id, description, time_text)

            success_text = f"✅ Задача добавлена!\n\n"
            success_text += f"📝 Описание: {description}\n"
            success_text += f"🕐 Время: {time_text}"

            bot.send_message(message.chat.id, success_text, reply_markup=main_keyboard())
            del user_states[user_id]
        else:
            bot.send_message(message.chat.id,
                             "❌ Неверный формат времени. Попробуйте еще раз:\n"
                             "Примеры: 14:30, 9:00, утром, днем, вечером",
                             reply_markup=cancel_keyboard())


def process_ai_input(message):
    user_id = message.from_user.id

    try:
        # Показываем индикатор печати
        bot.send_chat_action(message.chat.id, 'typing')

        # Обрабатываем текст с помощью ИИ
        ai_result = process_natural_language(message.text)

        if ai_result['success']:
            description = ai_result['description']
            time = ai_result['time']

            # Добавляем задачу в базу данных
            if add_task(user_id, description, time):
                success_text = f"🤖 ИИ успешно обработал вашу задачу!\n\n"
                success_text += f"📝 Описание: {description}\n"
                success_text += f"🕐 Время: {time}\n\n"

                if ai_result.get('explanation'):
                    success_text += f"💡 Пояснение: {ai_result['explanation']}"

                bot.send_message(message.chat.id, success_text, reply_markup=main_keyboard())
            else:
                bot.send_message(message.chat.id,
                                 "❌ Ошибка при сохранении задачи. Попробуйте еще раз.",
                                 reply_markup=main_keyboard())
        else:
            error_text = f"❌ Не удалось обработать задачу: {ai_result.get('error', 'Неизвестная ошибка')}\n\n"
            error_text += "Попробуйте переформулировать или воспользуйтесь обычным добавлением задачи."

            bot.send_message(message.chat.id, error_text, reply_markup=main_keyboard())

    except Exception as e:
        print(f"Ошибка обработки ИИ: {e}")
        bot.send_message(message.chat.id,
                         "❌ Произошла ошибка при обработке. Попробуйте еще раз или воспользуйтесь обычным режимом.",
                         reply_markup=main_keyboard())

    # Очищаем состояние пользователя
    if user_id in user_states:
        del user_states[user_id]


def validate_time(time_str):
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if re.match(time_pattern, time_str):
        return True

    time_words = ['утром', 'утро', 'днем', 'день', 'вечером', 'вечер', 'ночью', 'ночь']
    if time_str.lower() in time_words:
        return True

    if len(time_str) > 0 and len(time_str) < 50:
        return True

    return False


@bot.message_handler(content_types=['photo', 'video', 'audio', 'document', 'voice', 'sticker'])
def handle_media(message):
    bot.send_message(message.chat.id,
                     "Я работаю только с текстовыми сообщениями. 📝\n"
                     "Попробуйте описать задачу текстом - я пойму! 🤖\n"
                     "Выберите действие из меню:",
                     reply_markup=main_keyboard())


if __name__ == "__main__":
    print("🤖 Умный бот с ИИ запущен...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")