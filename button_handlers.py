from handlers import *
from utils import *

# Список хэндлеров
callback_handlers = {
    "start": start,
    "getting_started": getting_started,
    "documents": get_documents,
    "public_offer": get_public_offer,
    "privacy_policy": get_privacy_policy,
    "pay_course": handle_pay_command,
    "earn_new_clients": earn_new_clients,
    "get_invite_link": send_invite_link,
    "get_referral": send_referral_link,
    "bind_card": bind_card,
    "generate_report": generate_report,
    "report_overview": generate_overview_report,
    "report_clients": generate_clients_report,
    "tax_info": get_tax_info,
}

# Универсальная функция-обработчик
async def universal_callback_handler(callback_query: types.CallbackQuery):
    await callback_query.bot.answer_callback_query(callback_query.id)
    handler_func = callback_handlers.get(callback_query.data)
    await handler_func(callback_query.message, callback_query.from_user.id, callback_query.from_user.username)  

# Регистрация универсального обработчика
def register_callback_handlers(dp: Dispatcher):
    dp.callback_query_handler()(universal_callback_handler)