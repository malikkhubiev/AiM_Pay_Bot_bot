from utils import log
import os
import io
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
    GROUP_ID,
)
import aiohttp
import asyncio
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
    
    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={username} нажал кнопку /start"
    )

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
                    # InlineKeyboardButton("Оплатить курс 💰", callback_data='pay_course'),
                    InlineKeyboardButton("Оплатить курс 💰", callback_data='fake_buy_course'),
                )
            
            if response["to_show"] == "trial":
                keyboard.add(
                    InlineKeyboardButton("Пробный период 24 часа 🌌", callback_data='get_trial')
                )

            # Промокодеры упразднены
            # if response["with_promo"] == True:
            #     keyboard.add(
            #         InlineKeyboardButton("Ввести промокод 🎩", callback_data='type_promo'),
            #     )
            

            # Ссылка упразднена
            # else:
            #     keyboard.add(
            #         InlineKeyboardButton("Получить ссылку", callback_data='get_invite_link'),
            #     )
            
            # С рефералом
            # info_text = response["response_message"] + "\n\n💎Мы очень рады тебя видеть!💎\n\nОПЛАТИ КУРС, получи ЗНАНИЯ и ЗАРАБОТАЙ, советуя друзьям КАЧЕСТВЕННЫЙ ПРОДУКТ."
            
            # Без
            info_text = response["response_message"] + "\n\n💎Мы очень рады тебя видеть!💎\n\nОПЛАТИ КУРС, получи ЗНАНИЯ, построй свои стартапы и добавляй проекты в портфолио.\n\nСомневаешься, что курс тебе подходит? Нажми на кнопку и получи бесплатный пробный период для ознакомления СО ВСЕМИ материалами курса."
            
            keyboard.add(
                InlineKeyboardButton("Получить сертфикат 🎓", callback_data='get_certificate'),
                InlineKeyboardButton("Подробнее о курсе 🔬", callback_data='more_about_course'),
                # InlineKeyboardButton("Заработать на новых клиентах 💸", callback_data='earn_new_clients')
            )
            await bot.send_video(
                chat_id=message.chat.id,
                video=START_VIDEO_URL,
                caption=info_text,
                reply_markup=keyboard
            )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def getting_started(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /getting_started от {telegram_id}")

    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={u_name} нажал кнопку /getting started"
    )

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

        # Промокодеры упразднены
        # if response["with_promo"] == True:
        #     keyboard.add(
        #         InlineKeyboardButton("Ввести промокод 🎩", callback_data='type_promo'),
        #     )

        keyboard.add(
            # InlineKeyboardButton("Оплатить курс 💰", callback_data='pay_course'),
            InlineKeyboardButton("Оплатить курс 💰", callback_data='fake_buy_course'),
            InlineKeyboardButton("Пробный период 24 часа 🌌", callback_data='get_trial'),
            InlineKeyboardButton("Получить сертфикат 🎓", callback_data='get_certificate'),
            InlineKeyboardButton("Подробнее о курсе 🔬", callback_data='more_about_course'),
            # InlineKeyboardButton("Заработать, советуя друзьям 💸", callback_data='earn_new_clients')
        )
        await bot.send_video(
            chat_id=message.chat.id,
            video=START_VIDEO_URL,
            caption="💎Мы очень рады тебя видеть!💎\n\nОПЛАТИ КУРС, получи ЗНАНИЯ, построй свои стартапы и добавляй проекты в портфолио.\n\nСомневаешься, что курс тебе подходит? Нажми на кнопку и получи бесплатный пробный период для ознакомления СО ВСЕМИ материалами курса.",
            reply_markup=keyboard
        )
    elif response["status"] == "error":
        await message.answer(response["message"])

async def get_documents(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_documents от {telegram_id}")
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Публичная оферта 📗", callback_data='public_offer'),
        InlineKeyboardButton("Политика Конфиденциальности 📙", callback_data='privacy_policy'),
        InlineKeyboardButton("Назад", callback_data='start'),
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text="Внимательно прочитайте следующие документы.",
        reply_markup=keyboard
    )

