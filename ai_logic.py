import openai
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any

# Глобальная переменная для клиента OpenAI
client = None


def setup_ai(api_key: str):
    """Инициализация OpenAI клиента"""
    global client
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

    client = openai.OpenAI(api_key=api_key)
    print("✅ ИИ клиент инициализирован успешно")


def process_natural_language(text: str) -> Dict[str, Any]:
    """
    Обрабатывает текст на естественном языке и извлекает задачу

    Args:
        text: Текст пользователя

    Returns:
        Dict с ключами: success, description, time, explanation, error
    """
    if not client:
        return {
            'success': False,
            'error': 'ИИ не инициализирован'
        }

    try:
        # Получаем текущую дату и время
        current_datetime = datetime.now()
        current_date_str = current_datetime.strftime("%Y-%m-%d")
        current_time_str = current_datetime.strftime("%H:%M")
        current_weekday = current_datetime.strftime("%A")

        # Системный промпт для ИИ
        system_prompt = f"""
Ты - умный помощник для анализа задач на русском языке. Твоя задача - извлечь из текста пользователя описание задачи и время её выполнения.

Текущая дата: {current_date_str}
Текущее время: {current_time_str}
День недели: {current_weekday}

ВАЖНЫЕ ПРАВИЛА:
1. Всегда отвечай ТОЛЬКО в формате JSON
2. Если время не указано точно, используй логические предположения
3. Для относительных дат (завтра, послезавтра, через неделю) рассчитывай точное время
4. Время должно быть в удобном для чтения формате на русском языке

Формат ответа (JSON):
{{
    "success": true/false,
    "description": "описание задачи",
    "time": "время выполнения",
    "explanation": "краткое пояснение того, как ты понял задачу"
}}

Примеры обработки:
- "Встреча с Иваном завтра в 14:00" → description: "Встреча с Иваном", time: "завтра в 14:00"
- "Купить продукты вечером" → description: "Купить продукты", time: "вечером"
- "Позвонить врачу на следующей неделе" → description: "Позвонить врачу", time: "на следующей неделе"
- "Подготовить презентацию к пятнице" → description: "Подготовить презентацию", time: "к пятнице"

Если не можешь понять задачу, верни success: false с объяснением проблемы.
"""

        # Отправляем запрос к OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=300
        )

        # Получаем ответ от ИИ
        ai_response = response.choices[0].message.content.strip()

        # Пытаемся распарсить JSON
        try:
            result = json.loads(ai_response)
        except json.JSONDecodeError:
            # Если JSON некорректный, пытаемся извлечь информацию регулярными выражениями
            return fallback_parsing(text)

        # Проверяем обязательные поля
        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('explanation', 'ИИ не смог обработать задачу')
            }

        description = result.get('description', '').strip()
        time = result.get('time', '').strip()

        if not description:
            return {
                'success': False,
                'error': 'Не удалось определить описание задачи'
            }

        if not time:
            time = 'не указано'

        return {
            'success': True,
            'description': description,
            'time': time,
            'explanation': result.get('explanation', '')
        }

    except Exception as e:
        print(f"Ошибка ИИ обработки: {e}")
        # Используем fallback парсинг
        return fallback_parsing(text)


def fallback_parsing(text: str) -> Dict[str, Any]:
    """
    Базовая обработка текста без ИИ на случай ошибок
    """
    try:
        # Простые паттерны для извлечения времени
        time_patterns = [
            r'(\d{1,2}:\d{2})',  # 14:30
            r'\b(утром|днем|днём|вечером|ночью)\b',  # утром
            r'\b(завтра|послезавтра|сегодня)\b',  # завтра
            r'\b(в \d{1,2} утра|в \d{1,2} дня|в \d{1,2} вечера)\b',  # в 2 дня
            r'\b(на следующей неделе|через неделю)\b',  # на следующей неделе
            r'\b(в понедельник|во вторник|в среду|в четверг|в пятницу|в субботу|в воскресенье)\b',  # в пятницу
            r'\b(к понедельнику|ко вторнику|к среде|к четвергу|к пятнице|к субботе|к воскресенью)\b'  # к пятнице
        ]

        found_time = "не указано"
        description = text.strip()

        # Ищем время в тексте
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                found_time = match.group(1)
                # Убираем найденное время из описания
                description = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                description = re.sub(r'\s+', ' ', description)  # Убираем лишние пробелы
                break

        # Очищаем описание от лишних слов
        cleanup_patterns = [
            r'\b(напомни|напоминай|напомнить)\b',
            r'\b(мне|я должен|нужно)\b',
            r'\b(в|на|к|до|после)\s*$'
        ]

        for pattern in cleanup_patterns:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE).strip()

        if not description:
            description = text.strip()

        return {
            'success': True,
            'description': description,
            'time': found_time,
            'explanation': 'Обработано базовым анализатором'
        }

    except Exception as e:
        print(f"Ошибка fallback парсинга: {e}")
        return {
            'success': False,
            'error': 'Не удалось обработать текст'
        }


def enhance_time_description(time_str: str) -> str:
    """
    Улучшает описание времени, делая его более понятным
    """
    current_date = datetime.now()

    # Словарь для замены дней недели
    weekday_mapping = {
        'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3,
        'пятница': 4, 'суббота': 5, 'воскресенье': 6
    }

    # Обработка относительных дат
    if 'завтра' in time_str.lower():
        tomorrow = current_date + timedelta(days=1)
        return time_str.replace('завтра', f"завтра ({tomorrow.strftime('%d.%m')})")

    elif 'послезавтра' in time_str.lower():
        day_after_tomorrow = current_date + timedelta(days=2)
        return time_str.replace('послезавтра', f"послезавтра ({day_after_tomorrow.strftime('%d.%m')})")

    elif 'через неделю' in time_str.lower():
        next_week = current_date + timedelta(weeks=1)
        return time_str.replace('через неделю', f"через неделю ({next_week.strftime('%d.%m')})")

    return time_str


def test_ai_processing():
    """
    Функция для тестирования ИИ обработки
    """
    test_cases = [
        "Встреча с Иваном завтра в 14:00",
        "Купить продукты вечером",
        "Позвонить врачу на следующей неделе",
        "Подготовить презентацию к пятнице",
        "Записаться к стоматологу через неделю",
        "Сходить в спортзал утром",
        "Оплатить счета до конца месяца"
    ]

    print("🧪 Тестирование ИИ обработки:")
    for test_text in test_cases:
        result = process_natural_language(test_text)
        print(f"\nВход: {test_text}")
        print(f"Результат: {result}")


if __name__ == "__main__":
    # Для тестирования
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        setup_ai(api_key)
        test_ai_processing()
    else:
        print("❌ OPENAI_API_KEY не найден")