# 📝 AITeleBotDiary — Telegram-бот-ежедневник с напоминаниями

**AITeleBotDiary** — это удобный Telegram-бот, помогающий управлять задачами и получать напоминания о предстоящих событиях. Написан на Python.

## 🚀 Возможности

- ✅ Добавление задач с указанием даты и времени
- ⏰ Автоматические напоминания о событиях
- 📋 Просмотр всех запланированных дел
- 🗑 Удаление задач
- 💾 Хранение задач в SQLite
- 👥 Поддержка нескольких пользователей

## 🛠 Стек технологий

- Python 3.10+
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- SQLite
- python-dotenv

## 📦 Установка

1. Клонируй репозиторий:

    ```bash
    git clone https://github.com/yourusername/dailybot.git
    cd AITeleBotDiary
    ```

2. Установи зависимости:

    ```bash
    pip install -r requirements.txt
    ```

3. Создай файл `.env` и добавь токен своего Telegram-бота:

    ```env
    BOT_TOKEN=your_telegram_bot_token_here
    ```

4. Запусти бота:

    ```bash
    python bot.py
    ```

## 💬 Команды бота

| Команда      | Описание                      |
|--------------|-------------------------------|
| `/start`     | Начало работы с ботом         |
| `/add`       | Добавить новую задачу         |
| `/list`      | Показать все задачи           |
| `/clear`     | Удалить все задачи            |
| `/help`      | Справка по командам           |

## 🧠 Пример логики добавления задачи

```python
def add_task(user_id: int, text: str, time: datetime):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, text, time) VALUES (?, ?, ?)", (user_id, text, time))
    conn.commit()
    conn.close()
