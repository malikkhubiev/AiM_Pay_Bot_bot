from config import (
    SECRET_CODE
)
import logging as log
import httpx
from loader import *
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from time import time

log.basicConfig(level=log.DEBUG)
logger = log.getLogger(__name__)

async def send_request(url, method="GET", headers=None, **kwargs):
    if headers is None:
        headers = {}
    headers["X-Secret-Code"] = SECRET_CODE  # Добавляем заголовок

    async with httpx.AsyncClient() as client:
        try:
            # Выбор метода запроса
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, **kwargs)
            elif method.upper() == "GET":
                response = await client.get(url, headers=headers, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, **kwargs)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Проверяем статус ответа
            response.raise_for_status()  # Вызывает исключение для ошибок статуса

            # Проверяем Content-Type
            content_type = response.headers.get("Content-Type", "")

            if content_type.startswith("application/json"):
                return response.json()  # Возвращаем JSON-ответ
            elif content_type.startswith("application/vnd.openxmlformats"):
                return response.content  # Возвращаем бинарные данные (файл)
            elif content_type.startswith("application/pdf"):
                return response.content  # Возвращаем бинарные данные (файл PDF)
            else:
                logger.error(f"Неизвестный Content-Type: {content_type}")
                return {"status": "error", "message": "Сервер вернул данные неизвестного формата."}

        except httpx.RequestError as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return {"status": "error", "message": "Ошибка при подключении к серверу."}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP статус-код {e.response.status_code}: {e}")
            return {"status": "error", "message": f"Сервер вернул ошибку: {e.response.status_code}."}
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            return {"status": "error", "message": "Произошла ошибка."}

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit=1):
        super().__init__()
        self.rate_limit = rate_limit
        self.user_timestamps = {}

    async def on_pre_process_message(self, message: Message, data: dict):
        user_id = message.from_user.id
        current_time = time()

        if user_id not in self.user_timestamps:
            self.user_timestamps[user_id] = current_time
            return
        
        last_time = self.user_timestamps[user_id]
        if current_time - last_time < self.rate_limit:
            await message.answer("Слишком много запросов. Попробуйте позже.")
            raise CancelHandler()

        self.user_timestamps[user_id] = current_time

test_questions = [
    {
        "question": "За что отвечает коэффициент k в модели линейной регрессии y = kx + b?",
        "answers": ["Наклон", "Отступ", "Длина", "Смещение"],
        "correct": 0
    },
    {
        "question": "Среди данных встретилась строчка, в которой рост человека равен 300 метрам. Такое значение параметра является...",
        "answers": ["Нонсенс", "Шумом", "Выбросом", "Глюком"],
        "correct": 2
    },
    {
        "question": "В процесс очистки данных не входит удаление ...",
        "answers": ["Дубликатов", "Выбросов", "Предикторов", "Ошибок"],
        "correct": 2
    },
    {
        "question": "Между умом и возрастом обнаружили прямую зависимость, её ещё называют ...",
        "answers": ["Тенденцией", "Корреляцией", "Графиком", "Параметром"],
        "correct": 1
    },
    {
        "question": "Необходимо спрогнозировать цену на квартиру в новом районе. Больше всего цена зависит от количества комнат, затем от района, близости к метро и магазинам. Что является здесь целевой переменной?",
        "answers": ["Комнаты", "Район", "Метро", "Цена"],
        "correct": 3
    },
    {
        "question": "Чем больше тренируется спортсмен, тем меньше его вес. Какой вид корреляции между количеством тренировок и весом?",
        "answers": ["Обратная", "Прямая", "Ровная", "Гладкая"],
        "correct": 0
    },
    {
        "question": "Какой метод позволяет уменьшить размерность данных, сохраняя важную информацию",
        "answers": ["LDA", "DimReducer", "PCA", "InfoCut"],
        "correct": 2
    },
    {
        "question": "При подготовке к построению модели линейной регрессии, мы обнаружили, что между предикторами наблюдается сильная",
        "answers": ["Корреляция", "Предзагрузка", "Стагнация", "Эмиссия"],
        "correct": 0
    },
    {
        "question": "Когда среди предикторов есть переменная, имеющая значения огромных масштабов, мы должны применить",
        "answers": ["Искажение", "Приращение", "Смещение", "Стандартизацию"],
        "correct": 3
    },
    {
        "question": "Для того, чтобы преобразовать категориальную переменную 'Пол' в бинарные столбцы, мы будем использовать инструмент",
        "answers": ["BinaryCoder", "SplitMapper", "LabelExpander", "OneHotEncoder"],
        "correct": 3
    },
    {
        "question": "Для того, чтобы поделить данные на обучающую и тестовую выборки, мы используем функцию",
        "answers": ["split_data", "train_test_split", "data_cut", "sample_divide"],
        "correct": 1
    },
    {
        "question": "Для несбалансированных данных мы хотим применить метод, который сочетает в себе подходы андерсэмплинга (делаем меньше примеров там, где этих примеров много) и бустинга (объединяем несколько слабых моделей). Из нижеперечисленных выберем",
        "answers": ["BoostSampler", "EasyEnsemble", "ComboBoost", "MixBoost"],
        "correct": 1
    },
    {
        "question": "В задаче между признаками и целевой переменной есть прямая зависимость и датасет не содержит мультиколлинеарности. Простейшая модель, решающая такую задачу регрессии это ___ регрессия",
        "answers": ["Логистическая", "Линейная", "SVR", "MixBoost"],
        "correct": 1
    },
    {
        "question": "Для того, чтобы понять насколько хорошо модель линейной регрессии справилась с задачей, мы можем использовать метрику",
        "answers": ["RMSE", "ErrFit", "MSE", "LossSquare"],
        "correct": 2
    },
    {
        "question": "Для решения задачи регрессии, нам нужна модель, которая будет штрафовать данные за мультиколлинеарность, используя 2 переменные как одну, не удаляя их. Речь идёт о методе ...",
        "answers": ["Elastic", "DualFit", "SoftReg", "Ridge"],
        "correct": 3
    },
    {
        "question": "Полиномиальная регрессия крута, но мы решили выбрать модель, которая не ограничена заданной формой как полиномиальная регрессия, а изгибается так, как нужно в зависимости от текущей точки и наш выбор пал на ...",
        "answers": ["RBF SVR", "SplineNet", "FlexReg", "NonLinearSVR"],
        "correct": 0
    },
    {
        "question": "Решая задачу классификации нам потребовалась легко интерпретируемая модель, которую мы могли бы красиво визуализировать в виде иерархии. Конечно мы выберем ...",
        "answers": ["ClassViz", "LogicMap", "RuleTree", "DecisionTree"],
        "correct": 3
    },
    {
        "question": "Мы заранее знаем количество кластеров, все они однородны, имеют форму сфер. Лучшее что мы можем выбрать для задачи кластеризации это простая модель",
        "answers": ["Centroider", "MeanCluster", "SpheriSplit", "K-Means"],
        "correct": 3
    },
    {
        "question": "У нас небольшой объём данных и не знаем изначально количество кластеров. Плюс ко всему, хотим самую простую модель для этого случая. Мы выберем метод кластеризации ...",
        "answers": ["SimpleSplit", "Иерархический", "ClustStep", "TopDown"],
        "correct": 1
    },
    {
        "question": "Одного дерева нам недостаточно и мы решили собрать их вместе, собирая их решения для большей надёжности. Мы используем ...",
        "answers": ["RandomForest", "DeepTrees", "TreeBag", "Forester"],
        "correct": 0
    },
    {
        "question": "Нужен метод, использующий несколько слабых моделей, которые последовательно корректируют вес ошибочно классифицированных наблюдений, чтобы улучшить общую производительность и для классификации, и для регрессии. Нам определённо нужен",
        "answers": ["ErrorFixer", "BoostStep", "AdaBoost", "AdaFlow"],
        "correct": 2
    },
    {
        "question": "Один из самых мощных и популярных алгоритмов градиентного бустинга это ...",
        "answers": ["TreePower", "XGBoost", "BoostNet", "XTree"],
        "correct": 1
    },
    {
        "question": "Вы опоздали на занятии и услышали отрывок '... - последовательность шагов, где каждый шаг выполняет определенную функцию, и результаты одного шага передаются на вход следующему. Это может включать в себя предобработку данных, преобразование признаков и обучение модели.'. Вы сразу поняли, что тема занятия",
        "answers": ["ProcTrack", "StageMap", "Chainflow", "Pipeline"],
        "correct": 3
    },
    {
        "question": "Поделим данные на 5 групп (партов), будем обучать и тестировать модель на разных группах, чтобы оценить насколько хороша модель. Метод называется ...",
        "answers": ["Cross-validation", "SplitTest", "FoldEval", "TrainLoop"],
        "correct": 0
    },
    {
        "question": "Для диаграммы рассеяния используется метод plt. ...()",
        "answers": ["scatter", "dot", "cloud", "points"],
        "correct": 0
    },
    {
        "question": "Для построения ящика с усами используем метод plt. ...()",
        "answers": ["whiskers", "boxplot", "rangebox", "medplot"],
        "correct": 1
    },
    {
        "question": "Для добавления сетки в график используем метод plt. ...()",
        "answers": ["net", "lines", "grid", "mesh"],
        "correct": 2
    },
    {
        "question": "Добавим заголовок к графику. Используем метод plt. ...()",
        "answers": ["caption", "label", "title", "header"],
        "correct": 2
    },
    {
        "question": "Анализируя текст, модель NLP решила, что текст имеет позитивный ...",
        "answers": ["атмосфера", "сентимент", "настроение", "vibe"],
        "correct": 1
    },
    {
        "question": "Вставьте пропущенное слово. 'Разбирая текст, модель NLP извлекла все ... сущности'",
        "answers": ["именованные", "важные", "ключевые", "речевые"],
        "correct": 0
    },
    {
        "question": "Простейший вид искусственного нейрона, выполняющий линейную классификацию бинарных данных",
        "answers": ["Neuronet", "ClassNode", "OneLine", "Perceptron"],
        "correct": 3
    },
    {
        "question": "Нейронные сети, в которых информация проходит только в одном направлении: от входного слоя к выходному через один или несколько скрытых слоёв это",
        "answers": ["SeqNet", "FlatNet", "FFNN", "UniPass"],
        "correct": 2
    },
    {
        "question": "Расширенная версия FFNN, имеющая больше несколько скрытых слоёв это",
        "answers": ["DeepFF", "FullNet", "MultiFF", "DFF"],
        "correct": 3
    },
    {
        "question": "Необходимо обработать последовательные данные и нужен тип нейронной сети, имеющий механизм памяти. Для этой задачи идеально подходит",
        "answers": ["LoopNet", "RNN", "TimeNet", "TrackNet"],
        "correct": 1
    },
    {
        "question": "Во избежание переобучения мы решаем применить метод регуляризации, случайно отключающий определённые нейроны. Для этого мы используем",
        "answers": ["Dropout", "CutLayer", "NoiseOut", "NullNodes"],
        "correct": 0
    },
    {
        "question": "Самая популярная функция активации",
        "answers": ["Ramp", "MaxZero", "ReLU", "CutAct"],
        "correct": 2
    },
    {
        "question": "'При обратном распространении ошибки веса слоёв обновляются очень медленно или вовсе не обновляются например из-за таких функций как Sigmoid и Tanh, сжимающих свои выходные значения в небольшие диапазоны'. Это было описание проблемы исчезающих ...",
        "answers": ["весов", "сигналов", "градиентов", "слоёв"],
        "correct": 2
    },
    {
        "question": "Если на валидационных данных ошибка не улучшить в течение нескольких эпох, мы хотим, чтобы обучение остановилось. Для этого используем коллбэк",
        "answers": ["EarlyStopping", "StopLoss", "HaltTrain", "BreakEpoch"],
        "correct": 0
    },
    {
        "question": "Изначально learning_rate был огромен, но в один момент потребовалось его уменьшить, чтобы он 'семимильными шагами' не перепрыгивал важные точки минимума. Для решения этой задачи используется коллбэк ReduceLR...",
        "answers": ["OnPlateu", "SoftDrop", "LevelWatch", "StepDecay"],
        "correct": 0
    },
    {
        "question": "Кто легенда, потому что довёл дело до конца?",
        "answers": ["Я", "Он", "Она", "Они"],
        "correct": 0
    }
]

async def generate_conversion_stats_by_source(stats):
    report = "📊 **Статистика по источникам**:\n\n"
    report += "| Источник | Всего | Зарегистрировались | % Регистраций | Оплатили | % Оплат от всех | % Оплат от зарегистрированных |\n"
    report += "|----------|-------|---------------------|----------------|----------|------------------|-----------------------------|\n"

    for stat in stats:
        report += f"| {stat['Источник']} | {stat['Всего']} | {stat['Зарегистрировались']} | {stat['% Регистраций']} | {stat['Оплатили']} | {stat['% Оплат от всех']} | {stat['% Оплат от зарегистрированных']} |\n"

    return report

async def generate_referral_conversion_stats(stats):
    report = "📊 **Статистика по рефералам**:\n\n"
    report += "| Реферер ID | Пришло по рефералке | Зарегистрировались | % Регистраций | Оплатили | % Оплат от всех | % Оплат от зарегистрированных |\n"
    report += "|------------|---------------------|---------------------|----------------|----------|------------------|-----------------------------|\n"

    for stat in stats:
        report += f"| {stat['Реферер ID']} | {stat['Пришло по рефералке']} | {stat['Зарегистрировались']} | {stat['% Регистраций']} | {stat['Оплатили']} | {stat['% Оплат от всех']} | {stat['% Оплат от зарегистрированных']} |\n"

    return report