async def more_about_course(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /more_about_course от {telegram_id}")

    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={u_name} нажал кнопку /more_about_course"
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Структура курса", callback_data='course_structure'),
        InlineKeyboardButton("Назад", callback_data='start'),
    )

    message1 = """
    💎 <b>Мгновенное погружение в машинное обучение и построение нейросетей</b> 💎
    Ты начинаешь разбираться <b>в мире аналитики данных</b>? Этот курс создан для <b>новичков</b>, которые хотят быстро освоить Python и библиотеки работы с данными, <b>машинным обучением и построением нейросетей</b>.

    🧠 <b>Что ты получишь?</b>
    Мы даём <b>тонну практики и простых аналогий</b>, чтобы ты понял теорию на лету, начал писать код, постоянно закрепляя пройденный материал. Темы объясняются через <b>примеры из жизни</b>, сложные концепции объясняются <b>простым языком</b>.

🔮 <b>Дополнительно ты получишь:</b>
    <b>Красивые графические материалы</b> в виде роадмэпов — разноцветные схемы и пошаговые инструкции, которые помогут тебе <b>ориентироваться в различных этапах</b> построения моделей машинного обучения. Эти материалы будут твоими <b>визуальными шпаргалками</b>. 
    
    💸 <b>Реферальная программа — заработай, советуя друзьям!:</b>
    Пригласи друзей на курс. Приведи <b>3 друзей</b> — <b>за каждого ты получишь по 2000 рублей</b>. Это твой шанс полностью окупить курс и начать <b>зарабатывать на рекомендациях</b>!

🔥 <b>Начни прямо сейчас:</b>
    Чем <b>раньше начнёшь</b>, тем раньше окажешься в мире новых технологии и открывающихся возможностей. <b>Не откладывай:</b> этот курс — твой быстрый старт в мире аналитики данных, машинного обучения и нейросетей.

    🎂 <b>Максимум пользы:</b>
    После прохождения курса ты можешь продолжать развиваться. Мы даём ссылки на <b>бесплатные курсы</b> и <b>дополнительные материалы</b>, чтобы ты извлёк <b>максимальную пользу</b> и развивался без ограничений)
    
Посмотри краткий <a href="https://drive.google.com/file/d/1esKuOAHOBAXiLXYiZFyoPoFlSHCRIQdT/view?usp=sharing">Обзор курса</a>, а если хочешь подробнее, нажми на кнопку ниже
    """

    await bot.send_message(
        chat_id=message.chat.id,
        text=message1,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )

async def course_structure(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /course_structure от {telegram_id}")

    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={u_name} нажал кнопку /course_structure"
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='start'),
    )

    message1 = """
    <b>1. Python — твой новый инструмент для работы с данными</b>
    - Мы начнем с <a href="https://drive.google.com/file/d/1AhFOQzWrh_MtWn37zBQaavtafDrTPRY1/view?usp=sharing">основ Python</a>: переменные, циклы, функции — всё, что нужно для дальнейшей работы с библиотеками. Ты увидишь, что язык программирования — это не сложные закорючки, а <b>логический инструмент</b>, которым ты будешь управлять легко и уверенно.

    <b>2. Работа с данными и числами</b>
    - <a href="https://drive.google.com/file/d/1BOzNNFSB1AluKH65gdpbetMSVVYiMZ8Y/view?usp=sharing">numpy</a> — это библиотека, которая ускоряет обработку чисел. Представь, что у тебя в руках супермощный калькулятор, который мгновенно справляется с большими объемами данных.
    - <a href="https://drive.google.com/file/d/1XHsVm35lQrkCt1R__0HQe0-TyDjw8g2y/view?usp=sharing">pandas</a> — библиотека для работы с таблицами. Это твой новый помощник для обработки и анализа данных: ты сможешь фильтровать, сортировать и преобразовывать данные буквально в несколько строк кода.
    
    <b>3. Визуализация данных</b>
    - <a href="https://drive.google.com/file/d/1_N56NcItsRq8v5kZ7rkiQKxCVuuSBI_C/view?usp=sharing">matplotlib</a> и <a href="https://drive.google.com/file/d/19xlbqr4TGdQXW91Pb8FOH8va35cn2wfA/view?usp=sharing">seaborn</a> помогут тебе создавать красивые и информативные графики. Эти библиотеки откроют для тебя мир визуализации, где ты сможешь наглядно представлять свои данные и находить скрытые закономерности.
    - <a href="https://drive.google.com/file/d/1mF0XfrdPPQ5EUAg_CvHVbfhHuobCpeVS/view?usp=sharing">plotly</a> — инструмент для создания <b>интерактивных графиков</b>, которые можно использовать для динамических презентаций или анализа данных в реальном времени. Ты сможешь визуализировать сложные процессы и превращать их в понятные и наглядные отчёты.

    <b>4. Машинное обучение: прогнозируй будущее</b>
    - <a href="https://drive.google.com/file/d/1gvdoXCaDHvqQgsrpYHfdCb8SIX042EGi/view?usp=sharing">scikit-learn</a> — твой первый шаг в мир прогнозирования. Эта библиотека поможет тебе строить модели машинного обучения для прогнозирования цен, анализа маркетинговых данных, финансовых показателей и даже медицинских прогнозов. Мы научим тебя не только строить модели, но и объясним каждый шаг процесса — от подготовки данных до анализа ошибок. Всего мы разберём 15 шагов построения модели. 
    """

    message2 = """
    <b>5. Нейросети: глубокое обучение с Keras</b>
    - <a href="https://drive.google.com/file/d/1TGS4iKxVjmlESsVZs_DoAYKKo7-yD3Re/view?usp=sharing">keras</a> — библиотека для работы с нейросетями и второй по важности инструмент. Даже если ты совсем не знаком с нейросетями, мы начнем с самых простых примеров и постепенно погрузим тебя в более сложные многослойные архитектуры. Ты научишься строить сети для анализа как числовых так и графических данных.

    <b>6. Обработка текстов (NLP)</b>
    - <a href="https://drive.google.com/file/d/1fvRdWG-XNJB8h6ItdxmH2_6STcF8x7we/view?usp=sharing">spacy</a> и <a href="https://drive.google.com/file/d/1fvRdWG-XNJB8h6ItdxmH2_6STcF8x7we/view?usp=sharing">transformers</a> — библиотеки для работы с текстами. Изучим только основы: покажем как анализировать текст, извлекать ключевую информацию, производить синтаксический анализ. 

    <b>7. Компьютерное зрение</b>
    - <a href="https://drive.google.com/file/d/1p2Fy8S8QO12ZEUhYPdDQrb-EzpgZMMh_/view?usp=sharing">OpenCV</a> — основа компьютерного зрения. Очень поверхностно пройдёмся по части её функций, связанных с обработкой имеющихся изображений. 
    
    <b>8. SQL: работа с базами данных</b>
    - <a href="https://drive.google.com/file/d/13hQAQ3mQ138u28WvIMzHMzDoMqRjFeOc/view?usp=sharing">SQL</a> — третий по важности инструмент, предназначенный для работы с базами данных. Мы научим тебя строить запросы, извлекать информацию и комбинировать данные для качественного анализа. Мы используем этот инструмент для <b>извлечения данных</b> из связанных и несвязанных таблиц базы данных, который ты сможешь использовать как в аналитике, так и в машинном обучении.
    
<b>Хочешь попробовать - Присоединяйся</b>! 
    """

    await bot.send_message(text=message1, parse_mode='HTML', chat_id=message.chat.id)
    await bot.send_message(
        chat_id=message.chat.id,
        text=message2,
        parse_mode=ParseMode.HTML,
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
    await message.answer(f"Проверка регистрации...")
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
        await message.answer(f"Проверка пройдена! Построение ссылки для оплаты...")
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
        InlineKeyboardButton("Напечатать список в боте", callback_data='report_list_as_is'),
        InlineKeyboardButton("Напечатать список в Excel-таблице", callback_data='report_list_as_file'),
        InlineKeyboardButton("Построить график оплат рефералов", callback_data='request_referral_chart'),
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
    elif response["status"] == "error":
        await message.answer(response["message"])

async def report_list_as_is(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"report_list_as_is")
    generate_clients_report_list_as_is_url = SERVER_URL + "/generate_clients_report_list_as_is"
    user_data = {"telegram_id": telegram_id}

    log.info(f"telegram_id {telegram_id}")
    log.info(f"generate_clients_report_list_as_is_url {generate_clients_report_list_as_is_url}")
    log.info(f"user_data {user_data}")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='earn_new_clients')
    )

    response = await send_request(
        generate_clients_report_list_as_is_url,
        method="POST",
        json=user_data
    )

    if response["status"] == "success":
        invited_list = response.get("invited_list")

        # Send the list of invited users
        if invited_list:
            log.info(f"invited_list {invited_list}")
            for invited in invited_list:
                log.info(f"invited_list invited перебор начался")
                user_info = (
                    f"<b>Пользователь:</b> {invited['username']}\n"
                    f"<b>Telegram ID:</b> {invited['telegram_id']}\n"
                    f"<b>Дата и время первого входа в бота:</b> {invited['start_working_date']}\n"
                    f"<b>Дата и время оплаты курса:</b> {invited['payment_date']}\n"
                    f"<b>Время от первого входа до оплаты:</b> {invited['time_for_pay']}\n"
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

async def report_list_as_file(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"report_list_as_file вызван для {telegram_id}")
    url = SERVER_URL + "/generate_clients_report_list_as_file"
    user_data = {"telegram_id": telegram_id}

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Назад", callback_data="earn_new_clients"))

    response = await send_request(url, method="POST", json=user_data)

    # 1️⃣ Проверяем, что сервер не вернул ошибку
    if isinstance(response, dict):
        log.error(f"Ошибка при генерации отчёта: {response}")
        await message.answer(response.get("message", "Ошибка при генерации отчёта"), reply_markup=keyboard)
        return

    # 2️⃣ Используем BytesIO для работы с файлом в памяти
    try:
        file_stream = io.BytesIO(response)  # response — это бинарные данные (файл)
        file_stream.name = "clients_report.xlsx"  # Telegram требует имя файла

        # 3️⃣ Отправляем файл пользователю
        await bot.send_document(
            message.chat.id,
            InputFile(file_stream),
            reply_markup=keyboard
        )

    except Exception as e:
        log.error(f"Ошибка при отправке файла: {e}")
        await message.answer("Ошибка при отправке отчёта", reply_markup=keyboard)

async def request_referral_chart(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"inside request_referral_chart")
    url = f"{SERVER_URL}/generate_referral_chart_link"
    payload = {"telegram_id": telegram_id}
    log.info(f"payload {payload}")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='earn_new_clients')
    )

    response = await send_request(
        url,
        method="POST",
        json=payload
    )

    log.info(f"response {response}")

    if response["status"] == "success":
        data = response.get("data")
        chart_url = data.get("chart_url")
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Ваш график доступен по ссылке:\n\n{chart_url}",
            reply_markup=keyboard
        )
    elif response["status"] == "error":
        await bot.send_message(
            chat_id=message.chat.id,
            text=response["message"],
            reply_markup=keyboard
        )

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
            InlineKeyboardButton("Админ 👑", callback_data='admin'),
        )

    keyboard.add(
        InlineKeyboardButton("Список лидеров 🤴", callback_data='get_top_referrers'),
        InlineKeyboardButton("Привязать/изменить карту 💎", callback_data='bind_card'),
        InlineKeyboardButton("Получить реферальную ссылку 🚀", callback_data='get_referral'),
        InlineKeyboardButton("Сформировать отчёт о заработке 🏰", callback_data='generate_report'),
        InlineKeyboardButton("Налоги 🏫", callback_data='tax_info'),
        InlineKeyboardButton("Документы 📚", callback_data='documents'),
        InlineKeyboardButton("Назад", callback_data='start'),
    )

    await bot.send_video(
        chat_id=message.chat.id,
        video=EARN_NEW_CLIENTS_VIDEO_URL,
        caption=f"💸Курс стоит {COURSE_AMOUNT} рублей.💸\n- За каждого друга, который купил курс, ты заработаешь {REFERRAL_AMOUNT} рублей.\n- Приведи 3-х таких друзей и отбей стоимость курса.\n- Начиная с 4-го друга, ты начнёшь зарабатывать."
    )
    await bot.send_message(
        message.chat.id,
        f"Твои друзья обычно сидят:\n- в чатах по изучению программирования 👩‍💻\n- в тг-группах российских ВУЗов 🏤.\n\nТы выйдешь на ПРИБЫЛЬ в {float(REFERRAL_AMOUNT)*50} рублей после приглашения 50 друзей.🌍\n\nДружить - это полезно 🍯 \n\nПеред тем как начать, ещё раз внимательно прочитай документы на всякий случай. 📚",
        reply_markup=keyboard
    )

