from utils import log
import math
import os
import io
from config import (
    COURSE_AMOUNT,
    REFERRAL_AMOUNT,
    SERVER_URL,
    LANDING_URL,
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
from utils import *
from loader import *
import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ContentType
import re

# Кэш для хранения ссылок
links_cache = {}

# ЕДИНАЯ СИСТЕМА СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЕЙ
# Структура: {telegram_id: "waiting_fio" | "waiting_email" | "waiting_card" | None}
user_states = {}
# Состояния:
# - "waiting_fio" - ожидается ввод ФИО
# - "waiting_email" - ожидается ввод email
# - "waiting_card" - ожидается ввод номера карты
# - None или отсутствие ключа - нет активного состояния

# In-memory временное хранилище email-flow для каждого пользователя (telegram_id)
user_payment_email_flow = {}
# Структура: {telegram_id: {"email": str, "status": "waiting_confirm"/"confirmed"}}

# Функция для инициализации словаря кэша, если его ещё нет
def init_user_cache(telegram_id: str):
    if telegram_id not in links_cache:
        links_cache[telegram_id] = {
            'invite_link': None,
            'referral_link': None
        }

# ОБРАБОТЧИК СОСТОЯНИЙ С МАКСИМАЛЬНЫМ ПРИОРИТЕТОМ
# Должен быть зарегистрирован ПЕРВЫМ, до всех остальных обработчиков
@dp.message_handler(content_types=ContentType.TEXT)
async def handle_user_state(message: types.Message):
    """Обрабатывает текстовые сообщения на основе состояния пользователя. Имеет максимальный приоритет."""
    telegram_id = str(message.from_user.id)
    message_text = message.text.strip() if message.text else ""
    
    # ПРОПУСКАЕМ КОМАНДЫ (начинающиеся с /)
    if message_text.startswith('/'):
        log.info(f"handle_user_state: пропускаем команду '{message_text}'")
        return  # Пропускаем команды, чтобы их обработали другие обработчики
    
    # ПОДРОБНОЕ ЛОГИРОВАНИЕ
    log.info(f"=== handle_user_state вызван ===")
    log.info(f"Пользователь: {telegram_id}")
    log.info(f"Текст сообщения: '{message_text}'")
    log.info(f"Текущие состояния всех пользователей: {user_states}")
    log.info(f"Состояние этого пользователя: {user_states.get(telegram_id)}")
    log.info(f"user_payment_email_flow для этого пользователя: {user_payment_email_flow.get(telegram_id)}")
    
    state = user_states.get(telegram_id)
    
    # Если состояние не установлено, пропускаем дальше (не останавливаем обработку)
    if not state:
        log.info(f"Состояние не установлено для {telegram_id}, пропускаем дальше к другим обработчикам")
        return  # Пропускаем дальше, чтобы другие обработчики могли обработать сообщение
    
    log.info(f"✅ ОБРАБОТКА СОСТОЯНИЯ '{state}' для пользователя {telegram_id}")
    
    # Обработка состояния ожидания ФИО
    if state == "waiting_fio":
        log.info(f"🔵 Обработка ввода ФИО для пользователя {telegram_id}")
        log.info(f"Полученный текст: '{message_text}'")
        
        # Убираем префикс "ФИО: " если есть, но берём любой текст
        fio_value = message_text.replace("ФИО: ", "").strip()
        
        log.info(f"ФИО после обработки: '{fio_value}'")
        
        # БЕЗ ВАЛИДАЦИИ - просто берём то, что прислали
        if not fio_value:
            log.warning(f"ФИО пустое, но всё равно отправляем на сервер")
            fio_value = message_text  # Если после обработки пусто, берём исходный текст
        
        log.info(f"Отправляем на сервер ФИО: '{fio_value}'")
        
        save_fio_url = SERVER_URL + "/save_fio"
        user_data = {
            "telegram_id": telegram_id,
            "fio": fio_value,
        }
        log.info(f"Данные для отправки: {user_data}")
        
        response = await send_request(
            save_fio_url,
            method="POST",
            json=user_data
        )
        
        log.info(f"Ответ сервера: {response}")
        
        if response.get("status") == "success":
            # Сбрасываем состояние только при успехе
            user_states[telegram_id] = None
            log.info(f"✅ Состояние 'waiting_fio' сброшено для пользователя {telegram_id}")
            
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Скачать сертификат", callback_data='download_certificate'),
                InlineKeyboardButton("Сгенерировать ссылку", callback_data='generate_certificate_link'),
                InlineKeyboardButton("Назад", callback_data='start')
            )
            text = response.get("data", {}).get("message", "ФИО успешно сохранено")
            await message.answer(
                text=text,
                reply_markup=keyboard
            )
            log.info(f"✅ ФИО успешно сохранено для пользователя {telegram_id}")
        else:
            text = response.get("message", "Ошибка при сохранении ФИО")
            await message.answer(text)
            log.error(f"❌ Ошибка при сохранении ФИО: {text}")
            # Не сбрасываем состояние при ошибке, чтобы пользователь мог попробовать снова
        
        log.info(f"=== Завершение обработки состояния waiting_fio ===")
        raise CancelHandler()  # Останавливаем дальнейшую обработку в любом случае
    
    # Обработка состояния ожидания email
    elif state == "waiting_email":
        log.info(f"Обработка ввода email для пользователя {telegram_id}")
        await handle_email_input(message)
        # Состояние сбрасывается внутри handle_email_input после успешной обработки
        raise CancelHandler()  # Останавливаем дальнейшую обработку
    
    # Обработка состояния ожидания номера карты
    elif state == "waiting_card":
        log.info(f"Обработка ввода карты для пользователя {telegram_id}")
        # handle_card_input обрабатывает валидацию и отправку на сервер
        # Если валидация не прошла или произошла ошибка, функция делает return раньше
        # и состояние не сбрасывается, чтобы пользователь мог попробовать снова
        await handle_card_input(message)
        # Если мы дошли сюда без исключений, значит обработка прошла успешно
        # (handle_card_input делает return при ошибках, поэтому если мы здесь - значит успех)
        user_states[telegram_id] = None
        log.info(f"Состояние 'waiting_card' сброшено для пользователя {telegram_id}")
        raise CancelHandler()  # Останавливаем дальнейшую обработку

