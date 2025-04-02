from loader import *
from utils import test_questions, log

# Словарь для хранения ответов пользователей
user_answers = {}

def get_question_keyboard(question_id):
    question_data = test_questions[question_id]
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, answer in enumerate(question_data["answers"]):
        keyboard.add(InlineKeyboardButton(answer, callback_data=f"test_{question_id}_{i}"))
    return keyboard

async def start_test(message: types.Message, telegram_id: str, u_name: str = None):
    log.info(f"Пользователь {telegram_id} начал тест")
    user_answers[telegram_id] = []  # Обнуляем ответы пользователя
    await send_question(message.chat.id, telegram_id, 0)

async def send_question(chat_id, telegram_id, question_id):
    if question_id >= len(test_questions):
        await finish_test(chat_id, telegram_id)
        return
    
    question_data = test_questions[question_id]
    text = f"{question_id + 1}/{len(test_questions)}: {question_data['question']}"
    keyboard = get_question_keyboard(question_id)
    await bot.send_message(chat_id, text, reply_markup=keyboard)

async def handle_test_answer(callback_query: types.CallbackQuery):
    _, question_id, answer_id = callback_query.data.split("_")
    question_id, answer_id = int(question_id), int(answer_id)
    
    telegram_id = callback_query.from_user.id
    user_answers[telegram_id].append(answer_id)
    
    await callback_query.bot.answer_callback_query(callback_query.id)
    await send_question(callback_query.message.chat.id, telegram_id, question_id + 1)

async def finish_test(chat_id, telegram_id):
    correct_count = sum(
        1 for i, ans in enumerate(user_answers[telegram_id])
        if ans == test_questions[i]["correct"]
    )
    
    text = f"Тест завершён!\nВаш результат: {correct_count}/{len(test_questions)}"
    await bot.send_message(chat_id, text)