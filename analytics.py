import httpx
from config import (
    GOOGLE_ANALYTICS_STEAM_ID,
    GOOGLE_ANALYTICS_API_SECRET_KEY,
    GOOGLE_FORM_URL,
    GOOGLE_FORM_FIELDS
)
from utils import *

def send_event_to_ga4(telegram_id, event_category, event_action, event_label=None, event_value=None):
    log.info(f"send_event_to_ga4 inside")
    # Получаем уникальный идентификатор пользователя (cid)
    cid = str(telegram_id)  # или можно использовать UUID: str(uuid.uuid4())
    log.info(f"cid {cid}")
    # Ваш идентификатор потока данных GA4
    stream_id = GOOGLE_ANALYTICS_STEAM_ID

    # Формируем запрос
    url = "https://www.google-analytics.com/mp/collect"
    params = {
        "measurement_id": stream_id,
        "api_secret": GOOGLE_ANALYTICS_API_SECRET_KEY,  # Получите API секрет на странице настроек в GA4
        "client_id": cid,
        "events": [
            {
                "name": event_action,  # Действие события (например, "start_click")
                "params": {
                    "event_category": event_category,  # Категория события (например, "interaction")
                    "event_label": event_label,  # Метка события (можно оставить None, если не нужно)
                    "event_value": event_value  # Значение события (можно оставить None, если не нужно)
                }
            }
        ]
    }
    
    log.info(f"before sending ga")
    
    # Отправляем запрос
    with httpx.Client() as client:
        response = client.post(url, json=params)
        log.info(f"we have response")
        log.info(f"{response}")
        if response.status_code == 204:
            log.info(f"sent")
            print("Событие успешно отправлено в GA4.")
        else:
            log.info(f"error with sending")
            print(f"Ошибка при отправке события: {response.status_code}, {response.text}")

async def send_event_to_google_form(data: dict):
    payload = {
        GOOGLE_FORM_FIELDS["telegram_id"]: data.get("telegram_id"),
        GOOGLE_FORM_FIELDS["username"]: data.get("username"),
        GOOGLE_FORM_FIELDS["event_type"]: data.get("event_type"),
        GOOGLE_FORM_FIELDS["button_name"]: data.get("button_name"),
        GOOGLE_FORM_FIELDS["session_id"]: data.get("session_id"),
        GOOGLE_FORM_FIELDS["session_start"]: data.get("session_start"),
        GOOGLE_FORM_FIELDS["session_end"]: data.get("session_end"),
        GOOGLE_FORM_FIELDS["session_duration"]: data.get("session_duration"),
    }
    async with httpx.AsyncClient() as client:
        await client.post(GOOGLE_FORM_URL, data=payload)
