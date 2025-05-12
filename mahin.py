import os
import asyncio
import nest_asyncio
from loader import *
from utils import *
from web_server import start_web_server
from button_handlers import register_callback_handlers
from handlers import BlacklistMiddleware

from config import (
    SERVER_URL
)

nest_asyncio.apply()

register_callback_handlers(dp)

dp.middleware.setup(BlacklistMiddleware()) 
dp.middleware.setup(ThrottlingMiddleware(rate_limit=2)) 

async def start_polling():
    await dp.start_polling()

USE_RENDER = os.getenv("USE_RENDER", "false").lower() == "true"

if __name__ == "__main__":
    if USE_RENDER:
        # Render: запускаем веб-сервер
        asyncio.run(start_web_server())
    else:
        # Локально: запускаем polling
        asyncio.run(start_polling())
