from utils import log
from config import (
    COURSE_AMOUNT,
    SERVER_URL,
    START_VIDEO_URL,
    REPORT_VIDEO_URL,
    REFERRAL_VIDEO_URL,
)
from utils import *
from loader import *

@dp.message_handler(commands=['start'])
async def start(message: types.Message, telegram_id: str = None, username: str = None):
    log.info(f"Получена команда /start от {telegram_id}")

    if not(telegram_id):
        telegram_id = message.from_user.id
    if not(username):
        username = message.from_user.username or message.from_user.first_name
    referrer_id = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else None

    if referrer_id and not(referrer_id.isdigit()):
        referrer_id = None

    await message.answer(f"referrer_id {referrer_id}")

    start_url = SERVER_URL + "/start"
    user_data = {
        "telegram_id": telegram_id,
        "username": username,
        "referrer_id": referrer_id
    }
    await message.answer(f"user_data {user_data}")
    keyboard = InlineKeyboardMarkup(row_width=1)
    try:
        response = send_request(
            start_url,
            method="POST",
            json=user_data
        )
        await message.answer(f"response {response}")
        
        if response["status"] == "error":
            await message.answer(response["message"])

        if response["type"] == "temp_user":
            await message.answer(f"temp")
            keyboard.add(
                InlineKeyboardButton("Начало работы", callback_data='getting_started'),
                InlineKeyboardButton("Документы", callback_data='documents'),
            )
            await message.answer(f"sendMessage")
            await bot.send_message(
                chat_id=message.chat.id,
                text="Добро пожаловать! Для начала работы с ботом вам нужно согласиться с политикой конфиденциальности и публичной офертой. Нажимая кнопку «Начало работы», вы подтверждаете своё согласие.",
                reply_markup=keyboard
            )
        elif response["type"] == "user":
            if response["to_show"] == "pay_course":
                keyboard.add(
                    InlineKeyboardButton("Оплатить курс", callback_data='pay_course'),
                )
            else:
                keyboard.add(
                    InlineKeyboardButton("Получить ссылку", callback_data='get_own_link'),
                )
            keyboard.add(
                InlineKeyboardButton("Заработать на новых клиентах", callback_data='earn_new_clients')
            )
            await bot.send_video(
                chat_id=message.chat.id,
                video=START_VIDEO_URL,
                caption="Добро пожаловать! Здесь Вы можете оплатить курс и заработать на привлечении новых клиентов.",
                reply_markup=keyboard
            )

    except RequestException as e:
        logger.error("Ошибка при запросе к серверу: %s", e)
        await bot.send_message(message.chat.id, "Ошибка при проверке регистрации. Пожалуйста, попробуйте позже.")
        return
    except KeyError:
        logger.warning("Пользователь не зарегистрирован в базе данных.")
        return

async def getting_started(message: types.Message, telegram_id: str):
    log.info(f"Получена команда /getting_started от {telegram_id}")

    await message.answer(f"hey")

    getting_started_url = SERVER_URL + "/getting_started"
    user_data = {
        "telegram_id": telegram_id
    }
    await message.answer(f"{user_data} user_data")

    response = send_request(
        getting_started_url,
        method="POST",
        json=user_data
    )
    await message.answer(f"{response}")
    
    if response["status"] == "error":
        await message.answer(response["message"])

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Оплатить курс", callback_data='pay_course'),
        InlineKeyboardButton("Заработать на новых клиентах", callback_data='earn_new_clients')
    )
    await bot.send_video(
        chat_id=message.chat.id,
        video=START_VIDEO_URL,
        caption="Добро пожаловать! Здесь Вы можете оплатить курс и заработать на привлечении новых клиентов.",
        reply_markup=keyboard
    )

async def get_documents(message: types.Message, telegram_id: str):
    log.info(f"Получена команда /get_documents от {telegram_id}")
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Публичная оферта", callback_data='public_offer'),
        InlineKeyboardButton("Политика Конфиденциальности", callback_data='privacy_policy'),
        InlineKeyboardButton("Назад", callback_data='start'),
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text="Внимательно прочитайте следующие документы.",
        reply_markup=keyboard
    )

async def get_public_offer(message: types.Message, telegram_id: str):
    log.info(f"Получена команда /get_public_offer от {telegram_id}")
    public_offer_url = SERVER_URL + "/offer"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='documents')
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Для ознакомления с Публичной офертой перейдите по ссылке: {public_offer_url}",
        reply_markup=keyboard
    )

