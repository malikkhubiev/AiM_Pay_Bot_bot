from utils import log
from config import (
    COURSE_AMOUNT,
    REFERRAL_AMOUNT,
    SERVER_URL,
    START_VIDEO_URL,
    REPORT_VIDEO_URL,
    REFERRAL_VIDEO_URL,
    EARN_NEW_CLIENTS_VIDEO_URL,
    TAX_INFO_IMG_URL,
    MAIN_TELEGRAM_ID,
    PROMO_CODE
)
from analytics import send_event_to_ga4
from utils import *
from loader import *

# Кэш для хранения ссылок
links_cache = {}

# Функция для инициализации словаря кэша, если его ещё нет
def init_user_cache(telegram_id: str):
    if telegram_id not in links_cache:
        links_cache[telegram_id] = {
            'invite_link': None,
            'referral_link': None
        }

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

    log.info(f"referrer_id {referrer_id}")

    start_url = SERVER_URL + "/start"
    user_data = {
        "telegram_id": telegram_id,
        "username": username,
        "referrer_id": referrer_id
    }
    log.info(f"user_data  {user_data}")
    keyboard = InlineKeyboardMarkup(row_width=1)

    response = await send_request(
        start_url,
        method="POST",
        json=user_data
    )
    log.info(f"response {response}")

    if response["status"] == "success":
        if response["type"] == "temp_user":
            log.info(f"temp")
            keyboard.add(
                InlineKeyboardButton("Начало работы 🏔️", callback_data='getting_started'),
                InlineKeyboardButton("Документы 📚", callback_data='documents'),
            )
            log.info(f"send_message")
            await bot.send_message(
                chat_id=message.chat.id,
                text="Добро пожаловать! Для начала работы с ботом вам нужно согласиться с политикой конфиденциальности и публичной офертой. Нажимая кнопку «Начало работы», вы подтверждаете своё согласие.",
                reply_markup=keyboard
            )
        elif response["type"] == "user":
            if response["to_show"] == "pay_course":
                keyboard.add(
                    InlineKeyboardButton("Оплатить курс 💰", callback_data='pay_course'),
                )

            if response["with_promo"] == True:
                keyboard.add(
                    InlineKeyboardButton("Ввести промокод 🎩", callback_data='type_promo'),
                )
            # else:
            #     keyboard.add(
            #         InlineKeyboardButton("Получить ссылку", callback_data='get_invite_link'),
            #     )
            keyboard.add(
                InlineKeyboardButton("Заработать на новых клиентах 💸", callback_data='earn_new_clients')
            )
            await bot.send_video(
                chat_id=message.chat.id,
                video=START_VIDEO_URL,
                caption="Добро пожаловать! Здесь Вы можете оплатить курс и заработать на привлечении новых клиентов.",
                reply_markup=keyboard
            )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def getting_started(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /getting_started от {telegram_id}")

    getting_started_url = SERVER_URL + "/getting_started"
    user_data = {
        "telegram_id": telegram_id
    }
    log.info(f"user_data {user_data}")

    response = await send_request(
        getting_started_url,
        method="POST",
        json=user_data
    )
    log.info(f"response {response}")

    if response["status"] == "success":
        keyboard = InlineKeyboardMarkup(row_width=1)

        if response["with_promo"] == True:
            keyboard.add(
                InlineKeyboardButton("Ввести промокод 🎩", callback_data='type_promo'),
            )

        keyboard.add(
            InlineKeyboardButton("Оплатить курс 💰", callback_data='pay_course'),
            InlineKeyboardButton("Заработать на новых клиентах 💸", callback_data='earn_new_clients')
        )
        await bot.send_video(
            chat_id=message.chat.id,
            video=START_VIDEO_URL,
            caption="Добро пожаловать! Здесь Вы можете оплатить курс и заработать на привлечении новых клиентов.",
            reply_markup=keyboard
        )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def get_documents(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_documents от {telegram_id}")
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Публичная оферта 📜", callback_data='public_offer'),
        InlineKeyboardButton("Политика Конфиденциальности 📝", callback_data='privacy_policy'),
        InlineKeyboardButton("Назад", callback_data='start'),
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text="Внимательно прочитайте следующие документы.",
        reply_markup=keyboard
    )

async def get_public_offer(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_public_offer от {telegram_id}")
    public_offer_url = "https://docs.google.com/document/d/1N6ZZoRyW1uIBNVATMaFC_lxQDIpUi1vwNpS8YWvGr-U/edit?usp=sharing"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='documents')
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Для ознакомления с Публичной офертой перейдите по ссылке: {public_offer_url}",
        reply_markup=keyboard
    )

