from loader import *
from utils import test_questions, log
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# Словарь для хранения ответов пользователей
user_answers = {}
# Словарь для хранения информации о прохождении теста
user_test_info = {}
# Планировщик задач
scheduler = AsyncIOScheduler()

def get_question_keyboard(question_id):
    question_data = test_questions[question_id]
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, answer in enumerate(question_data["answers"]):
        keyboard.add(InlineKeyboardButton(answer, callback_data=f"test_{question_id}_{i}"))
    return keyboard

async def start_test(message: types.Message, telegram_id: str, u_name: str = None):
    now = datetime.now()

    # Проверяем, не прошло ли 7 дней с последнего теста
    if telegram_id in user_test_info:
        retry_time = user_test_info[telegram_id]["next_attempt"]
        if now < retry_time:
            await message.answer(f"Вы уже проходили тест. Повторно пройти можно {retry_time.strftime('%Y-%m-%d %H:%M:%S')} или позже.")
            return

    log.info(f"Пользователь {telegram_id} начал тест")
    user_answers[telegram_id] = {"answers": [], "current_question": 0}
    user_test_info[telegram_id] = {
        "start_time": now,
        # "next_attempt": now + timedelta(days=7)
        "next_attempt": now + timedelta(minutes=2)
    }

    # Запланировать завершение теста через 30 минут
    # scheduler.add_job(finish_test, 'date', run_date=now + timedelta(minutes=30), args=[message.chat.id, telegram_id])
    scheduler.add_job(finish_test, 'date', run_date=now + timedelta(minutes=1), args=[message.chat.id, telegram_id])
    await send_question(message.chat.id, telegram_id, 0)

async def send_question(chat_id, telegram_id, question_id):
    log.info(f"send_question вызвана")
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
    _, question_id, answer_id = callback_query.data.split("_")
    question_id, answer_id = int(question_id), int(answer_id)
    
    telegram_id = callback_query.from_user.id

    # Проверяем, не пытается ли пользователь ответить на предыдущий вопрос
    if question_id != user_answers[telegram_id]["current_question"]:
        return

    log.info(f"telegramId = {telegram_id}, question_id={question_id}, answer_id={answer_id}")

    user_answers[telegram_id]["answers"].append(answer_id)
    log.info("user_answers = {user_answers}")
    log.info(user_answers)
    
    await callback_query.bot.answer_callback_query(callback_query.id)
    await send_question(callback_query.message.chat.id, telegram_id, question_id + 1)

async def finish_test(chat_id, telegram_id):
    if telegram_id not in user_answers:
        return
    
    log.info(f"finish_test called")
    correct_count = sum(
        1 for i, ans in enumerate(user_answers[telegram_id]["answers"])
        if ans == test_questions[i]["correct"]
    )
    log.info(f"correct_count = {correct_count}")
    
    text = f"Тест завершён!\nВаш результат: {correct_count}/{len(test_questions)}"
    log.info(f"text = {text}")
    await bot.send_message(chat_id, text)
    # Удаляем данные через 7 дней
    # scheduler.add_job(lambda: user_test_info.pop(telegram_id, None), 'date', run_date=datetime.now() + timedelta(days=7))
    # scheduler.add_job(lambda: user_answers.pop(telegram_id, None), 'date', run_date=datetime.now() + timedelta(days=7))
    scheduler.add_job(lambda: user_test_info.pop(telegram_id, None), 'date', run_date=datetime.now() + timedelta(minutes=2))
    scheduler.add_job(lambda: user_answers.pop(telegram_id, None), 'date', run_date=datetime.now() + timedelta(minutes=2))