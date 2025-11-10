import os
from datetime import datetime, timedelta, timezone
from aiohttp import web
from loader import *
from utils import *
from config import (
    GROUP_ID,
    SERVER_URL
)

def web_server():
    async def handle(request):
        response_data = {"message": "pong"}
        return web.json_response(response_data)
    
    async def notify_user(request):
        log.info(f"notify_user handler started")
        data = await request.json()
        log.info(f"data {data}")
        tg_id = data.get("telegram_id")
        log.info(f"tg_id {tg_id}")
        message_text = data.get("message")
        log.info(f"message_text {message_text}")

        if tg_id and message_text:
            log.info(f"check tg_id and message_text passed")
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Реферальная программа", callback_data='earn_new_clients'),
            )

            log.info(f"before sending message")
            await bot.send_message(
                chat_id=tg_id,
                text=message_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return web.json_response({"status": "notification sent"}, status=200)
        return web.json_response({"error": "Invalid data"}, status=400)
    
    async def send_invite_link(request):
        try:
            data = await request.json()
            tg_id = data.get("telegram_id")
            
            # При официальном
            # payment_id = data.get("payment_id")
            log.info("Начало обработки запроса...")
            
            invite_link: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1,
                expire_date=datetime.now(timezone.utc) + timedelta(minutes=30)
                # expire_date=datetime.now(timezone.utc) + timedelta(minutes=1)
            )
            link = invite_link.invite_link
            log.info("Пригласительная ссылка создана: %s", link)
            
            # if response["status"] == "success":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                # InlineKeyboardButton("Реферальная программа", callback_data='earn_new_clients'),
                InlineKeyboardButton("Назад", callback_data='start')
            )

            # Возвращаем ссылку для отправки на email
            return web.json_response({"status": "notification sent", "invite_link": link}, status=200)
        except Exception as e:
            log.error("Ошибка при создании ссылки: %s", e)
            raise web.HTTPInternalServerError(text="Ошибка на стороне Telegram API")
    
    async def kick_user(request):
        try:
            log.info("kick_user called")
            data = await request.json()
            tg_id = data.get("telegram_id")
            
            log.info(f"Начало обработки запроса для {tg_id}...")
            
            until_date = datetime.now()
            await bot.kick_chat_member(chat_id=GROUP_ID, user_id=tg_id, until_date=int(until_date.timestamp()))
            await bot.unban_chat_member(chat_id=GROUP_ID, user_id=tg_id)

            return web.json_response({"status": f"{tg_id} kicked"}, status=200)
        except Exception as e:
            log.error("Ошибка при создании ссылки: %s", e)
            raise web.HTTPInternalServerError(text="Ошибка на стороне Telegram API")

    app = web.Application()
    app.router.add_route("HEAD", "/", handle)
    app.router.add_route("GET", "/", handle)
    app.router.add_post("/notify_user", notify_user)
    app.router.add_post("/send_invite_link", send_invite_link)
    app.router.add_post("/kick_user", kick_user)
    return app

async def start_web_server():
    # Настройка веб-сервера с использованием aiohttp
    app = web.AppRunner(web_server())
    await app.setup()

    # Привязка адреса и порта
    bind_address = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8080))
    site = web.TCPSite(app, bind_address, PORT)
    await site.start()

    log.info(f"Веб-сервер запущен на порту {PORT}")

    # Запуск бота с ожиданием завершения
    await executor.start_polling(dp, skip_updates=True)