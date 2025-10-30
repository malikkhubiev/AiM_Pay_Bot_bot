import os
from dotenv import load_dotenv

load_dotenv() 

USE_RENDER = os.getenv("USE_RENDER")

API_TOKEN = os.getenv("API_TOKEN")
SERVER_URL = os.getenv("SERVER_URL")
LANDING_URL = os.getenv("LANDING_URL")

MAIN_TELEGRAM_ID = os.getenv("MAIN_TELEGRAM_ID")
GROUP_ID = os.getenv("GROUP_ID")

COURSE_AMOUNT = os.getenv("COURSE_AMOUNT")
REFERRAL_AMOUNT = os.getenv("REFERRAL_AMOUNT")

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

GOOGLE_ANALYTICS_STEAM_ID = os.getenv("GOOGLE_ANALYTICS_STEAM_ID")
GOOGLE_ANALYTICS_API_SECRET_KEY = os.getenv("GOOGLE_ANALYTICS_API_SECRET_KEY")

TAX_INFO_IMG_URL = os.getenv("TAX_INFO_IMG_URL")
EARN_NEW_CLIENTS_VIDEO_URL = os.getenv("EARN_NEW_CLIENTS_VIDEO_URL")
START_VIDEO_URL = os.getenv("START_VIDEO_URL")
REPORT_VIDEO_URL = os.getenv("REPORT_VIDEO_URL")
REFERRAL_VIDEO_URL = os.getenv("REFERRAL_VIDEO_URL")

PORT = os.getenv("PORT")

SECRET_CODE = os.getenv("SECRET_CODE")
PROMO_CODE = os.getenv("PROMO_CODE")

GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScmXr-rBxTDx3_0MOtPbu02J66ME91L-VSAP9V3KU4VLyAUtg/formResponse"
GOOGLE_FORM_FIELDS = {
    "timestamp": "entry.1923603260",
    "telegram_id": "entry.1553449545",
    "username": "entry.1553449545",
    "event_type": "entry.1552469486",
    "button_name": "entry.765630597",
    "session_id": "entry.641306121",
    "session_start": "entry.1290285040",
    "session_end": "entry.631112949",
    "session_duration": "entry.1698616418",
}