@dp.message_handler(commands=['start'])
async def start(message: types.Message, telegram_id: str = None, username: str = None):
    log.info(f"Получена команда /start от {telegram_id}")
    
    if not(telegram_id):
        telegram_id = message.from_user.id
    if not(username):
        username = message.from_user.username or message.from_user.first_name
    
    # Сбрасываем все состояния при возврате в главное меню
    telegram_id_str = str(telegram_id)
    if telegram_id_str in user_states:
        user_states[telegram_id_str] = None
        log.info(f"Все состояния сброшены для пользователя {telegram_id_str} при возврате в главное меню")

    if telegram_id != str(MAIN_TELEGRAM_ID):
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
        # Переходим к основному меню как для зарегистрированного пользователя
        response["type"] = "user"
        response["response_message"] = f"Добро пожаловать, {username}!"

        if response["type"] == "user":
            log.info("type = user")
            log.info(f"response['to_show'] = {response['to_show']}")
            can_show_cert = None
            if response["to_show"] == "pay_course":
                can_show_cert = False
                keyboard.add(
                    InlineKeyboardButton("Оплатить курс 💖", callback_data='fake_buy_course'),
                )
            elif response["to_show"] == "paid":
                can_show_cert = True
            info_text = response["response_message"] + "\n\n💎Мы очень рады тебя видеть!💎\n\nЧто внутри курса:\n- 300+ видео-уроков С ГОТОВЫМ КОДОМ БЕЗ МАТЕМАТИКИ\n- Твоя первая модель и нейросеть С НУЛЯ, УЖЕ СЕГОДНЯ\n- СТИЛЬНЫЙ СЕРТИФИКАТ после сдачи теста\n\nЖдём тебя внутри, чтобы сэкономить твоё время и дать тебе практику как можно быстрее)" 
            # Проверяем оплаченный статус, чтобы показать кнопку сертификата только оплаченным
            try:
                cu_resp = await send_request(
                    SERVER_URL + "/check_user",
                    method="POST",
                    json={"telegram_id": str(telegram_id), "to_throw": False}
                )
                user_obj = cu_resp.get("user") if isinstance(cu_resp, dict) else None
                paid_flag = (user_obj or {}).get("paid") if isinstance(user_obj, dict) else getattr(user_obj, 'paid', False)
                can_show_cert = bool(paid_flag)
            except Exception as e:
                log.error(f"Ошибка проверки статуса оплаты: {e}")

            # Основные кнопки
            keyboard.add(
                InlineKeyboardButton("Заработать на новых клиентах 💸", callback_data='earn_new_clients')
            )

            # Убрать
            can_show_cert = True
            if can_show_cert:
                keyboard.add(InlineKeyboardButton("Получить сертфикат 🎓", callback_data='get_certificate'))
            keyboard.add(InlineKeyboardButton("Подробнее о курсе 🔬", callback_data='more_about_course'))
            await bot.send_video(
                chat_id=message.chat.id,
                video=START_VIDEO_URL,
                caption=info_text,
                reply_markup=keyboard
            )
    elif response["status"] == "error":
        await message.answer(response["message"])

