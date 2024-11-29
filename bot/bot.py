import os
import sys

import django
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

project_root = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(project_root)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "bot_backend"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot_backend.settings")

django.setup()

try:
    from event_planner.models import Speaker,  Question, User
    from event_planner.utils import get_schedule, get_user_role

except Exception as e:
    print(f"Error importing models: {e}")
bot = TeleBot("8066339717:AAFqYwMs5zx8va4mYBMgV8i9xFwXVK_4RKI")

# словарь, чтобы чекать, если пользователь в состоянии ввода вопроса
user_states = {}


def is_asking_question(message):
    tg_id = str(message.chat.id)
    return user_states.get(tg_id) == 'asking_question'


def create_reply_keyboard(role):
    if role == 'speaker':
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = KeyboardButton("О программе")
        btn2 = KeyboardButton("Посмотреть вопросы")
        keyboard.add(btn1, btn2)
        return keyboard
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = KeyboardButton("О программе")
        btn2 = KeyboardButton("Задать вопрос")
        keyboard.add(btn1, btn2)
        return keyboard

# начало


@bot.message_handler(commands=['start'])
def start(message):
    """Идентифицируем роль пользователя"""
    tg_id = str(message.chat.id)
    username = message.from_user.username
    try:
        user, created = User.objects.get_or_create(
            tg_id=tg_id,
            defaults={
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'username': username
            }
        )

        if username and Speaker.objects.filter(tg_id=f"@{username}").exists():
            user.role = 'speaker'
        else:
            user.role = 'listener'
        user.save()

        keyboard = create_reply_keyboard(user.role)
        role = 'Докладчик' if user.role == 'speaker' else 'Слушатель'
        bot.send_message(
            message.chat.id,
            f"Добро пожаловать, {user.first_name}! Ваша роль: {role}.",
            reply_markup=keyboard
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при идентификации: {e}")


def is_about_command(message):
    return message.text == "О программе"


@bot.message_handler(func=is_about_command)
def handle_about(message):
    """"
    Обработка команды "О программе"
    """
    try:
        schedule = get_schedule()
        bot.send_message(message.chat.id, schedule)
    except Exception as e:
        bot.send_message(
            message.chat.id, f"Ошибка при получении расписания: {e}")


# Чекаем, если пользователь задает вопрос
def is_ask_question_command(message):
    return message.text == "Задать вопрос"


@bot.message_handler(func=is_ask_question_command)
def ask_question(message):
    """обработка вопроса"""
    tg_id = str(message.chat.id)
    user = User.objects.filter(tg_id=tg_id).first()

    if user and user.role == 'listener':
        user_states[tg_id] = 'asking_question'
        bot.send_message(message.chat.id, "Пожалуйста, введите ваш вопрос.")
    else:
        bot.send_message(message.chat.id, "Вы не можете задать вопрос.")
# Проверяем, если пользователь в состоянии ввода вопроса


@bot.message_handler(func=is_asking_question)
def save_question(message):
    """
    Сохранение вопроса в БД
    """
    tg_id = str(message.chat.id)
    user = User.objects.filter(tg_id=tg_id).first()

    if user:
        text = message.text
        speaker = Speaker.objects.first()
        if speaker:
            Question.objects.create(user=user, speaker=speaker, text=text)
            bot.send_message(message.chat.id, "Ваш вопрос отправлен.")
        else:
            bot.send_message(
                message.chat.id, "В настоящий момент нет докладчиков.")
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы.")

    # Ну и очищаем состояние
    user_states.pop(tg_id, None)


# Проверяем, если пользователь нажал кнопку "Посмотреть вопросы"
def is_view_questions_command(message):
    return message.text == "Посмотреть вопросы"


@bot.message_handler(func=is_view_questions_command)
def view_questions(message):
    """
    Handle the "Посмотреть вопросы" button for speakers.
    """
    tg_id = str(message.chat.id)
    speaker = Speaker.objects.filter(
        tg_id=f"@{message.from_user.username}").first()

    if speaker:
        # Fetch all questions assigned to the speaker
        questions = Question.objects.filter(
            speaker=speaker).order_by('-created_at')
        if questions.exists():
            response = "Ваши вопросы:\n\n" + "\n".join(
                [f"{q.user.first_name}: {q.text}" for q in questions]
            )
        else:
            response = "У вас пока нет вопросов."
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Вы не докладчик.")


if __name__ == "__main__":
    bot.polling()
