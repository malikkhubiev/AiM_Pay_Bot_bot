from handlers import *
from test_handlers import *
from utils import *
import datetime

# Список хэндлеров
callback_handlers = {
    "start": start,
    "more_about_course": more_about_course,
    "course_structure": course_structure,
    "admin": admin,
    "get_payments_frequency": get_payments_frequency,
    "get_payout_balance": get_payout_balance,
    "public_offer": get_public_offer,
    "privacy_policy": get_privacy_policy,
    "earn_new_clients": earn_new_clients,
    "get_referral": send_referral_link,
    "bind_card": bind_card,
    "generate_report": generate_clients_report,
    "get_source_referral_stats": get_source_referral_stats,
    "get_top_referrers": get_top_referrers,
    "report_list_as_is": report_list_as_is,
    "report_list_as_file": report_list_as_file,
    "request_referral_chart": request_referral_chart,
    "tax_info": get_tax_info,
    "get_certificate": get_certificate,
    "start_test": start_test,
    "generate_certificate_link": generate_certificate_link,
    "download_certificate": download_certificate,
    "get_trial": get_trial,
    "fake_buy_course": fake_buy_course,
    # "get_invite_link": send_invite_link,
}

# Универсальная функция-обработчик
async def universal_callback_handler(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    username = callback_query.from_user.username or callback_query.from_user.first_name
    
    if user_id in BLACKLIST:
        raise CancelHandler()

    await callback_query.bot.answer_callback_query(callback_query.id)
    handler_func = callback_handlers.get(callback_query.data)
    if handler_func:
        await handler_func(callback_query.message, callback_query.from_user.id, callback_query.from_user.username)

# Регистрация универсального обработчика и хэндлера ввода текста
def register_callback_handlers(dp: Dispatcher):
    dp.callback_query_handler(lambda c: c.data.startswith("test_"))(handle_test_answer)  # Обработка ответов теста
    
    dp.callback_query_handler()(universal_callback_handler)
    # Передаем telegram_id в обработчики через обертку

    # Обработчик номера карты уже зарегистрирован через декоратор @dp.message_handler в handlers.py

    dp.register_message_handler(lambda message: save_fio(message, message.from_user.id),
                                lambda message: message.text.startswith("ФИО: "))
    
    dp.register_message_handler(lambda message: handle_fake_payment_command(message, message.from_user.id),
                                lambda message: message.text.startswith("Добавить: "))
    
    dp.register_message_handler(lambda message: ban_user_by_id(message, message.from_user.id),
                                lambda message: message.text.startswith("Блокировать: "))
    
    dp.register_message_handler(lambda message: unban_user_by_id(message, message.from_user.id),
                                lambda message: message.text.startswith("Разблокировать: "))
    
    dp.register_message_handler(lambda message: kick_user_by_id(message, message.from_user.id),
                                lambda message: message.text.startswith("Выгнать: "))

    # Регистрация хэндлера для фотографий
    dp.register_message_handler(lambda message: handle_photo(message, message.from_user.id),
                                content_types=types.ContentType.PHOTO)
    