# Handle contact to save referral phone
@dp.message_handler(content_types=ContentType.CONTACT)
async def handle_contact(message: types.Message):
    try:
        contact = message.contact
        telegram_id = str(message.from_user.id)
        phone = contact.phone_number
        payload = {"telegram_id": telegram_id, "phone": phone}
        resp = await send_request(SERVER_URL + "/save_referral_phone", method="POST", json=payload)
        if isinstance(resp, dict) and resp.get("status") == "success":
            await bot.send_message(
                chat_id=message.chat.id,
                text="Спасибо! Номер сохранён. Вы участвуете в реферальной программе.",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"Ошибка сохранения номера: {resp.get('message','') if isinstance(resp, dict) else 'сервер не ответил'}",
                reply_markup=types.ReplyKeyboardRemove()
            )
    except Exception as e:
        await bot.send_message(chat_id=message.chat.id, text=f"Ошибка обработки номера: {e}")

async def more_about_course(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Получена команда /more_about_course от {telegram_id}")

    if telegram_id != str(MAIN_TELEGRAM_ID):
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

    if telegram_id != str(MAIN_TELEGRAM_ID):
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
            json=payment_data
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
    # Упрощенный механизм: просто просим пользователя написать номер карты
    telegram_id_str = str(telegram_id)  # Убеждаемся, что это строка
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Отмена", callback_data='earn_new_clients')
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text="💳 Пожалуйста, напишите номер вашей банковской карты для получения выплат.\n\nФормат: 16 цифр без пробелов (например: 1234567890123456)",
        reply_markup=keyboard
    )
    # Устанавливаем состояние ожидания номера карты
    user_states[telegram_id_str] = "waiting_card"
    log.info(f"Установлено состояние 'waiting_card' для пользователя {telegram_id_str}")

