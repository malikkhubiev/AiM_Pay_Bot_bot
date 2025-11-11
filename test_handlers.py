from loader import *
from config import (
    SERVER_URL
)
from utils import test_questions, log, send_request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# Словарь для хранения ответов пользователей
user_answers = {}
# Словарь для хранения информации о прохождении теста
user_test_info = {}
# Планировщик задач
scheduler = AsyncIOScheduler()

TEST_DURATION = timedelta(minutes=30)
RETRY_TIMEOUT = timedelta(days=3)

def get_question_keyboard(question_id):
    question_data = test_questions[question_id]
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, answer in enumerate(question_data["answers"]):
        keyboard.add(InlineKeyboardButton(answer, callback_data=f"test_{question_id}_{i}"))
    return keyboard

async def start_test(message: types.Message, telegram_id: str, u_name: str = None):
    now = datetime.now()

    # Проверяем статус пользователя через API
    try:
        from utils import send_request
        from config import SERVER_URL
        url = SERVER_URL + "/can_get_certificate"
        user_data = {"telegram_id": telegram_id}
        response = await send_request(url, method="POST", json=user_data)
        
        # Если тест сдан, но ФИО не указано - запрашиваем ФИО
        if response.get("status") == "success" and response.get("result") == "need_fio":
            text = response.get("message", "Вы не установили своё ФИО для получения сертификата. Введите ФИО в формате: 'ФИО: Иванов Иван Иванович'. Будьте аккуратны в написании, исправить ФИО невозможно. Дата установки ФИО считается датой формирования сертификата.")
            await message.answer(text)
            return
        
        # Если тест уже сдан и ФИО указано - показываем сообщение о возможности получить сертификат
        if response.get("status") == "success" and response.get("result") == "passed":
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("Скачать сертификат", callback_data='download_certificate'),
                InlineKeyboardButton("Сгенерировать ссылку", callback_data='generate_certificate_link'),
                InlineKeyboardButton("Назад", callback_data='start')
            )
            await message.answer(
                "Ваш тест на получение сертификата был успешно пройден!\nВы можете скачать сертификат в формате PDF или перейти на страницу просмотра сертификата.\nПоздравляем 🎉)",
                reply_markup=keyboard
            )
            return
    except Exception as e:
        log.error(f"Ошибка при проверке статуса сертификата: {e}")

    # Проверяем, не прошло ли 3 дня с последнего теста
    if telegram_id in user_test_info and now < user_test_info[telegram_id]["next_attempt"]:
        retry_time = user_test_info[telegram_id]["next_attempt"].strftime('%Y-%m-%d %H:%M:%S')
        await message.answer(f"Вы уже проходили тест. Повторно пройти можно {retry_time} UTC (Лондон) или позже.")
        return

    log.info(f"Пользователь {telegram_id} начал тест")

    user_answers[telegram_id] = {"answers": [], "current_question": 0}
    user_test_info[telegram_id] = {
        "start_time": now,
        "next_attempt": now + RETRY_TIMEOUT
    }

    log.info(f"Время истечения {now + timedelta(minutes=1)}")

    await send_question(message.chat.id, telegram_id, 0)

async def send_question(chat_id, telegram_id, question_id):
    log.info(f"send_question вызвана")
    if telegram_id not in user_answers:
        return
    
    if question_id >= len(test_questions):
        log.info(f"Вопросы закончились. Финиш")
        await finish_test(chat_id, telegram_id)
        return
    
    log.info(f"Игра продолжается")
    question_data = test_questions[question_id]
    log.info(f"question_data = {question_data}")
    log.info(question_data)
    text = f"{question_id + 1}/{len(test_questions)}: {question_data['question']}"
    log.info(f"text = {text}")
    keyboard = get_question_keyboard(question_id)
    
    user_answers[telegram_id]["current_question"] = question_id  # Обновляем текущий вопрос
    await bot.send_message(chat_id, text, reply_markup=keyboard)

async def handle_test_answer(callback_query: types.CallbackQuery):
    try:
        _, qid, aid = callback_query.data.split("_")
        question_id, answer_id = int(qid), int(aid)
    except Exception as e:
        log.error(f"Ошибка в парсинге callback: {e}")
        return

    telegram_id = callback_query.from_user.id
    now = datetime.now()

    # Проверяем, есть ли telegram_id в user_answers
    if telegram_id not in user_answers:
        await callback_query.answer("Тест ещё не начат или время истекло.", show_alert=True)
        return

    start_time = user_test_info[telegram_id]["start_time"]
    if now > start_time + TEST_DURATION:
        await callback_query.answer("Время вышло. Тест завершён.", show_alert=True)
        await bot.send_message(callback_query.message.chat.id, "Время теста истекло. Попробуйте снова позже.")
        user_answers.pop(telegram_id, None)
        user_test_info.pop(telegram_id, None)
        return

    # Проверяем, не пытается ли пользователь ответить на предыдущий вопрос
    if question_id != user_answers[telegram_id]["current_question"]:
        return

    log.info(f"telegramId = {telegram_id}, question_id={question_id}, answer_id={answer_id}")

    user_answers[telegram_id]["answers"].append(answer_id)
    log.info(f"user_answers = {user_answers}")

    await callback_query.answer()
    await send_question(callback_query.message.chat.id, telegram_id, question_id + 1)

async def finish_test(chat_id, telegram_id):
    if telegram_id not in user_answers:
        return
    
    log.info(f"finish_test called")
    answers = user_answers[telegram_id]["answers"]
    correct_count = sum(1 for i, ans in enumerate(answers) if ans == test_questions[i]["correct"])
    total_questions = len(test_questions)
    log.info(f"correct_count = {correct_count} total_questions = {total_questions}")
    
    text = f"Тест завершён!\nВаш результат: {correct_count}/{len(test_questions)}."
    log.info(f"text = {text}")
    await bot.send_message(chat_id, text)
    log.info(f"баллы набраны = {correct_count} из {len(test_questions)} = {correct_count / len(test_questions)}")

    if (correct_count / len(test_questions)) >= 0.8:
        log.info("passed")
        url = SERVER_URL + "/update_passed_exam"
        user_data = {
            "telegram_id": telegram_id
        }
        response = await send_request(
            url,
            method="POST",
            json=user_data
        )
        if response["status"] == "success":
            text = "Введите ФИО в формате: 'ФИО: Иванов Иван Иванович'. Будьте аккуратны в написании, исправить ФИО невозможно. Дата установки ФИО считается датой формирования сертификата."
            await bot.send_message(chat_id, text)
        elif response["status"] == "error":
            text = response["message"]
            await bot.send_message(chat_id, text)

    # Чистим данные через 30 секунд
    cleanup_time = datetime.now() + TEST_DURATION
    scheduler.add_job(lambda: user_answers.pop(telegram_id, None), 'date', run_date=cleanup_time)
    scheduler.add_job(lambda: user_test_info.pop(telegram_id, None), 'date', run_date=cleanup_time)