async def get_privacy_policy(message: types.Message, telegram_id: str):
    log.info(f"Получена команда /get_privacy_policy от {telegram_id}")
    privacy_url = SERVER_URL + "/privacy"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='documents')
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Для ознакомления с Политикой конфиденциальности перейдите по ссылке: {privacy_url}",
        reply_markup=keyboard
    )

async def handle_pay_command(message: types.Message, telegram_id: str):
    amount = float(COURSE_AMOUNT)  # Пример суммы, можно заменить
    
    await message.answer(f"{amount} amount")

    # Шаг 1: Проверка, зарегистрирован ли пользователь
    check_user_url = SERVER_URL + "/check_user"

    await message.answer(f"{check_user_url} check_user_url")

    user_data = {"telegram_id": telegram_id}
    await message.answer(f"{user_data} user_data")

    try:
        response = send_request(
            check_user_url,
            method="POST",
            json=user_data
        )
        await message.answer(f"{response} response")
        user_id = response["user"]["id"]
        
        await message.answer(f"{user_id} user_id")
    except RequestException as e:
        logger.error("Ошибка при проверке пользователя: %s", e)
        await message.answer("Ошибка при проверке регистрации. Пожалуйста, попробуйте позже.")
        return
    except KeyError:
        logger.warning("Пользователь не зарегистрирован, запрос /pay отклонён.")
        await message.answer("Сначала нажмите /start для регистрации.")
        return

    # Шаг 2: Отправка запроса на создание платежа
    create_payment_url = SERVER_URL + "/create_payment"
    await message.answer(f"{create_payment_url} create_payment_url")

    payment_data = {
        "telegram_id": telegram_id
    }

    await message.answer(f"{payment_data} payment_data")
    try:
        response = send_request(
            create_payment_url,
            method="POST",
            json=user_data
        )

        if response["status"] == "error":
            await message.answer(response["message"])
        elif response["status"] == "success":
            payment_url = response.get("confirmation", {}).get("confirmation_url")
            
            await message.answer(f"{payment_url} payment_url")

            if payment_url:
                await message.answer(f"Для оплаты курса, перейдите по ссылке: {payment_url}")
            else:
                logger.error("Ошибка: Confirmation URL отсутствует в ответе сервера.")
                await message.answer("Ошибка при создании ссылки для оплаты.")
    except RequestException as e:
        logger.error("Ошибка при отправке запроса на сервер: %s", e)
        await message.answer("Ошибка при обработке платежа.")