# Старый функционал с созданием ссылки - закомментирован
# async def bind_card(message: types.Message, telegram_id: str, u_name: str = None):
#     bind_card_url = SERVER_URL + "/bind_card"
#     user_data = {"telegram_id": telegram_id}
#     response = await send_request(
#         bind_card_url,
#         method="POST",
#         json=user_data
#     )
#     if response["status"] == "success":
#         binding_url = response["binding_url"]
#         log.info(f"binding_url {binding_url}")
#         keyboard = InlineKeyboardMarkup(row_width=1)
#         keyboard.add(
#             InlineKeyboardButton("Назад", callback_data='earn_new_clients')
#         )
#         text = ""
#         if binding_url:
#             text = f"Перейдите по следующей ссылке для привязки карты: {binding_url}"
#         else:
#             text = "Ошибка при генерации ссылки."
#         await bot.send_message(
#             chat_id=message.chat.id,
#             text=text,
#             reply_markup=keyboard
#         )
#     elif response["status"] == "error":
#         await message.answer(response["message"])
#         return

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

    # Проверяем, привязана ли карта
    check_card_url = SERVER_URL + "/check_card"
    card_response = await send_request(
        check_card_url,
        method="POST",
        json={"telegram_id": telegram_id}
    )
    has_card = card_response.get("status") == "success" and card_response.get("has_card", False)

    # По-умолчанию
    keyboard.add(
        InlineKeyboardButton("Привязать/изменить карту 💎", callback_data='bind_card'),
    )
    # Если привязана карта
    if has_card:
        keyboard.add(
            InlineKeyboardButton("Получить реферальную ссылку 🚀", callback_data='get_referral'),
            InlineKeyboardButton("Сформировать отчёт о заработке 🏰", callback_data='generate_report'),
            InlineKeyboardButton("Список лидеров 🤴", callback_data='get_top_referrers'),
        )
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data='start')
    )

    price = int(COURSE_AMOUNT)
    refka = int(REFERRAL_AMOUNT)

    await bot.send_video(
        chat_id=message.chat.id,
        video=EARN_NEW_CLIENTS_VIDEO_URL,
        caption=f"💸Курс стоит {COURSE_AMOUNT} рублей.💸\n- За каждого друга, который купил курс, ты заработаешь {REFERRAL_AMOUNT} рублей.\n- Приведи {math.ceil(price/refka)}-х таких друзей и отбей стоимость курса."
    )
    await bot.send_message(
        message.chat.id,
        f"Твои друзья обычно сидят:\n- в чатах по изучению программирования 👩‍💻\n- в тг-группах российских ВУЗов 🏤.\n\nТы выйдешь на ПРИБЫЛЬ в {float(REFERRAL_AMOUNT)*50} рублей после приглашения 50 друзей.🌍\n\nДружить - это полезно 🍯",
        reply_markup=keyboard
    )

async def admin(message: types.Message, telegram_id: str, u_name: str = None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Мультипликаторы 🏛", callback_data='get_source_referral_stats'),
        InlineKeyboardButton("Информация о выплатах 💳", callback_data='get_payout_balance'),
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
                    log.info(f"payments_frequency перебор начался")
                    
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

    if telegram_id != str(MAIN_TELEGRAM_ID):
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
            await bot.send_message(
                chat_id=message.chat.id,
                text=info_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        elif response["result"] == "need_fio":
            # Тест сдан, но ФИО не указано - запрашиваем ФИО
            log.info(f"=== get_certificate: need_fio ===")
            log.info(f"Пользователь: {telegram_id}")
            log.info(f"Текущие состояния ДО установки: {user_states}")
            
            text = response.get("message", "Вы не установили своё ФИО для получения сертификата. Введите ФИО (например: Иванов Иван Иванович). Будьте аккуратны в написании, исправить ФИО невозможно. Дата установки ФИО считается датой формирования сертификата.")
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton("Назад", callback_data='start'))
            await bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard
            )
            
            # Устанавливаем состояние ожидания ФИО
            telegram_id_str = str(telegram_id)
            user_states[telegram_id_str] = "waiting_fio"
            log.info(f"✅ УСТАНОВЛЕНО состояние 'waiting_fio' для пользователя {telegram_id_str}")
            log.info(f"Текущие состояния ПОСЛЕ установки: {user_states}")
            log.info(f"Состояние пользователя {telegram_id_str}: {user_states.get(telegram_id_str)}")
            log.info(f"=== get_certificate: need_fio завершено ===")
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
    # Поддерживаем оба формата: с префиксом "ФИО: " и без него
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
        # Состояние уже сброшено в handle_user_state
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
    if telegram_id != str(MAIN_TELEGRAM_ID):
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

    if telegram_id != str(MAIN_TELEGRAM_ID):
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
    email = response["email"]

    text = (
    f"💳 Стоимость курса по машинному обучению = {price} рублей\n\n"
    "💌 Ваша электронная почта: {email}\n"
    "✅ При успешной оплате, на указанную почту вы получите пригласительную ссылку"
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=text
    )

