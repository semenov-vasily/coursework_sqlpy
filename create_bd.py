import psycopg2
import configparser

from work_bd import get_password


# Функция создания таблиц words, users, users_words
def create_table(conn):
    cur.execute("""
        DROP TABLE IF EXISTS users_words;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS words;
        """)
    conn.commit()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS words(
        id SERIAL PRIMARY KEY,
        eng VARCHAR(40) NOT NULL UNIQUE,
        rus VARCHAR(40) NOT NULL);
         """)
    conn.commit()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name VARCHAR(40) NOT NULL,
        surname VARCHAR(40),
        nickname VARCHAR(40) UNIQUE);
        """)
    conn.commit()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_words(
        id_word INTEGER NOT NULL REFERENCES words(id),
        id_user INTEGER NOT NULL REFERENCES users(id),
        CONSTRAINT users_words_fk PRIMARY KEY (id_word, id_user));
         """)
    conn.commit()


# Функция добавления первоначального списка слов в таблицу words
def add_initial_words(conn, eng, rus):
            cur.execute("""
                INSERT INTO words(eng, rus) 
                VALUES(%s, %s)
                ON CONFLICT (eng) DO NOTHING
                RETURNING id, eng, rus
                """, (eng, rus))
            new_word = cur.fetchone()
            print(f'Добавлена пара слов английское-русский перевод {new_word}')
            conn.commit()


# Отдельное самостоятельное создание, наполнение первоначальным списком слов и
# удаление таблиц users_words, users, words
if __name__ == '__main__':

    with psycopg2.connect(database=get_password()[1], user="postgres", password=get_password()[0]) as conn:
        with conn.cursor() as cur:
            # Создание таблиц
            create_table(conn)

            # Добавление первоначального списка слов в таблицу words
            add_initial_words(conn, 'dictionary', 'словарь')
            add_initial_words(conn, 'green', 'зеленый')
            add_initial_words(conn, 'purple', 'фиолетовый')
            add_initial_words(conn, 'circle', 'круг')
            add_initial_words(conn, 'giant', 'огромный')
            add_initial_words(conn, 'small', 'маленький')
            add_initial_words(conn, 'smartphone', 'смартфон')
            add_initial_words(conn, 'cup', 'чашка')
            add_initial_words(conn, 'bed', 'кровать')
            add_initial_words(conn, 'window', 'окно')
            add_initial_words(conn, 'fear', 'страх')
            add_initial_words(conn, 'headphones', 'наушники')
            add_initial_words(conn, 'table', 'стол')
            add_initial_words(conn, 'wallpaper', 'обои')
            add_initial_words(conn, 'glasses', 'очки')
    conn.close()
