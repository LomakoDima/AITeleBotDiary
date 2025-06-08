import telebot
from telebot import types
from logic import init_db, add_task, get_tasks, clear_tasks
from datetime import datetime
from dotenv import load_dotenv
import re
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

init_db()

user_states = {}

def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("➕ Добавить задачу", "📋 Мои задачи")
    keyboard.row("🗑️ Очистить все", "ℹ️ Помощь")
    return keyboard

def cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("❌ Отмена")
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    user_name = message.from_user.first_name
    welcome_text = f"Привет, {user_name}! 👋\n\n"
    welcome_text += "Я бот-ежедневник, который поможет тебе организовать свои задачи.\n"
    welcome_text += "Выбери действие из меню ниже:"

    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = "🤖 Как пользоваться ботом:\n\n"
    help_text += "➕ Добавить задачу - добавить новую задачу с указанием времени\n"
    help_text += "📋 Мои задачи - посмотреть все ваши задачи\n"
    help_text += "🗑️ Очистить все - удалить все задачи\n"
    help_text += "ℹ️ Помощь - показать это сообщение\n\n"
    help_text += "Формат времени: ЧЧ:ММ (например, 14:30)\n"
    help_text += "или просто время словами (например, 'утром', 'вечером')"

    bot.send_message(message.chat.id, help_text, reply_markup=main_keyboard())

@bot.message_handler(
    func=lambda message: message.text in ["➕ Добавить задачу", "📋 Мои задачи", "🗑️ Очистить все", "ℹ️ Помощь"])
def handle_menu_buttons(message):
    user_id = message.from_user.id

    if message.text == "➕ Добавить задачу":
        user_states[user_id] = "waiting_task_description"
        bot.send_message(message.chat.id,
                         "📝 Введите описание задачи:",
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
                         "📭 У вас пока нет задач.\nДобавьте первую задачу!",
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
                         "Можете добавить новые задачи.",
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
        bot.send_message(message.chat.id,
                         "Выберите действие из меню:",
                         reply_markup=main_keyboard())
        return

    state = user_states[user_id]

    if state == "waiting_task_description":
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
                     "Выберите действие из меню:",
                     reply_markup=main_keyboard())


if __name__ == "__main__":
    print("🤖 Бот запущен...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")