# async def handle_photo(message: Message, telegram_id: str, u_name: str = None):
#     """
#     Получает фото от пользователя и пересылает его на заданный Telegram ID.
#     """
#     log.info(f"Получена фотография от пользователя: {telegram_id}")

#     try:
#         # Получаем ID последней версии фото (наивысшее качество)
#         photo_id = message.photo[-1].file_id
#         # Пересылаем изображение определённому пользователю
#         await bot.send_photo(chat_id=MAIN_TELEGRAM_ID, photo=photo_id)
#         await bot.send_message(
#             chat_id=message.chat.id,
#             text=f"Добавить: {telegram_id}"
#         )

#         log.info(f"Фото успешно отправлено админу с ID: {MAIN_TELEGRAM_ID}")
    
#     except Exception as e:
#         log.error(f"Ошибка при отправке фото админу: {e}")


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
            

@dp.callback_query_handler(lambda c: c.data == 'fake_buy_course')
async def callback_fake_buy_course(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    # Проверим, есть ли подтвержденный email (запрошен и подтвержден ранее)
    response = await send_request(
        SERVER_URL + "/get_pay_email",
        method="POST",
        json={"telegram_id": telegram_id}
    )
    pay_email = response.get('email')
    if not pay_email:
        # Если email не сохранён, просим ввести email
        user_states[telegram_id] = "waiting_email"
        log.info(f"Установлено состояние 'waiting_email' для пользователя {telegram_id}")
        await call.message.answer(
            "Напишите email, куда мы отправим одноразовую пригласительную ссылку на материалы курса и чек об успешной оплате. Будьте внимательны"
        )
        # Сбрасываем инлайн-клаву
        await call.answer()
        return
    # Если email уже есть, показываем данные + кнопки Оплатить/Изменить почту
    await show_payment_prompt(call.message, telegram_id, pay_email)
    await call.answer()

# Функция обработки ввода номера карты (вызывается из handle_user_state)
async def handle_card_input(message: types.Message):
    telegram_id = str(message.from_user.id)
    log.info(f"Обработка ввода карты для пользователя {telegram_id}")
    
    card_number = message.text.strip().replace(' ', '').replace('-', '')
    log.info(f"Получен номер карты: {card_number[:4]}****{card_number[-4:] if len(card_number) >= 4 else ''}")
    
    # Валидация номера карты (должно быть 16 цифр)
    if not card_number.isdigit() or len(card_number) != 16:
        await message.answer("❌ Номер карты должен содержать 16 цифр. Пожалуйста, введите номер карты ещё раз (например: 1234567890123456)")
        return  # Не сбрасываем состояние, чтобы пользователь мог попробовать снова
    
    # Отправляем на сервер для сохранения
    server_resp = await send_request(
        SERVER_URL + "/set_card_number",
        method="POST",
        json={"telegram_id": telegram_id, "card_number": card_number}
    )
    
    if server_resp.get("status") != "success":
        await message.answer(f"❌ Ошибка: {server_resp.get('message', 'Не удалось сохранить номер карты')}")
        return  # Не сбрасываем состояние при ошибке
    
    # Состояние будет сброшено в handle_user_state после успешной обработки
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Назад", callback_data='earn_new_clients'))
    
    await message.answer(
        f"✅ Номер карты успешно сохранён!\n\n💳 Карта: ****{card_number[-4:]}\n\nТеперь вы можете получать выплаты по реферальной программе.",
        reply_markup=keyboard
    )

# Функция обработки ввода email (вызывается из handle_user_state)
async def handle_email_input(message: types.Message):
    telegram_id = str(message.from_user.id)
    email = message.text.strip()
    if not is_valid_email_local(email):
        await message.answer("Пожалуйста, введите корректный email (пример: name@domain.com)")
        return  # Не сбрасываем состояние, чтобы пользователь мог попробовать снова
    existing = user_payment_email_flow.get(telegram_id, {}).get("email")
    if existing == email:
        await message.answer("Этот email уже был введён. Введите другой или нажмите 'Изменить'.")
        return  # Не сбрасываем состояние
    # Валидация сервером
    server_resp = await send_request(
        SERVER_URL + "/set_pay_email",
        method="POST",
        json={"telegram_id": telegram_id, "email": email}
    )
    if server_resp.get("status") != "success":
        await message.answer(f"Ошибка: {server_resp.get('message', 'Не удалось сохранить email')}")
        return  # Не сбрасываем состояние при ошибке
    
    # Сохраняем email во временное хранилище для подтверждения
    user_payment_email_flow[telegram_id] = {"status": "waiting_confirm", "email": email}
    
    # Сбрасываем состояние ожидания email, так как теперь ждем подтверждения
    user_states[telegram_id] = None
    
    keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("Подтвердить ✅", callback_data='confirm_pay_email'),
        InlineKeyboardButton("Изменить 🧠", callback_data='change_pay_email'),
    )
    await message.answer(
        f"Вы указали email: {email}\nПроверьте, правильно ли написан email.\nТеперь выберите действие:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'confirm_pay_email')
async def confirm_pay_email(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)
    username = call.from_user.username or call.from_user.first_name
    email_data = user_payment_email_flow.get(telegram_id)
    if not email_data or 'email' not in email_data:
        await call.message.answer("Email не найден. Попробуйте ещё раз.")
        await call.answer()
        return
    email = email_data['email']
    # Сохраняем email на сервере с подтверждением
    await send_request(
        SERVER_URL + "/set_pay_email",
        method="POST",
        json={"telegram_id": telegram_id, "username": username, "email": email, "action_type": "confirmed"}
    )
    user_payment_email_flow[telegram_id] = {"status": "confirmed", "email": email}
    await show_payment_prompt(call.message, telegram_id, email)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'change_pay_email')
