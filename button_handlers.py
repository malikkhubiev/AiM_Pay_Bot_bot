from handlers import *
from test_handlers import *
from utils import *

# Список хэндлеров
callback_handlers = {
    "start": start,
    "getting_started": getting_started,
    "more_about_course": more_about_course,
    "course_structure": course_structure,
    "type_promo": type_promo,
    "admin": admin,
    "get_payments_frequency": get_payments_frequency,
    "get_promo_users_frequency": get_promo_users_frequency,
    "get_payout_balance": get_payout_balance,
    "documents": get_documents,
    "public_offer": get_public_offer,
    "privacy_policy": get_privacy_policy,
    "pay_course": handle_pay_command,
    "earn_new_clients": earn_new_clients,
    # "get_invite_link": send_invite_link,
    "get_referral": send_referral_link,
    "bind_card": bind_card,
    "generate_report": generate_clients_report,
    "report_list_as_is": report_list_as_is,
    "report_list_as_file": report_list_as_file,
    "request_referral_chart": request_referral_chart,
    "tax_info": get_tax_info,
    "pass_test": pass_test,  # Добавляем тест в список хэндлеров
    "start_test": start_test,  # Добавляем тест в список хэндлеров
    "download_certificate": download_certificate
}

# Универсальная функция-обработчик
async def universal_callback_handler(callback_query: types.CallbackQuery):
    await callback_query.bot.answer_callback_query(callback_query.id)
    handler_func = callback_handlers.get(callback_query.data)
    if handler_func:
        await handler_func(callback_query.message, callback_query.from_user.id, callback_query.from_user.username)

# Регистрация универсального обработчика и хэндлера ввода текста
def register_callback_handlers(dp: Dispatcher):
    dp.callback_query_handler(lambda c: c.data.startswith("test_"))(handle_test_answer)  # Обработка ответов теста
    
    dp.callback_query_handler()(universal_callback_handler)
    dp.message_handler()(handle_promo_input)

    dp.register_message_handler(save_fio, lambda message: message.text.startswith("ФИО: "))