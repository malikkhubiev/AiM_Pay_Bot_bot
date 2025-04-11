import os
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
                reply_markup=keyboard
            )
            return web.json_response({"status": "notification sent"}, status=200)
        return web.json_response({"error": "Invalid data"}, status=400)
    
    async def send_invite_link(request):
        try:
            data = await request.json()
            tg_id = data.get("telegram_id")
            payment_id = data.get("payment_id")
            log.info("Начало обработки запроса...")
            
            invite_link: ChatInviteLink = await bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1,
                expire_date=None
            )
            link = invite_link.invite_link
            log.info("Пригласительная ссылка создана: %s", link)

            # save_invite_link_url = SERVER_URL + "/save_invite_link"
            # user_data = {
            #     "telegram_id": tg_id,
            #     "invite_link": link
            # }
            # response = await send_request(
            #     save_invite_link_url,
            #     method="POST",
            #     json=user_data
            # )
            
            # if response["status"] == "success":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Реферальная программа", callback_data='earn_new_clients'),
            )

            text_info = f"Поздравляем! Всё прошло успешно 🎉. Вот ссылка для присоединения к нашей группе. Обращайтесь с ней очень аккуратно. Она одноразовая и если вы воспользуетесь единственным шансом неверно, исправить ничего не получится: {link}."
            if payment_id:
                text_info += "\nДополнительно отправляем ваш идентификатор платежа: {payment_id}."    
            
            await bot.send_message(
                chat_id=tg_id,
                text=text_info,
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