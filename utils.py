from config import (
    SECRET_CODE
)
import logging as log
import httpx
from loader import *
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from time import time

log.basicConfig(level=log.DEBUG)
logger = log.getLogger(__name__)

async def send_request(url, method="GET", headers=None, **kwargs):
    if headers is None:
        headers = {}
    headers["X-Secret-Code"] = SECRET_CODE  # Добавляем заголовок

    async with httpx.AsyncClient() as client:
        try:
            # Выбор метода запроса
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, **kwargs)
            elif method.upper() == "GET":
                response = await client.get(url, headers=headers, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, **kwargs)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Проверяем статус ответа
            response.raise_for_status()  # Вызывает исключение для ошибок статуса

            # Проверяем Content-Type
            content_type = response.headers.get("Content-Type", "")

            if content_type.startswith("application/json"):
                return response.json()  # Возвращаем JSON-ответ
            elif content_type.startswith("application/vnd.openxmlformats"):
                return response.content  # Возвращаем бинарные данные (файл)
            elif content_type.startswith("application/pdf"):
                return response.content  # Возвращаем бинарные данные (файл PDF)
            else:
                logger.error(f"Неизвестный Content-Type: {content_type}")
                return {"status": "error", "message": "Сервер вернул данные неизвестного формата."}

        except httpx.RequestError as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return {"status": "error", "message": "Ошибка при подключении к серверу."}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP статус-код {e.response.status_code}: {e}")
            return {"status": "error", "message": f"Сервер вернул ошибку: {e.response.status_code}."}
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            return {"status": "error", "message": "Произошла ошибка."}

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit=1):
        super().__init__()
        self.rate_limit = rate_limit
        self.user_timestamps = {}

    async def on_pre_process_message(self, message: Message, data: dict):
        user_id = message.from_user.id
        current_time = time()

        if user_id not in self.user_timestamps:
            self.user_timestamps[user_id] = current_time
            return
        
        last_time = self.user_timestamps[user_id]
        if current_time - last_time < self.rate_limit:
            await message.answer("Слишком много запросов. Попробуйте позже.")
            raise CancelHandler()

        self.user_timestamps[user_id] = current_time

test_questions = [
    {
        "question": "Что такое машинное обучение?",
        "answers": ["Алгоритм", "Язык программирования", "Фреймворк", "База данных"],
        "correct": 0
    },
    {
        "question": "Какая библиотека чаще всего используется для машинного обучения в Python?",
        "answers": ["Django", "NumPy", "TensorFlow", "Flask"],
        "correct": 2
    },
    {
        "question": "Какой метод обучения использует размеченные данные?",
        "answers": ["Надзорное обучение", "Безнадзорное обучение", "Реинфорсмент", "Эволюционные алгоритмы"],
        "correct": 0
    },
    # Добавь еще 22 вопроса в таком же формате
]

async def generate_conversion_stats_by_source(stats):
    report = "📊 **Статистика по источникам**:\n\n"
    report += "| Источник | Всего | Зарегистрировались | % Регистраций | Оплатили | % Оплат от всех | % Оплат от зарегистрированных |\n"
    report += "|----------|-------|---------------------|----------------|----------|------------------|-----------------------------|\n"

    for stat in stats:
        report += f"| {stat['Источник']} | {stat['Всего']} | {stat['Зарегистрировались']} | {stat['% Регистраций']} | {stat['Оплатили']} | {stat['% Оплат от всех']} | {stat['% Оплат от зарегистрированных']} |\n"

    return report

async def generate_referral_conversion_stats(stats):
    report = "📊 **Статистика по рефералам**:\n\n"
    report += "| Реферер ID | Пришло по рефералке | Зарегистрировались | % Регистраций | Оплатили | % Оплат от всех | % Оплат от зарегистрированных |\n"
    report += "|------------|---------------------|---------------------|----------------|----------|------------------|-----------------------------|\n"

    for stat in stats:
        report += f"| {stat['Реферер ID']} | {stat['Пришло по рефералке']} | {stat['Зарегистрировались']} | {stat['% Регистраций']} | {stat['Оплатили']} | {stat['% Оплат от всех']} | {stat['% Оплат от зарегистрированных']} |\n"

    return report