async def admin(message: types.Message, telegram_id: str, u_name: str = None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Мультипликаторы 🏛", callback_data='get_source_referral_stats'),
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
                f"Число рефереров: {num_of_users}\n"
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
                        f"<b>Пользователь:</b> {user['name']}\n\n"
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
            number_of_promo = data["number_of_promo"]
            promo_num_left = data["promo_num_left"]
            promo_users = data["promo_users_frequency"]
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Назад", callback_data='admin'),
            )
            log.info(f"response data {response}")
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"Количество свободных промокодов: {promo_num_left}\nКоличество пользователей по промокоду: {number_of_promo}"
            )
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

async def get_source_referral_stats(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /get_source_referral_stats от {telegram_id}")

    url = SERVER_URL + "/get_multiplicators"

    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        response = await send_request(
            url,
            method="POST",
            json={"telegram_id": telegram_id}
        )
        log.info(f"response {response}")

        if response["status"] == "success":
            result = response.get("result", {})
            source_stats = result.get("source_stats", [])
            referral_stats = result.get("referral_stats", [])
            log.info(f"source_stats {source_stats}")
            log.info(f"referral_stats {referral_stats}")

            # Формирование отчета по источникам
            source_report = "Отчет по источникам:\n\n"
            if source_stats:
                for source in source_stats:
                    source_report += f"- Источник: {source.get('Источник', 'Неизвестно')}\n"
                    source_report += f"- Всего: {source.get('Всего', 0)}\n"
                    source_report += f"- Зарегистрировались: {source.get('Зарегистрировались', 0)}\n"
                    source_report += f"- Процент регистраций: {source.get('% Регистраций', '0.0')}%\n"
                    source_report += f"- Оплатили: {source.get('Оплатили', 0)}\n"
                    source_report += f"- Процент оплат от всех: {source.get('% Оплат от всех', '0.0')}%\n"
                    source_report += f"- Процент оплат от зарегистрированных: {source.get('% Оплат от зарегистрированных', '0.0')}%\n"
                    source_report += "\n"  # Разделение для следующего источника
            else:
                source_report += "Нет данных по источникам.\n"
            # Формирование отчета по рефералам
            referral_report = "Отчет по рефералам:\n\n"

            if referral_stats:
                for referral in referral_stats:
                    referrer_id = referral.get('Реферер ID', 'Неизвестно')
                    referred = referral.get('Пришло по рефералке', 0)
                    registered = referral.get('Зарегистрировались', 0)
                    registration_percentage = referral.get('% Регистраций', '0.0')
                    paid = referral.get('Оплатили', 0)
                    paid_percentage = referral.get('% Оплат от всех', '0.0')
                    paid_registration_percentage = referral.get('% Оплат от зарегистрированных', '0.0')

                    referral_report += f"- Реферер ID: {referrer_id}\n"
                    referral_report += f"- Пришло по рефералке: {referred}\n"
                    referral_report += f"- Зарегистрировались: {registered}\n"
                    referral_report += f"- Процент регистраций: {registration_percentage}%\n"
                    referral_report += f"- Оплатили: {paid}\n"
                    referral_report += f"- Процент оплат от всех: {paid_percentage}%\n"
                    referral_report += f"- Процент оплат от зарегистрированных: {paid_registration_percentage}%\n"
                    referral_report += "\n"  # Разделение для следующего реферала
            else:
                referral_report += "Нет данных по рефералам.\n"
            # Кнопка "Назад"
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("Назад", callback_data='admin'))

            log.info(f"Before source_report {source_report}")
            log.info(f"Before referral_report {referral_report}")

            # Отправка отчёта по источникам
            if source_report:
                source_parts = [source_report[i:i+4000] for i in range(0, len(source_report), 4000)]
                for part in source_parts:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=part,
                        parse_mode="HTML",
                        reply_markup=keyboard if part == source_parts[-1] else None
                    )
                    await asyncio.sleep(1)

            # Отправка отчёта по рефералам
            if referral_report:
                referral_parts = [referral_report[i:i+4000] for i in range(0, len(referral_report), 4000)]
                for part in referral_parts:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=part,
                        parse_mode="HTML",
                        reply_markup=keyboard if part == referral_parts[-1] else None
                    )

            elif response["status"] == "error":
                await message.answer(response.get("message", "Произошла ошибка при получении отчёта."))
    else:
        await message.answer("У вас нет доступа к этой команде.")

