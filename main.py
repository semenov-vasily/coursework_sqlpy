import random
from telebot_router import TeleBot
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
import psycopg2

from work_bd import delete_words
from work_bd import get_password
from work_bd import add_user
from work_bd import get_current_user_id
from work_bd import add_user_words
from work_bd import get_one_random_word
from work_bd import get_three_random_words


try:
    # Попытка подключения с БД и проверка на ошибку
    connection = psycopg2.connect(dbname=get_password()[1], user='postgres', password=get_password()[0])
except:
    # Выполнение если подключение не удалось
    print('Не удалось подключится к базе данных')

print('Start telegram bot...')

#  Объект для связи с БД объявление курсора
cursor = connection.cursor()

state_storage = StateMemoryStorage()

# Установка значения токена Telegram-бота
token_bot = get_password()[2]
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []  # Список кнопок


# Функция подсказок при вводе ответа в Telegram-боте
def show_hint(*lines):
    return '\n'.join(lines)


# Функция показывающая слово для перевода
def show_target(data):
    return f'слово ({data['target_word']}) переводится как ({data['translate_word']})'


class Command:  # Надписи на кнопках в Telegram-боте
    ADD_WORD = 'ДОБАВИТЬ СЛОВО ➕'
    DELETE_WORD = 'УДАЛИТЬ СЛОВО 🔙'
    NEXT = 'ДАЛЬШЕ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