async def change_pay_email(call: types.CallbackQuery):
    telegram_id = str(call.from_user.id)

    resp = await send_request(
        SERVER_URL + "/is_paid",
        method="POST",
        json={"telegram_id": telegram_id}
    )
    if resp.get("paid") != True:
        user_states[telegram_id] = "waiting_email"
        log.info(f"Установлено состояние 'waiting_email' для пользователя {telegram_id}")
        await call.message.answer("Введите email ещё раз:")
        await call.answer()
    else:
        await call.message.answer("💌 Почта после оплаты не изменяется")
        await call.answer()

async def show_payment_prompt(message, telegram_id, email):
    # Получить актуальные данные о цене, карте и прочем
    get_price_url = SERVER_URL + "/get_payment_data"
    response = await send_request(
        get_price_url,
        method="POST",
        json={"telegram_id": telegram_id}
    )
    price = response.get("price", "-")
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Оплатить 💖", callback_data="actually_pay_for_course"))
    keyboard.add(InlineKeyboardButton("Изменить почту 💌", callback_data="change_pay_email"))
    keyboard.add(InlineKeyboardButton("Публичная оферта 🏦", callback_data='public_offer'))
    text1 = (
        f"💳 Стоимость курса по машинному обучению = {price} рублей\n"
        f"💌 Ваша электронная почта: {email}"
    )
    text2 = (
        f"🔥 Очень сильно рекомендуем СБП как САМЫЙ БЫСТРЫЙ и УДОБНЫЙ способ оплаты)\n"
        f"✅ При успешной оплате, на указанную почту вы получите пригласительную ссылку"
    )
    text3 = (
        f"🏦 Нажимая кнопку «Оплатить», вы подтверждаете, что ознакомлены и согласны с условиями публичной оферты"
    )
    await message.answer(text1)
    await message.answer(text2)
    await message.answer(text3, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'actually_pay_for_course')
async def actually_pay_for_course(call: types.CallbackQuery):
    log.info(f"actually_pay_for_course called")
    telegram_id = str(call.from_user.id)
    username = call.from_user.username or call.from_user.first_name
    log.info(f"telegram_id {telegram_id}, username {username}")
    # Вызываем handle_pay_command для выполнения полного flow оплаты
    await handle_pay_command(call.message, telegram_id, username)
    await call.answer()