async def type_promo(message: types.Message, telegram_id: str, u_name: str = None):
    await bot.send_message(
        chat_id=message.chat.id,
        text="Введите промокод без пробелов:"
    )

# Промокодеры упразднены
# async def handle_promo_input(message: types.Message, telegram_id: str, u_name: str = None):
#     promo_code = message.text.strip()
#     log.info("Введённый промокод")
#     if str(promo_code) == str(PROMO_CODE):
#         log.info("Верный промокод")
#         register_user_with_promo_url = SERVER_URL + "/register_user_with_promo"
#         telegram_id = message.from_user.id
#         user_data = {"telegram_id": telegram_id}
#         response = await send_request(
#             register_user_with_promo_url,
#             method="POST",
#             json=user_data
#         )
#         if response["status"] == "error":
#             text = response["message"]
#             await bot.send_message(
#                 chat_id=message.chat.id,
#                 text=text
#             )

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

async def get_certificate(message: types.Message, telegram_id: str, u_name: str = None):
    log.info("get_certificate called")

    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={u_name} нажал кнопку /get_certificate"
    )

    await bot.send_message(
        chat_id=message.chat.id,
        text="Получаем информацию о сертификации..."
    )

    url = SERVER_URL + "/can_get_certificate"
    user_data = {"telegram_id": telegram_id}

    response = await send_request(
        url,
        method="POST",
        json=user_data
    )
    if response["status"] == "success":
        if response["result"] == "test":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Сдать тест", callback_data='start_test'),
                InlineKeyboardButton("Назад", callback_data='earn_new_clients')
            )

            info_text = """
Для получения сертификата вы пройдёте тест, состоящий из 25 вопросов.
    - Длительность теста 30 минут.
    - Для успешного прохождения теста необходимо ответить правильно на 80 и более процентов вопросов.
    - Для подготовки к тесту рекомендуем изучить все видеоуроки, а также дополнительные материалы, хранящиеся в General.
    - Пересдать тест можно через 3 дня после начала прохождения.
    - Нажмите на кнопку, если уверены в своей подготовке.
Желаем успехов!
            """
        elif response["result"] == "passed":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Скачать сертификат", callback_data='download_certificate'),
                InlineKeyboardButton("Сгенерировать ссылку", callback_data='generate_certificate_link'),
                InlineKeyboardButton("Назад", callback_data='start')
            )

            info_text = """
Ваш тест на получение сертификата был успешно пройден!
Вы можете скачать сертификат в формате PDF или перейти на страницу просмотра сертификата.
Поздравляем 🎉)
            """
        
        await bot.send_message(
            chat_id=message.chat.id,
            text=info_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    elif response["status"] == "error":
        text = response["message"]
        await bot.send_message(
            chat_id=message.chat.id,
            text=text
        )  

async def save_fio(message: types.Message, telegram_id: str, u_name: str = None):
    
    log.info("save_fio called")

    fio_input = message.text.strip()
    fio_value = fio_input.replace("ФИО: ", "").strip()
    if not fio_value.strip():
        await bot.send_message(
            chat_id=message.chat.id,
            text="ФИО не может быть пустым"
        )
        return

    save_fio_url = SERVER_URL + "/save_fio"
    user_data = {
        "telegram_id": telegram_id,
        "fio": fio_value,
    }
    response = await send_request(
        save_fio_url,
        method="POST",
        json=user_data
    )
    if response["status"] == "success":
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("Скачать сертификат", callback_data='download_certificate'),
            InlineKeyboardButton("Сгенерировать ссылку", callback_data='generate_certificate_link'),
            InlineKeyboardButton("Назад", callback_data='start')
        )
        text = response["data"]["message"]
        await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
    elif response["status"] == "error":
        text = response["message"]
        await bot.send_message(
            chat_id=message.chat.id,
            text=text
        )

