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
    git clone https://github.com/LomakoDima/AITeleBotDiary.git
    cd AITeleBotDiary
    ```

2. Установи зависимости:

    ```bash
    pip install -r requirements.txt
    ```

3. Создай файл `.env` и добавь токен своего Telegram-бота:

    ```env
    BOT_TOKEN=your_telegram_bot_token_here
    OPENAI_API_KEY=your_openai_api_key_here
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
def add_task(user_id: int, description: str, time: str):
    """Добавляет новую задачу для пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_id, description, time) VALUES (?, ?, ?)",
            (user_id, description.strip(), time.strip())
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Ошибка добавления задачи: {e}")
        return False