# Функция при работе с Telegram-ботом от пользователя
def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['cards', 'start', 's'])  # Аннатация для запуска бота
# функция для создания вариантов ответов
def create_cards(message):
    cid = message.chat.id
    # Добавление в таблицу users текущего пользователя
    # Присваиваем переменной current_user_id id текущего пользователя
    current_user_id = get_current_user_id(message.from_user.first_name)
    # Если id текущего пользователя пустое значение (пользователь впервые запустил Telegram-бота)
    if not current_user_id:
        # Добавляем текущего пользователя в таблицу users
        add_user(message.from_user.first_name, message.from_user.last_name,message.from_user.username)
        print('Пользователь добавлен')
        # Приветственное сообщение в Telegram-боте
        bot.send_message(cid, "Привет 👋 Давай попрактикуемся в английском языке.")
        # Присваиваем переменной current_user_id id текущего пользователя
        current_user_id = get_current_user_id(message.from_user.first_name)
    # Если текущий пользователь уже записан в таблицу users выдаем сообщение
    else:
        bot.send_message(cid, "Давай еще попрактикуемся в английском языке.")
    print(current_user_id)
    if cid not in known_users:  # Если пользователя нет в списке known_users
        known_users.append(cid)  # Добавляем пользователя в список known_users
        userStep[cid] = 0
    markup = types.ReplyKeyboardMarkup(row_width=4)  # Задаем количество кнопок в одной строке

    global buttons  # Объявляем глобальную переменную кнопок
    buttons = []  # Список кнопок
    # Получение слова с переводом из списка, доступного для данного пользователя
    # Присваивание этих слов переменным target_word, translate
    target_word, translate = get_one_random_word(current_user_id)
    # Присваиваем одной из кнопок правильное значение перевода
    target_word_btn = types.KeyboardButton(str(target_word))
    # Добавляем эту кнопку в список кнопок buttons
    buttons.append(target_word_btn)

    # Получение трех случайных вариантов неправильного перевода,
    # В этом списке нет дублирования слов
    others = get_three_random_words(current_user_id, target_word)
    print(others)  # Вывод в консоль список этих трех случайных слов

    # Создание 3 кнопок с вариантами неправильных ответов
    other_words_btns = [types.KeyboardButton(str(word)) for word in others]
    # Добавление в список buttons списка other_words_btns (с вариантами неправильных ответов)
    buttons.extend(other_words_btns)
    random.shuffle(buttons)  # Перемешиваем значения внутри списка buttons
    next_btn = types.KeyboardButton(Command.NEXT)  # Создание кнопки ДАЛЬШЕ
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)  # создание кнопки ДОБАВИТЬ СЛОВО
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)  # создание кнопки УДАЛИТЬ СЛОВО
    # Добавление в список buttons кнопок  ДАЛЬШЕ, ДОБАВИТЬ СЛОВО, УДАЛИТЬ СЛОВО
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)  # Добавление списка  кнопок buttons в разметку бота

    # Присваиваем переменной greeting значение русского слова для перевода
    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    # Отправка сообщения greeting пользователю с установленными параметрами разметки
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    # Установка нового состояния пользователя
    bot.set_state(message.from_user.id, MyStates.target_word,message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


# Функция запуска кнопки ДАЛЬШЕ
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


# Функция запуска кнопки УДАЛИТЬ СЛОВО
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
# Функция запрашивающая слово для удаления
def delete_word(message):
    # Присваиваем переменной cid значение текущего id чата, полученного из сообщения message
    cid = message.chat.id
    # Присваиваем значение текущего шага
    userStep[cid] = 1
    # Отправка сообщения в текущий чат
    bot.send_message(cid,"Введите слово на английском или на русском для удаления:")
    bot.register_next_step_handler(message, process_user_deleteinput)


# Функция вызывающая функцию , удаляющую слово, полученное из delete_word
def process_user_deleteinput(message):
    # Присваиваем cid значение текущего id чата, полученного из сообщения message
    cid = message.chat.id
    # Присваиваем word_to_delete значение message.text
    word_to_delete = str(message.text)
    print(word_to_delete)
    current_uid = get_current_user_id(message.from_user.first_name)
    # Если удаляемое слово прошло проверку и было удалено в функции delete_words
    # Если при выполнении функции delete_words вернулось True
    if delete_words(word_to_delete, current_uid):
        bot.send_message(cid, "Слово удалено")
    # Если при выполнении функции delete_words вернулось False
    else:
        bot.send_message(cid, "Вы можете удалить только те слова которые добавили сами")
    create_cards(message)  # Возврат на стартовую страницу в Telegram-боте


# Функция запуска кнопки ДОБАВИТЬ СЛОВО
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
# функция запрашивающая слово для добавления
def add_word(message):
    # Присваиваем cid значение текущего id чата, полученного из сообщения message
    cid = message.chat.id
    # Присваиваем значение текущего шага
    userStep[cid] = 1
    # Отправка сообщения в текущий чат
    bot.send_message(cid,"Введите слово на английском и русском языке ЧЕРЕЗ ПРОБЕЛ,"
                            " для добавления в таблицу слов:")
    bot.register_next_step_handler(message, process_user_input)


# Функция обработки введенных слов, разделение строки на два слова, добавление в БД
def process_user_input(message):
    # присваиваем cid значение текущего id чата, полученного из сообщения message
    cid = message.chat.id
    # Присваиваем переменной words список из двух слов которые ввел пользователь
    words = str(message.text).split()
    if len(words) == 2:
        # Присваиваем переменным eng_word_to_add, rus_word_to_add значения списка words
        eng_word_to_add, rus_word_to_add = words
    # Присваиваем переменная current_uid id текущего пользователя
    current_uid = get_current_user_id(message.from_user.first_name)
    # Вызов функции add_user_words для добавления в таблицу words значения списка words
    # Если при выполнении функции add_user_words вернулось True
    if add_user_words(connection, eng_word_to_add, rus_word_to_add, current_uid):
        # Отправляем сообщение в текущий чат
        bot.send_message(cid, "Добавлена новая пара слов английское слово - русский перевод")
        create_cards(message)  # возврат на стартовую страницу в боте
    # Если при выполнении функции add_user_words вернулось False
    else:
        bot.send_message(cid, "Слово уже присутствует в таблице")
        create_cards(message)  # Возврат на стартовую страницу в Telegram-боте
    print(add_user_words(connection, eng_word_to_add, rus_word_to_add, current_uid))


# Функция, отвечающая за ответы Telegram-боте
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    # Присваиваем переменной text значение text из сообщения message
    text = message.text
    # Задаем количество кнопок в одой строке
    markup = types.ReplyKeyboardMarkup(row_width=4)
    # Вызываем в контексте id пользователя и id чата
    with bot.retrieve_data(message.from_user.id,message.chat.id) as data:
        # Присваиваем переменной target_word значение из контекста
        target_word = data['target_word']
        if text == target_word:  # Проверка правильности выбранного ответа
            # Присваиваем переменной hint значение,
            # полученное в результате выполнения функции show_target
            hint = show_target(data)
            # Создаем список hint_text
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)  # Формирование строки ответа
            for btn in buttons:
                if btn.text == text:
                    # Добавление сердечка в кнопку правильного ответа
                    btn.text = text + '❤'
                    break
        else:
            # Если ответ неправильный
            for btn in buttons:
                if btn.text == text:
                    # Добавление крестика в кнопку неправильного ответа
                    btn.text = text + '❌'
                    break
            # Формируем сообщение
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)  # Формируем разметку кнопок
    # Отправка сообщения с ответом пользователю о правильном/нет переводе слова
    bot.send_message(message.chat.id, hint, reply_markup=markup)
    if text == target_word:
        create_cards(message)  # Возврат на стартовую страницу в Telegram-боте


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