async def get_top_referrers(message: types.Message, telegram_id: str, u_name: str = None):
    
    log.info("get_top_referrers called")

    url = SERVER_URL + "/get_top_referrers"
    user_data = {
        "telegram_id": telegram_id
    }
    response = await send_request(
        url,
        method="POST",
        json=user_data
    )
    if response["status"] == "success":
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("Назад", callback_data='earn_new_clients')
        )
        text = response["top"]
        await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
    elif response["status"] == "error":
        text = response["message"]
        await bot.send_message(
            chat_id=message.chat.id,
            text=text
        )

async def download_certificate(message: types.Message, telegram_id: str, u_name: str = None):
    
    log.info("download_certificate called")

    await bot.send_message(
        chat_id=message.chat.id,
        text="Обрабатываем запрос на генерацию сертификата..."
    )

    url = SERVER_URL + "/generate_certificate"
    user_data = {"telegram_id": telegram_id}

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Назад", callback_data="start"))

    response = await send_request(url, method="POST", json=user_data)

    # 1️⃣ Проверяем, что сервер не вернул ошибку
    if isinstance(response, dict):
        if response["status"] == "error":
            text = response["message"]
            await bot.send_message(
                chat_id=message.chat.id,
                text=text
            )
            return

    # 2️⃣ Создаём BytesIO и задаём имя файла
    try:
        file_stream = io.BytesIO(response)  
        file_stream.name = "certificate.pdf"  # Telegram требует имя файла

        # 3️⃣ Отправляем файл пользователю
        await message.answer_document(
            InputFile(file_stream, filename="certificate.pdf"),
            reply_markup=keyboard
        )

    except Exception as e:
        log.error(f"Ошибка при отправке сертификата: {e}")
        await message.answer("Ошибка при отправке сертификата", reply_markup=keyboard)