async def get_privacy_policy(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_privacy_policy от {telegram_id}")
    privacy_url = "https://docs.google.com/document/d/1CWVSyjuYJXPIpMApAdMevFVnFuIxHbF7xE-Ngqmd-B0/edit?usp=sharing"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='documents')
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Для ознакомления с Политикой конфиденциальности перейдите по ссылке: {privacy_url}",
        reply_markup=keyboard
    )

async def handle_pay_command(message: types.Message, telegram_id: str, u_name: str = None):
    amount = float(COURSE_AMOUNT)  # Пример суммы, можно заменить
    
    log.info(f"amount {amount}")

    # Шаг 1: Проверка, зарегистрирован ли пользователь
    check_user_url = SERVER_URL + "/check_user"

    log.info(f"check_user_url {check_user_url}")

    user_data = {"telegram_id": telegram_id}
    log.info(f"user_data {user_data}")

    response = await send_request(
        check_user_url,
        method="POST",
        json=user_data
    )

    if response["status"] == "success":
        log.info(f"response {response}")
        user_id = response["user"]["id"]
        
        log.info(f"user_id {user_id}")

        # Шаг 2: Отправка запроса на создание платежа
        create_payment_url = SERVER_URL + "/create_payment"
        log.info(f"create_payment_url {create_payment_url}")

        payment_data = {
            "telegram_id": telegram_id
        }

        log.info(f"payment_data {payment_data}")
        response = await send_request(
            create_payment_url,
            method="POST",
            json=user_data
        )

        if response["status"] == "success":
            payment_url = response.get("confirmation", {}).get("confirmation_url")
            
            log.info(f"payment_url {payment_url}")

            if payment_url:
                await message.answer(f"Для оплаты курса, перейдите по ссылке: {payment_url}")
            else:
                logger.error("Ошибка: Confirmation URL отсутствует в ответе сервера.")
                await message.answer("Ошибка при создании ссылки для оплаты.")
        elif response["status"] == "error":
            await message.answer(response["message"])
    elif response["status"] == "error":
        if response["message"] == "Internal server error":    
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start для начала работы")
        else:
            await message.answer(response["message"])

async def generate_clients_report(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"generate_clients_report")
    clients_report_url = SERVER_URL + "/generate_clients_report"
    user_data = {"telegram_id": telegram_id}

    log.info(f"telegram_id {telegram_id}")
    log.info(f"clients_report_url {clients_report_url}")
    log.info(f"user_data {user_data}")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='earn_new_clients')
    )

    response = await send_request(
        clients_report_url,
        method="POST",
        json=user_data
    )

    if response["status"] == "success":
        report = response["report"]
        # Формируем текст отчета на основе данных из ответа
        username = report.get("username")
        balance = report.get("balance")
        invited_list = report.get("invited_list")
        total_payout = report.get("total_payout")
        paid_count = report.get("paid_count")

        log.info(f"username {username}")
        log.info(f"invited_list {invited_list}")

        report = (
            f"<b>Отчёт для {username}:</b>\n\n"
            f"👨‍🎓 Количество привлечённых пользователей, оплативших курс: {paid_count}\n"
            f"💸 Количество выплаченных денег: {total_payout:.2f} руб.\n"
            f"💰 Баланс: {balance} руб.\n"
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
            log.info(f"invited_list {invited_list}")
            for invited in invited_list:
                log.info(f"invited_list invited перебор начался")
                user_info = (
                    f"<b>Пользователь:</b> {invited['username']}\n"
                    f"<b>Telegram ID:</b> {invited['telegram_id']}\n\n"
                )
                log.info(f"user_info {user_info}")
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=user_info,
                    parse_mode=ParseMode.HTML
                )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def bind_card(message: types.Message, telegram_id: str, u_name: str = None):
    bind_card_url = SERVER_URL + "/bind_card"
    user_data = {"telegram_id": telegram_id}
    response = await send_request(
        bind_card_url,
        method="POST",
        json=user_data
    )
    if response["status"] == "success":
        binding_url = response["binding_url"]
        log.info(f"binding_url {binding_url}")
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
    elif response["status"] == "error":
        await message.answer(response["message"])
        return

