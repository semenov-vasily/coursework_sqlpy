import psycopg2
import configparser


# Функция для чтения password (пароль к postgresSQL),
# name_bd (название базы данных),
# token пользователя Telegram-бота из файла 'password.ini'
def get_password():
    data = configparser.ConfigParser()
    data.read('password.ini')
    password = data["password"]["password"]
    name_bd = data["password"]["name_bd"]
    token = data["password"]["token"]
    return [password, name_bd, token]


# Функция добавления пользователя Telegram в таблицу users
def add_user(name, surname, nickname):
    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                            INSERT INTO users (name, surname, nickname) 
                            VALUES(%s, %s, %s) 
                            ON CONFLICT (nickname) DO NOTHING 
                            RETURNING id, name, surname, nickname""", (name, surname, nickname))
            print(f"Добавлен пользователь {name} {surname} под ником: {nickname}")
            conn.commit()
    conn.close()


# Функция выбора случайного слова для перевода
def get_one_random_word(current_user_id):
    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            try:  # Попытка получения случайной пары слов из таблицы words
                # Выбор одной случайной строки из таблицы words
                cur.execute("""
                                SELECT words.id, eng, rus FROM words
                                LEFT JOIN users_words ON words.id = users_words.id_word
                                WHERE users_words.id_word IS NULL OR users_words.id_user = %s
                                ORDER BY RANDOM() LIMIT 1;
                            """, (current_user_id))
                row = cur.fetchone()
                if row:  # Если есть не пустое значение одной случайной строки из таблицы words
                    # Распределение значений полей в переменные row[1] и row[2]
                    return row[1], row[2]
                else:  # Если в таблице нет значений
                    print("Таблица 'words' пуста.")
            except psycopg2.Error as f:  # Вывод ошибки в консоль при неудачном выполнении запроса
                print("Ошибка при выполнении запроса:", f)
    conn.close()


# Функция выбора случайных трех слов для неправильных ответов
def get_three_random_words(current_user_id, target_word):
    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT eng, rus FROM words
                    LEFT JOIN users_words ON words.id = users_words.id_word
                    WHERE (users_words.id_word IS NULL OR users_words.id_user = %s) AND eng != %s
                    ORDER BY RANDOM() LIMIT 3;
                    """, (current_user_id, target_word,))  # Выбор трех случайных строк из таблицы words
            selected_rows = cur.fetchall()
            others = []  # Список трех случайных слов
            # Запись трех случайных слов в список others
            for row in selected_rows:
                word_info = row[0]
                others.append(word_info)
            return others  # Возвращаем список трех случайных слов
    conn.close()


# Функция возвращающая id текущего пользователя Telegram-бота
def get_current_user_id(name):
    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                            SELECT id FROM users  
                            WHERE name = %s 
                            """, (name,))
            curUser = cur.fetchone()
            conn.commit()
    return curUser  # Возвращаем id текущего пользователя Telegram-бота
    conn.close()


# Функция добавления слов в таблицу words пользователем
def add_user_words(conn, eng, rus, user_id):
    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO words(eng, rus) 
                VALUES(%s, %s)
                ON CONFLICT (eng) DO NOTHING
                RETURNING id
                """, (eng, rus))
            word_id = cur.fetchone()
            if not word_id:  # Если id слова NULL (слово не добавилось в таблицу)
                print(f'Слово уже присутствует в таблице')
                return False
            else:  # Иначе (слово добавилось в таблицу) запись в таблицу users_words
                #  id пользователя - id добавленного слова
                cur.execute("""
                    INSERT INTO users_words (id_user, id_word) 
                    VALUES (%s, %s);
                    """, (user_id, word_id))
                print(f'Добавлена новая пара слов английское слово - русский перевод')
                conn.commit()
                return True
    conn.close()


# Функция удаления слов из таблицы words
def delete_words(word, user_id):
    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            cur.execute(""" 
                SELECT id FROM words
                WHERE eng = %s OR rus = %s
                """, (word, word))  # Слово для удаления (русский или английский вариант)
            word_id = cur.fetchone()  # id удаляемого слова
            if word_id is not None:  # Если id удаляемого слова не пустое значение
                cur.execute("""
                    SELECT * FROM users_words
                    WHERE id_user = %s AND id_word = %s
                    """, (user_id, word_id))
                user_word = cur.fetchone()  # Значения строки users_words по параметрам
                if user_word is not None:  # Если значения строки users_words не пустое значение
                    # Удаление значений из таблицы users_words
                    cur.execute("""
                        DELETE FROM users_words
                        WHERE id_user = %s AND id_word = %s
                        """, (user_id, word_id))
                    # Удаление значений из таблицы words
                    cur.execute("""
                        DELETE FROM words
                        WHERE id = %s
                        """, (word_id,))
                    print(f'Удалено слово')
                    conn.commit()
                    return True
                else:
                    return False
            else:
                return False
    conn.close()