async def generate_certificate_link(message: types.Message, telegram_id: str, u_name: str = None):
    
    log.info("generate_certificate_link called")

    await bot.send_message(
        chat_id=message.chat.id,
        text="Обрабатываем запрос на генерацию ссылки..."
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Назад", callback_data="start"))

    text = f"Вы можете посмотреть сертификат по следующей ссылке: {SERVER_URL}/certifications?cert_id={telegram_id}"

    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=keyboard
    )

async def get_trial(message: types.Message, telegram_id: str, u_name: str = None):
    
    log.info("get_trial called")
    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={u_name} нажал кнопку /get_trial"
    )

    url = SERVER_URL + "/start_trial"
    user_data = {"telegram_id": telegram_id}

    response = await send_request(url, method="POST", json=user_data)

    if response["status"] == "error":
        text = response["message"]
        await bot.send_message(
            chat_id=message.chat.id,
            text=text
        )

async def fake_buy_course(message: types.Message, telegram_id: str, u_name: str = None):
    
    log.info("fake_buy_course called")

    await bot.send_message(
        chat_id=str(MAIN_TELEGRAM_ID),
        text=f"Пользователь telegram_id={telegram_id} username={u_name} нажал кнопку /fake_buy_course"
    )

    get_price_url = SERVER_URL + "/get_payment_data"
    user_data = {"telegram_id": telegram_id}
    response = await send_request(
        get_price_url,
        method="POST",
        json=user_data
    )
    price = response["price"]
    card_number = response["card_number"]

    text = (
    f"Для оплаты курса необходимо выполнить банковский перевод на номер карты:\n"
    f"**{card_number}**\n\n"
    f"**Сумма перевода:** {price} рублей\n\n"
    "*Будьте очень внимательны, так как возврат денежных средств не предусмотрен.\n\n"
    "После завершения перевода отправьте боту скриншот, подтверждающий успешную оплату.\n"
    "При успешной оплате, вы получите пригласительную ссылку в группу в течение 24 часов."
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=text
    )

async def handle_photo(message: Message, telegram_id: str, u_name: str = None):
    """
    Получает фото от пользователя и пересылает его на заданный Telegram ID.
    """
    log.info(f"Получена фотография от пользователя: {telegram_id}")

    try:
        # Получаем ID последней версии фото (наивысшее качество)
        photo_id = message.photo[-1].file_id
        caption = f"{telegram_id}"

        # Пересылаем изображение определённому пользователю
        await bot.send_photo(chat_id=MAIN_TELEGRAM_ID, photo=photo_id, caption=caption)
        
        log.info(f"Фото успешно отправлено админу с ID: {MAIN_TELEGRAM_ID}")
    
    except Exception as e:
        log.error(f"Ошибка при отправке фото админу: {e}")