async def send_referral_link(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"send_referral_link")
    init_user_cache(telegram_id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='earn_new_clients')
    )

    if links_cache[telegram_id]['referral_link'] is not None:
        log.info(f"из кэша")
        await bot.send_video(
            chat_id=message.chat.id,
            video=REFERRAL_VIDEO_URL,
            caption=(
                f"Отправляю тебе реферальную ссылку:\n{links_cache[telegram_id]['referral_link']}\n"
                f"Зарабатывай, продвигая It - образование."
            ),
            reply_markup=keyboard
        )
        return 
    
    referral_url = SERVER_URL + "/get_referral_link"
    user_data = {"telegram_id": telegram_id}

    log.info(f"telegram_id {telegram_id}")
    log.info(f"referral_url {referral_url}")
    log.info(f"user_data {user_data}")

    response = await send_request(
        referral_url,
        method="POST",
        json=user_data
    ) 

    text = ""

    if response["status"] == "success":
        referral_link = response.get("referral_link")
        links_cache[telegram_id]['referral_link'] = referral_link
        
        log.info(f"referral_link {referral_link}")

        await bot.send_video(
            chat_id=message.chat.id,
            video=REFERRAL_VIDEO_URL,
            caption=(
                f"Отправляю тебе реферальную ссылку:\n{referral_link}\n"
                f"Зарабатывай, продвигая It - образование."
            ),
            reply_markup=keyboard
        )

        return

    elif response["status"] == "error":
        text = response["message"]
    else:
        text = "Ошибка при генерации ссылки"
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=keyboard
    )

# async def send_invite_link(message: types.Message, telegram_id: str, u_name: str = None):
#     log.info(f"send_invite_link")
#     init_user_cache(telegram_id)
    
#     keyboard = InlineKeyboardMarkup(row_width=1)
#     keyboard.add(
#         InlineKeyboardButton("Назад", callback_data='earn_new_clients')
#     )

#     if links_cache[telegram_id]['invite_link'] is not None:
#         log.info(f"из кэша")
#         await bot.send_video(
#             chat_id=message.chat.id,
#             video=REFERRAL_VIDEO_URL,
#             caption=(
#                 f"Вот ссылка для присоединения к нашей группе. Обращайтесь с ней очень аккуратно. Она одноразовая и если вы воспользуетесь единственным шансом неверно, исправить ничего не получится: {links_cache[telegram_id]['invite_link']}"
#             ),
#             reply_markup=keyboard
#         )
#         return 

#     invite_url = SERVER_URL + "/get_invite_link"
#     user_data = {"telegram_id": telegram_id}

#     log.info(f"user_data {user_data}")

#     response = await send_request(
#         invite_url,
#         method="POST",
#         json=user_data
#     ) 

#     text = ""

#     if response["status"] == "success":
#         invite_link = response.get("invite_link")
#         links_cache[telegram_id]['invite_link'] = invite_link
        
#         log.info(f"invite_link {invite_link}")

#         await bot.send_video(
#             chat_id=message.chat.id,
#             video=REFERRAL_VIDEO_URL,
#             caption=(
#                 f"Вот ссылка для присоединения к нашей группе. Обращайтесь с ней очень аккуратно. Она одноразовая и если вы воспользуетесь единственным шансом неверно, исправить ничего не получится: {invite_link}"
#             ),
#             reply_markup=keyboard
#         )

#         return

#     elif response["status"] == "error":
#         text = response["message"]
#     else:
#         text = "Ошибка при генерации ссылки"
#     await bot.send_message(
#         chat_id=message.chat.id,
#         text=text,
#         reply_markup=keyboard
#     )