def is_valid_email_local(email):
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email) is not None

# ОБЩИЙ ОБРАБОТЧИК-ЛОВУШКА ДЛЯ ВСЕХ НЕОБРАБОТАННЫХ ТЕКСТОВЫХ СООБЩЕНИЙ
# Регистрируется последним, чтобы поймать все сообщения, которые не обработались другими обработчиками
@dp.message_handler(content_types=ContentType.TEXT)
async def catch_all_messages(message: types.Message):
    """Ловушка для всех необработанных текстовых сообщений. Логирует для отладки."""
    telegram_id = str(message.from_user.id)
    message_text = message.text.strip() if message.text else ""
    
    # ПРОПУСКАЕМ КОМАНДЫ (начинающиеся с /)
    if message_text.startswith('/'):
        return  # Пропускаем команды
    
    log.warning(f"⚠️⚠️⚠️ CATCH_ALL_MESSAGES вызван ⚠️⚠️⚠️")
    log.warning(f"Это означает, что сообщение НЕ было обработано другими обработчиками!")
    log.warning(f"Пользователь: {telegram_id}")
    log.warning(f"Текст сообщения: '{message_text}'")
    log.warning(f"Текущие состояния всех пользователей: {user_states}")
    log.warning(f"Состояние этого пользователя: {user_states.get(telegram_id)}")
    log.warning(f"user_payment_email_flow для этого пользователя: {user_payment_email_flow.get(telegram_id)}")
    log.warning(f"⚠️⚠️⚠️ КОНЕЦ CATCH_ALL_MESSAGES ⚠️⚠️⚠️")
    
    # Если состояние установлено, но мы попали сюда - значит handle_user_state не обработал его
    # Это критическая ошибка - обрабатываем вручную
    state = user_states.get(telegram_id)
    if state:
        log.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Состояние '{state}' установлено, но handle_user_state не обработал сообщение!")
        log.error(f"Это означает, что handle_user_state либо не сработал, либо не обработал состояние правильно!")
        log.error(f"Попытка обработать состояние '{state}' вручную из catch_all")
        
        # Попытка обработать вручную
        if state == "waiting_fio":
            try:
                fio_value = message_text.replace("ФИО: ", "").strip() or message_text
                log.info(f"Отправляем на сервер ФИО: '{fio_value}'")
                
                save_fio_url = SERVER_URL + "/save_fio"
                user_data = {
                    "telegram_id": telegram_id,
                    "fio": fio_value,
                }
                log.info(f"Данные для отправки: {user_data}")
                
                response = await send_request(
                    save_fio_url,
                    method="POST",
                    json=user_data
                )
                
                log.info(f"Ответ сервера: {response}")
                
                if response.get("status") == "success":
                    user_states[telegram_id] = None
                    log.info(f"✅ Состояние 'waiting_fio' сброшено")
                    keyboard = InlineKeyboardMarkup(row_width=1)
                    keyboard.add(
                        InlineKeyboardButton("Скачать сертификат", callback_data='download_certificate'),
                        InlineKeyboardButton("Сгенерировать ссылку", callback_data='generate_certificate_link'),
                        InlineKeyboardButton("Назад", callback_data='start')
                    )
                    text = response.get("data", {}).get("message", "ФИО успешно сохранено")
                    await message.answer(text=text, reply_markup=keyboard)
                    log.info(f"✅ ФИО успешно обработано вручную из catch_all")
                else:
                    error_text = response.get("message", "Ошибка при сохранении ФИО")
                    await message.answer(error_text)
                    log.error(f"❌ Ошибка при сохранении ФИО: {error_text}")
            except Exception as e:
                log.error(f"❌ Ошибка при ручной обработке ФИО: {e}", exc_info=True)
    
    log.warning(f"⚠️⚠️⚠️ КОНЕЦ CATCH_ALL_MESSAGES ⚠️⚠️⚠️")