async def handle_fake_payment_command(message: types.Message, telegram_id: str, u_name: str = None):
    """
    Обработчик команды добавления пользователя в группу.
    """
    log.info(f"handle_fake_payment_command called by {telegram_id}")
    log.info(f"telegram_id {telegram_id}")
    log.info(f"MAIN_TELEGRAM_ID {MAIN_TELEGRAM_ID}")

    # Проверяем, что это именно админ отправил команду
    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        log.info(f"main tg id")
        
        add_input = message.text.strip()
        log.info(f"add_input {add_input}")

        new_user_id = add_input.replace("Добавить: ", "").strip()
        log.info(f"new_user_id {new_user_id}")

        if not new_user_id.strip():
            await bot.send_message(
                chat_id=message.chat.id,
                text="TG id не может быть пустым"
            )
            return
        
        fake_payment_url = SERVER_URL + "/fake_payment"
        user_data = {"telegram_id": new_user_id}
        response = await send_request(
            fake_payment_url,
            method="POST",
            json=user_data
        )
        if response["status"] == "success":
            text = "Добавлен"
            await bot.send_message(
                chat_id=message.chat.id,
                text=text
            )
        elif response["status"] == "error":
            text = response["message"]
            await bot.send_message(
                chat_id=message.chat.id,
                text=text
            )

BLACKLIST = set()

async def ban_user_by_id(message: types.Message, telegram_id: str, u_name: str = None):
    """
    Обработчик команды блокировки пользователя.
    """
    log.info(f"ban_user_by_id called by {MAIN_TELEGRAM_ID} = {telegram_id}")

    # Проверяем, что это именно админ отправил команду
    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        log.info(f"main tg id")
        
        id_input = message.text.strip()
        log.info(f"id_input {id_input}")

        tg_id = id_input.replace("Блокировать: ", "").strip()
        log.info(f"tg_id {tg_id}")

        if not tg_id.strip():
            await bot.send_message(
                chat_id=message.chat.id,
                text="TG id не может быть пустым"
            )
            return

        log.info(f"message.chat.id {message.chat.id}")
        log.info(f"tg_id {tg_id}")
        
        BLACKLIST.add(str(tg_id))
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Заблокирован. Актуальный список {BLACKLIST}"
        )

async def unban_user_by_id(message: types.Message, telegram_id: str, u_name: str = None):
    """
    Обработчик команды разблокировки пользователя.
    """
    log.info(f"unban_user_by_id called by {MAIN_TELEGRAM_ID} = {telegram_id}")

    # Проверяем, что это именно админ отправил команду
    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        log.info(f"main tg id")
        
        id_input = message.text.strip()
        log.info(f"id_input {id_input}")

        tg_id = id_input.replace("Разблокировать: ", "").strip()
        log.info(f"tg_id {tg_id}")

        if not tg_id.strip():
            await bot.send_message(
                chat_id=message.chat.id,
                text="TG id не может быть пустым"
            )
            return
        
        BLACKLIST.remove(str(tg_id))
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Разблокирован. Актуальный список {BLACKLIST}"
        )

async def kick_user_by_id(message: types.Message, telegram_id: str, u_name: str = None):
    """
    Обработчик команды исключения пользователя из группы.
    """
    log.info(f"kick_user_by_id called by {MAIN_TELEGRAM_ID} = {telegram_id}")

    # Проверяем, что это именно админ отправил команду
    if str(telegram_id) == str(MAIN_TELEGRAM_ID):
        log.info(f"main tg id")
        
        id_input = message.text.strip()
        log.info(f"id_input {id_input}")

        tg_id = id_input.replace("Выгнать: ", "").strip()
        log.info(f"tg_id {tg_id}")

        if not tg_id.strip():
            await bot.send_message(
                chat_id=message.chat.id,
                text="TG id не может быть пустым"
            )
            return
        
        await bot.kick_chat_member(chat_id=GROUP_ID, user_id=tg_id)
        await bot.unban_chat_member(chat_id=GROUP_ID, user_id=tg_id)
        text = "Выгнал"
        await bot.send_message(
            chat_id=message.chat.id,
            text=text
        )
            