async def earn_new_clients(message: types.Message, telegram_id: str, u_name: str = None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    log.info(f"telegram_id {telegram_id}")
    log.info(f"{MAIN_TELEGRAM_ID}")
    log.info(f"telegram_id = MAIN_TELEGRAM_ID{telegram_id == MAIN_TELEGRAM_ID}")
    
    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        keyboard.add(
            InlineKeyboardButton("Админ 👨‍💻", callback_data='admin'),
        )

    keyboard.add(
        InlineKeyboardButton("Привязать/изменить карту 💳", callback_data='bind_card'),
        InlineKeyboardButton("Получить реферальную ссылку 🏎", callback_data='get_referral'),
        InlineKeyboardButton("Сформировать отчёт о заработке 🚀", callback_data='generate_report'),
        InlineKeyboardButton("Налоги 🏫", callback_data='tax_info'),
        InlineKeyboardButton("Документы 📚", callback_data='documents'),
        InlineKeyboardButton("Назад", callback_data='start'),
    )

    await bot.send_video(
        chat_id=message.chat.id,
        video=EARN_NEW_CLIENTS_VIDEO_URL,
        caption=f"Курс стоит {COURSE_AMOUNT} рублей.\nЗа каждого привлечённого вами клиента вы заработаете {REFERRAL_AMOUNT} рублей.\nПосле 3-х клиентов курс становится для Вас бесплатным.\nНачиная с 4-го клиента, вы начинаете зарабатывать на продвижении It-образования."
    )
    await bot.send_message(
        message.chat.id,
        f"Отправляйте рекламные сообщения в тематические чаты по изучению программирования, а также в телеграм-группы различных российских вузов и вы можете выйти на прибыль в {float(REFERRAL_AMOUNT)*50} рублей после привлечения 50 клиентов.\n\nПеред тем как начать, ещё раз внимательно прочитайте документы, чтобы не было никаких неприятностей.",
        reply_markup=keyboard
    )

async def admin(message: types.Message, telegram_id: str, u_name: str = None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Информация о выплатах 💳", callback_data='get_payout_balance'),
        InlineKeyboardButton("Промокодеры по датам 🐝", callback_data='get_promo_users_frequency'),
        InlineKeyboardButton("Оплаты по датам 🍰", callback_data='get_payments_frequency'),
        InlineKeyboardButton("Назад", callback_data='earn_new_clients'),
    )
    log.info(f"telegram_id {telegram_id}")
    log.info(f"{MAIN_TELEGRAM_ID}")
    log.info(f"telegram_id = MAIN_TELEGRAM_ID{telegram_id == MAIN_TELEGRAM_ID}")

    await bot.send_message(
        message.chat.id,
        f"Добро пожаловать, мистер администратор!",
        reply_markup=keyboard
    )

async def get_payout_balance(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_payout_balance от {telegram_id}")

    get_payout_balance_url = SERVER_URL + "/payout_balance"

    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        response = await send_request(
            get_payout_balance_url,
            method="POST",
            json={}
        )
        log.info(f"response {response}")

        if response["status"] == "success":
            data = response["data"]
            total_balance = data["total_balance"]
            total_extra = data["total_extra"]
            num_of_users = data["num_of_users"]
            num_of_users_plus_30 = data["num_of_users_plus_30"]
            result = data["result"]
            users = data["users"]
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Назад", callback_data='start'),
            )
            report = (
                f"<b>Отчёт:</b>\n\n"
                f"Общий баланс: {total_balance}\n"
                f"Общий процент: {total_extra}\n"
                f"Число пользователей: {num_of_users}\n"
                f"Общая сумма +30 рублей за каждого пользователя: {num_of_users_plus_30}\n"
                f"Итого: {result}"
            )
            await bot.send_message(
                chat_id=message.chat.id,
                text=report,
                parse_mode=ParseMode.HTML
            )
            log.info(f"response data {data}")
            if users:
                log.info(f"users {users}")
                for user in users:
                    log.info(f"users перебор начался")
                    user_info = (
                        f"<b>Telegram ID:</b> {user['id']}\n"
                        f"<b>Пользователь:</b> {user['name']}\n"
                        f"<b>Количество привлечённых рефералов:</b> {user['paid_referrals']}\n\n"
                    )
                    log.info(f"user_info {user_info}")
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=user_info,
                        parse_mode=ParseMode.HTML
                    )
            await bot.send_message(
                message.chat.id,
                f"Что-нибудь ещё?",
                reply_markup=keyboard
            )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def get_promo_users_frequency(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_promo_users_frequency от {telegram_id}")

    get_promo_users_frequency_url = SERVER_URL + "/get_promo_users_frequency"

    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        response = await send_request(
            get_promo_users_frequency_url,
            method="POST",
            json={"message": "hey"}
        )
        log.info(f"response {response}")

        if response["status"] == "success":
            data = response["data"]
            promo_users = data["promo_users_frequency"]
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Назад", callback_data='admin'),
            )
            log.info(f"response data {response}")
            if promo_users:
                log.info(f"users {promo_users}")
                await bot.send_message(
                    chat_id=message.chat.id,
                    text="Список промокодеров по датам:"
                )
                for user in promo_users:
                    log.info(f"promo_users перебор начался")
                    
                    user_info = f"{user['date']}\t{user['promo_users_count']}"
                    log.info(f"user_info {user_info}")
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=user_info,
                        parse_mode=ParseMode.HTML
                    )
            await bot.send_message(
                message.chat.id,
                f"Что-нибудь ещё?",
                reply_markup=keyboard
            )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def get_payments_frequency(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_payments_frequency от {telegram_id}")

    get_payments_frequency_url = SERVER_URL + "/get_payments_frequency"

    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        response = await send_request(
            get_payments_frequency_url,
            method="POST",
            json={"message": "hey"}
        )
        log.info(f"response {response}")

        if response["status"] == "success":
            data = response["data"]
            payments_frequency = data["payments_frequency"]
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Назад", callback_data='admin'),
            )
            log.info(f"response data {response}")
            if payments_frequency:
                log.info(f"payments_frequency {payments_frequency}")
                await bot.send_message(
                    chat_id=message.chat.id,
                    text="Список оплат по датам:"
                )
                for payment in payments_frequency:
                    log.info(f"promo_users перебор начался")
                    
                    payments_info = f"{payment['date']}\t{payment['payments_count']}"
                    log.info(f"payments_info {payments_info}")
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=payments_info,
                        parse_mode=ParseMode.HTML
                    )
            await bot.send_message(
                message.chat.id,
                f"Что-нибудь ещё?",
                reply_markup=keyboard
            )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def type_promo(message: types.Message, telegram_id: str, u_name: str = None):
    await bot.send_message(
        chat_id=message.chat.id,
        text="Введите промокод без пробелов:"
    )

