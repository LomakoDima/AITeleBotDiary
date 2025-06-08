import sqlite3
from datetime import datetime
import os

# Путь к базе данных
DB_PATH = "tasks.db"


# Инициализация базы данных
def init_db():
    """Создает базу данных и таблицу tasks, если они не существуют"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована успешно")
    except sqlite3.Error as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")


# Добавление задачи
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


# Получение задач пользователя
def get_tasks(user_id: int):
    """Возвращает все задачи пользователя, отсортированные по времени создания"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT description, time FROM tasks WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,)
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    except sqlite3.Error as e:
        print(f"❌ Ошибка получения задач: {e}")
        return []


# Получение количества задач пользователя
def get_tasks_count(user_id: int):
    """Возвращает количество задач пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error as e:
        print(f"❌ Ошибка подсчета задач: {e}")
        return 0


# Удаление всех задач пользователя
def clear_tasks(user_id: int):
    """Удаляет все задачи пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count
    except sqlite3.Error as e:
        print(f"❌ Ошибка удаления задач: {e}")
        return 0


# Удаление конкретной задачи по ID
def delete_task(user_id: int, task_id: int):
    """Удаляет конкретную задачу пользователя по ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM tasks WHERE user_id = ? AND id = ?",
            (user_id, task_id)
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except sqlite3.Error as e:
        print(f"❌ Ошибка удаления задачи: {e}")
        return False


# Получение задач с ID (для удаления конкретных задач)
def get_tasks_with_id(user_id: int):
    """Возвращает все задачи пользователя с их ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, description, time FROM tasks WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,)
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    except sqlite3.Error as e:
        print(f"❌ Ошибка получения задач с ID: {e}")
        return []


# Проверка существования базы данных
def check_db_exists():
    """Проверяет, существует ли файл базы данных"""
    return os.path.exists(DB_PATH)


# Получение статистики базы данных
def get_db_stats():
    """Возвращает общую статистику базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Общее количество задач
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]

        # Количество уникальных пользователей
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM tasks")
        unique_users = cursor.fetchone()[0]

        conn.close()

        return {
            'total_tasks': total_tasks,
            'unique_users': unique_users
        }
    except sqlite3.Error as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {'total_tasks': 0, 'unique_users': 0}