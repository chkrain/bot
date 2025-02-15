import logging
import hashlib
import asyncio
import json
import io  
from io import BytesIO
import os
import random
from PIL import Image, ImageDraw, ImageFont
from urllib.request import Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
from telegram.ext import MessageHandler, filters, ContextTypes
from collections import defaultdict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------

NEW = 'Добавлено: /kazik /kazik_rules /usercard'
FIXED = 'Исправлено: reply_and_delete изменено на 30 секунд (удаление сообщений)'

# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------

TOKEN = os.getenv("TOKEN")

LOG_CHANNEL = "-1002470364095"

lock = asyncio.Lock()

USER_DATA_FILE = "users_data.json"
REPORTS_FILE = "reports.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)

family_hashes = {}
GUESS_GAMES = {}

LAUGHTER = ['хахахахах', 'хыхахвхаувзхпамх', 'АХАХВХЖВЖХАЖХАВХВ', 'дзаЗДАЗДАЗВВ', 'ххАХПХПХ', 'АХАХАХВХАВХ', 'НЬЕХЕХЕХЕХЕХЕХ', 'ЛОЛ ЧЁ БЛЯЯ', 'ХЪаХах, воспользуйся командой /help, хотя даже она вряд ли тебе поможет))))']

PREDICTIONS = [
    "😄 Мои магические силы подсказывают мне, что в ближайшее время тебя ждет неожиданная встреча",
    "😁 Верь в себя, и всё получится! Это не мои слова, это духи подсказали мне",
    "😖 Остерегайся красных носков после заката, жуть какая..",
    "🙌 Твоя мечта сбудется, когда ты поможешь другу",
    "💲 Финансовая удача на твоей стороне! Возможно, стоит подождать",
    "🍺 Сегодня лучше остаться дома и пить чай. А может и не чай",
    "😈 Прочитай статьи про выживание в пост-апокалипсис",
    "😴 Тебе лучше отдохнуть денёк-другой, перетруждаться плохо",
    "😑 Пора взяться за изучение квантовой физики",
    "😟 Ты всё еще помнишь таблицу умножения? Забудь..",
    "😵 Думаю, книги по финансовой грамотносте тебе пригодятся",
    "😴 Звёзды подсказывают мне, что тебе нужно больше спать",
    "😤 Пора перестать лениться",
    "👻 Возьмись за новое дело, время идёт",
    "😒 Это сообщение удалится через [float('inf')] секунд, если всё пойдет как надо",
    "♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ Ты думаешь, я смогу решить твои проблемы?",
    "🌷 Не переставай мечтать",
    "😁 Чаще дари улыбку людям",
    "👴 👵 Скажи что-нибудь доброе своим родным",
    "😟 Не кажется ли тебе, что уже слишком поздно?",
    "😱 По-моему, твои часы спешат",
    "😥 Да, в тот раз надо было сказать по-другому",
    "😈 Терпи, потому что Господь с тобой ещё не закончил",
    "🗿 😤 Больше свежего воздуха",
    "🙏 Меньше негативных мыслей",
    "🚴 Больше активного отдыха",
    "☕ Не стоит употреблять алкоголь",
    "⛔ Не надевай дырявые носки послезавтра",
    "🚷 Будь внимательнее в четверг на улице",
    "🐗 Отдай деньги кабану",
    "😁 Молись, падла (сообщение не несёт негативный характер и лишь передаёт настроение звёзд на данный момент, все вопросы к ним)",
    "😜 Если хочешь что-то выкинуть, но жалко - выкинь",
    "😳 Venom",
    "😍 I'm Slim Shady, yes, I'm the real Shady",
    "😑 Долго будешь в телефоне сидеть?",
    "😱 Ты можешь решить чью-то судьбу. Напечатай /report [текст] и предложи своё предсказание! Вдруг звёзды с ним согласятся?",
    "😠 Не подходи к странным личностям, особенно ночью",
    "💬 Неприятно, когда попадается гнилая фисташка. К чему это? На этой неделе остерегайся фисташек",
    "💎 Сегодня ты можешь добиться успеха! А можешь и не добиться",
    "🐔 Тебе станет казаться, что жизнь напоминает бесконечный день сурка. Это не так. Она напоминает день петуха",
    "👍 Делая важный выбор сегодня, помни: лучше синица в руках, чем хуй в жопе",
    "💅 Во всём знай меру: если не справляешься с задачей самостоятельно, не стесняйся забить на неё хуй",
    "👤 Сегодня ты пойдёшь ва-банк! Или на хуй. Будущее пока неизвестно",
    "👨 Возможно, сегодня ты узнаешь что-то новое про себя. Вряд ли это будет что-то хорошее"
]

PENDING_ACTIONS = {}
PENDING_REQUESTS = {} 
ACTION_TYPES = {
    'kiss': '💋 Поцеловать',
    'hug': '🤗 Обнять',
    'slap': '👋 Дать пощечину',
    'sex': '💕 Секс',
    'highfive': '🖐️ Дать пять'
}

def load_user_data():
    default_data = {
        "username": None,
        "role": "участник",
        "family": None,
        "family_role": None,
        "family_points": 0,
        "warnings": 0,
        "muted_until": None,
        "family_title": "Нет титула",
        "default_username": 'None'
    }

    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.error("Файл users_data.json загружен неправильно! Загружаем пустую базу.")
            return {}

        logger.info(f"✅ Загружено пользователей: {len(data)}")
        logger.debug(f"📜 Все ID пользователей: {list(data.keys())}")

        updated_data = {}
        for user_id, user_info in data.items():
            str_user_id = str(user_id)
            updated_data[str_user_id] = {**default_data, **user_info}

        return updated_data

    except FileNotFoundError:
        logger.error(f"❌ Файл {USER_DATA_FILE} не найден! Создаём новый.")
        return {}

    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка JSON в {USER_DATA_FILE}: {e}")
        return {}


def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def log_to_channel(level, message):
    try:
        await bot.send_message(chat_id=LOG_CHANNEL, text=f"{level}: {message}")
    except Exception as e:
        logger.error(f"Ошибка отправки в канал: {e}")

# Функция для обработки покупки должности
async def buy_title(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data or not user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Вы не состоите в семье.")
        return

    if not context.args:
        await reply_and_delete(update, context, "❌ Пожалуйста, укажите название должности.")
        return

    title_name = " ".join(context.args)  # Название должности
    family_name = user_data[user_id]["family"]
    family_points = sum(data.get("family_points", 0) for data in user_data.values() if data.get("family") == family_name)

    # Проверяем, хватает ли очков на покупку должности
    cost = 50000
    if family_points < cost:
        await reply_and_delete(update, context, f"❌ Нужно {pluralize_points(cost)} семьи для выполнения действия.")
        return

    # Списываем 50 000 очков с общего баланса семьи
    for uid in user_data:
        if user_data[uid].get("family") == family_name:
            user_data[uid]["family_points"] = max(0, user_data[uid].get("family_points", 0) - cost)

    # Присваиваем пользователю новую должность
    user_data[user_id]["family_title"] = title_name

    # Формируем информацию о пользователе
    user_info = user_data[user_id]
    user_info_str = json.dumps(user_info, indent=4, ensure_ascii=False)

    # Отправляем сообщение в канал LOG_CHANNEL
    await context.bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"Пользователь {user_id} купил должность '{title_name}':\n\n{user_info_str}"
    )

    # Сохраняем обновленные данные
    save_user_data(user_data)

    await reply_and_delete(update, context, f"✅ Вы купили должность '{title_name}'. Информация отправлена в канал администрации.")

# магическое предсказание
async def prediction(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    last_prediction = user_data.get(user_id, {}).get("last_prediction")
    if last_prediction:
        last_time = datetime.fromisoformat(last_prediction)
        if (datetime.now() - last_time).seconds < 3600:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="❌ Магия устала :(\nПредсказания доступны раз в сутки\n(сокращено до одного раза в час)\n/prediction"
            )
            return
    
    # Получаем username из объекта update
    username = update.message.from_user.username or "хорошего человека"
    
    # Выбираем случайное предсказание
    prediction_text = random.choice(PREDICTIONS)
    user_data.setdefault(user_id, {})["last_prediction"] = datetime.now().isoformat()
    save_user_data(user_data)
    
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f"🔮 Магическое предсказание для {username}:\n\n{prediction_text}"
    )

# удаление сообщений
async def reply_and_delete(update: Update, context: CallbackContext, text: str, delete_after: int = 30, reply_markup=None, chat_id=None):
    try:
        # Если chat_id передан, используем его, иначе используем chat_id из update
        if chat_id is None:
            chat_id = update.message.chat_id

        # Отправляем сообщение
        message = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

        # Запускаем удаление в фоне, не дожидаясь его выполнения
        if delete_after > 0:
            asyncio.create_task(delete_message_later(message, delete_after))

    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")



async def delete_user_command(update: Update, context: CallbackContext):
    """Удаляет команду пользователя через 5 секунд"""
    logger.debug(f"⏳ Получена команда: {update.message.text}")

    # Логируем тип сообщения
    logger.debug(f"Тип сообщения: {type(update.message)}")
    
    user_message = update.message

    try:
        # Запускаем фоновую задачу для удаления сообщения через 5 секунд
        asyncio.create_task(delete_message_later(user_message, 15))
        logger.debug(f"✅ Сообщение будет удалено через 5 секунд: {update.message.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка удаления команды пользователя: {e}")

async def delete_message_later(message, delay):
    """Фоновое удаление сообщения с задержкой"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
        logger.debug(f"✅ Сообщение удалено после {delay} секунд")
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_data = load_user_data()
    user_id = str(user.id)  # Преобразуем ID в строку для JSON

    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,
            "default_username": user.username,
            "role": "участник"
        }
        save_user_data(user_data)
        await reply_and_delete(update, context, f"Привет, {user.username}! Добавила тебя в базу с ролью 'участник'.")
        await log_to_channel("INFO", f"{user.username} добавлен в базу с ролью участник.")
    else:
        await reply_and_delete(update, context, f"Привет, {user.username}! Ты уже в базе.")

async def role(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = str(user.id)
    user_data = load_user_data()

    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,
            "default_username": user.username,
            "role": "участник"
        }
        save_user_data(user_data)
        await reply_and_delete(update, context, "Добавила тебя в базу с ролью 'участник'.")
        await log_to_channel("INFO", f"{user.username} добавлен в базу с ролью участник по запросу /role")
    else:
        role = user_data[user_id]["role"]
        await reply_and_delete(update, context, f"На данный момент у тебя роль [{role}], если роль не та, пиши в чат балбесок или в /report")
        

# Команда /username
async def set_username(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = str(user.id)
    new_username = " ".join(context.args) if context.args else user.username
    
    user_data = load_user_data()
    
    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,         
            "default_username": user.username,  
            "role": "участник",                 
            "warnings": 0,                      
            "family": None,                     
            "family_role": None,                
        }
    
    user_data[user_id]["username"] = new_username
    save_user_data(user_data)
    
    await reply_and_delete(update, context, f"✅ Твой ник изменен на {new_username}")
    await log_to_channel("INFO", f"Пользователь с неизменным ником {user_data['default_username']} поставил новый изменяемый ник: {user_data['username']}")
    
# Команды /warn и /mute + авто-мут
async def warn_user(update: Update, context: CallbackContext):
    user_data = load_user_data()
    moderator = update.message.from_user  
    moderator_id = str(moderator.id)
    moderator_username = moderator.username or f"ID:{moderator_id}" 

    if user_data.get(moderator_id, {}).get("role") not in ["модератор", "администратор", "стример"]:
        await reply_and_delete(update, context, "❌ Куда мы лезем, тут только для модераторов и выше")
        return

    if not context.args:
        await reply_and_delete(update, context, "Используй /warn @username")
        return

    target_username = context.args[0].lstrip('@')
    target_id = next((uid for uid, data in user_data.items() if data["default_username"] == target_username), None)

    if not target_id:
        await reply_and_delete(update, context, "❌ Нет такого пользователя, ты за меня придурка не держи")
        return

    user_data[target_id]["warnings"] += 1
    save_user_data(user_data)

    await log_to_channel(
        "WARNING", 
        f"🛑 Модератор @{moderator_username} выдал предупреждение пользователю @{target_username}. "
        f"Всего предов: {user_data[target_id]['warnings']}"
    )

    if user_data[target_id]["warnings"] >= 3:
        user_data[target_id]["warnings"] = 2
        await mute_user_logic(context, target_id, timedelta(hours=1))
        await reply_and_delete(update, context, f"⚠️ Пользователь {target_username} получил мут на 1 час за 3 предупреждения!\nПредупреждения сброшены до {user_data[target_id]['warnings']}")
        
        await log_to_channel(
            "WARNING", 
            f"🔇 Модератор @{moderator_username} замутил @{target_username} на 1 час "
            f"за 3 предупреждения. Преды сброшены."
        )

    await reply_and_delete(update, context, f"✅ Пользователь {target_username} получил предупреждение, а в следующий раз получит по шее. Всего предов: {user_data[target_id]['warnings']}")


# 1. Команда для выгона из семьи
async def kick_from_family(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if user_data.get(user_id, {}).get("role") not in ["администратор"] or \
       user_data.get(user_id, {}).get("admin") not in ["true"] or \
       user_data.get(user_id, {}).get("family_role") != "Глава":
        await reply_and_delete(update, context, "❌ Только глава семьи или администратор может выгонять, ваще офигели?")
        return
    
    if not context.args:
        await reply_and_delete(update, context, "Используй /kickfam @username")
        return
    
    target_username = context.args[0].lstrip('@')
    target_id = next((uid for uid, data in user_data.items() if data["username"] == target_username), None)
    
    if not target_id or user_data[target_id].get("family") != user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Пользователь не найден или не в твоей семье")
        return
    
    # Удаление из семьи
    family_name = user_data[target_id]["family"]
    user_data[target_id]["family"] = None
    user_data[target_id]["family_role"] = None
    save_user_data(user_data)
    
    await reply_and_delete(update, context, f"❌ Пользователь {target_username} выгнан из семьи {family_name}! Как думаете, что наделал?")
    await context.bot.send_message(
        chat_id=target_id,
        text=f"⚠️ Тебя исключили из семьи {family_name}, бай-бай!"
    )
    await log_to_channel("WARNING", f"Пользователь {target_username} исключён из семьи {family_name}, печалька TT")

# Система интерактивных действий
async def family_action(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    chat_id = update.effective_chat.id

    now = datetime.now()
    last_reset_str = user_data.get(user_id, {}).get("daily_actions", {}).get("last_reset", "2000-01-01")
    last_reset = datetime.fromisoformat(last_reset_str)
    
    if (now - last_reset).days >= 1:
        user_data.setdefault(user_id, {})["daily_actions"] = {
            "last_reset": now.isoformat(),
            "hug": 0,
            "kiss": 0,
            "sex": 0
        }
        save_user_data(user_data)

    # Определяем тип действия
    action_type = update.message.text.split()[0].lstrip('/').lower()
    
    action_limits = {
        'hug': 25,
        'kiss': 10,
        'sex': 2
    }
    
    if action_type in action_limits:
        current_count = user_data[user_id]["daily_actions"].get(action_type, 0)
        if current_count >= action_limits[action_type]:
            await reply_and_delete(
                update, context,
                f"❌ Лимит {ACTION_TYPES[action_type]} исчерпан! Доступно {action_limits[action_type]}/день"
            )
            return

    if not context.args:
        await reply_and_delete(update, context, f"Используй: /{action_type} @username")
        return

    target_username = context.args[0].lstrip('@')
    target_id = next((uid for uid, data in user_data.items() if data.get("username") == target_username), None)

    # Проверки
    if not target_id:
        await reply_and_delete(update, context, "❌ Пользователь не найден или съебался с канала")
        return
    if user_id == target_id:
        await reply_and_delete(update, context, "❌ Нельзя взаимодействовать с самим собой, шалунишка")
        return
    if user_data[user_id].get("family") != user_data[target_id].get("family"):
        await reply_and_delete(update, context, "❌ Можно взаимодействовать только с членами своей семьи")
        return
    if action_type not in ACTION_TYPES:
        await reply_and_delete(update, context, "❌ Неверное действие. Доступно: " + ", ".join(ACTION_TYPES.keys()))
        return

    # Проверка очков семьи
    family_name = user_data[user_id]["family"]
    family_points = sum(data["family_points"] for data in user_data.values() if data.get("family") == family_name)
    
    if action_type == "kiss" and family_points < 150:
        await reply_and_delete(update, context, "❌ Нужно минимум 150 очков семьи для поцелуя, узнайте друг друга хотяб хз")
        return
    if action_type == "sex" and family_points < 1000:
        await reply_and_delete(update, context, "❌ Нужно минимум 1000 очков и 300 рубасов на гандоны для секса")
        return

    # Формируем callback_data
    action_key = f"{chat_id}_{target_id}"
    callback_data_accept = f"accept_{action_key}_{action_type}_{target_id}"
    callback_data_reject = f"reject_{action_key}_{target_id}"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=callback_data_accept),
            InlineKeyboardButton("❌ Отклонить", callback_data=callback_data_reject)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Сохраняем запрос
    PENDING_ACTIONS[action_key] = {
        'from_id': user_id,
        'chat_id': chat_id,
        'action': action_type,
        'timestamp': datetime.now()
    }

    # Отправляем сообщение
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎭 {user_data[user_id]['username']} хочет {ACTION_TYPES[action_type]} @{target_username}!\n"
                 f"@{target_username}, чё думаешь?",
            reply_markup=reply_markup
        )
        PENDING_ACTIONS[action_key]['message_id'] = message.message_id
    except BadRequest as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return

# жулик доп награда
async def set_family_title(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    
    if user_role not in ["модератор", "администратор", "стример", "жулик"] and not is_admin:
        await reply_and_delete( update, context, "❌ Только обладатели роли жулик могут менять титул, накопи бабок")
        return
    
    if not context.args:
        await reply_and_delete(update, context, "❌ Используй /settitle [титул]")
        return
    
    new_title = " ".join(context.args)
    user_data[user_id]["family_title"] = new_title
    save_user_data(user_data)
    await reply_and_delete(update, context, f"✅ У тебя новый титул: {new_title}\nПосмотреть можно командой /user")


# Обработчик ответов
async def handle_action_response(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        data = query.data.split('_')
        action = data[0]  # "accept" или "reject"
        action_key = "_".join(data[1:-2])  # chat_id_target_id
        action_type = data[-2] if action == "accept" else None
        target_id = data[-1]  # ID получателя

        # Проверяем, что действие нажал целевой пользователь
        if str(query.from_user.id) != target_id:
            await query.answer("❌ Это действие не для тебя!", show_alert=True)
            return

        # Проверяем наличие действия
        action_data = PENDING_ACTIONS.get(action_key)
        if not action_data:
            await query.answer("❌ Запрос устарел или отменён")
            return

        user_data = load_user_data()

        # Обработка принятия
        if action == "accept":
            # Начисляем очки
            bonus = 2 if user_data[action_data['from_id']].get("role") in ["жулик", "стример", "администратор"] else 1
            rewards = {
                'hug': 1 * bonus,
                'kiss': 3 * bonus,
                'sex': 10,
                'slap': -20,
                'highfive': 3
            }
            reward = rewards.get(action_type, 0)

            # Обновляем очки семьи
            family_name = user_data[action_data['from_id']]['family']
            for uid in user_data:
                if user_data[uid].get("family") == family_name:
                    user_data[uid]["family_points"] += reward
            save_user_data(user_data)

            # Обновляем счетчик действий
            user_data[action_data['from_id']]["daily_actions"][action_type] += 1
            save_user_data(user_data)

            response_text = (
                f"✅ @{query.from_user.username} принял действие!\n"
                f"Семья {family_name} получила {pluralize_points(reward)}."
            )
        else:
            response_text = f"❌ @{query.from_user.username} отклонил запрос."

        # Удаляем сообщение с кнопками
        if query.message:
            try:
                await query.message.delete()
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения: {e}")

        # Отправляем результат
        await context.bot.send_message(
            chat_id=action_data['chat_id'],
            text=response_text
        )

        # Удаляем запрос из очереди
        if action_key in PENDING_ACTIONS:
            del PENDING_ACTIONS[action_key]

    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}", exc_info=True)
    
async def mute_user(update: Update, context: CallbackContext):
    user_data = load_user_data()

    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    moderator_username = user_data.get(moderator_id, {}).get("default_username")
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    

    # Проверка прав модератора
    if user_role not in ["модератор", "администратор", "стример"] and not is_admin:
        await reply_and_delete(update, context, "❌ Только для модераторов и выше, не борзеть")
        return

    # Парсинг аргументов
    if len(context.args) < 2:
        await reply_and_delete(update, context, "Используй /mute @username 1h/m/d (Час, минуда, день. Максимальное практикуемое наказание - мут на сутки, не переусердствуй)")
        return

    target_username = context.args[0].lstrip('@')
    time_arg = context.args[1]

    # Поиск пользователя
    target_id = next((uid for uid, data in user_data.items() if data["username"] == target_username), None)
    if not target_id:
        await reply_and_delete(update, context, "❌ Пользователь не найден!")
        return

    # Конвертация времени
    try:
        duration = int(time_arg[:-1])
        unit = time_arg[-1].lower()
        delta = {
            'm': timedelta(minutes=duration),
            'h': timedelta(hours=duration),
            'd': timedelta(days=duration)
        }[unit]
    except Exception as e:
        await reply_and_delete(update, context, "❌ Неверный формат времени, должно быть чёт типа 30m, 1h, 2d")
        return

    # Вызов mute_user_logic
    await mute_user_logic(context, target_id, delta)
    
    # Логирование
    await log_to_channel(
        "WARNING",
        f"🔇 Модератор @{moderator_username} выдал мут пользователю @{target_username} "
        f"на {time_arg} (причина: {', '.join(context.args[2:]) or 'не указана'})"
    )

    await reply_and_delete(update, context, f"🔇 Пользователь {target_username} замучен на {time_arg} за плохое поведение")


async def safe_reply(update: Update, context: CallbackContext, text: str, is_moder_command: bool = False):
    try:
        if is_moder_command or update.message.chat.type == "private":
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text
            )
        else:
            await reply_and_delete(update, context, text)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        if update.message.chat.type != "private":
            await reply_and_delete(update, context, "⚠️ Личка закрыта")


from datetime import datetime, timedelta
import random
import json

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Обработчик команды /guess
async def start_guess_game(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    # Проверяем, когда была последняя игра
    last_game_time = user_data.get(user_id, {}).get("last_guess_game")
    if last_game_time and datetime.now() - datetime.fromisoformat(last_game_time) < timedelta(hours=1):
        await reply_and_delete(update, context, "❌ Ты уже играл, попробуй через час.")
        return
    
    # Генерация случайного числа
    random_number = random.randint(1, 100)
    
    # Запись новой игры
    user_data.setdefault(user_id, {})
    user_data[user_id]["last_guess_game"] = datetime.now().isoformat()
    user_data[user_id]["random_number"] = random_number
    user_data[user_id]["attempts"] = 0
    save_user_data(user_data)
    
    await reply_and_delete(update, context, "🔮 Игра началась! Угадай число от 1 до 100")

class GameFilter(filters.MessageFilter):
    def filter(self, message):
        user_data = load_user_data()
        user_id = str(message.from_user.id)
        return 'random_number' in user_data.get(user_id, {})
    
game_filter = GameFilter()

# Обработчик ответа пользователя
async def handle_guess(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if 'random_number' not in user_data.get(user_id, {}):
        return

    random_number = user_data[user_id]['random_number']
    
    try:
        user_guess = int(update.message.text)
        
        if not (1 <= user_guess <= 100):
            await reply_and_delete(update, context, "❌ Число должно быть целым в диапазоне от 1 до 100")
            return
        
        user_data[user_id]["attempts"] = user_data[user_id].get("attempts", 0) + 1
        
        # Удаляем игру сразу после первой попытки
        del user_data[user_id]['random_number']
        del user_data[user_id]['attempts']
        
        if user_guess == random_number:
            won = True
            family_name = user_data.get(user_id, {}).get('family')
            if family_name:
                for uid in user_data:
                    if user_data[uid].get("family") == family_name:
                        user_data[uid]["family_points"] += 10000
                reply_text = f"✅ Поздравляю! Число {random_number} верное. Каждый член семьи [{family_name}] получил 10 000 очков"
            else:
                reply_text = f"✅ Поздравляю! Число {random_number} верное. Для бонуса вступите в семью"
        else:
            won = False
            reply_text = f"❌ Неправильно! Верное число: {random_number}. Попробуй через час (/guess)"
        
        await update_user_stats(user_data, user_id, won)
        save_user_data(user_data)  # Сохраняем после всех изменений
        await reply_and_delete(update, context, reply_text)

    except ValueError:
        await reply_and_delete(update, context, "❌ Введи корректное число от 1 до 100.")
        # Удаляем игру даже при ошибке ввода
        del user_data[user_id]['random_number']
        save_user_data(user_data)

# Статус
async def update_user_stats(user_data, user_id, won):
    """Обновляет статистику пользователя в БД"""
    user_data.setdefault(user_id, {}).setdefault("wins", 0)
    user_data.setdefault(user_id, {}).setdefault("games", 0)
    user_data.setdefault(user_id, {}).setdefault("level", 0)
    user_data.setdefault(user_id, {}).setdefault("status", "Новичок")

    # Обновляем общее число игр
    user_data[user_id]["games"] += 1

    if won:
        user_data[user_id]["wins"] += 1

        # Проверка на число Фибоначчи для повышения уровня
        if is_fibonacci(user_data[user_id]["wins"]):
            user_data[user_id]["level"] += 1

        # Обновляем статус игрока
        user_data[user_id]["status"] = get_user_status(user_data[user_id]["level"])

    # Вычисляем win_rate
        user_data[user_id]["win_rate"] = round((user_data[user_id]["wins"] / user_data[user_id]["games"]) * 100, 2)
    
    save_user_data(user_data)  # Сохраняем изменения


def is_fibonacci(n):
    """Проверяет, является ли число частью последовательности Фибоначчи"""
    if n in {0, 1}:  # Числа 0 и 1 — часть последовательности
        return True
    a, b = 0, 1
    while b < n:
        a, b = b, a + b
    return b == n

def get_user_status(level):
    if level < 4:
        return "Новичок"
    elif level < 8:
        return "Опытный"
    elif level < 12:
        return "Профессионал"
    elif level < 16:
        return "Мастер"
    elif level < 20:
        return "Легенда"
    elif level < 24:
        return "Читер"
    else:
        return "Божество"

# /buyrole 
async def buy_role(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if user_id not in user_data or not user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Вы не состоите в семье.")
        return

    if not context.args:
        await reply_and_delete(update, context, "❌ Используйте: /buyrole жулик, /buyrole защитник или /buyrole вип.")
        return
    
    role_to_buy = context.args[0].lower()
    family_name = user_data[user_id]["family"]
    family_points = sum(data.get("family_points", 0) for data in user_data.values() if data.get("family") == family_name)

    # Проверяем, какую роль хочет купить пользователь
    if role_to_buy == "жулик":
        cost = 10000
        new_role = "жулик"
    elif role_to_buy == "защитник":
        cost = 100
        new_role = "защитник"
    elif role_to_buy == "вип":
        cost = 200000
        new_role = "вип"
    else:
        await reply_and_delete(update, context, "❌ Доступные роли для покупки: 'жулик' (10 000 очков семьи), 'защитник' (100 очков семьи), 'вип' (200 000 очков семьи).")
        return

    # Проверяем, хватает ли очков семьи
    if family_points < cost:
        await reply_and_delete(update, context, f"❌ Нужно {pluralize_points(cost)} семьи для покупки роли '{new_role}'. Посмотри свои очки с помощью команды /points")
        return

    # Списываем очки семьи у всех участников семьи
    for uid in user_data:
        if user_data[uid].get("family") == family_name:
            user_data[uid]["family_points"] = max(0, user_data[uid].get("family_points", 0) - cost)

    # Назначаем новую роль пользователю
    user_data[user_id]["role"] = new_role
    save_user_data(user_data)

    await reply_and_delete(update, context, f"✅ {user_data[user_id]['username']} купил роль '{new_role}'! {cost} очков списано со всей семьи {family_name}.")
    await log_to_channel("INFO", f"{user_data[user_id]['username']} купил роль '{new_role}'! {pluralize_points(cost)} списано со всей семьи {family_name}.")

# накрут очков 
async def modify_family_points(update: Update, context: CallbackContext):
    admin = update.message.from_user  # Получаем объект администратора
    admin_id = str(admin.id)
    admin_username = admin.username or f"ID:{admin_id}"  # На случай отсутствия username
    
    user_data = load_user_data()
    
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    
    if user_role not in ["администратор", "стример"] and not is_admin:
        await reply_and_delete(update, context, "❌ Только администраторы могут изменять очки семьи.")
        return
    
    if len(context.args) < 2:
        await reply_and_delete(update, context, "Используйте /modifypoints @username [количество]")
        return
    
    target_username = context.args[0].lstrip('@')
    points_change = int(context.args[1])
    target_id = next((uid for uid, data in user_data.items() if data["username"] == target_username), None)
    
    if not target_id or not user_data[target_id].get("family"):
        await reply_and_delete(update, context, "❌ Пользователь не найден или не состоит в семье.")
        return
    
    family_name = user_data[target_id]["family"]
    for uid in user_data:
        if user_data[uid].get("family") == family_name:
            user_data[uid]["family_points"] = user_data[uid].get("family_points", 0) + points_change
    
    save_user_data(user_data)
    await reply_and_delete(update, context, f"✅ Изменено {pluralize_points(points_change)} для семьи {family_name}.")
    
    # Логируем с указанием администратора
    await log_to_channel(
        "ALARM", 
        f"🚨 Администратор @{admin_username} изменил очки семьи {family_name} "
        f"на {points_change} (целевой пользователь: @{target_username})"
    )
    
# логика замута
async def mute_user_logic(context: CallbackContext, user_id: str, delta: timedelta):
    user_data = load_user_data()
    mute_end = datetime.now() + delta
    
    user_data[user_id]["muted_until"] = mute_end.isoformat()
    save_user_data(user_data)
    
    # Запланировать автоматический размут
    context.job_queue.run_once(
        callback=unmute_job,
        when=delta.total_seconds(),
        chat_id=user_id,
        name=f"unmute_{user_id}"
    )

# 5-8. Функции семьи
async def create_family(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Ты уже в семье че творишь")
        return
    
    family_name = " ".join(context.args) if context.args else f"Семья {user_data[user_id]['username']}"
    user_data[user_id]["family"] = family_name
    user_data[user_id]["family_role"] = "Глава"
    save_user_data(user_data)
    
    await reply_and_delete(update, context, f"👨👩👧👦 Семья '{family_name}' создана! Поздравляю! Ты сломал её, ты победил, ты король!")

# Проверка мута
# Упрощенная логика мута
async def mute_user_logic(context: CallbackContext, user_id: str, delta: timedelta):
    user_data = load_user_data()
    mute_end = datetime.now() + delta
    
    user_data[user_id]["muted_until"] = mute_end.isoformat()
    save_user_data(user_data)
    
    # Запланировать автоматический размут
    context.job_queue.run_once(
        callback=unmute_job,
        when=delta.total_seconds(),
        user_id=user_id,
        name=f"unmute_{user_id}"
    )

async def report(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    
    if not context.args:
        await reply_and_delete(update, context, "❌ Используй команду так: `/report текст`")
        return

    # Получаем текст репорта
    report_text = " ".join(context.args).strip()

    # Проверяем длину текста репорта
    if len(report_text) > 500:
        await reply_and_delete(update, context, "❌ Текст слишком длинный, ваще не кайф, мне же это всё читать потом.. максимум 500 символов")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Загружаем существующие отчёты (если файл есть)
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "r", encoding="utf-8") as file:
            try:
                reports = json.load(file)
            except json.JSONDecodeError:
                reports = []
    else:
        reports = []

    user_data = load_user_data()
    # Добавляем новый отчет
    new_report = {
        "id": user_id,
        "text": report_text,
        "time": timestamp
    }
    reports.append(new_report)

    # Записываем в файл
    with open(REPORTS_FILE, "w", encoding="utf-8") as file:
        json.dump(reports, file, indent=4, ensure_ascii=False)

    await reply_and_delete(update, context, "✅ Репорт записан, если там чет непристойное по айпи вычислю 🙌")
    await log_to_channel("INFO", f"{user_data[user_id]['default_username']} он же {user_data[user_id]['username']} кинул репорт")

async def unmute_job(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.user_id
    user_data = load_user_data()
    if user_data.get(user_id, {}).get("muted_until"):
        user_data[user_id]["muted_until"] = None
        save_user_data(user_data)

async def join_family(update: Update, context: CallbackContext):
    """Пользователь отправляет заявку на вступление в семью"""
    user_id = str(update.message.from_user.id)
    user = update.message.from_user  # Получаем объект пользователя
    chat_id = update.message.chat_id
    user_data = load_user_data()

    # Если пользователя нет в базе - создаем запись
    if user_id not in user_data:
        user_data[user_id] = {
            "username": user.username,
            "role": "участник",
            "family": None,
            "family_role": None,
            "family_points": 0,
            "warnings": 0,
            "muted_until": None,
            "family_title": "Нет титула",
            "default_username": user.username,  # Сохраняем исходный username
            "admin": False
        }
        save_user_data(user_data)
        await log_to_channel(f"✅ Добавлен новый пользователь (попытка вступления в семью) {user_id}")
    
    if user_data.get(user_id, {}).get("family"):
        await reply_and_delete(update, context, "❌ Вы уже состоите в семье!")
        return

    if not context.args:
        await reply_and_delete(update, context, "❌ Укажите название семьи: /joinfam НазваниеСемьи")
        return

    family_name = " ".join(context.args).strip()
    
    # Генерируем хэш для семьи
    family_hash = hashlib.md5(family_name.encode()).hexdigest()[:8]
    family_hashes[family_hash] = family_name  # Сохраняем хэш

    # Поиск главы семьи
    family_head = next(
        (uid for uid, data in user_data.items()
         if data.get("family") == family_name and 
         data.get("family_role", "").lower() in ["глава", "мама", "папа", "мама поля", "глава семейства"]),
        None
    )

    if not family_head:
        await reply_and_delete(update, context, "❌ Семья не найдена или в ней нет главы. Если ГЛАВА поменял роль, кто-либо другой должен поменять роль на ГЛАВУ")
        return

    # Формируем callback_data с хэшем
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_join_{family_hash}_{user_id}_{chat_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_join_{family_hash}_{user_id}_{chat_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Сохраняем запрос
    PENDING_REQUESTS.setdefault(family_name, {})[user_id] = {
        "username": user_data.get(user_id, {}).get('username', 'Неизвестный'),
        "timestamp": datetime.now()
    }

    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎟 Новый запрос на вступление в семью {family_name}:\n"
                 f"Пользователь: @{user_data.get(user_id, {}).get('username', 'Неизвестный')}\n"
                 "Глава семьи, выбери действие:",
            reply_markup=reply_markup
        )
        asyncio.create_task(delete_message_later(message, 60))  # Удаление через 60 сек
    except BadRequest as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        await reply_and_delete(update, context, "❌ Не удалось отправить запрос")


async def handle_join_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        data = query.data.split('_')
        action = data[0]  # "accept_join" или "reject_join"
        family_hash = data[2]  # Хэш семьи
        target_user_id = data[3]
        chat_id = int(data[4])

        # Получаем название семьи из хэша
        family_name = family_hashes.get(family_hash, "неизвестная_семья")
        
        user_data = load_user_data()
        approver_id = str(query.from_user.id)

        # Проверка существования пользователя
        approver_info = user_data.get(approver_id) or {}  # Защита от None
        if not approver_info:
            await query.answer("❌ Ваш профиль не найден!", show_alert=True)
            return

        # Безопасное получение данных
        approver_family = approver_info.get("family", "")
        approver_role = approver_info.get("family_role") or ""  # Защита от None
        approver_role = approver_role.strip().lower()  # Очистка и приведение к нижнему регистру

        # Проверка прав главы
        if approver_family != family_name or approver_role not in {"глава", "мама", "папа", "мама поля"}:
            await query.answer("❌ Только глава семьи может принимать заявки!", show_alert=True)
            logger.warning(f"User {approver_id} не имеет прав для семьи {family_name}!")
            return

        # Обработка принятия/отклонения
        if action == "accept":
            if target_user_id not in user_data:
                await query.answer("❌ Пользователь не найден!", show_alert=True)
                return

            user_data[target_user_id]["family"] = family_name
            user_data[target_user_id]["family_role"] = "Участник"
            save_user_data(user_data)

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🎉 @{user_data[target_user_id]['username']} принят в семью {family_name}!"
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"😞 Запрос @{user_data[target_user_id]['username']} отклонён."
            )

        # Удаляем запрос
        PENDING_REQUESTS.pop(family_name, {}).pop(target_user_id, None)

    except Exception as e:
        logger.error(f"Ошибка в handle_join_request: {e}", exc_info=True)


async def leave_family(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if not user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Нет у тебя семьи, а часики-то тикают")
        return
    
    user_data[user_id]["family"] = None
    user_data[user_id]["family_role"] = None
    save_user_data(user_data)
    
    await reply_and_delete(update, context, "✅ Ты больше не принадлежишь семье, че теперь по 👄 клубам 👄 ?)")

async def set_family_role(update: Update, context: CallbackContext):
    if not context.args:
        await reply_and_delete(update, context, "Используй /familyrole [роль]")
        return
    
    new_role = " ".join(context.args).strip()
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    # Проверяем, есть ли уже глава
    has_leader = any(user.get("family_role") in ["Глава", "глава", "админ", "администратор"] for user in user_data.values())

    if new_role.lower() == "глава":
        if has_leader:
            await reply_and_delete(update, context, "❌ В семье уже есть глава, сначала пускай уйдёт")
            return

    # Устанавливаем новую семейную роль
    user_data.setdefault(user_id, {})["family_role"] = new_role
    save_user_data(user_data)
    
    await reply_and_delete(update, context, f"✅ Твоя семейная роль изменена на: {new_role}. {random.choice(LAUGHTER)} ты серьезно??")

# очко
def pluralize_points(n):
    if 11 <= n % 100 <= 19:  # Обрабатываем исключения (11-19 всегда "очков")
        return f"{n} очков"
    elif n % 10 == 1:  # Оканчивается на 1 (кроме 11)
        return f"{n} очко"
    elif 2 <= n % 10 <= 4:  # Оканчивается на 2, 3, 4 (кроме 12-14)
        return f"{n} очка"
    else:  # Все остальные случаи (5-9, 0)
        return f"{n} очков"

def igra(count: int) -> str:
    if 11 <= count % 100 <= 14:  
        return "игр"
    elif count % 10 == 1:  
        return "игры"
    elif 2 <= count % 10 <= 4: 
        return "игр"
    else:  
        return "игр"

def pobeda(count: int) -> str:
    if 11 <= count % 100 <= 14:  
        return "побед"
    elif count % 10 == 1:  
        return "победа"
    elif 2 <= count % 10 <= 4:  
        return "победы"
    else:  
        return "побед"

def get_background_image(level):
    """Возвращает путь к фону в зависимости от уровня."""
    if level < 4:
        return "backgrounds/"
    elif level < 8:
        return "backgrounds/"
    elif level < 12:
        return "backgrounds/"
    elif level < 16:
        return "backgrounds/"
    elif level < 20:
        return "backgrounds/"
    elif level < 24:
        return "backgrounds/"
    else:
        return "backgrounds/"

def get_level_emojis(points):
    if points < 10:
        return "🔹"
    elif points < 50:
        return "🔹🔹"
    elif points < 100:
        return "🔹🔹🔹"
    elif points < 500:
        return "💎"
    elif points < 1000:
        return "💎💎"
    elif points < 3000:
        return "💎💎💎"
    elif points < 7000:
        return "🥇"
    elif points < 15000:
        return "🥇🥇"
    elif points < 50000:
        return "🥇🥇🥇"
    elif points < 100000:
        return "👑"
    elif points < 300000:
        return "👑👑"
    elif points < 500000:
        return "👑👑👑"
    elif points < 1000000:
        return "🌟"
    elif points < 12000000:
        return "🌟🌟"
    elif points < 15000000:
        return "🌟🌟🌟"
    elif points < 17000000:
        return "💎🥇👑"
    elif points < 20000000:
        return "🥇👑🌟"
    elif points < 35000000:
        return "👑🌟👑"
    elif points < 40000000:
        return "🌟👑🌟"
    elif points < 50000000:
        return "🌟🌟👑🌟🌟"
    else:
        return "🌟🌟🌟🌟🌟"

def calculate_offset(emojis_count):
    base_offset = 525  # Базовый отступ (1 эмоджи)
    step = 10  # Разница в отступе между эмодзи
    return base_offset - (emojis_count - 1) * step

# Карточка картинка /usercard
async def user_card(update: Update, context: CallbackContext):
    user_data = load_user_data()
    target_id = str(update.message.from_user.id)

    if target_id not in user_data:
        await update.message.reply_text("❌ О тебе нет данных. Пропиши /start")
        return

    data = user_data[target_id]
    username = user_data[target_id].get("username", "Крутышка")
    points = data.get("family_points", 0)
    level = data.get("level", 1)
    title = get_user_status(level)
    games = data.get("games", 0)
    wins = data.get("wins", 0)
    role = data.get("role", "участник")
    family_title = data.get("family_title", "подписчик")

    win_rate = round((wins / games * 100), 1) if games > 0 else 0

    # Фон для изображения (градиент или текстура)
    try:
        base_img = Image.open("background_image.jpg")
    except FileNotFoundError:
        base_img = Image.new("RGB", (600, 300), (0, 0, 0))  # Черный фон по умолчанию
    img = base_img.resize((600, 300))  # Подгоняем под нужный размер

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 28)
    title_font = ImageFont.truetype("arial.ttf", 32)
    emoji_font = ImageFont.truetype("segoe.ttf", 28)
    emoji_avatar_font = ImageFont.truetype("segoe.ttf", 16)

    # Получение аватарки пользователя
    user_photo = await update.message.from_user.get_profile_photos()
    if user_photo.total_count > 0:
        print("Фото пользователя получено.")
        photo = user_photo.photos[0][-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        avatar = Image.open(io.BytesIO(photo_bytes))
        avatar = avatar.resize((100, 100))  # Уменьшаем размер аватарки
        
        mask = Image.new('L', (100, 100), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 100, 100), fill=255)
        avatar.putalpha(mask)

        img.paste(avatar, (485, 5), mask)  # Вставка аватарки на картинку
    else:
        print("Фото пользователя не найдено. Использую default_avatar")
        avatar = Image.open("default_avatar.png")  # Убедись, что у тебя есть этот файл
        avatar = avatar.resize((100, 100))  # Размер аватарки
        
        mask = Image.new('L', (100, 100), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 100, 100), fill=255)
        avatar.putalpha(mask)
        
        img.paste(avatar, (485, 5), mask)

    point_emojis = get_level_emojis(points)
    offset_x = calculate_offset(len(point_emojis))
    draw.text((offset_x, 110), point_emojis, font=emoji_avatar_font, fill="black")
    
    draw.text((10, 23), f"📜", font=emoji_font, fill="black")
    draw.text((10, 93), f"🦹", font=emoji_font, fill="black")
    draw.text((10, 133), f"👑", font=emoji_font, fill="black")
    draw.text((10, 173), f"⚜️", font=emoji_font, fill="black")
    draw.text((10, 213), f"🏆", font=emoji_font, fill="black")
    draw.text((10, 253), f"🎲", font=emoji_font, fill="black")
    # Текстовая информация на картинке
    draw.text((50, 20), f"Статистика {username}", font=title_font, fill="black")
    draw.text((50, 90), f"Роль - {role}", font=font, fill="black")
    draw.text((50, 130), f"Титулован как {family_title}", font=font, fill="black")
    draw.text((50, 170), f"Имеет {pluralize_points(points)}", font=font, fill="black")
    draw.text((50, 210), f"Уровень {level}: {title}", font=font, fill="black")
    draw.text((50, 250), f"Из {games} {igra(games)} {wins} {pobeda(wins)}, это {float(win_rate):.1f}%", font=font, fill="black")

    # Сохранение и отправка картинки
    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)

    # Отправка фото пользователю
    await update.message.reply_photo(photo=bio, caption="📊 Твоя статистика!")

async def set_admin(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_data.get(user_id, {}).get("role") not in ["администратор", "стример"]:
        await reply_and_delete(update, context, "❌ Только администраторы могут назначать других администраторов!")
        return

    if not context.args:
        await reply_and_delete(update, context, "❌ Укажи ник пользователя.")
        return

    target_username = context.args[0].lstrip('@')
    target_id = next((uid for uid, data in user_data.items() if data["username"] == target_username), None)

    if not target_id:
        await reply_and_delete(update, context, "❌ Пользователь не найден.")
        return

    user_data[target_id]["admin"] = True  

    save_user_data(user_data)
    await reply_and_delete(update, context, f"✅ Пользователь @{target_username} теперь администратор!")
    await log_to_channel("INFO", f"{user_data[user_id]['username']} назначил @{target_username} администратором.")


# Ежедневное начисление очков
async def daily_points_task():
    while True:
        await asyncio.sleep(86400)  # сутки
        user_data = load_user_data()
        families = defaultdict(list)

        # Группируем пользователей по семьям
        for uid, data in user_data.items():
            if data.get("family"):
                families[data["family"]].append(uid)

        all_log_messages = []  # Собираем все сообщения здесь

        # Начисляем очки
        for fam_name, members in families.items():
            base_points = 48
            multiplier = 192 * len(members)
            total = min(base_points + multiplier, 1000)  # Максимум 1000 на семью
            points_per_member = int(total / len(members))
            family_bonus = 0  # Общий бонус семьи

            family_log = [f"--------------------------------------------"]
            
            for uid in members:
                user_data[uid]["family_points"] += points_per_member
                family_bonus += points_per_member
                default_username = user_data.get(uid, {}).get("default_username", "неизвестно")
                current_username = user_data.get(uid, {}).get("username", "неизвестно")
                family_log.append(f"Бонус у @{current_username} ({default_username}): +{pluralize_points(points_per_member)}")
            
            # Добавляем общий бонус семьи
            family_log.append(f"Общий бонус у [{fam_name}] составляет {pluralize_points(family_bonus)}")
            family_log.append(f"--------------------------------------------")

            all_log_messages.append("\n".join(family_log))

        save_user_data(user_data)

        # Отправляем все бонусы одним сообщением
        if all_log_messages:
            await log_to_channel("INFO", "\n".join(all_log_messages))

        await log_to_channel("INFO", "✅ Ежедневные бонусы начислены! 📢 ВНИМАНИЕ! Зарплата. Пойду дом куплю 💵💸💴")


# 1. /faminfo
async def faminfo(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if not user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Вы не состоите в семье, вероятно, вы - босс пикме")
        return
    
    family_name = user_data[user_id]["family"]
    members = [
        f"• {data['username']} ({data['family_role']})" 
        for uid, data in user_data.items() 
        if data.get("family") == family_name
    ]
    
    text = (
        f"👨👩👧👦 Семья: {family_name}\n"
        f"🏆 Очки: {int(user_data[user_id]['family_points'])}\n"
        f"👥 Участники ({len(members)}):\n" + "\n".join(members)
    )
    await reply_and_delete(update, context, text)

# 2. /topfam
async def topfam(update: Update, context: CallbackContext):
    user_data = load_user_data()
    user_id = str(update.message.from_user.id)
    
    family_name = user_data[user_id]["family"]
    members = [
        f"• {data['username']} ({data['family_role']})" 
        for uid, data in user_data.items() 
        if data.get("family") == family_name
    ]
    
    families = defaultdict(int)
    for data in user_data.values():
        if data.get("family"):
            families[data["family"]] += data.get("family_points", 0)

    if not families:
        await reply_and_delete(update, context, "❌ Семьи не найдены")
        return

    sorted_families = sorted(families.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 Топ семей:\n" + "\n".join(
        [f"{i+1}. {name} — {pluralize_points(int(points / len(members)))}" for i, (name, points) in enumerate(sorted_families)]
    )

    await reply_and_delete(update, context, text)


# казик
# Определение цветов для номеров рулетки
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

weights = {
    "red": 55,   
    "black": 40, 
    "zero": 5  
}

async def play_kazik(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    if len(context.args) < 2:
        await reply_and_delete(update, context, "❌ Команда выглядит так: /kazik [ставка] [тип_ставки] [число/цвет]")
        return
    
    try:
        bet_amount = int(context.args[0])
        bet_type = context.args[1].upper()
        bet_value = context.args[2] if len(context.args) > 2 else None
    except ValueError:
        await reply_and_delete(update, context, "❌ Неверный формат ставки. Пример: /kazik 100 A 7")
        return
    
    if user_id not in user_data or user_data[user_id].get("family_points", 0) < bet_amount:
        await reply_and_delete(update, context, f"❌ Недостаточно очков для ставки, {random.choice(LAUGHTER)}")
        return
    
    # Выпадение случайного числа рулетки (0-36)
    # result_number = random.randint(0, 36)
    result_color = random.choices(["red", "black", "zero"], weights=[weights["red"], weights["black"], weights["zero"]])[0]
    if result_color == "red":
        result_number = random.choice(list(RED_NUMBERS))
    elif result_color == "black":
        result_number = random.choice(list(BLACK_NUMBERS))
    else:
        result_number = 0
    
    # Таблица коэффициентов
    payout_multipliers = {
        "A": 35,  # Прямая ставка
        "B": 17,  # Сплит
        "C": 11,  # Стрит
        "D": 8,   # Каре
        "E": 5,   # Сикслайн
        "F": 2,   # Ряд
        "G": 2,   # Дюжина
        "H": 1    # Четное/нечетное, красное/черное, больше/меньше
    }
    
    if bet_type == "A":  # Прямая ставка
        if bet_value is None or not bet_value.isdigit() or not (0 <= int(bet_value) <= 36):
            await reply_and_delete(update, context, "❌ Неверная ставка. Пример: /kazik 100 A 7")
            return
        if int(bet_value) == result_number:
            multiplier = payout_multipliers["A"]
        else:
            multiplier = 0
    elif bet_type == "B":  # Сплит
        if len(context.args) < 3:
            await reply_and_delete(update, context, "❌ Для сплита нужно указать два числа. Пример: /kazik 100 B 1 2")
            return
        bet_values = [int(value) for value in context.args[2:]]
        
        if len(bet_values) != 2 or bet_values[0] < 0 or bet_values[0] > 36 or bet_values[1] < 0 or bet_values[1] > 36:
            await reply_and_delete(update, context, "❌ Для сплита укажите два числа от 0 до 36.")
            return
        
        adjacent_numbers = [
            (1, 2), (2, 3), (4, 5), (5, 6), (7, 8), (8, 9), (10, 11), (11, 12),
            (13, 14), (14, 15), (16, 17), (17, 18), (19, 20), (20, 21), (22, 23),
            (23, 24), (25, 26), (26, 27), (28, 29), (29, 30), (31, 32), (32, 33), (34, 35), (35, 36)
        ]
        
        if (bet_values[0], bet_values[1]) not in adjacent_numbers and (bet_values[1], bet_values[0]) not in adjacent_numbers:
            await reply_and_delete(update, context, "❌ Числа для сплита должны быть соседними.")
            return
        
        if result_number in bet_values:
            multiplier = payout_multipliers["B"]
        else:
            multiplier = 0
    elif bet_type == "C":  # Стрит
        if len(context.args) < 3:
            await reply_and_delete(update, context, "❌ Для стрита нужно указать три числа. Пример: /kazik 100 C 1 2 3")
            return
        bet_values = [int(value) for value in context.args[2:]]
        
        if len(bet_values) != 3 or any(value < 0 or value > 36 for value in bet_values):
            await reply_and_delete(update, context, "❌ Для стрита укажите три числа от 0 до 36.")
            return
        
        if result_number in bet_values:
            multiplier = payout_multipliers["C"]
        else:
            multiplier = 0
    elif bet_type == "D":  # Каре
        if len(context.args) < 3:
            await reply_and_delete(update, context, "❌ Для каре нужно указать четыре числа. Пример: /kazik 100 D 1 2 3 4")
            return
        bet_values = [int(value) for value in context.args[2:]]
        
        if len(bet_values) != 4 or any(value < 0 or value > 36 for value in bet_values):
            await reply_and_delete(update, context, "❌ Для каре укажите четыре числа от 0 до 36.")
            return
        
        if result_number in bet_values:
            multiplier = payout_multipliers["D"]
        else:
            multiplier = 0
    elif bet_type == "E":  # Сикслайн
        if len(context.args) < 3:
            await reply_and_delete(update, context, "❌ Для сикслайна нужно указать шесть чисел. Пример: /kazik 100 E 1 2 3 4 5 6")
            return
        bet_values = [int(value) for value in context.args[2:]]
        
        if len(bet_values) != 6 or any(value < 0 or value > 36 for value in bet_values):
            await reply_and_delete(update, context, "❌ Для сикслайна укажите шесть чисел от 0 до 36.")
            return
        
        if result_number in bet_values:
            multiplier = payout_multipliers["E"]
        else:
            multiplier = 0
    elif bet_type == "F":  # Ставка на ряд (колонку)
        if bet_value not in ["1st", "2nd", "3rd"]:
            await reply_and_delete(update, context, "❌ Неверная ставка. Доступные ряды: 1st, 2nd, 3rd")
            return
        
        first_column = {1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34}
        second_column = {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}
        third_column = {3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36}
        
        if (bet_value == "1st" and result_number in first_column) or \
           (bet_value == "2nd" and result_number in second_column) or \
           (bet_value == "3rd" and result_number in third_column):
            multiplier = payout_multipliers["F"]
        else:
            multiplier = 0
    elif bet_type == "H":  # Ставки на цвета, чет/нечет, диапазоны
        if bet_value not in ["red", "black", "even", "odd", "low", "high"]:
            await reply_and_delete(update, context, "❌ Неверная ставка. Доступно: red, black, even, odd, low, high")
            return
        if (bet_value == result_color) or \
           (bet_value == "even" and result_number % 2 == 0 and result_number != 0) or \
           (bet_value == "odd" and result_number % 2 == 1) or \
           (bet_value == "low" and 1 <= result_number <= 18) or \
           (bet_value == "high" and 19 <= result_number <= 36):
            multiplier = payout_multipliers["H"]
        else:
            multiplier = 0
    else:
        await reply_and_delete(update, context, "❌ Неверный тип ставки. Посмотри /kazik_rules")
        return
    
    if multiplier > 0:
        winnings = int(bet_amount * multiplier)
        user_data[user_id]["family_points"] += winnings
        won = True
        await reply_and_delete(update, context, f"✅ Выпало {result_number} ({result_color})! Ты выиграл {pluralize_points(winnings)}!")
    else:
        user_data[user_id]["family_points"] -= bet_amount
        won = False
        await reply_and_delete(update, context, f"❌ Выпало {result_number} ({result_color}). Ты проиграл {pluralize_points(bet_amount)}, бывает")
    
    await update_user_stats(user_data, user_id, won)

# 1. Команда /unmute (для модераторов+)
async def unmute_user(update: Update, context: CallbackContext):
    user_data = load_user_data()
    # Получаем данные модератора
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    moderator_username = moderator.username or f"ID:{moderator_id}"  # Актуальный username или ID
    
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    # Проверка прав
    if user_role not in ["модератор", "администратор", "стример"] and not is_admin:
        await reply_and_delete(update, context, "❌ Только для модераторов и выше!")
        return
    
    # Проверка аргументов
    if not context.args:
        await reply_and_delete(update, context, "Используй /unmute @username")
        return
    
    target_username = context.args[0].lstrip('@')
    target_id = next((uid for uid, data in user_data.items() if data["username"] == target_username), None)
    
    if not target_id:
        await reply_and_delete(update, context, "❌ Не помню такой транзакции, у вас есть молоко?")
        return
    
    # Снимаем мут
    user_data[target_id]["muted_until"] = None
    save_user_data(user_data)
    
    # Логируем действие
    await log_to_channel(
        "INFO", 
        f"🔊 Мистер пипискин @{moderator_username} размутил пользователя @{target_username}\n"
        f"• ID модератора: {moderator_id}\n"
        f"• ID пользователя: {target_id}"
    )
    
    await reply_and_delete(update, context, f"🔊 Пользователь {target_username} размучен")

# Команда /user (вся информация)
async def user_info(update: Update, context: CallbackContext):
    user_data = load_user_data()
    
    if update.message:
        target_id = str(update.message.from_user.id)
    elif update.callback_query:
        target_id = str(update.callback_query.from_user.id)
    else:
        await update.message.reply_text("❌ Не удалось определить ID пользователя.")
        logger.error("Ошибка: target_id не определён!")
        return

    if target_id not in user_data:
        logger.warning(f"❌ Пользователь {target_id} не найден в user_data!")
        logger.debug(f"📜 Все загруженные ID: {list(user_data.keys())}")
        await update.message.reply_text(f"❌ О тебе нет данных, голубиная ты пиписька ID: {target_id}")
        return

    data = user_data[target_id]
    muted_status = "Да" if data.get("muted_until") and datetime.now() < datetime.fromisoformat(data["muted_until"]) else "Нет"
    
    # Формируем текст с информацией о пользователе
    text = (
        f"👤 Пользователь: @{data['username']}\n"
        f"🆔 ID: скрыт\n"
        f"👑 Роль: {data['role']}\n"
        f"⚠️ Предупреждения: {data['warnings']}\n"
        f"🔇 В муте: {muted_status}\n"
        f"👪 Семья: {data.get('family', 'Нет')}\n"
        f"🏷️ Роль в семье: {data.get('family_role', 'Нет')}\n"
        f"🏅 Очки: {int(data.get('family_points', 0))}\n"
        f"👳 Титул: {data.get('family_title', 'Нет титула')}\n"
        f"👀 Имя при рождении: {data.get('default_username', 'Нет его')}\n"
    )
    
    # Отправка ответа всегда в текущий чат
    await reply_and_delete(update, context, text)


# 3. Проверка мута
async def check_mute(update: Update, context: CallbackContext):
    """ Проверяет, замучен ли пользователь, и удаляет его сообщение, если да. """
    # Проверка на наличие сообщения в обновлении
    if update.message is None:
        return  # Если сообщения нет, ничего не делаем

    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    muted_until = user_data.get(user_id, {}).get("muted_until")
    
    if muted_until:
        try:
            muted_time = datetime.fromisoformat(muted_until)
            if datetime.now() < muted_time:
                # Удаляем сообщение, если пользователь в муте
                await update.message.delete()
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔇 У тебя мут до {muted_time.strftime('%d.%m.%Y %H:%M')}, не рыпайся, сиди и думай над своим поведением"
                )
                return
            else:
                # Удаляем мут при истечении времени
                del user_data[user_id]["muted_until"]
                save_user_data(user_data)
        except ValueError:
            # Если формат времени некорректен, удаляем мут
            del user_data[user_id]["muted_until"]
            save_user_data(user_data)


# 3. /points
async def points(update: Update, context: CallbackContext):
    user_data = load_user_data()
    requester_id = str(update.message.from_user.id)
    
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    # Просмотр своих очков
    if not context.args:
        points = user_data[requester_id].get("family_points", 0)
        await reply_and_delete(update, context, f"🏅 У вашей семьи {pluralize_points(int(points))}")
        return
    
    # Просмотр чужих очков (только для модераторов+)
    if user_role not in ["модератор", "администратор", "стример"] and not is_admin:
        await reply_and_delete(update, context, "❌ Недостаточно прав!")
        return
    
    target_username = context.args[0].lstrip('@')
    target_id = next((uid for uid, data in user_data.items() if data["username"] == target_username), None)
    
    if not target_id or not user_data[target_id].get("family"):
        await reply_and_delete(update, context, "❌ Боту, видимо, гг. Или какая-то ошибка. Вау-вау-вау юпиё юпией")
        return
    
    points = user_data[target_id]["family_points"]
    await reply_and_delete(update, context, f"🏅 Семейные очки {target_username}: {points}")

# Правила казика
async def kazik_rules(update: Update, context: CallbackContext):
    text = (
            """
            ❗❗❗ Ставки и казино - плохо. Не играйте в подобное на настоящие деньги и не относитесь к этому как к способу заработка ❗❗❗ \n
            ❗❗❗ Здесь вы можете почувствовать себя Джеймсом Бондом, но ни в коем случае не повторяйте это на сторонних сайтах ❗❗❗ \n
            ❗❗❗ Если вы легко подсаживаетесь на азартные игры не стоит начинать даже тут. Команда создана исключительно для развлечения ❗❗❗ \n
            
            🎰 Правила игры в рулетку 🎰
            
            В рулетке можно делать следующие виды ставок:
            
            A — Прямая ставка (ставка на 1 номер) → 35 к 1
            Пример: /kazik 100 A 7
            Это самая высокооплачиваемая ставка. Вы ставите на один конкретный номер, и если этот номер выпадает, ваша ставка умножается на 35.
            Круто? Это же как быстро можно накопить на вип? При стоимосте в 200К (стоимость может поменяться, если это так, сообщите через /report) 
            достаточно поставить всего 5.7К!

            B — Сплит (ставка на 2 номера) → 17 к 1
            Пример: /kazik 100 B 7 8
            Сплит — ставка на два соседних номера. Например, если ставите на номера 7 и 8, и любой из них выпадает, ваша ставка умножается на 17.
            Неплохо, если любите рискнуть по-крупному!

            C — Стрит (ставка на 3 номера) → 11 к 1
            Пример: /kazik 100 C 7 8 9
            Стрит — ставка на три последующих номера. Например, если ставите на номера 7, 8 и 9, и один из них выпадает, ваша ставка умножается на 11.
            Тоже рисковая ставка, но окуп достаточно неплохой.

            D — Каре (ставка на 4 номера) → 8 к 1
            Пример: /kazik 100 D 7 8 10 11
            Каре — ставка на четыре номера, расположенных рядом. Например, для номеров 7, 8, 10 и 11, если любой из этих номеров выпадает, ставка умножается на 8.
            Уже менее рисковано и всё еще с большим коэффициентом. Попробуешь?

            E — Сикслайн (ставка на 6 номеров) → 5 к 1
            Пример: /kazik 100 E 7 8 9 10 11 12
            Сикслайн — ставка на шесть номеров, которые идут подряд по горизонтали на поле. Например, ставите на 7, 8, 9, 10, 11 и 12, и если любой из этих номеров выпадает, 
            ставка умножается на 5. Не выиграть здесь за несколько ставок - тяжело, а х5 коэффициент даёт возможность разгуляться.

            F — Ставка на ряд (12 номеров) → 2 к 1
            Пример: /kazik 100 F 1st
            Ставка на ряд (или "столбец") включает 12 чисел. Например, ставка на первый ряд (1st) включает номера 1, 2, 3, ..., 12. В случае выигрыша выплата составит 2 к 1.
            Здесь можно начинать ставить по-крупному!

            G — Ставка на дюжину (12 номеров) → 2 к 1
            Пример: /kazik 100 G 2nd
            Дюжина — ставка на 12 номеров из одной группы: 1st (1-12), 2nd (13-24) или 3rd (25-36). Если выпадает один из номеров вашей дюжины, выплата составит 2 к 1.
            Здесь можно начинать ставить по-крупному!
            """
    )
            
    text_2 = (
            """
            H — Ставки на равные шансы (красное/черное, четное/нечетное, больше/меньше) → 1 к 1
            Пример: /kazik 100 H red
            Доступные ставки:
            - red (красное) — ставка на все красные номера (например, 1, 3, 5, 7, ...).
            - black (черное) — ставка на все черные номера.
            - even (четное) — ставка на все четные номера (2, 4, 6, ...).
            - odd (нечетное) — ставка на все нечетные номера (1, 3, 5, ...).
            - low (меньше) — ставка на числа от 1 до 18.
            - high (больше) — ставка на числа от 19 до 36.
            Если выпадет один из выбранных вами номеров для этих ставок, выплата составит 1 к 1.
            Вот тут можно поставить все свои очки! А что? Один раз живём.
            
            ❗ При выпадении 0 все ставки, кроме A, проигрывают.
            
            Even (четное) — ставка выигрывает, если выпадает любое четное число (2, 4, 6, ..., 36). Исключение: 0 — ставка проигрывает.
            Odd (нечетное) — ставка выигрывает, если выпадает любое нечетное число (1, 3, 5, ..., 35). Исключение: 0 — ставка проигрывает.
            Low (1-18, меньше) — ставка выигрывает, если выпадает число от 1 до 18 включительно. Исключение: 0 — ставка проигрывает.
            High (19-36, больше) — ставка выигрывает, если выпадает число от 19 до 36 включительно. Исключение: 0 — ставка проигрывает.
            Эти ставки относятся к ставкам на равные шансы (H), выплата составляет 1 к 1.
            """
    )
    await reply_and_delete(update, context, text)
    await reply_and_delete(update, context, text_2)

    
    
# /yupointsinfo
async def yupointsinfo(update: Update, context: CallbackContext):  # Добавлен context
    text = (
        "При вступлении в семью вам начисляется по 10 Юпоинтов в час\n"
        "За каждого нового члена семьи вы получаете дополнительно 8 Юпоинтов в час\n"
        "Максимальный суточный лимит — 1000 Юпоинтов.\n\n"
        "За баллы на данный момент можно купить роль [жулик]\n\n"
        "ВНИМАНИЕ!\n"
        "✔ Для накопления Юпоинтов необходимо состоять в семье.\n"
        "❗ В случае утраты базы данных бота очки восстановлению не подлежат, резервных копий нет.\n"
        "Полезные команды для накопления Юпоинтов:\n"
        "/kiss, /hug, /sex, /joinfam. Подробнее в /help\n"
        "По поводу использований команд:\n"
        "/hug - доступно всегда, /kiss - от 150 очков, /sex - от 1000 очков.\n"
        "Если заметили ошибку в накоплении поинтов - обращайтесь.\n"
    )
    await reply_and_delete(update, context, text)
    
# /moder
async def moder(update: Update, context: CallbackContext):
    user_data = load_user_data()
    
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    # Если аргументов нет
    if not context.args:
        text = (
            "Вам доступны команды /warn, /mute, /unmute.\n\n"
            "Нах*я (sorry) спрашивается нужна команда /moder, но ладно\n"
            "Я так подумал и бан с киком не стал добавлять, тут всё по старинке\n"
            "Добавлена команда /modifypoints ник количество\n"
        )
        await reply_and_delete(update, context, text)  # Отправляем сообщение
        return
    
    # Проверка прав
    if user_role not in ["модератор", "администратор", "стример"] and not is_admin:
        await reply_and_delete(update, context, "❌ Недостаточно прав!")
        return


# /steal 
async def steal_points(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    # Проверка прав и ограничений
    if user_role not in ["модератор", "администратор", "стример", "жулик"] and not is_admin:
        await reply_and_delete(update, context, "❌ Только жулики могут воровать очки, ты же не опустишься до такого?")
        return
    
    if not user_data[user_id].get("family"):
        await reply_and_delete(update, context, "❌ Сперма вступи в семью")
        return
    
    # Проверка времени последней кражи
    last_theft = user_data[user_id].get("last_theft")
    if last_theft and (datetime.now() - datetime.fromisoformat(last_theft)).days < 1:
        await reply_and_delete(update, context, "❌ Кража доступна раз в сутки, побойся Бога")
        return
    
    # Получаем семью вора
    thief_family = user_data[user_id]["family"]
    
    # Собираем семьи без защитников
    families = defaultdict(list)
    for uid, data in user_data.items():
        family = data.get("family")
        # Исключаем семью вора и семьи с защитниками
        if family and family != thief_family:
            # Проверяем, есть ли в семье защитник
            has_defender = any(
                user_data[member].get("family_role") == "защитник"
                for member in user_data
                if user_data[member].get("family") == family
            )
            if not has_defender:
                families[family].append(uid)
    
    if not families:
        await reply_and_delete(update, context, "❌ Все семьи защищены или их нет")
        return
    
    # Выбираем случайную незащищенную семью
    target_family = random.choice(list(families.keys()))
    target_members = families[target_family]
    
    # Вычисляем общие очки семьи-цели
    family_points = sum(user_data[uid].get("family_points", 0) for uid in target_members)
    if family_points <= 0:
        await reply_and_delete(update, context, "❌ У выбранной семьи нет очков.. каким-то образом")
        return
    
    # Генерируем процент кражи (1-5%)
    steal_percent = random.randint(1, 5)
    stolen_points = round(family_points * steal_percent / 100)
    
    # Забираем очки у цели
    for uid in target_members:
        user_data[uid]["family_points"] = max(0, user_data[uid]["family_points"] - stolen_points)
    
    # Добавляем очки семье вора
    for uid in user_data:
        if user_data[uid].get("family") == thief_family:
            user_data[uid]["family_points"] += stolen_points
    
    # Обновляем время последней кражи
    user_data[user_id]["last_theft"] = datetime.now().isoformat()
    save_user_data(user_data)
    
    # Логирование
    await log_to_channel(
        "WARNING",
        f"🦹♂️ @{user_data[user_id]['username']} (семья '{thief_family}') "
        f"украл {steal_percent}% ({pluralize_points(stolen_points)}) у незащищенной семьи '{target_family}'!"
    )
    
    await reply_and_delete(update, context, f"✅ Вы украли {steal_percent}% ({pluralize_points(stolen_points)}) у семьи {target_family}, нормальная добыча")

# Бригада: это вроде катя самбука ее заставили раздеться на концерте или где я хз
# /brigada
async def brigada(update: Update, context: CallbackContext):
    user_data = load_user_data()
    requester_id = str(update.message.from_user.id)
    
    # Если аргументов нет
    if not context.args:
        text = (
            "Бригада: это вроде катя самбука ее заставили раздеться на концерте или где я хз\n"
        )
        audio_path = "mp/brig.mp3"
        audio_path_1 = "mp/brig_1.mp3"
        audio_path_2 = "mp/brig_2.mp3"
        audio_path_3 = "mp/brig_3.mp3"
        audio_files = [audio_path, audio_path_1, audio_path_2, audio_path_3]
        random_audio = random.choice(audio_files)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(random_audio, 'rb'))
        return
    
    # Проверка прав
    if user_data.get(requester_id, {}).get("role") not in ["модератор", "администратор", "стример", "участник", "жулик", "vip", "вип"]:
        await reply_and_delete(update, context, "❌ Отрицательно достаточно прав!")
        return

# /жулик
async def testrole(update: Update, context: CallbackContext):
    user_data = load_user_data()
    
    moderator = update.message.from_user
    moderator_id = str(moderator.id)
    user_role = user_data.get(moderator_id, {}).get("role")
    is_admin = user_data.get(moderator_id, {}).get("admin", False)
    
    # Если аргументов нет
    if not context.args:
        text = (
            "Вам доступны команды /settitle - поменять семейное звание.\n"
            "Увеличенные очки за действия. Очки выдаются на всю семью.\n"
            "Возможность красть чужие очки и присваивать их себе:\n"
            "Команда /steal. Работает раз в сутки, максимальное количество украденного - 5%.\n"
            "Защититься от кражи можно купив роль защитник.\n"
        )
        await reply_and_delete(update, context, text)  # Отправляем сообщение
        return
    
    # Проверка прав
    if user_role not in ["модератор", "администратор", "стример", "жулик"] and not is_admin:
        await reply_and_delete(update, context, "❌ Недостаточно прав, нужно быть жуликом")
        return
    
async def show_info(update: Update, context: CallbackContext):
    info_text = """
    Лор бота: 
    Во главе всего здесь стоят очки, которые 
    можно заработать только одним способом:
    создать семью и жить припеваючи (или накрутить их,
    но это для админов или читеров).
    Что можно сделать за очки?
    Во-первых, купить роли: жулик, защитник, вип. 
    Да, самое крутое здесь - вип, ведь он распространяется
    ещё и на твич. О жулике (/stealer) и защитнике смотрите в других командах.
    Помимо ролей на данный момент можно купить должность в тгк,
    но на этом мы не останавливаемся и ждём обновлений.
    Для развития бота нужна обратная связь, ее можно дать здесь: /report
    """
    await reply_and_delete(update, context, info_text)

# 9. Команда /help
async def show_help(update: Update, context: CallbackContext):
    help_text = """
    📜 Доступные команды:
    /start - Бот добавит в базу
    /username [новый_ник] - Изменить свой ник
    /role - Показать свою роль
    /changerole - Поменять роль
    /createfam [название] - Создать семью
    /joinfam [название] - Вступить в семью
    /leavefam - Покинуть семью
    /familyrole [роль] - Установить семейную роль
    /yupointsinfo - Информация по Юпоинтам
    /faminfo - Инфа о семье
    /topfam - Список семей
    /points - Очки свои/чужие(модер+)
    /moder - Модерам инфа
    /user - Инфа о пользователе
    /kickfam @user - Выгнать из семьи
    /kiss @user - Послать запрос на поцелуй
    /hug @user - Послать запрос на объятие
    /slap @user - Запрос на пощечину, вдруг задефает
    /sex @user - Послать запрос на сегс
    /help - Показать это сообщение
    /buyrole - Купить таинственную роль
    /жулик - Узнать о роли
    /brigada - Дайте бригаду
    /report - Сообщить/предложить
    /buytitle [должность] - Купить должность в канале
    /info - Запросить информацию
    /prediction - Магическое предсказание
    /guess - Шанс выиграть 10 000 очков!
    /kazik - Казино (асу)
    /kazik_rules - Правила игры в /kazik
    /usercard - Посмотреть статистику (победы считаются в /kazik и /guess)
    """
    await reply_and_delete(update, context, help_text)

async def test_command_handler(update: Update, context: CallbackContext):
    logger.debug(f"🔥 Поймал команду: {update.message.text}")


async def change_role(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = str(user.id)
    user_data = load_user_data()

    # Проверка прав администратора
    if user_data.get(user_id, {}).get("role") != "администратор":
        await reply_and_delete(update, context, "❌ Эта команда только для администраторов!")
        return

    # Проверка аргументов
    if len(context.args) < 2:
        await reply_and_delete(update, context, "Используй /changerole [user_id] [роль]")
        return

    target_user_id, new_role = context.args[0], " ".join(context.args[1:]).lower()
    if new_role not in ["участник", "модератор", "администратор", "стример", "жулик", "защитник"]:
        await reply_and_delete(update, context, "❌ Недопустимая роль. Доступные: участник, модератор, администратор, жулик, стример")
        return

    if target_user_id not in user_data:
        await reply_and_delete(update, context, "❌ Пользователь не найден.")
        return

    user_data[target_user_id]["role"] = new_role
    save_user_data(user_data)
    await reply_and_delete(update, context, f"✅ Роль пользователя {user_data[target_user_id]['username']} изменена на {new_role}.")
    await log_to_channel("INFO", f"Админ {user.username} изменил роль {target_user_id} на {new_role}")

async def debug_all_messages(update: Update, context: CallbackContext):
    logger.debug(f"📩 Получено обновление: {update}")
    await log_to_channel("INFO", f"Получено обновление: {update}")

async def run_bot():
    app = Application.builder().token(TOKEN).build()
    
    asyncio.create_task(daily_points_task())
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("role", role))
    app.add_handler(CommandHandler("changerole", change_role))
    app.add_handler(CommandHandler("username", set_username))
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("createfam", create_family))
    app.add_handler(CommandHandler("joinfam", join_family))
    app.add_handler(CommandHandler("leavefam", leave_family))
    app.add_handler(CommandHandler("familyrole", set_family_role))
    app.add_handler(CommandHandler("help", show_help))
    app.add_handler(CommandHandler("faminfo", faminfo))
    app.add_handler(CommandHandler("topfam", topfam))
    app.add_handler(CommandHandler("points", points))
    app.add_handler(CommandHandler("moder", moder))
    app.add_handler(CommandHandler("stealer", testrole))
    app.add_handler(CommandHandler("yupointsinfo", yupointsinfo))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("user", user_info))
    app.add_handler(CommandHandler("kickfam", kick_from_family))
    app.add_handler(CommandHandler("kiss", family_action))
    app.add_handler(CommandHandler("hug", family_action))
    app.add_handler(CommandHandler("slap", family_action))
    app.add_handler(CommandHandler("sex", family_action))
    app.add_handler(CommandHandler("buyrole", buy_role))
    app.add_handler(CommandHandler("modifypoints", modify_family_points))
    app.add_handler(CommandHandler("settitle", set_family_title))
    app.add_handler(CommandHandler("steal", steal_points))
    app.add_handler(CommandHandler("brigada", brigada))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("guess", start_guess_game))
    app.add_handler(CommandHandler("info", show_info))
    app.add_handler(CommandHandler("buytitle", buy_title))
    app.add_handler(CommandHandler("prediction", prediction))
    app.add_handler(CommandHandler("setadm", set_admin))
    app.add_handler(CommandHandler("kazik", play_kazik))
    app.add_handler(CommandHandler("usercard", user_card))
    app.add_handler(CommandHandler("kazik_rules", kazik_rules))
    app.add_handler(CallbackQueryHandler(handle_join_request, pattern="^(accept_join|reject_join)_"))
    app.add_handler(CallbackQueryHandler(handle_action_response))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & game_filter, handle_guess))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_mute))
    app.add_handler(MessageHandler(filters.COMMAND & ~filters.Regex(r'^/brigada'), delete_user_command), group=1)
    

    await log_to_channel("INFO", 
        "✅ Бот запущен и подключён к защите от вылетов.\n"
        "HELP: /help - помощь с командами\n"
        f"NEW: {NEW}\n"
        f"FIXED: {FIXED}\n"
    )

    while True:  # Бесконечный цикл с защитой от вылетов
        try:
            await app.run_polling()
        except Exception as e:
            logger.error(f"❌ Ошибка в работе бота: {e}")
            await log_to_channel("ERROR", f"Ошибка в работе бота: {e}. Инициализация перезапуска через: 5")
            await asyncio.sleep(5)  # Ждём 5 секунд перед повторным запуском


if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()  

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())  # Правильный запуск


    
    
# 1
# 2
# 3 
# 4
# 5
# 6
# 7
# 8
# 9
# 10
# 11
# 12
# 13
# 14
# 15