async def handle_promo_input(message: types.Message):
    promo_code = message.text.strip()
    log.info("Введённый промокод")
    if str(promo_code) == str(PROMO_CODE):
        log.info("Верный промокод")
        register_user_with_promo_url = SERVER_URL + "/register_user_with_promo"
        telegram_id = message.from_user.id
        user_data = {"telegram_id": telegram_id}
        response = await send_request(
            register_user_with_promo_url,
            method="POST",
            json=user_data
        )
        if response["status"] == "error":
            text = response["message"]
            await bot.send_message(
                chat_id=message.chat.id,
                text=text
            )

async def generate_report(message: types.Message, telegram_id: str, u_name: str = None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Общая информация 🌍", callback_data='report_overview'),
        InlineKeyboardButton("Список привлечённых клиентов 👨‍👩‍👧‍👦", callback_data='report_clients'),
        InlineKeyboardButton("Назад", callback_data='earn_new_clients')
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text="Какой отчёт вы хотите сформировать?",
        reply_markup=keyboard
    )

async def get_tax_info(message: types.Message, telegram_id: str, u_name: str = None):
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=TAX_INFO_IMG_URL,
        caption="Реферальные выплаты могут облагаться налогом. Рекомендуем зарегистрироваться как самозанятый."
    )
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='earn_new_clients')
    )

    info_text = """
    <b>Как зарегистрироваться и выбрать вид деятельности для уплаты налогов:</b>

    1. Информацию о способах регистрации и не только вы можете найти на официальном сайте <a href="https://npd.nalog.ru/app/">npd.nalog.ru/app</a>.
    
    2. При выборе вида деятельности рекомендуем указать: «Реферальные выплаты» или «Услуги».

    <i>Пока вы платите налоги, вы защищаете себя и делаете реферальные выплаты законными.</i>
    """
    await bot.send_message(
        chat_id=message.chat.id,
        text=info_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )
