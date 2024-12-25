import os
from aiohttp import web
from loader import *
from utils import log
from config import (
    GROUP_ID,
)

def web_server():
    async def handle(request):
        response_data = {"message": "pong"}
        return web.json_response(response_data)
    
    async def notify_user(request):
        data = await request.json()
        tg_id = data.get("telegram_id")
        message_text = data.get("message")

        if tg_id and message_text:
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Реферальная программа", callback_data='earn_new_clients'),
            )
            await bot.send_message(
                chat_id=tg_id,
                text=message_text,
                reply_markup=keyboard
            )
            return web.json_response({"status": "notification sent"}, status=200)
        return web.json_response({"error": "Invalid data"}, status=400)
    
    async def send_invite_link(request):
        try:
            data = await request.json()
            tg_id = data.get("telegram_id")
            log.info("Начало обработки запроса...")
            
            invite_link: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1
            )
            link = invite_link.invite_link
            log.info("Пригласительная ссылка создана: %s", link)

            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Реферальная программа", callback_data='earn_new_clients'),
            )
            
            await bot.send_message(
                chat_id=tg_id,
                text=f"Поздравляем! Ваш платёж прошёл успешно, вы оплатили курс 🎉. Вот ссылка для присоединения к нашей группе. Обращайтесь с ней очень аккуратно. Она одноразовая и если вы воспользуетесь единственным шансом неверно, исправить ничего не получится: {link}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            return web.json_response({"status": "notification sent"}, status=200)
        except Exception as e:
            log.error("Ошибка при создании ссылки: %s", e)
            raise web.HTTPInternalServerError(text="Ошибка на стороне Telegram API")

    app = web.Application()
    app.router.add_route("HEAD", "/", handle)
    app.router.add_route("GET", "/", handle)
    app.router.add_post("/notify_user", notify_user)
    app.router.add_post("/send_invite_link", send_invite_link)
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