import sqlite3

def get_connection():
    return sqlite3.connect('databases.db')

def init_db():
    """Создает таблицы, если они не существуют"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age TEXT NOT NULL
            )
        ''')
        conn.commit()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        ''')
        conn.commit()
# Добавление фото
def add_photo(user_name, file_path):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO photos (user_name, file_path) VALUES (?, ?)', (user_name, file_path))
        conn.commit()
#  Выборка фото пользователя
def get_user_photos(user_name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM photos WHERE user_name = ?', (user_name,))
        return [row[0] for row in cursor.fetchall()]
#    Добавление нового пользователя
def add_user(name, age):
    """Добавляет нового пользователя"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, age) VALUES (?, ?)', (name, age))
        conn.commit()
#  Получение списка всех пользователей
def get_all_users():
    """Возвращает список всех пользователей"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()
#  Проверка авторизации
def prover(name, pas):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE name = ? AND age = ?', (name, pas))
        result = cursor.fetchone()
        return result is not None

# Удаление фото
def delete_photo(file_path):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM photos WHERE file_path = ?', (file_path,))
        conn.commit()