async def generate_overview_report(message: types.Message, telegram_id: str):
    await message.answer(f"generate_overview_report")
    overview_report_url = SERVER_URL + "/generate_overview_report"
    user_data = {"telegram_id": telegram_id}

    await message.answer(f"{telegram_id} telegram_id")
    await message.answer(f"{overview_report_url} report_url")
    await message.answer(f"{user_data} user_data")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='generate_report')
    )

    try:
        response = send_request(
            overview_report_url,
            method="POST",
            json=user_data
        )

        if response["status"] == "error":
            await message.answer(response["message"])
        elif response["status"] == "success":
            # Формируем текст отчета на основе данных из ответа
            username = response.get("username")
            referral_count = response.get("referral_count")
            total_payout = response.get("total_payout")
            paid_count = response.get("paid_count")
            paid_percentage = response.get("paid_percentage")

            
            await message.answer(f"{username} username")
            await message.answer(f"{referral_count} referral_count")
            await message.answer(f"{total_payout} total_payout")

            report = (
                f"<b>Отчёт для {username}:</b>\n\n"
                f"Привлечённые пользователи: {referral_count}\n"
                f"Оплатили курс: {paid_count} ({paid_percentage:.2f}%)\n"
                f"Общее количество заработанных денег: {total_payout:.2f} руб.\n"
            )

            await bot.send_video(
                chat_id=message.chat.id,
                video=REPORT_VIDEO_URL,
                caption=report,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
    except RequestException as e:
        logger.error("Ошибка при отправке запроса на сервер: %s", e)
        await bot.send_message(
            chat_id=message.chat.id,
            text="Ошибка при генерации отчета.",
            reply_markup=keyboard
        )
    except KeyError:
        await bot.send_message(
            chat_id=message.chat.id,
            text="Пользователь не зарегистрирован. Пожалуйста, нажмите /start для регистрации.",
            reply_markup=keyboard
        )

async def generate_clients_report(message: types.Message, telegram_id: str):
    await message.answer(f"generate_clients_report")
    clients_report_url = SERVER_URL + "/generate_clients_report"
    user_data = {"telegram_id": telegram_id}

    await message.answer(f"{telegram_id} telegram_id")
    await message.answer(f"{clients_report_url} report_url")
    await message.answer(f"{user_data} user_data")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='generate_report')
    )

    try:
        response = send_request(
            clients_report_url,
            method="POST",
            json=user_data
        )

        if response["status"] == "error":
            await message.answer(response["message"])
        elif response["status"] == "success":
            # Формируем текст отчета на основе данных из ответа
            username = response.get("username")
            invited_list = response.get("invited_list")

            await message.answer(f"{username} username")
            await message.answer(f"{invited_list} invited_list")

            report = (
                f"<b>Отчёт для {username}:</b>\n"
            )

            await bot.send_video(
                chat_id=message.chat.id,
                video=REPORT_VIDEO_URL,
                caption=report,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

            # Send the list of invited users
            if invited_list:
                await message.answer(f"{invited_list} invited_list есть")
                for invited in invited_list:
                    await message.answer(f"{invited} invited перебор начался")
                    user_status = "Оплатил" if invited["paid"] else "Не оплатил"
                    user_info = (
                        f"<b>Пользователь:</b> {invited['username']}\n"
                        f"<b>Telegram ID:</b> {invited['telegram_id']}\n"
                        f"<b>Статус:</b> {user_status}\n\n"
                    )
                    await message.answer(f"{user_info} user_info")
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=user_info,
                        parse_mode=ParseMode.HTML
                    )

    except RequestException as e:
        logger.error("Ошибка при отправке запроса на сервер: %s", e)
        await bot.send_message(
            chat_id=message.chat.id,
            text="Ошибка при генерации отчета.",
            reply_markup=keyboard
        )
    except KeyError:
        await bot.send_message(
            chat_id=message.chat.id,
            text="Пользователь не зарегистрирован. Пожалуйста, нажмите /start для регистрации.",
            reply_markup=keyboard
        )

async def bind_card(message: types.Message, telegram_id: str):
    bind_card_url = SERVER_URL + "/bind_card"
    user_data = {"telegram_id": telegram_id}
    try:
        response = send_request(
            bind_card_url,
            method="POST",
            json=user_data
        )
        if response["status"] == "error":
            await message.answer(response["message"])
            return
        elif response["status"] == "success":

            binding_url = response["binding_url"]

            await message.answer(f"{binding_url} binding_url")

            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Назад", callback_data='earn_new_clients')
            )

            text = ""
        
            if binding_url:
                text = f"Перейдите по следующей ссылке для привязки карты: {binding_url}"
            else:
                text = "Ошибка при генерации ссылки."
            
            await bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard
            )

    except RequestException as e:
        logger.error("Ошибка при отправке запроса на сервер: %s", e)
        await message.answer("Ошибка при генерации ссылки.")
    except KeyError:
        await message.answer("Пользователь не зарегистрирован. Пожалуйста, нажмите /start для регистрации.")

async def send_referral_link(message: types.Message, telegram_id: str):
    await message.answer(f"send_referral_link")
    referral_url = SERVER_URL + "/get_referral_link"
    user_data = {"telegram_id": telegram_id}

    await message.answer(f"{telegram_id} telegram_id")
    await message.answer(f"{referral_url} referral_url")
    await message.answer(f"{user_data} user_data")

    try:
        response = send_request(
            referral_url,
            method="POST",
            json=user_data
        ) 

        text = ""
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("Назад", callback_data='earn_new_clients')
        )
    
        if response["status"] == "success":
            referral_link = response.get("referral_link")
            
            await message.answer(f"{referral_link} referral_link")

            await bot.send_video(
                chat_id=message.chat.id,
                video=REFERRAL_VIDEO_URL,
                caption=(
                    f"Отправляю тебе реферальную ссылку:\n{referral_link}\n"
                    f"Зарабатывай, продвигая It - образование."
                ),
                reply_markup=keyboard
            )

        elif response["status"] == "error":
            text = response["message"]
        else:
            text = "Ошибка при генерации ссылки"
        await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
    except RequestException as e:
        logger.error("Ошибка при отправке запроса на сервер: %s", e)
        await message.answer("Ошибка при генерации реферальной ссылки.")
    except KeyError:
        await message.answer("Пользователь не зарегистрирован. Пожалуйста, нажмите /start для регистрации.")
