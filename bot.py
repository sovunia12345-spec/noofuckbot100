import telebot
from telebot import types
import json
import os
import csv
from datetime import datetime, timedelta
import requests
import time
import sqlite3
import logging
import threading
import random
import socket

# ================== НАСТРОЙКА ЛОГГИРОВАНИЯ ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ================== ПРОВЕРКА ПОДКЛЮЧЕНИЯ К ИНТЕРНЕТУ ==================
def test_internet_connection():
    """Проверяет подключение к интернету"""
    try:
        socket.gethostbyname('api.telegram.org')
        print("✅ DNS разрешение работает")
        response = requests.get('https://api.telegram.org', timeout=10)
        print("✅ Подключение к Telegram API работает")
        return True
    except socket.gaierror as e:
        print(f"❌ Ошибка DNS: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


print("🔍 Проверяем подключение к интернету...")
if not test_internet_connection():
    print("❌ Нет подключения к интернету. Проверьте:")
    print("   • Интернет-соединение")
    print("   • Настройки DNS")
    print("   • Блокировку Telegram")
    exit(1)

# ================== СОЗДАНИЕ БОТА ==================
import os

# Получаем токен из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("✕ Ошибка: BOT_TOKEN не установлен")
    exit(1)

try:
    bot = telebot.TeleBot(BOT_TOKEN)
    bot_info = bot.get_me()
    print(f"☐ Бот {bot_info.first_name} создан успешно")
except Exception as e:
    print(f"✕ Ошибка создания бота: {e}")
    exit(1)

# ================== КОНФИГУРАЦИЯ ==================
USERS_FILE = 'users.json'
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1qsffjxK5k8RZpAViVctPW8_hGmxVxGyrFbcGiBxeh18/edit#gid=0"
SUGGESTIONS_CHANNEL = '-1003025188845'
PASSWORD = "admin123"
CREDIT_CHANNEL = '-1003025188845'

ADMIN_IDS = [755395834, 6702500580]

# Система ежедневных бонусов
DAILY_BONUS_VARIANTS = [
    {"min": 5, "max": 15, "probability": 0.6},
    {"min": 16, "max": 30, "probability": 0.3},
    {"min": 31, "max": 50, "probability": 0.1}
]

BONUS_STREAK_REWARDS = {
    3: 25,
    7: 50,
    14: 100,
    30: 200
}

# Система уровней и опыта
LEVELS_CONFIG = {
    1: {"xp_required": 0, "reward": 0, "name": "Новичок"},
    2: {"xp_required": 100, "reward": 50, "name": "Ученик"},
    3: {"xp_required": 300, "reward": 100, "name": "Активист"},
    4: {"xp_required": 600, "reward": 150, "name": "Опытный"},
    5: {"xp_required": 1000, "reward": 200, "name": "Эксперт"},
    6: {"xp_required": 1500, "reward": 300, "name": "Мастер"},
    7: {"xp_required": 2100, "reward": 400, "name": "Гуру"},
    8: {"xp_required": 2800, "reward": 500, "name": "Легенда"}
}

XP_REWARDS = {
    "daily_bonus": 10,
    "purchase": 5,
    "suggestion": 15,
    "quiz_participation": 20,
    "loan_taken": 25,
    "loan_repaid": 30,
    "referral": 50,
    "lottery_purchase": 3
}

user_states = {}
google_sheets_cache = {}
CACHE_DURATION = 300

# ================== ДАННЫЕ МАГАЗИНА ==================
PRODUCTS = {
    "Подарок малый": {
        "name": "🎁 Подарок в Telegram малый",
        "description": "Любой подарок в Telegram на ваш вкус\n\n• Максимальное количество: 100 ⭐",
        "price": 250,
        "category": "🎁 Подарки в Telegram"
    },
    "Подарок большой": {
        "name": "🎁 Подарок в Telegram большой",
        "description": "Любой подарок в Telegram на ваш вкус\n\n• Максимальное количество: 250 ⭐",
        "price": 320,
        "category": "🎁 Подарки в Telegram"
    },
    "Урок": {
        "name": "💬 Консультация",
        "description": "Индивидуальный урок с Никитой по любым темам, которые трудно даются\n\n• Длительность: 1,5-2 часа\n• Формат: онлайн\n• Запись: предоставляется",
        "price": 200,
        "category": "👥 Персональные"
    },
    "Подписка": {
        "name": "💎 Telegram-Премиум",
        "description": "Подарочная платная подписка, которая открывает доступ к расширенному функционалу мессенджера\n\n• Длительность: 3 месяца",
        "price": 600,
        "category": "🎁 Подарки в Telegram"
    },
    "Сертификат 500 руб": {
        "name": "🎫 Сертификат №1",
        "description": "Сертификат, который позволяет оплатить покупку на маркет-плейсах\n\n• Максимальная цена: 500 рублей\n• Озон/ Золотое яблоко/ Л'Этуаль\n• Длительность: бессрочные",
        "price": 360,
        "category": "📜 Сертификаты"
    },
    "Сертификат 1000 руб": {
        "name": "🎫 Сертификат №2",
        "description": "Сертификат, который позволяет оплатить покупку на маркет-плейсах\n\n• Максимальная цена: 1000 рублей\n• Озон/ Золотое яблоко/ Л'Этуаль\n• Длительность: бессрочные",
        "price": 550,
        "category": "📜 Сертификаты"
    },
    "Сладости": {
        "name": "🍬 Сладости",
        "description": "Вкусняшки на ваш вкус, которые заказываются курьерской доставкой (например, Самокат)\n\n• Максимальная цена: 500 рублей",
        "price": 340,
        "category": "👥 Персональные"
    },
    "Сходка": {
        "name": "🥳 Сходка",
        "description": "Если вы идете на сходка - можете воспользоваться данной услугой вместо оплаты квеста\n\n• Квест оплачивается за вас\n• В данной опции включен перекус до 500 рублей после квеста (по традиции)",
        "price": 790,
        "category": "👥 Персональные"
    },
    "Мерч": {
        "name": "🔥 Мерч нооfuck'а",
        "description": "Эклюзивный контент, разработанный командой нооfuck'а\n\n• Версия ограничена по количеством\n• Уточняйте наличие перед покупкай",
        "price": 300,
        "category": "👥 Персональные"
    }
}

# ================= БАЗА ДАННЫХ БАЛАНСОВ ==================
BALANCE_DB = 'user_balances.db'


def get_db_connection():
    """Создает соединение с базой данных"""
    conn = sqlite3.connect(
        BALANCE_DB,
        timeout=30.0,
        check_same_thread=False
    )
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_balance_db():
    """Инициализация базы данных для балансов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                credit_balance INTEGER DEFAULT 0,
                google_balance INTEGER DEFAULT 0,
                google_sync_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                amount INTEGER,
                type TEXT,
                description TEXT,
                product_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                amount INTEGER,
                interest_rate REAL DEFAULT 14.0,
                term_weeks INTEGER DEFAULT 12,
                weekly_payment INTEGER,
                interest_payment_cycle_hours INTEGER DEFAULT 504,
                next_principal_date TEXT,
                next_interest_date TEXT,
                total_paid_principal INTEGER DEFAULT 0,
                total_paid_interest INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id INTEGER,
                user_id TEXT,
                amount INTEGER,
                payment_type TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (loan_id) REFERENCES loans (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                last_claim_date TEXT,
                streak_count INTEGER DEFAULT 0,
                total_claims INTEGER DEFAULT 0,
                total_bonus_received INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_levels (
                user_id TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                total_xp INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                purchases_count INTEGER DEFAULT 0,
                bonuses_claimed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lotteries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                ticket_price INTEGER,
                prize_pool INTEGER DEFAULT 0,
                max_tickets INTEGER,
                tickets_sold INTEGER DEFAULT 0,
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'active',
                winner_user_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lottery_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lottery_id INTEGER,
                user_id TEXT,
                ticket_number INTEGER,
                purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lottery_id) REFERENCES lotteries (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT,
                message_text TEXT,
                message_type TEXT DEFAULT 'text',
                file_id TEXT,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                scheduled_for TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                notification_type TEXT,
                title TEXT,
                message TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                related_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ТАБЛИЦА ДЛЯ КОДОВЫХ СЛОВ ВИКТОРИН
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                quiz_name TEXT NOT NULL,
                xp_reward INTEGER DEFAULT 20,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )
        ''')

        # ТАБЛИЦА ДЛЯ ИСПОЛЬЗОВАНИЯ КОДОВ ПОЛЬЗОВАТЕЛЯМИ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                code TEXT NOT NULL,
                quiz_name TEXT NOT NULL,
                xp_earned INTEGER NOT NULL,
                used_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, code)
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Все таблицы базы данных инициализированы")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")


def upgrade_database():
    """Обновляет структуру базы данных до актуальной версии"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'google_balance' not in columns:
            print("🔄 Добавляем поле google_balance...")
            cursor.execute('ALTER TABLE users ADD COLUMN google_balance INTEGER DEFAULT 0')
            cursor.execute('UPDATE users SET google_balance = balance WHERE google_balance IS NULL')
            print("✅ Поле google_balance добавлено")

        conn.commit()
        conn.close()
        print("✅ База данных успешно обновлена")

    except Exception as e:
        print(f"❌ Ошибка обновления БД: {e}")


# Инициализируем БД
init_balance_db()
upgrade_database()


# ================== ФУНКЦИИ ДЛЯ АДМИНИСТРАТОРОВ ==================
def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


def admin_required(func):
    """Декоратор для ограничения доступа к командам администратора"""

    def wrapper(message):
        user_id = message.from_user.id
        if is_admin(user_id):
            return func(message)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды")

    return wrapper


# ================== ФУНКЦИИ GOOGLE ТАБЛИЦ ==================
def load_google_sheets_data(force_refresh=False):
    """Загружает и парсит данные из Google Sheets"""
    global google_sheets_cache

    if not force_refresh and 'data' in google_sheets_cache:
        cache_time = google_sheets_cache.get('timestamp', 0)
        if time.time() - cache_time < CACHE_DURATION:
            print("📊 Используем кэшированные данные Google Sheets")
            return google_sheets_cache['data']

    try:
        sheet_id = GOOGLE_SHEETS_URL.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

        print(f"📥 Загружаем данные из: {csv_url}")
        response = requests.get(csv_url, timeout=30)

        if response.status_code == 200:
            response.encoding = 'utf-8'
            csv_data = response.text

            if '    ' in csv_data or 'Ð' in csv_data:
                response.encoding = 'cp1251'
                csv_data = response.text

            lines = csv_data.strip().split('\n')
            print(f"📊 Получено строк: {len(lines)}")

            users_data = {}
            headers = []

            for i, line in enumerate(lines):
                cells = []
                current_cell = ""
                in_quotes = False

                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        cells.append(current_cell.strip())
                        current_cell = ""
                    else:
                        current_cell += char

                if current_cell:
                    cells.append(current_cell.strip())

                cells = [cell.strip('"') for cell in cells]

                if i == 0:
                    headers = cells
                    continue

                if not any(cells) or len(cells) < 4:
                    continue

                user_id = cells[1] if len(cells) > 1 else None

                if user_id and user_id.isdigit():
                    user_name = cells[2] if len(cells) > 2 else "Неизвестно"

                    credit_column_index = 3
                    if len(cells) > credit_column_index:
                        credit_value = cells[credit_column_index]
                        try:
                            credit_amount = float(credit_value) if credit_value.strip() else 0
                        except ValueError:
                            credit_amount = 0
                    else:
                        credit_amount = 0

                    scores = {}
                    total_score = 0
                    count_3_4 = 0
                    penalty_applied = 0

                    for j in range(5, len(cells)):
                        if j < len(headers) and j < len(cells):
                            column_name = headers[j] if j < len(headers) else f"Column_{j}"
                            cell_value = cells[j]

                            if cell_value and cell_value.strip():
                                try:
                                    numeric_value = int(cell_value)
                                    points = 0

                                    if numeric_value == 1:
                                        points = 10
                                    elif numeric_value == 2:
                                        points = 5
                                    elif numeric_value in [3, 4]:
                                        points = 0
                                        count_3_4 += 1
                                        if count_3_4 > 2:
                                            points = -20
                                            penalty_applied += 1
                                    elif numeric_value == 5:
                                        points = 15
                                    elif numeric_value == 6:
                                        points = 8
                                    elif numeric_value == 7:
                                        points = 20
                                    elif numeric_value == 8:
                                        points = -20
                                    elif numeric_value == 9:
                                        points = 15
                                    elif numeric_value == 10:
                                        points = 15
                                    elif numeric_value == 11:
                                        points = 8
                                    elif numeric_value == 12:
                                        points = 30
                                    elif numeric_value == 13:
                                        points = -30
                                    elif numeric_value == 14:
                                        points = -15
                                    elif numeric_value == 15:
                                        points = -10
                                    elif numeric_value == 16:
                                        points = -15
                                    elif numeric_value == 17:
                                        points = -20
                                    elif numeric_value == 18:
                                        points = -20
                                    elif numeric_value == 19:
                                        points = 15
                                    elif numeric_value == 20:
                                        points = -10
                                    elif numeric_value == 21:
                                        points = 25
                                    elif numeric_value == 22:
                                        points = -25
                                    elif numeric_value == 23:
                                        points = 5
                                    elif numeric_value == 24:
                                        points = 3
                                    else:
                                        points = 0

                                    scores[column_name] = {
                                        'value': numeric_value,
                                        'points': points
                                    }
                                    total_score += points

                                except ValueError:
                                    scores[column_name] = {
                                        'value': cell_value,
                                        'points': 0,
                                        'description': f'Текстовое значение: {cell_value}'
                                    }

                    if penalty_applied > 0:
                        scores['penalty_info'] = {
                            'value': f'Штраф за просроченные ДД',
                            'points': -20 * penalty_applied,
                            'description': f'Штраф -20 баллов за {penalty_applied} просроченных ДД после лимита'
                        }

                    users_data[user_id] = {
                        'name': user_name,
                        'scores': scores,
                        'total_score': total_score,
                        'count_3_4': count_3_4,
                        'penalty_applied': penalty_applied,
                        'credit': credit_amount,
                        'raw_data': cells
                    }

            print(f"✅ Обработано пользователей: {len(users_data)}")

            google_sheets_cache = {
                'data': users_data,
                'timestamp': time.time()
            }

            return users_data

        else:
            print(f"❌ Ошибка загрузки: HTTP {response.status_code}")
            return {}

    except Exception as e:
        print(f"❌ Ошибка загрузки из Google Sheets: {e}")
        return {}


def calculate_balance_from_google(user_id):
    """Рассчитывает баланс из Google таблицы"""
    try:
        users_data = load_google_sheets_data()
        user_id_str = str(user_id)

        if user_id_str in users_data:
            return users_data[user_id_str]['total_score']
        else:
            return 0
    except Exception as e:
        print(f"❌ Ошибка расчета баланса из Google: {e}")
        return 0


def sync_user_balance(user_id):
    """Синхронизирует баланс пользователя с Google таблицей"""
    try:
        users_data = load_google_sheets_data()
        user_id_str = str(user_id)

        if user_id_str in users_data:
            google_balance = users_data[user_id_str]['total_score']
        else:
            google_balance = 0

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance, google_balance FROM users WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        if result:
            current_balance, current_google_balance = result

            if current_google_balance != google_balance:
                balance_diff = google_balance - current_google_balance

                if balance_diff != 0:
                    cursor.execute(
                        'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                        (str(user_id), balance_diff, 'google_sync', 'Корректировка по Google таблице')
                    )

                    cursor.execute('''
                        SELECT COALESCE(SUM(amount), 0) FROM transactions 
                        WHERE user_id = ? AND type != 'initial'
                    ''', (str(user_id),))

                    total_transactions = cursor.fetchone()[0]
                    new_balance = google_balance + total_transactions

                    cursor.execute(
                        'UPDATE users SET balance = ?, google_balance = ?, google_sync_date = ? WHERE user_id = ?',
                        (new_balance, google_balance, datetime.now().isoformat(), str(user_id))
                    )

                    print(
                        f"✅ Баланс синхронизирован: {user_id} Google: {google_balance} -> Локальные: {total_transactions} = Итого: {new_balance}")
                else:
                    cursor.execute(
                        'UPDATE users SET google_sync_date = ? WHERE user_id = ?',
                        (datetime.now().isoformat(), str(user_id))
                    )
                    print(f"✅ Баланс пользователя {user_id} уже актуален")
        else:
            cursor.execute(
                'INSERT INTO users (user_id, balance, credit_balance, google_balance, google_sync_date) VALUES (?, ?, ?, ?, ?)',
                (str(user_id), google_balance, 0, google_balance, datetime.now().isoformat())
            )

            cursor.execute(
                'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (str(user_id), google_balance, 'initial', 'Начальный баланс из Google таблицы')
            )

            print(f"✅ Создан пользователь {user_id} с балансом {google_balance}")

        conn.commit()
        conn.close()

        return google_balance

    except Exception as e:
        print(f"❌ Ошибка синхронизации баланса: {e}")
        return 0


# ================== ФУНКЦИИ БАЗЫ ДАННЫХ ==================
def get_user_balance(user_id):
    """Получает основной баланс пользователя"""
    try:
        sync_user_balance(user_id)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        else:
            return create_user_in_db(user_id)

    except Exception as e:
        print(f"❌ Ошибка получения баланса: {e}")
        return 0


def get_user_credit_balance(user_id):
    """Получает кредитный баланс пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT credit_balance FROM users WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        conn.close()

        if result:
            return result[0]
        else:
            create_user_in_db(user_id)
            return 0

    except Exception as e:
        print(f"❌ Ошибка получения кредитного баланса: {e}")
        return 0


def create_user_in_db(user_id):
    """Создает пользователя в БД с начальным балансом из Google таблицы"""
    try:
        initial_balance = calculate_balance_from_google(user_id)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO users (user_id, balance, credit_balance, google_sync_date) VALUES (?, ?, ?, ?)',
            (str(user_id), initial_balance, 0, datetime.now().isoformat())
        )

        cursor.execute(
            'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
            (str(user_id), initial_balance, 'initial', 'Начальный баланс из Google таблицы')
        )

        cursor.execute(
            'INSERT INTO daily_bonuses (user_id, streak_count, total_claims, total_bonus_received) VALUES (?, ?, ?, ?)',
            (str(user_id), 0, 0, 0)
        )

        cursor.execute(
            'INSERT INTO user_levels (user_id, xp, level, total_xp) VALUES (?, ?, ?, ?)',
            (str(user_id), 0, 1, 0)
        )

        conn.commit()
        conn.close()

        print(f"✅ Создан пользователь {user_id} с балансом {initial_balance}")
        return initial_balance

    except Exception as e:
        print(f"❌ Ошибка создания пользователя в БД: {e}")
        return 0


def update_user_balance(user_id, amount, description, product_id=None):
    """Обновляет основной баланс пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        if not result:
            conn.close()
            create_user_in_db(user_id)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (str(user_id),))
            result = cursor.fetchone()

        current_balance = result[0]
        new_balance = current_balance + amount

        if new_balance < 0:
            conn.close()
            return False

        cursor.execute(
            'UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?',
            (new_balance, datetime.now().isoformat(), str(user_id))
        )

        transaction_type = 'purchase' if amount < 0 else 'credit' if amount > 0 else 'other'
        cursor.execute(
            'INSERT INTO transactions (user_id, amount, type, description, product_id) VALUES (?, ?, ?, ?, ?)',
            (str(user_id), amount, transaction_type, description, product_id)
        )

        conn.commit()
        conn.close()

        print(f"✅ Баланс обновлен: {user_id} {amount:+} = {new_balance} ({description})")
        return True

    except Exception as e:
        print(f"❌ Ошибка обновления баланса: {e}")
        return False


def update_user_credit_balance(user_id, amount, description):
    """Обновляет кредитный баланс пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT credit_balance FROM users WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        if not result:
            conn.close()
            create_user_in_db(user_id)
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT credit_balance FROM users WHERE user_id = ?', (str(user_id),))
            result = cursor.fetchone()

        current_credit = result[0]
        new_credit = current_credit + amount

        cursor.execute(
            'UPDATE users SET credit_balance = ?, updated_at = ? WHERE user_id = ?',
            (new_credit, datetime.now().isoformat(), str(user_id))
        )

        cursor.execute(
            'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
            (str(user_id), amount, 'credit_operation', description)
        )

        conn.commit()
        conn.close()

        print(f"✅ Кредитный баланс обновлен: {user_id} {amount:+} = {new_credit} ({description})")
        return True

    except Exception as e:
        print(f"❌ Ошибка обновления кредитного баланса: {e}")
        return False


def get_user_transactions(user_id, limit=10):
    """Получает историю транзакций пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT amount, type, description, created_at 
            FROM transactions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (str(user_id), limit))

        transactions = cursor.fetchall()
        conn.close()

        return transactions

    except Exception as e:
        print(f"❌ Ошибка получения транзакций: {e}")
        return []


# ================== СИСТЕМА УРОВНЕЙ И ОПЫТА ==================
def add_xp(user_id, xp_amount, reason):
    """Добавляет опыт пользователю и проверяет повышение уровня"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT xp, level, total_xp FROM user_levels WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        if not result:
            cursor.execute(
                'INSERT INTO user_levels (user_id, xp, level, total_xp) VALUES (?, ?, ?, ?)',
                (str(user_id), xp_amount, 1, xp_amount)
            )
            current_xp = xp_amount
            current_level = 1
            total_xp = xp_amount
        else:
            current_xp = result[0] + xp_amount
            current_level = result[1]
            total_xp = result[2] + xp_amount

            cursor.execute(
                'UPDATE user_levels SET xp = ?, total_xp = ?, updated_at = ? WHERE user_id = ?',
                (current_xp, total_xp, datetime.now().isoformat(), str(user_id))
            )

        new_level = calculate_level(current_xp)
        level_up = False
        level_reward = 0

        if new_level > current_level:
            level_up = True
            cursor.execute(
                'UPDATE user_levels SET level = ? WHERE user_id = ?',
                (new_level, str(user_id))
            )

            reward = LEVELS_CONFIG[new_level]["reward"]
            if reward > 0:
                cursor.execute('SELECT balance FROM users WHERE user_id = ?', (str(user_id),))
                user_balance_result = cursor.fetchone()

                if user_balance_result:
                    new_balance = user_balance_result[0] + reward
                    cursor.execute(
                        'UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?',
                        (new_balance, datetime.now().isoformat(), str(user_id))
                    )

                    cursor.execute(
                        'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                        (str(user_id), reward, 'level_reward', f'Награда за достижение {new_level} уровня')
                    )

                    level_reward = reward

                    print(f"🎉 Пользователь {user_id} достиг {new_level} уровня! Награда: {reward} баллов")

        conn.commit()
        conn.close()

        if level_up and level_reward > 0:
            try:
                level_up_message = f"""🎉 ПОЗДРАВЛЯЕМ! ВЫ ДОСТИГЛИ {new_level} УРОВНЯ!

🏆 Новый уровень: {new_level} ({LEVELS_CONFIG[new_level]['name']})
💰 Награда: +{level_reward} баллов
⭐ Текущий опыт: {current_xp}

Продолжайте в том же духе! 🚀"""

                bot.send_message(user_id, level_up_message)

                send_user_notification(
                    user_id,
                    "level_up",
                    f"🎉 Поздравляем! Вы достигли {new_level} уровня!",
                    f"Вы достигли уровня {new_level} ({LEVELS_CONFIG[new_level]['name']}) и получаете {level_reward} баллов!",
                    f"level_{new_level}"
                )
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления о уровне: {e}")

        return level_up, new_level, level_reward

    except Exception as e:
        print(f"❌ Ошибка добавления опыта: {e}")
        return False, 1, 0


def calculate_level(xp):
    """Рассчитывает уровень на основе опыта"""
    try:
        sorted_levels = sorted(LEVELS_CONFIG.items(), key=lambda x: x[1]["xp_required"])

        current_level = 1
        for level, config in sorted_levels:
            if xp >= config["xp_required"]:
                current_level = level
            else:
                break

        return current_level
    except Exception as e:
        print(f"❌ Ошибка расчета уровня: {e}")
        return 1


def get_user_level_info(user_id):
    """Получает информацию об уровне пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT xp, level, total_xp FROM user_levels WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()
        conn.close()

        if result:
            xp, level, total_xp = result
            next_level = level + 1
            if next_level in LEVELS_CONFIG:
                xp_required = LEVELS_CONFIG[next_level]["xp_required"]
                xp_needed = xp_required - xp
            else:
                xp_required = "Макс."
                xp_needed = 0

            return {
                'level': level,
                'xp': xp,
                'total_xp': total_xp,
                'level_name': LEVELS_CONFIG[level]["name"],
                'next_level': next_level,
                'xp_needed': xp_needed,
                'xp_required': xp_required
            }
        else:
            add_xp(user_id, 0, "initial")
            return get_user_level_info(user_id)

    except Exception as e:
        print(f"❌ Ошибка получения информации об уровне: {e}")
        return None


def show_levels_menu(message):
    """Показывает меню уровней"""
    user_id = str(message.from_user.id)
    level_info = get_user_level_info(user_id)

    if not level_info:
        bot.send_message(user_id, "❌ Ошибка загрузки информации об уровнях")
        return

    levels_text = f"""🏆 СИСТЕМА УРОВНЕЙ

📊 Ваш прогресс:
• 🎯 Уровень: {level_info['level']} ({level_info['level_name']})
• ⭐ Опыт: {level_info['xp']} / {level_info['xp_required']}
• 💫 До следующего уровня: {level_info['xp_needed']} опыта
• 📈 Всего опыта: {level_info['total_xp']}

🎁 Награды за уровни:"""

    for level in range(2, min(level_info['level'] + 4, len(LEVELS_CONFIG) + 1)):
        if level in LEVELS_CONFIG:
            reward = LEVELS_CONFIG[level]["reward"]
            levels_text += f"\n• {level} уровень: {reward} баллов"

    levels_text += f"\n\n🎯 Как получать опыт:"
    levels_text += f"\n• 🎁 Ежедневный бонус: +{XP_REWARDS['daily_bonus']} опыта"
    levels_text += f"\n• 🛒 Покупки: +{XP_REWARDS['purchase']} за каждые 100 баллов"
    levels_text += f"\n• 💡 Предложения: +{XP_REWARDS['suggestion']} опыта"
    levels_text += f"\n• 🎯 Викторины: +{XP_REWARDS['quiz_participation']} опыта"
    levels_text += f"\n• 💰 Кредиты: +{XP_REWARDS['loan_taken']} за взятие, +{XP_REWARDS['loan_repaid']} за погашение"
    levels_text += f"\n• 🎪 Лотереи: +{XP_REWARDS['lottery_purchase']} за билет"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 В меню"))

    bot.send_message(user_id, levels_text, reply_markup=markup)


# ================== СИСТЕМА ЕЖЕДНЕВНЫХ БОНУСОВ ==================
def get_daily_bonus_info(user_id):
    """Получает информацию о ежедневном бонусе пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT last_claim_date, streak_count, total_claims, total_bonus_received FROM daily_bonuses WHERE user_id = ?',
            (str(user_id),)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'last_claim_date': result[0],
                'streak_count': result[1],
                'total_claims': result[2],
                'total_bonus_received': result[3]
            }
        else:
            create_daily_bonus_user(str(user_id))
            return {
                'last_claim_date': None,
                'streak_count': 0,
                'total_claims': 0,
                'total_bonus_received': 0
            }

    except Exception as e:
        print(f"❌ Ошибка получения информации о бонусе: {e}")
        return None


def create_daily_bonus_user(user_id):
    """Создает запись пользователя в таблице бонусов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO daily_bonuses (user_id, streak_count, total_claims, total_bonus_received) VALUES (?, ?, ?, ?)',
            (str(user_id), 0, 0, 0)
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка создания пользователя бонусов: {e}")
        return False


def can_claim_bonus(user_id):
    """Проверяет, может ли пользователь получить бонус"""
    bonus_info = get_daily_bonus_info(user_id)
    if not bonus_info or not bonus_info['last_claim_date']:
        return True, 0

    last_claim = datetime.fromisoformat(bonus_info['last_claim_date'])
    now = datetime.now()

    if last_claim.date() < now.date():
        days_passed = (now.date() - last_claim.date()).days
        if days_passed == 1:
            return True, bonus_info['streak_count'] + 1
        else:
            return True, 1
    else:
        return False, bonus_info['streak_count']


def generate_daily_bonus(streak):
    """Генерирует случайный бонус с учетом вероятностей"""
    rand = random.random()
    cumulative_prob = 0

    for variant in DAILY_BONUS_VARIANTS:
        cumulative_prob += variant['probability']
        if rand <= cumulative_prob:
            base_bonus = random.randint(variant['min'], variant['max'])
            break
    else:
        base_bonus = random.randint(5, 15)

    streak_bonus = 0
    if streak in BONUS_STREAK_REWARDS:
        streak_bonus = BONUS_STREAK_REWARDS[streak]

    total_bonus = base_bonus + streak_bonus

    return base_bonus, streak_bonus, total_bonus


def claim_daily_bonus(user_id):
    """Выдает ежедневный бонус пользователю"""
    try:
        can_claim, new_streak = can_claim_bonus(user_id)

        if not can_claim:
            return False, "❌ Вы уже получали бонус сегодня!\n\nПриходите завтра! 🎁"

        base_bonus, streak_bonus, total_bonus = generate_daily_bonus(new_streak)

        success = update_user_balance(
            user_id,
            total_bonus,
            'daily_bonus',
            f'Ежедневный бонус (стрик: {new_streak} дней)'
        )

        if not success:
            return False, "❌ Ошибка при начислении бонуса"

        conn = get_db_connection()
        cursor = conn.cursor()

        bonus_info = get_daily_bonus_info(user_id)
        if bonus_info:
            cursor.execute('''
                UPDATE daily_bonuses 
                SET last_claim_date = ?, streak_count = ?, total_claims = total_claims + 1, 
                    total_bonus_received = total_bonus_received + ?, updated_at = ?
                WHERE user_id = ?
            ''', (
                datetime.now().isoformat(),
                new_streak,
                total_bonus,
                datetime.now().isoformat(),
                str(user_id)
            ))
        else:
            cursor.execute('''
                INSERT INTO daily_bonuses (user_id, last_claim_date, streak_count, total_claims, total_bonus_received)
                VALUES (?, ?, ?, 1, ?)
            ''', (
                str(user_id),
                datetime.now().isoformat(),
                new_streak,
                total_bonus
            ))

        conn.commit()
        conn.close()

        add_xp(user_id, XP_REWARDS["daily_bonus"], "daily_bonus")

        message = f"""🎉 ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН!

💰 Основной бонус: {base_bonus} баллов"""

        if streak_bonus > 0:
            message += f"\n🏆 Бонус за серию ({new_streak} дней): +{streak_bonus} баллов"

        message += f"\n💎 Всего получено: {total_bonus} баллов"
        message += f"\n📅 Серия: {new_streak} дней подряд"
        message += f"\n🎯 Опыт: +{XP_REWARDS['daily_bonus']}"
        message += f"\n\n💡 Возвращайтесь завтра за новым бонусом!"

        return True, message

    except Exception as e:
        print(f"❌ Ошибка выдачи бонуса: {e}")
        return False, "❌ Произошла ошибка при получении бонуса"


def handle_daily_bonus(message):
    """Обрабатывает запрос на получение ежедневного бонуса"""
    user_id = str(message.from_user.id)

    processing_msg = bot.send_message(user_id, "🎁 Проверяем ваш бонус...")

    success, result_message = claim_daily_bonus(user_id)

    bot.delete_message(user_id, processing_msg.message_id)

    bonus_info = get_daily_bonus_info(user_id)

    if bonus_info and success:
        stats_text = f"\n\n📊 Ваша статистика:\n"
        stats_text += f"• Текущая серия: {bonus_info['streak_count']} дней\n"
        stats_text += f"• Всего получено: {bonus_info['total_claims']} раз\n"
        stats_text += f"• Сумма бонусов: {bonus_info['total_bonus_received']} баллов"

        result_message += stats_text

    if success:
        next_streak = None
        current_streak = bonus_info['streak_count'] if bonus_info else 0

        for streak in sorted(BONUS_STREAK_REWARDS.keys()):
            if streak > current_streak:
                next_streak = streak
                break

        if next_streak:
            days_needed = next_streak - current_streak
            result_message += f"\n\n🎯 До бонуса за {next_streak} дней осталось: {days_needed} дней"

    bot.send_message(user_id, result_message)


# ================== СИСТЕМА ВИКТОРИН С КОДОВЫМИ СЛОВАМИ ==================
def create_quiz_code(code, quiz_name, xp_reward=20, max_uses=1, created_by="admin", expires_days=30):
    """Создает новое кодовое слово для викторины"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем, существует ли уже такой код
        cursor.execute('SELECT id FROM quiz_codes WHERE code = ?', (code.upper(),))
        if cursor.fetchone():
            conn.close()
            return False

        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat() if expires_days else None

        cursor.execute('''
            INSERT INTO quiz_codes (code, quiz_name, xp_reward, max_uses, created_by, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code.upper(), quiz_name, xp_reward, max_uses, created_by, expires_at))

        conn.commit()
        conn.close()

        print(f"✅ Создан код викторины: {code} для '{quiz_name}'")

        # Отправляем уведомление в канал (опционально)
        try:
            notification = f"🔤 СОЗДАН НОВЫЙ КОД ВИКТОРИНЫ\n\n📝 {quiz_name}\n🔤 Код: {code}\n⭐ Опыт: {xp_reward}\n🎫 Использований: {max_uses}"
            bot.send_message(SUGGESTIONS_CHANNEL, notification)
        except:
            pass

        return True
    except Exception as e:
        print(f"❌ Ошибка создания кода: {e}")
        return False


def use_quiz_code(user_id, code):
    """Использование кодового слова пользователем"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем существование и активность кода
        cursor.execute('''
            SELECT id, quiz_name, xp_reward, max_uses, used_count, is_active, expires_at 
            FROM quiz_codes 
            WHERE code = ?
        ''', (code.upper(),))

        code_data = cursor.fetchone()

        if not code_data:
            conn.close()
            return False, "❌ Код не найден"

        code_id, quiz_name, xp_reward, max_uses, used_count, is_active, expires_at = code_data

        # Проверяем активность кода
        if not is_active:
            conn.close()
            return False, "❌ Код больше не активен"

        # Проверяем срок действия
        if expires_at:
            expires_date = datetime.fromisoformat(expires_at)
            if datetime.now() > expires_date:
                cursor.execute('UPDATE quiz_codes SET is_active = FALSE WHERE id = ?', (code_id,))
                conn.commit()
                conn.close()
                return False, "❌ Срок действия кода истек"

        # Проверяем лимит использований
        if used_count >= max_uses:
            cursor.execute('UPDATE quiz_codes SET is_active = FALSE WHERE id = ?', (code_id,))
            conn.commit()
            conn.close()
            return False, "❌ Код уже использован максимальное количество раз"

        # Проверяем, не использовал ли уже пользователь этот код
        cursor.execute('''
            SELECT id FROM quiz_code_usage 
            WHERE user_id = ? AND code = ?
        ''', (str(user_id), code.upper()))

        if cursor.fetchone():
            conn.close()
            return False, "❌ Вы уже использовали этот код!"

        # Начисляем опыт
        level_up, new_level, reward = add_xp(user_id, xp_reward, f"quiz_{quiz_name}")

        # Обновляем счетчик использований кода
        cursor.execute('''
            UPDATE quiz_codes 
            SET used_count = used_count + 1 
            WHERE id = ?
        ''', (code_id,))

        # Записываем использование кода
        cursor.execute('''
            INSERT INTO quiz_code_usage (user_id, code, quiz_name, xp_earned)
            VALUES (?, ?, ?, ?)
        ''', (str(user_id), code.upper(), quiz_name, xp_reward))

        conn.commit()
        conn.close()

        # Формируем сообщение об успехе
        success_message = f"""🎯 ВИКТОРИНА ПРОЙДЕНА!

📝 Викторина: {quiz_name}
⭐ Получено опыта: +{xp_reward}"""

        if level_up:
            success_message += f"\n🎉 ПОЗДРАВЛЯЕМ! Вы достигли {new_level} уровня!"
            success_message += f"\n💰 Награда: +{reward} баллов"

        success_message += f"\n\n✅ Код успешно активирован!"

        return True, success_message

    except Exception as e:
        print(f"❌ Ошибка использования кода: {e}")
        return False, "❌ Произошла ошибка при активации кода"


def get_active_quiz_codes():
    """Получает список активных кодов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT code, quiz_name, xp_reward, max_uses, used_count, expires_at
            FROM quiz_codes 
            WHERE is_active = TRUE
            ORDER BY created_at DESC
        ''')

        codes = cursor.fetchall()
        conn.close()
        return codes
    except Exception as e:
        print(f"❌ Ошибка получения кодов: {e}")
        return []


def get_user_quiz_history(user_id):
    """Получает историю викторин пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT quiz_name, xp_earned, used_at 
            FROM quiz_code_usage 
            WHERE user_id = ?
            ORDER BY used_at DESC
        ''', (str(user_id),))

        history = cursor.fetchall()
        conn.close()
        return history
    except Exception as e:
        print(f"❌ Ошибка получения истории викторин: {e}")
        return []


def handle_quiz_code(message):
    """Обработчик кодовых слов из викторин"""
    user_id = str(message.from_user.id)
    code = message.text.strip().upper()

    # Игнорируем команды и другие тексты
    if len(code) < 4 or code in ["🔙 НАЗАД", "🔙 ОТМЕНА", "НАЗАД", "ОТМЕНА"]:
        return

    # Показываем индикатор обработки
    processing_msg = bot.send_message(user_id, "🔍 Проверяем код...")

    # Используем код
    success, result_message = use_quiz_code(user_id, code)

    # Удаляем индикатор обработки
    bot.delete_message(user_id, processing_msg.message_id)

    # Отправляем результат
    bot.send_message(user_id, result_message)

    # Если успешно, показываем обновленное меню
    if success:
        show_quizzes_menu(message)


def show_quizzes_menu(message):
    user_id = str(message.from_user.id)

    # Получаем историю викторин пользователя
    quiz_history = get_user_quiz_history(user_id)

    quizzes_text = """🎯 ВИКТОРИНЫ

Здесь вы можете пройти викторины по разным предметам и заработать дополнительные баллы!

📝 Как участвовать:
1. Нажмите на кнопку с нужным предметом
2. Пройдите викторину в Google Forms
3. В конце викторины вы получите кодовое слово
4. Вернитесь в бота и введите полученный код

💡 Награда за прохождение: +20 опыта"""

    # Добавляем историю пройденных викторин
    if quiz_history:
        quizzes_text += "\n\n📊 Ваши пройденные викторины:\n"
        for quiz_name, xp_earned, used_at in quiz_history[:5]:
            date_str = datetime.fromisoformat(used_at).strftime('%d.%m.%Y')
            quizzes_text += f"• {quiz_name} - +{xp_earned} опыта ({date_str})\n"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🧪 ХИМИЯ",
                                   url="https://docs.google.com/forms/d/1iaTFJP18arcNkgzio_z7h0yd-mA0L8HndX4D3VCBjOw/edit"),
        types.InlineKeyboardButton("📚 РУССКИЙ ЯЗЫК",
                                   url="https://docs.google.com/forms/d/19ehazW1CMK24Xw9qRoM9fKSzsFOXbIydGEiv16UOkZc/edit"),
        types.InlineKeyboardButton("🎯 ПРОФИЛЬ",
                                   url="https://docs.google.com/forms/d/1o0ec2Qae3oqKrABPHGZY3iCBcvxgs6eYZ0vs9tqDlo0/edit"),
        types.InlineKeyboardButton("🔢 БАЗА",
                                   url="https://docs.google.com/forms/d/1fa_NDfNVXmEWGhC2hh114c_NXIq19kC5htTMW9558cg/edit")
    )

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_markup.add(types.KeyboardButton("📊 Мои викторины"))
    reply_markup.add(types.KeyboardButton("🔙 В меню"))

    bot.send_message(message.from_user.id, quizzes_text, reply_markup=reply_markup)
    bot.send_message(message.from_user.id, "👇 Выберите викторину:", reply_markup=markup)


def show_my_quizzes(message):
    """Показывает историю викторин пользователя"""
    user_id = str(message.from_user.id)
    quiz_history = get_user_quiz_history(user_id)

    if quiz_history:
        history_text = "📊 ИСТОРИЯ ВАШИХ ВИКТОРИН\n\n"
        total_xp = 0

        for quiz_name, xp_earned, used_at in quiz_history:
            date_str = datetime.fromisoformat(used_at).strftime('%d.%m.%Y %H:%M')
            history_text += f"🎯 {quiz_name}\n"
            history_text += f"   ⭐ +{xp_earned} опыта\n"
            history_text += f"   📅 {date_str}\n\n"
            total_xp += xp_earned

        history_text += f"💫 Всего получено опыта: {total_xp}"
    else:
        history_text = "📊 ИСТОРИЯ ВАШИХ ВИКТОРИН\n\n"
        history_text += "Вы еще не прошли ни одной викторины.\n"
        history_text += "Выберите викторину из меню и начните зарабатывать опыт! 🎯"

    bot.send_message(user_id, history_text)


def create_initial_quiz_codes():
    """Создает начальные коды для викторин"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM quiz_codes')
        code_count = cursor.fetchone()[0]
        conn.close()

        if code_count == 0:
            test_codes = [
                ("CHEM001", "Викторина по химии", 20, 50),
                ("MATH001", "Викторина по математике", 20, 50),
                ("RUS001", "Викторина по русскому языку", 20, 50),
            ]

            for code, name, xp, uses in test_codes:
                create_quiz_code(code, name, xp, uses, "system", expires_days=365)

            print("✅ Созданы тестовые коды викторин")
    except Exception as e:
        print(f"⚠️ Не удалось создать тестовые коды: {e}")


# ================== СИСТЕМА ЛОТЕРЕЙ И РОЗЫГРЫШЕЙ ==================
def create_lottery(name, description, ticket_price, max_tickets, duration_days=7):
    """Создает новую лотерею с указанной продолжительностью"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)

        cursor.execute('''
            INSERT INTO lotteries (name, description, ticket_price, max_tickets, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, ticket_price, max_tickets,
              start_date.isoformat(), end_date.isoformat()))

        lottery_id = cursor.lastrowid
        conn.commit()
        conn.close()

        send_broadcast_to_all(
            "🎪 НОВАЯ ЛОТЕРЕЯ!",
            f"🎰 {name}\n\n{description}\n\n🎫 Цена билета: {ticket_price} баллов\n💰 Призовой фонд: растет!\n⏰ Участвуйте до {end_date.strftime('%d.%m.%Y %H:%M')}"
        )

        return lottery_id
    except Exception as e:
        print(f"❌ Ошибка создания лотереи: {e}")
        return None


def buy_lottery_ticket(user_id, lottery_id, ticket_count=1):
    """Покупка лотерейных билетов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT name, ticket_price, max_tickets, tickets_sold, status FROM lotteries WHERE id = ?',
                       (lottery_id,))
        lottery = cursor.fetchone()

        if not lottery or lottery[4] != 'active':
            conn.close()
            return False, "Лотерея не активна"

        lottery_name, ticket_price, max_tickets, tickets_sold, status = lottery

        total_cost = ticket_price * ticket_count

        if tickets_sold + ticket_count > max_tickets:
            conn.close()
            return False, "Недостаточно доступных билетов"

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (str(user_id),))
        user_balance_result = cursor.fetchone()

        if not user_balance_result:
            conn.close()
            return False, "Пользователь не найден"

        user_balance = user_balance_result[0]

        if user_balance < total_cost:
            conn.close()
            return False, f"Недостаточно баллов. Нужно: {total_cost}, доступно: {user_balance}"

        new_balance = user_balance - total_cost
        cursor.execute(
            'UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?',
            (new_balance, datetime.now().isoformat(), str(user_id))
        )

        cursor.execute(
            'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
            (str(user_id), -total_cost, 'purchase', f'Покупка {ticket_count} билетов лотереи "{lottery_name}"')
        )

        ticket_numbers = []
        for i in range(ticket_count):
            ticket_number = tickets_sold + i + 1
            cursor.execute('''
                INSERT INTO lottery_tickets (lottery_id, user_id, ticket_number)
                VALUES (?, ?, ?)
            ''', (lottery_id, str(user_id), ticket_number))
            ticket_numbers.append(ticket_number)

        cursor.execute('''
            UPDATE lotteries 
            SET tickets_sold = tickets_sold + ?, prize_pool = prize_pool + ? 
            WHERE id = ?
        ''', (ticket_count, total_cost, lottery_id))

        conn.commit()
        conn.close()

        add_xp(user_id, XP_REWARDS["lottery_purchase"] * ticket_count, "lottery_purchase")

        numbers_str = ", ".join(map(str, ticket_numbers))
        return True, f"✅ Куплено {ticket_count} билет(а/ов) в лотерее '{lottery_name}'! Номера: {numbers_str}"

    except Exception as e:
        print(f"❌ Ошибка покупки лотерейного билета: {e}")
        return False, "Ошибка при покупке билета"


def draw_lottery_winner(lottery_id):
    """Проводит розыгрыш лотереи"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT name, prize_pool, tickets_sold FROM lotteries WHERE id = ?', (lottery_id,))
        lottery = cursor.fetchone()

        if not lottery or lottery[2] == 0:
            return False, "Нет участников в лотерее"

        lottery_name, prize_pool, tickets_sold = lottery

        cursor.execute('''
            SELECT user_id FROM lottery_tickets 
            WHERE lottery_id = ? 
            ORDER BY RANDOM() 
            LIMIT 1
        ''', (lottery_id,))

        winner = cursor.fetchone()

        if winner:
            winner_user_id = winner[0]

            update_user_balance(winner_user_id, prize_pool, 'lottery_win', f'Выигрыш в лотерее #{lottery_id}')

            cursor.execute('''
                UPDATE lotteries 
                SET winner_user_id = ?, status = 'finished' 
                WHERE id = ?
            ''', (winner_user_id, lottery_id))

            conn.commit()
            conn.close()

            send_user_notification(
                winner_user_id,
                "lottery_win",
                "🎉 Поздравляем! Вы выиграли в лотерее!",
                f"Вы выиграли {prize_pool} баллов в лотерее '{lottery_name}'!",
                f"lottery_{lottery_id}"
            )

            send_broadcast_to_all(
                "🎊 РОЗЫГРЫШ ЛОТЕРЕИ ЗАВЕРШЕН!",
                f"Лотерея '{lottery_name}' завершена!\n\n🏆 Победитель: пользователь с ID {winner_user_id}\n💰 Выигрыш: {prize_pool} баллов\n🎫 Всего участников: {tickets_sold}"
            )

            return True, winner_user_id, prize_pool
        else:
            conn.close()
            return False, "Не удалось определить победителя", 0

    except Exception as e:
        print(f"❌ Ошибка розыгрыша лотереи: {e}")
        return False, f"Ошибка: {e}", 0


def generate_updated_lottery_message(lottery_id, user_id):
    """Генерирует обновленное сообщение о лотерее после покупки"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT name, description, ticket_price, prize_pool, max_tickets, tickets_sold, end_date 
            FROM lotteries 
            WHERE id = ?
        ''', (lottery_id,))

        lottery = cursor.fetchone()

        if not lottery:
            return "❌ Лотерея не найдена", None

        name, description, ticket_price, prize_pool, max_tickets, tickets_sold, end_date = lottery

        cursor.execute('SELECT COUNT(*) FROM lottery_tickets WHERE lottery_id = ? AND user_id = ?',
                       (lottery_id, user_id))
        user_tickets = cursor.fetchone()[0]

        conn.close()

        end_date_obj = datetime.fromisoformat(end_date)
        time_left = end_date_obj - datetime.now()
        days_left = time_left.days
        hours_left = time_left.seconds // 3600

        lottery_text = f"🎰 *{name}*\n\n"
        lottery_text += f"📝 {description}\n\n"
        lottery_text += f"💰 *Призовой фонд:* {prize_pool} баллов\n"
        lottery_text += f"🎫 *Цена билета:* {ticket_price} баллов\n"
        lottery_text += f"📊 *Продано:* {tickets_sold}/{max_tickets} билетов\n"
        lottery_text += f"🎯 *Ваши билеты:* {user_tickets} шт.\n"
        lottery_text += f"⏰ *Осталось:* {days_left}д {hours_left}ч\n"

        markup = types.InlineKeyboardMarkup()

        if tickets_sold < max_tickets:
            markup.add(
                types.InlineKeyboardButton(
                    f"🎫 Купить 1 билет ({ticket_price} баллов)",
                    callback_data=f"buy_ticket_{lottery_id}_1"
                )
            )

            if tickets_sold + 5 <= max_tickets:
                markup.add(
                    types.InlineKeyboardButton(
                        f"🎫 Купить 5 билетов ({ticket_price * 5} баллов)",
                        callback_data=f"buy_ticket_{lottery_id}_5"
                    )
                )

        markup.add(
            types.InlineKeyboardButton(
                "📊 Мои билеты",
                callback_data=f"my_tickets_{lottery_id}"
            )
        )

        return lottery_text, markup

    except Exception as e:
        print(f"❌ Ошибка генерации обновленного сообщения: {e}")
        return "❌ Ошибка обновления информации", None


def show_lottery_menu(message):
    """Показывает меню лотереи"""
    user_id = str(message.from_user.id)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, description, ticket_price, prize_pool, max_tickets, tickets_sold, end_date 
            FROM lotteries 
            WHERE status = 'active'
            ORDER BY created_at DESC
        ''')

        lotteries = cursor.fetchall()
        conn.close()

        if not lotteries:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("🔙 В меню"))
            bot.send_message(
                user_id,
                "🎭 На данный момент активных лотерей нет.\n\nСледите за обновлениями! 📢",
                reply_markup=markup
            )
            return

        bot.send_message(user_id, "🎪 *ЛОТЕРЕИ И РОЗЫГРЫШИ*\n\nВыберите лотерею для участия:", parse_mode='Markdown')

        for lottery in lotteries:
            lottery_id, name, description, ticket_price, prize_pool, max_tickets, tickets_sold, end_date = lottery

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM lottery_tickets WHERE lottery_id = ? AND user_id = ?',
                           (lottery_id, user_id))
            user_tickets = cursor.fetchone()[0]
            conn.close()

            end_date_obj = datetime.fromisoformat(end_date)
            time_left = end_date_obj - datetime.now()
            days_left = time_left.days
            hours_left = time_left.seconds // 3600

            lottery_text = f"🎰 *{name}*\n\n"
            lottery_text += f"📝 {description}\n\n"
            lottery_text += f"💰 *Призовой фонд:* {prize_pool} баллов\n"
            lottery_text += f"🎫 *Цена билета:* {ticket_price} баллов\n"
            lottery_text += f"📊 *Продано:* {tickets_sold}/{max_tickets} билетов\n"
            lottery_text += f"🎯 *Ваши билеты:* {user_tickets} шт.\n"
            lottery_text += f"⏰ *Осталось:* {days_left}д {hours_left}ч"

            markup = types.InlineKeyboardMarkup()

            if tickets_sold < max_tickets:
                markup.add(
                    types.InlineKeyboardButton(
                        f"🎫 Купить 1 билет ({ticket_price} баллов)",
                        callback_data=f"buy_ticket_{lottery_id}_1"
                    )
                )

                if tickets_sold + 5 <= max_tickets:
                    markup.add(
                        types.InlineKeyboardButton(
                            f"🎫 Купить 5 билетов ({ticket_price * 5} баллов)",
                            callback_data=f"buy_ticket_{lottery_id}_5"
                        )
                    )

            markup.add(
                types.InlineKeyboardButton(
                    "📊 Мои билеты",
                    callback_data=f"my_tickets_{lottery_id}"
                )
            )

            bot.send_message(user_id, lottery_text, reply_markup=markup, parse_mode='Markdown')

    except Exception as e:
        print(f"❌ Ошибка показа меню лотереи: {e}")
        bot.send_message(user_id, "❌ Произошла ошибка при загрузке лотерей")


def show_my_tickets(user_id, lottery_id):
    """Показывает билеты пользователя в лотерее"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT name FROM lotteries WHERE id = ?', (lottery_id,))
        lottery_name = cursor.fetchone()[0]

        cursor.execute('''
            SELECT ticket_number FROM lottery_tickets 
            WHERE lottery_id = ? AND user_id = ? 
            ORDER BY ticket_number
        ''', (lottery_id, user_id))

        tickets = cursor.fetchall()
        conn.close()

        if tickets:
            ticket_numbers = [str(ticket[0]) for ticket in tickets]
            tickets_text = f"🎫 Ваши билеты в лотерее '{lottery_name}':\n\n"
            tickets_text += ", ".join(ticket_numbers)
            tickets_text += f"\n\nВсего билетов: {len(tickets)}"

            bot.send_message(user_id, tickets_text)
        else:
            bot.send_message(user_id, f"У вас нет билетов в лотерее '{lottery_name}'")

    except Exception as e:
        print(f"❌ Ошибка показа билетов: {e}")
        bot.send_message(user_id, "❌ Ошибка загрузки билетов")


# ================== ОБРАБОТЧИКИ CALLBACK ==================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработчик callback-запросов"""
    user_id = str(call.from_user.id)

    if call.from_user.is_bot:
        try:
            bot.answer_callback_query(call.id, "❌ Боты не могут участвовать в лотереях")
        except:
            pass
        return

    try:
        if call.data.startswith('buy_ticket_'):
            handle_ticket_purchase(call)
        elif call.data.startswith('my_tickets_'):
            handle_my_tickets(call)
    except Exception as e:
        print(f"❌ Необработанная ошибка в callback: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        except:
            pass


def handle_ticket_purchase(call):
    """Обработчик покупки билетов"""
    user_id = str(call.from_user.id)

    try:
        parts = call.data.replace('buy_ticket_', '').split('_')
        lottery_id = int(parts[0])
        ticket_count = int(parts[1])

        bot.answer_callback_query(call.id, "🔄 Обрабатываем покупку...")

        success, message = buy_lottery_ticket(user_id, lottery_id, ticket_count)

        if success:
            updated_text, updated_markup = generate_updated_lottery_message(lottery_id, user_id)

            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text=updated_text,
                    reply_markup=updated_markup
                )
                bot.answer_callback_query(call.id, "✅ Билеты куплены!")
            except Exception as edit_error:
                print(f"⚠️ Не удалось обновить сообщение: {edit_error}")
                bot.send_message(user_id, f"✅ {message}")
        else:
            bot.answer_callback_query(call.id, f"❌ {message}")

    except Exception as e:
        print(f"❌ Ошибка обработки покупки билета: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка при покупке билета")
        except:
            pass


def handle_my_tickets(call):
    """Обработчик показа билетов пользователя"""
    user_id = str(call.from_user.id)

    try:
        lottery_id = int(call.data.replace('my_tickets_', ''))
        show_my_tickets(user_id, lottery_id)
        bot.answer_callback_query(call.id, "📊 Показываем ваши билеты...")
    except Exception as e:
        print(f"❌ Ошибка обработки показа билетов: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ Ошибка загрузки билетов")
        except:
            pass


# ================== СИСТЕМА РАССЫЛОК И УВЕДОМЛЕНИЙ ==================
def create_broadcast(admin_id, message_text, message_type='text', file_id=None, schedule_delay_minutes=0):
    """Создает рассылку"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        scheduled_for = None
        if schedule_delay_minutes > 0:
            scheduled_for = (datetime.now() + timedelta(minutes=schedule_delay_minutes)).isoformat()

        cursor.execute('''
            INSERT INTO broadcasts (admin_id, message_text, message_type, file_id, scheduled_for, status)
            VALUES (?, ?, ?, ?, ?, 'scheduled')
        ''', (str(admin_id), message_text, message_type, file_id, scheduled_for))

        broadcast_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return broadcast_id
    except Exception as e:
        print(f"❌ Ошибка создания рассылки: {e}")
        return None


def send_broadcast(broadcast_id):
    """Отправляет рассылку всем пользователям"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT message_text, message_type, file_id FROM broadcasts WHERE id = ?', (broadcast_id,))
        broadcast = cursor.fetchone()

        if not broadcast:
            return False, "Рассылка не найдена"

        message_text, message_type, file_id = broadcast

        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()

        sent_count = 0
        failed_count = 0

        cursor.execute('UPDATE broadcasts SET status = "sending" WHERE id = ?', (broadcast_id,))
        conn.commit()

        for user_tuple in users:
            user_id = user_tuple[0]
            try:
                if message_type == 'photo' and file_id:
                    bot.send_photo(user_id, file_id, caption=message_text)
                elif message_type == 'document' and file_id:
                    bot.send_document(user_id, file_id, caption=message_text)
                else:
                    bot.send_message(user_id, message_text)

                sent_count += 1
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
                failed_count += 1

        cursor.execute('''
            UPDATE broadcasts 
            SET sent_count = ?, failed_count = ?, status = 'sent', sent_at = ?
            WHERE id = ?
        ''', (sent_count, failed_count, datetime.now().isoformat(), broadcast_id))

        conn.commit()
        conn.close()

        return True, f"✅ Отправлено: {sent_count}, Не удалось: {failed_count}"

    except Exception as e:
        print(f"❌ Ошибка отправки рассылки: {e}")
        return False, f"Ошибка: {e}"


def send_broadcast_to_all(title, message):
    """Быстрая рассылка всем пользователям"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        conn.close()

        message_text = f"🔔 {title}\n\n{message}"

        sent_count = 0
        failed_count = 0

        for user_tuple in users:
            user_id = user_tuple[0]
            try:
                bot.send_message(user_id, message_text)
                sent_count += 1
                time.sleep(0.05)
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")
                failed_count += 1

        print(f"✅ Рассылка отправлена {sent_count} пользователям, не удалось: {failed_count}")
        return True

    except Exception as e:
        print(f"❌ Ошибка массовой рассылки: {e}")
        return False


def send_user_notification(user_id, notification_type, title, message, related_id=None):
    """Отправляет уведомление пользователю"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_notifications (user_id, notification_type, title, message, related_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(user_id), notification_type, title, message, related_id))

        conn.commit()
        conn.close()

        notification_text = f"🔔 {title}\n\n{message}"
        bot.send_message(user_id, notification_text)

        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        return False


# ================== ИСПРАВЛЕННЫЕ ФУНКЦИИ АДМИНИСТРАТОРА ==================
@admin_required
def admin_broadcast_menu(message):
    """Меню рассылок для админов"""
    user_id = str(message.from_user.id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📢 Создать рассылку"))
    markup.add(types.KeyboardButton("📊 Статистика рассылок"))
    markup.add(types.KeyboardButton("📋 История рассылок"))
    markup.add(types.KeyboardButton("🎪 Создать лотерею"))
    markup.add(types.KeyboardButton("🗑️ Удалить активные лотереи"))
    markup.add(types.KeyboardButton("🧹 Удалить завершенные лотереи"))
    markup.add(types.KeyboardButton("🔤 Создать код викторины"))
    markup.add(types.KeyboardButton("📊 Статистика викторин"))
    markup.add(types.KeyboardButton("🎰 Запустить розыгрыш"))
    markup.add(types.KeyboardButton("🔄 Обновить кэш Google"))
    markup.add(types.KeyboardButton("🔙 В меню"))

    bot.send_message(user_id, "📢 ПАНЕЛЬ АДМИНИСТРАТОРА\n\nВыберите действие:", reply_markup=markup)


def start_broadcast_creation(message):
    """Начинает процесс создания рассылки с улучшенной обработкой отмены"""
    user_id = str(message.from_user.id)
    user_states[user_id] = 'creating_broadcast'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Отмена"))

    bot.send_message(
        user_id,
        "✍️ Введите текст рассылки:\n\n"
        "Вы можете использовать форматирование Markdown:\n"
        "*жирный* текст\n"
        "_курсив_ текст\n"
        "`моноширинный` текст\n"
        "[ссылка](https://example.com)\n\n"
        "Для отмены нажмите кнопку '🔙 Отмена'",
        reply_markup=markup,
        parse_mode='Markdown'
    )


def handle_admin_broadcast_creation(message):
    """Обработчик создания рассылки"""
    user_id = str(message.from_user.id)

    if message.text in ["🔙 Отмена", "🔙 Назад", "🔙 В меню"]:
        user_states[user_id] = None
        start(message)
        return

    if user_id in user_states and user_states[user_id] == 'creating_broadcast':
        try:
            broadcast_text = message.text

            if len(broadcast_text.strip()) < 5:
                bot.send_message(user_id, "❌ Текст рассылки слишком короткий. Минимум 5 символов.")
                return

            broadcast_id = create_broadcast(user_id, broadcast_text)

            if broadcast_id:
                success, result = send_broadcast(broadcast_id)

                if success:
                    bot.send_message(user_id, f"✅ Рассылка создана и отправлена!\n\n{result}")
                else:
                    bot.send_message(user_id, f"❌ Рассылка создана, но возникли ошибки при отправке:\n{result}")
            else:
                bot.send_message(user_id, "❌ Ошибка создания рассылки")

        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка при создании рассылки: {e}")

        user_states[user_id] = None
        admin_broadcast_menu(message)


def handle_admin_broadcast_stats(message):
    """Показывает статистику рассылок"""
    user_id = str(message.from_user.id)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(sent_count) as total_sent,
                SUM(failed_count) as total_failed,
                AVG(sent_count) as avg_sent
            FROM broadcasts 
            WHERE status = 'sent'
        ''')
        stats = cursor.fetchone()

        cursor.execute('''
            SELECT message_text, sent_count, failed_count, sent_at 
            FROM broadcasts 
            WHERE status = 'sent'
            ORDER BY sent_at DESC 
            LIMIT 5
        ''')
        recent_broadcasts = cursor.fetchall()

        conn.close()

        if stats and stats[0] > 0:
            total, total_sent, total_failed, avg_sent = stats

            stats_text = f"📊 СТАТИСТИКА РАССЫЛОК\n\n"
            stats_text += f"📈 Общая статистика:\n"
            stats_text += f"• Всего рассылок: {total}\n"
            stats_text += f"• Всего отправлено: {total_sent or 0} сообщений\n"
            stats_text += f"• Всего ошибок: {total_failed or 0}\n"
            stats_text += f"• В среднем на рассылку: {avg_sent or 0:.1f} сообщений\n\n"

            stats_text += f"📋 Последние рассылки:\n"

            for i, (msg_text, sent, failed, sent_at) in enumerate(recent_broadcasts, 1):
                preview = msg_text[:50] + "..." if len(msg_text) > 50 else msg_text
                sent_date = datetime.fromisoformat(sent_at).strftime('%d.%m.%Y %H:%M') if sent_at else "Не отправлена"

                stats_text += f"{i}. {preview}\n"
                stats_text += f"   📤 {sent} отправлено, ❌ {failed} ошибок\n"
                stats_text += f"   🕒 {sent_date}\n\n"

        else:
            stats_text = "📊 СТАТИСТИКА РАССЫЛОК\n\n"
            stats_text += "Пока нет завершенных рассылок.\n"
            stats_text += "Создайте первую рассылку, чтобы увидеть статистику."

        bot.send_message(user_id, stats_text)

    except Exception as e:
        print(f"❌ Ошибка получения статистики рассылок: {e}")
        bot.send_message(user_id, "❌ Ошибка при загрузке статистики рассылок")

def start_quiz_code_creation(message):
    """Начинает процесс создания кодового слова"""
    user_id = str(message.from_user.id)
    user_states[user_id] = 'creating_quiz_code'

    instruction = """🔤 СОЗДАНИЕ КОДА ВИКТОРИНЫ

Отправьте данные в формате:
Код|Название викторины|Количество XP|Макс. использований

Примеры:
• CHEM001|Викторина по химии|20|50
• MATH2024|Математика для начинающих|15|100
• RUSSIAN01|Русский язык тест|25|1

📝 Пояснение полей:
• Код - уникальное слово (только латиница и цифры)
• Название - описание викторины
• XP - опыт за прохождение (10-50)
• Макс. использований - сколько раз можно использовать код

Для отмены нажмите кнопку '🔙 Отмена'"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Отмена"))

    bot.send_message(user_id, instruction, reply_markup=markup)

def handle_quiz_code_creation(message):
    """Обработчик создания кодового слова"""
    user_id = str(message.from_user.id)

    if message.text in ["🔙 Отмена", "🔙 Назад", "🔙 В меню"]:
        user_states[user_id] = None
        admin_broadcast_menu(message)
        return

    if user_id in user_states and user_states[user_id] == 'creating_quiz_code':
        try:
            parts = message.text.split('|')
            if len(parts) != 4:
                bot.send_message(user_id,
                               "❌ Неверный формат. Используйте:\n"
                               "Код|Название|XP|Макс. использований\n\n"
                               "Пример: CHEM001|Викторина по химии|20|50")
                return

            code = parts[0].strip().upper()
            quiz_name = parts[1].strip()
            xp_reward = int(parts[2].strip())
            max_uses = int(parts[3].strip())

            # Валидация данных
            if not code.isalnum():
                bot.send_message(user_id, "❌ Код должен содержать только буквы и цифры (без пробелов и спецсимволов)")
                return

            if len(code) < 3:
                bot.send_message(user_id, "❌ Код должен быть не менее 3 символов")
                return

            if xp_reward < 10 or xp_reward > 50:
                bot.send_message(user_id, "❌ Количество XP должно быть от 10 до 50")
                return

            if max_uses < 1 or max_uses > 1000:
                bot.send_message(user_id, "❌ Максимальное количество использований должно быть от 1 до 1000")
                return

            # Создаем код
            success = create_quiz_code(code, quiz_name, xp_reward, max_uses, str(user_id), expires_days=365)

            if success:
                bot.send_message(user_id,
                               f"✅ Код викторины создан!\n\n"
                               f"🔤 Код: {code}\n"
                               f"📝 Викторина: {quiz_name}\n"
                               f"⭐ Опыт: {xp_reward}\n"
                               f"🎫 Макс. использований: {max_uses}\n"
                               f"⏰ Срок действия: 1 год\n\n"
                               f"💡 Пользователи могут ввести этот код в боте для получения опыта!")
            else:
                bot.send_message(user_id, "❌ Ошибка создания кода. Возможно, код уже существует.")

        except ValueError:
            bot.send_message(user_id, "❌ Ошибка в числах. Убедитесь, что XP и макс. использований - целые числа")
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка: {e}")

        user_states[user_id] = None
        admin_broadcast_menu(message)


def show_quiz_stats(message):
    """Показывает статистику викторин и активные коды"""
    user_id = str(message.from_user.id)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Статистика по кодам
        cursor.execute('''
            SELECT COUNT(*) as total_codes,
                   SUM(used_count) as total_uses,
                   AVG(used_count) as avg_uses,
                   COUNT(*) FILTER (WHERE is_active = TRUE) as active_codes
            FROM quiz_codes
        ''')
        code_stats = cursor.fetchone()

        # Статистика по пользователям
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as unique_users,
                   SUM(xp_earned) as total_xp_given
            FROM quiz_code_usage
        ''')
        user_stats = cursor.fetchone()

        # Активные коды
        cursor.execute('''
            SELECT code, quiz_name, xp_reward, max_uses, used_count, expires_at
            FROM quiz_codes 
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        active_codes = cursor.fetchall()

        conn.close()

        stats_text = "📊 СТАТИСТИКА ВИКТОРИН\n\n"
        stats_text += f"🔤 Всего кодов: {code_stats[0]}\n"
        stats_text += f"🟢 Активных кодов: {code_stats[3]}\n"
        stats_text += f"🎫 Всего использований: {code_stats[1]}\n"
        stats_text += f"👥 Уникальных участников: {user_stats[0]}\n"
        stats_text += f"💫 Всего выдано опыта: {user_stats[1]}\n\n"

        if active_codes:
            stats_text += "🟢 АКТИВНЫЕ КОДЫ:\n\n"
            for code, quiz_name, xp_reward, max_uses, used_count, expires_at in active_codes:
                stats_text += f"🔤 {code}\n"
                stats_text += f"   📝 {quiz_name}\n"
                stats_text += f"   ⭐ {xp_reward} XP | 🎫 {used_count}/{max_uses}\n"

                if expires_at:
                    expires_date = datetime.fromisoformat(expires_at)
                    days_left = (expires_date - datetime.now()).days
                    stats_text += f"   ⏰ Осталось дней: {days_left}\n"

                stats_text += "\n"
        else:
            stats_text += "🟢 Активных кодов нет\n"

        bot.send_message(user_id, stats_text)

    except Exception as e:
        print(f"❌ Ошибка получения статистики викторин: {e}")
        bot.send_message(user_id, "❌ Ошибка при загрузке статистики викторин")

def handle_admin_broadcast_history(message):
    """Показывает историю рассылок"""
    user_id = str(message.from_user.id)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, message_text, sent_count, failed_count, status, created_at, sent_at
            FROM broadcasts 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')

        broadcasts = cursor.fetchall()
        conn.close()

        if broadcasts:
            history_text = "📋 ИСТОРИЯ РАССЫЛОК\n\n"

            for broadcast in broadcasts:
                broadcast_id, msg_text, sent_count, failed_count, status, created_at, sent_at = broadcast

                preview = msg_text[:30] + "..." if len(msg_text) > 30 else msg_text
                created_date = datetime.fromisoformat(created_at).strftime('%d.%m.%Y %H:%M')

                status_emoji = {
                    'draft': '📝',
                    'scheduled': '⏰',
                    'sending': '🔄',
                    'sent': '✅',
                    'failed': '❌'
                }.get(status, '❓')

                history_text += f"{status_emoji} Рассылка #{broadcast_id}\n"
                history_text += f"📝 {preview}\n"
                history_text += f"📊 Статус: {status}\n"

                if sent_count is not None:
                    history_text += f"📤 Отправлено: {sent_count}\n"
                if failed_count is not None:
                    history_text += f"❌ Ошибок: {failed_count}\n"

                history_text += f"🕒 Создана: {created_date}\n"

                if sent_at:
                    sent_date = datetime.fromisoformat(sent_at).strftime('%d.%m.%Y %H:%M')
                    history_text += f"📨 Отправлена: {sent_date}\n"

                history_text += "\n"

        else:
            history_text = "📋 ИСТОРИЯ РАССЫЛОК\n\n"
            history_text += "Пока нет созданных рассылок.\n"

        bot.send_message(user_id, history_text)

    except Exception as e:
        print(f"❌ Ошибка получения истории рассылок: {e}")
        bot.send_message(user_id, "❌ Ошибка при загрузке истории рассылок")


def start_lottery_creation(message):
    """Начинает процесс создания лотереи с улучшенной обработкой отмены"""
    user_id = str(message.from_user.id)
    user_states[user_id] = 'creating_lottery'

    instruction = """🎪 СОЗДАНИЕ ЛОТЕРЕИ

Отправьте данные в одном из форматов:

1. Базовый формат (7 дней):
Название|Описание|Цена_билета|Макс_билетов

2. Расширенный формат:
Название|Описание|Цена_билета|Макс_билетов|Продолжительность_дней

Примеры:
• Весенняя лотерея|Выиграй призы!|10|100
• Большая лотерея|Главный приз 1000 баллов!|25|200|14

Для отмены нажмите кнопку '🔙 Отмена'"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Отмена"))

    bot.send_message(user_id, instruction, reply_markup=markup)


def handle_admin_lottery_creation(message):
    """Обработчик создания лотереи с продолжительностью"""
    user_id = str(message.from_user.id)

    if message.text in ["🔙 Отмена", "🔙 Назад", "🔙 В меню"]:
        user_states[user_id] = None
        start(message)
        return

    if user_id in user_states and user_states[user_id] == 'creating_lottery':
        try:
            parts = message.text.split('|')
            if len(parts) == 4:
                name = parts[0].strip()
                description = parts[1].strip()
                ticket_price = int(parts[2].strip())
                max_tickets = int(parts[3].strip())
                duration_days = 7
            elif len(parts) == 5:
                name = parts[0].strip()
                description = parts[1].strip()
                ticket_price = int(parts[2].strip())
                max_tickets = int(parts[3].strip())
                duration_days = int(parts[4].strip())
            else:
                bot.send_message(user_id,
                                 "❌ Неверный формат. Используйте:\n"
                                 "• Название|Описание|Цена_билета|Макс_билетов\n"
                                 "• Название|Описание|Цена_билета|Макс_билетов|Продолжительность_дней")
                return

            if duration_days <= 0:
                duration_days = 7
            elif duration_days > 365:
                duration_days = 365

            lottery_id = create_lottery(name, description, ticket_price, max_tickets, duration_days)

            if lottery_id:
                bot.send_message(user_id,
                                 f"✅ Лотерея '{name}' создана успешно!\n"
                                 f"🆔 ID: {lottery_id}\n"
                                 f"⏰ Продолжительность: {duration_days} дней\n"
                                 f"🎫 Цена билета: {ticket_price} баллов\n"
                                 f"📊 Макс. билетов: {max_tickets}")
            else:
                bot.send_message(user_id, "❌ Ошибка создания лотереи")

        except ValueError as e:
            bot.send_message(user_id,
                             f"❌ Ошибка в числах: {e}\nУбедитесь, что цена, макс. билеты и продолжительность - числа")
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка: {e}")

        user_states[user_id] = None
        admin_broadcast_menu(message)


def handle_admin_refresh_cache(message):
    """Обновляет кэш Google таблицы"""
    user_id = str(message.from_user.id)

    try:
        bot.send_message(user_id, "🔄 Обновляем кэш Google таблицы...")
        load_google_sheets_data(force_refresh=True)
        bot.send_message(user_id, "✅ Кэш Google таблицы успешно обновлен!")
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка обновления кэша: {e}")


def delete_all_lotteries():
    """Удаляет все активные лотереи"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name FROM lotteries WHERE status = "active"')
        active_lotteries = cursor.fetchall()

        if not active_lotteries:
            conn.close()
            return "❌ Активных лотерей нет для удаления"

        for lottery_id, lottery_name in active_lotteries:
            cursor.execute('DELETE FROM lottery_tickets WHERE lottery_id = ?', (lottery_id,))

        cursor.execute('DELETE FROM lotteries WHERE status = "active"')

        conn.commit()
        conn.close()

        lottery_names = [name for _, name in active_lotteries]
        return f"✅ Удалено {len(active_lotteries)} активных лотерей: {', '.join(lottery_names)}"

    except Exception as e:
        print(f"❌ Ошибка удаления лотерей: {e}")
        return f"❌ Ошибка при удалении лотерей: {e}"


def delete_finished_lotteries():
    """Удаляет завершенные лотереи"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name FROM lotteries WHERE status = "finished"')
        finished_lotteries = cursor.fetchall()

        if not finished_lotteries:
            conn.close()
            return "❌ Завершенных лотерей нет для удаления"

        for lottery_id, lottery_name in finished_lotteries:
            cursor.execute('DELETE FROM lottery_tickets WHERE lottery_id = ?', (lottery_id,))

        cursor.execute('DELETE FROM lotteries WHERE status = "finished"')

        conn.commit()
        conn.close()

        lottery_names = [name for _, name in finished_lotteries]
        return f"✅ Удалено {len(finished_lotteries)} завершенных лотерей: {', '.join(lottery_names)}"

    except Exception as e:
        print(f"❌ Ошибка удаления завершенных лотерей: {e}")
        return f"❌ Ошибка при удалении завершенных лотерей: {e}"


def handle_admin_delete_active_lotteries(message):
    """Обработчик удаления активных лотерей"""
    user_id = str(message.from_user.id)

    try:
        result = delete_all_lotteries()
        bot.send_message(user_id, result)
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {e}")

    admin_broadcast_menu(message)


def handle_admin_delete_finished_lotteries(message):
    """Обработчик удаления завершенных лотерей"""
    user_id = str(message.from_user.id)

    try:
        result = delete_finished_lotteries()
        bot.send_message(user_id, result)
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {e}")

    admin_broadcast_menu(message)


def draw_lottery_manually(lottery_id):
    """Ручной запуск розыгрыша лотереи с улучшенной обработкой ошибок"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT name, status, tickets_sold FROM lotteries WHERE id = ?', (lottery_id,))
        lottery = cursor.fetchone()

        if not lottery:
            return False, "Лотерея не найдена"

        lottery_name, status, tickets_sold = lottery

        if status != 'active':
            return False, "Лотерея не активна"

        if tickets_sold == 0:
            return False, "В лотерее нет проданных билетов"

        conn.close()

        success, winner, prize = draw_lottery_winner(lottery_id)

        if success:
            return True, f"✅ Розыгрыш лотереи '{lottery_name}' завершен!\n🏆 Победитель: {winner}\n💰 Приз: {prize} баллов"
        else:
            return False, f"❌ Ошибка розыгрыша: {winner}"

    except Exception as e:
        return False, f"❌ Ошибка: {e}"


def handle_admin_draw_lottery(message):
    """Обработчик запуска розыгрыша лотереи с улучшенной логикой"""
    user_id = str(message.from_user.id)

    try:
        user_states[user_id] = None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, tickets_sold FROM lotteries WHERE status = "active"')
        active_lotteries = cursor.fetchall()
        conn.close()

        if not active_lotteries:
            bot.send_message(user_id, "❌ Нет активных лотерей для розыгрыша")
            admin_broadcast_menu(message)
            return

        lotteries_with_tickets = [lottery for lottery in active_lotteries if lottery[2] > 0]

        if not lotteries_with_tickets:
            bot.send_message(user_id, "❌ Нет активных лотерей с проданными билетами")
            admin_broadcast_menu(message)
            return

        if len(lotteries_with_tickets) == 1:
            lottery_id = lotteries_with_tickets[0][0]
            lottery_name = lotteries_with_tickets[0][1]

            bot.send_message(user_id, f"🎰 Запускаем розыгрыш лотереи '{lottery_name}'...")

            success, result = draw_lottery_manually(lottery_id)
            bot.send_message(user_id, result)

        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for lottery_id, lottery_name, tickets_sold in lotteries_with_tickets:
                markup.add(types.KeyboardButton(f"🎰 {lottery_name} (билетов: {tickets_sold})"))
            markup.add(types.KeyboardButton("🔙 Отмена"))

            bot.send_message(user_id, "🎰 Выберите лотерею для розыгрыша:", reply_markup=markup)
            user_states[user_id] = 'selecting_lottery_to_draw'

    except Exception as e:
        print(f"❌ Ошибка в handle_admin_draw_lottery: {e}")
        bot.send_message(user_id, f"❌ Ошибка: {e}")
        admin_broadcast_menu(message)


def handle_lottery_selection_for_draw(message):
    """Обработчик выбора лотереи для розыгрыша"""
    user_id = str(message.from_user.id)

    if message.text in ["🔙 Отмена", "🔙 Назад", "🔙 В меню"]:
        user_states[user_id] = None
        start(message)
        return

    try:
        lottery_name = message.text.replace("🎰 ", "").split(" (билетов: ")[0]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM lotteries WHERE name = ? AND status = "active"', (lottery_name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            lottery_id = result[0]
            bot.send_message(user_id, f"🎰 Запускаем розыгрыш лотереи '{lottery_name}'...")

            success, result_msg = draw_lottery_manually(lottery_id)
            bot.send_message(user_id, result_msg)
        else:
            bot.send_message(user_id, "❌ Лотерея не найдена")

    except Exception as e:
        print(f"❌ Ошибка в handle_lottery_selection_for_draw: {e}")
        bot.send_message(user_id, f"❌ Ошибка при выборе лотереи: {e}")

    user_states[user_id] = None
    admin_broadcast_menu(message)


# ================== СИСТЕМА КРЕДИТОВ ==================
def create_loan(user_id, amount):
    """Создает новый кредит для пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        weekly_payment = amount // 12
        if amount % 12 != 0:
            weekly_payment += 1

        now = datetime.now()
        next_principal_date = now + timedelta(hours=168)
        next_interest_date = now + timedelta(hours=504)

        cursor.execute('''
            INSERT INTO loans 
            (user_id, amount, weekly_payment, next_principal_date, next_interest_date, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        ''', (str(user_id), amount, weekly_payment,
              next_principal_date.isoformat(),
              next_interest_date.isoformat()))

        loan_id = cursor.lastrowid

        cursor.execute('SELECT credit_balance FROM users WHERE user_id = ?', (str(user_id),))
        result = cursor.fetchone()

        if result:
            current_credit = result[0]
            new_credit = current_credit + amount
            cursor.execute(
                'UPDATE users SET credit_balance = ?, updated_at = ? WHERE user_id = ?',
                (new_credit, now.isoformat(), str(user_id))
            )
        else:
            cursor.execute(
                'INSERT INTO users (user_id, balance, credit_balance, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
                (str(user_id), 0, amount, now.isoformat(), now.isoformat())
            )

        cursor.execute(
            'INSERT INTO transactions (user_id, amount, type, description, product_id) VALUES (?, ?, ?, ?, ?)',
            (str(user_id), amount, 'credit_issue', f"Выдача кредита #{loan_id}", f"loan_{loan_id}")
        )

        conn.commit()
        conn.close()

        add_xp(user_id, XP_REWARDS["loan_taken"], "loan_taken")

        print(f"✅ Создан кредит #{loan_id} для {user_id} на {amount} баллов")
        return loan_id

    except Exception as e:
        print(f"❌ Ошибка создания кредита: {e}")
        return None


def get_active_loans(user_id=None):
    """Получает активные кредиты"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if user_id:
            cursor.execute('''
                SELECT id, user_id, amount, interest_rate, term_weeks, weekly_payment,
                       interest_payment_cycle_hours, next_principal_date, next_interest_date,
                       total_paid_principal, total_paid_interest, status, created_at
                FROM loans 
                WHERE user_id = ? AND status = 'active'
                ORDER BY created_at DESC
            ''', (str(user_id),))
        else:
            cursor.execute('''
                SELECT id, user_id, amount, interest_rate, term_weeks, weekly_payment,
                       interest_payment_cycle_hours, next_principal_date, next_interest_date,
                       total_paid_principal, total_paid_interest, status, created_at
                FROM loans WHERE status = 'active'
                ORDER BY created_at DESC
            ''')

        loans = cursor.fetchall()
        conn.close()

        return loans

    except Exception as e:
        print(f"❌ Ошибка получения кредитов: {e}")
        return []


def send_loan_payment_notification(user_id, loan_id, amount, payment_type):
    """Отправляет уведомление о списании платежа по кредиту"""
    try:
        if payment_type == "principal":
            title = "💸 Списание по кредиту"
            message = f"Списан еженедельный платеж {amount} баллов по кредиту #{loan_id}"
        else:
            title = "📈 Списание процентов"
            message = f"Списаны проценты {amount} баллов по кредиту #{loan_id}"

        send_user_notification(user_id, "loan_payment", title, message, f"loan_{loan_id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления о платеже: {e}")
        return False


def get_loan_info(user_id):
    """Получает информацию о кредитах пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, amount, weekly_payment, next_principal_date, next_interest_date, 
                   total_paid_principal, total_paid_interest, status
            FROM loans 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (str(user_id),))

        loans = cursor.fetchall()
        conn.close()

        if not loans:
            return "У вас нет активных кредитов."

        info_text = "🏦 ВАШИ АКТИВНЫЕ КРЕДИТЫ\n\n"

        for loan in loans:
            if len(loan) >= 8:
                loan_id = loan[0]
                amount = loan[1]
                weekly_payment = loan[2]
                next_principal = loan[3]
                next_interest = loan[4]
                total_principal = loan[5]
                total_interest = loan[6]
                status = loan[7]

                remaining_debt = amount - (total_principal or 0)

                next_principal_str = "Не установлен"
                if next_principal:
                    try:
                        next_principal_date = datetime.fromisoformat(next_principal)
                        next_principal_str = next_principal_date.strftime('%d.%m.%Y %H:%M')
                    except:
                        pass

                next_interest_str = "Не установлен"
                if next_interest:
                    try:
                        next_interest_date = datetime.fromisoformat(next_interest)
                        next_interest_str = next_interest_date.strftime('%d.%m.%Y %H:%M')
                    except:
                        pass

                info_text += f"📋 Кредит #{loan_id}\n"
                info_text += f"💳 Сумма: {amount} баллов\n"
                info_text += f"📉 Остаток долга: {remaining_debt} баллов\n"
                info_text += f"💸 Еженедельный платеж: {weekly_payment} баллов\n"
                info_text += f"📅 Следующий платеж: {next_principal_str}\n"
                info_text += f"⏰ Следующие проценты: {next_interest_str}\n"
                info_text += f"💰 Уже выплачено: {total_principal or 0} баллов\n\n"
            else:
                print(f"⚠️ Неправильная структура данных кредита: {loan}")

        return info_text

    except Exception as e:
        print(f"❌ Ошибка получения информации о кредитах: {e}")
        return "Ошибка при получении информации о кредитах."


def process_loan_payments():
    """Обрабатывает все overdue платежи по кредитам"""
    try:
        now = datetime.now()
        active_loans = get_active_loans()

        print(f"🔍 Проверка платежей по {len(active_loans)} активным кредитам...")

        for loan in active_loans:
            if len(loan) >= 13:
                loan_id = loan[0]
                user_id = loan[1]
                amount = loan[2]
                interest_rate = loan[3]
                term_weeks = loan[4]
                weekly_payment = loan[5]
                interest_cycle = loan[6]
                next_principal = loan[7]
                next_interest = loan[8]
                total_principal = loan[9]
                total_interest = loan[10]
                status = loan[11]
                created_at = loan[12]

                print(f"🔍 Проверка кредита #{loan_id} для {user_id}")

                next_principal_date = datetime.fromisoformat(next_principal) if next_principal else None
                next_interest_date = datetime.fromisoformat(next_interest) if next_interest else None

                # Обработка просроченного платежа по основному долгу
                if next_principal_date and next_principal_date <= now:
                    print(f"💸 Найден overdue платеж по основному долгу для кредита #{loan_id}")
                    process_principal_payment(loan_id, user_id, weekly_payment, next_principal_date)

                # Обработка просроченного платежа по процентам
                if next_interest_date and next_interest_date <= now:
                    print(f"📈 Найден overdue платеж по процентам для кредита #{loan_id}")
                    process_interest_payment(loan_id, user_id, amount, interest_rate, next_interest_date)
            else:
                print(f"⚠️ Неправильная структура данных кредита: {loan}")

    except Exception as e:
        print(f"❌ Ошибка обработки платежей по кредитам: {e}")


def process_principal_payment(loan_id, user_id, weekly_payment, next_principal_date):
    """Обрабатывает платеж по основному долгу"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получаем текущий баланс пользователя
        cursor.execute('SELECT balance, credit_balance FROM users WHERE user_id = ?', (str(user_id),))
        user_data = cursor.fetchone()

        if not user_data:
            print(f"❌ Пользователь {user_id} не найден")
            conn.close()
            return False

        balance, credit_balance = user_data

        # Пытаемся списать сначала с основных баллов, потом с кредитных
        amount_to_deduct = weekly_payment
        description = f"Еженедельный платеж по кредиту #{loan_id}"

        success = False

        # Списание с основных баллов
        if balance >= amount_to_deduct:
            new_balance = balance - amount_to_deduct
            cursor.execute(
                'UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?',
                (new_balance, datetime.now().isoformat(), str(user_id))
            )
            cursor.execute(
                'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (str(user_id), -amount_to_deduct, 'loan_payment', description)
            )
            success = True
            print(f"✅ Списано {amount_to_deduct} баллов с основных средств пользователя {user_id}")

        # Если основных баллов не хватает, списываем с кредитных
        elif credit_balance >= amount_to_deduct:
            new_credit_balance = credit_balance - amount_to_deduct
            cursor.execute(
                'UPDATE users SET credit_balance = ?, updated_at = ? WHERE user_id = ?',
                (new_credit_balance, datetime.now().isoformat(), str(user_id))
            )
            cursor.execute(
                'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (str(user_id), -amount_to_deduct, 'loan_payment', description)
            )
            success = True
            print(f"✅ Списано {amount_to_deduct} баллов с кредитных средств пользователя {user_id}")
        else:
            # Если средств не хватает, начисляем штраф
            penalty = weekly_payment * 0.1  # 10% штраф
            print(f"⚠️ Недостаточно средств для платежа по кредиту #{loan_id}. Штраф: {penalty}")

        if success:
            # Обновляем данные по кредиту
            cursor.execute('''
                UPDATE loans 
                SET total_paid_principal = COALESCE(total_paid_principal, 0) + ?,
                    next_principal_date = ?
                WHERE id = ?
            ''', (amount_to_deduct,
                  (next_principal_date + timedelta(hours=168)).isoformat(),  # +7 дней
                  loan_id))

            # Проверяем, полностью ли погашен кредит
            cursor.execute('SELECT amount, total_paid_principal FROM loans WHERE id = ?', (loan_id,))
            loan_data = cursor.fetchone()
            if loan_data:
                total_amount, total_paid = loan_data
                if total_paid >= total_amount:
                    cursor.execute('UPDATE loans SET status = "paid" WHERE id = ?', (loan_id,))
                    print(f"🎉 Кредит #{loan_id} полностью погашен!")

                    # Начисляем опыт за погашение кредита
                    add_xp(user_id, XP_REWARDS["loan_repaid"], "loan_repaid")

                    send_user_notification(
                        user_id,
                        "loan_paid",
                        "🎉 Кредит погашен!",
                        f"Поздравляем! Вы полностью погасили кредит #{loan_id}",
                        f"loan_{loan_id}"
                    )

        conn.commit()
        conn.close()
        return success

    except Exception as e:
        print(f"❌ Ошибка обработки платежа по основному долгу: {e}")
        return False


def process_interest_payment(loan_id, user_id, amount, interest_rate, next_interest_date):
    """Обрабатывает платеж по процентам"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Расчет суммы процентов
        interest_amount = int(amount * (interest_rate / 100))

        # Получаем текущий баланс пользователя
        cursor.execute('SELECT balance, credit_balance FROM users WHERE user_id = ?', (str(user_id),))
        user_data = cursor.fetchone()

        if not user_data:
            print(f"❌ Пользователь {user_id} не найден")
            conn.close()
            return False

        balance, credit_balance = user_data

        # Пытаемся списать проценты
        description = f"Проценты по кредиту #{loan_id}"
        success = False

        # Списание с основных баллов
        if balance >= interest_amount:
            new_balance = balance - interest_amount
            cursor.execute(
                'UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?',
                (new_balance, datetime.now().isoformat(), str(user_id))
            )
            cursor.execute(
                'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (str(user_id), -interest_amount, 'loan_interest', description)
            )
            success = True
            print(f"✅ Списано {interest_amount} баллов процентов с основных средств пользователя {user_id}")

        # Если основных баллов не хватает, списываем с кредитных
        elif credit_balance >= interest_amount:
            new_credit_balance = credit_balance - interest_amount
            cursor.execute(
                'UPDATE users SET credit_balance = ?, updated_at = ? WHERE user_id = ?',
                (new_credit_balance, datetime.now().isoformat(), str(user_id))
            )
            cursor.execute(
                'INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)',
                (str(user_id), -interest_amount, 'loan_interest', description)
            )
            success = True
            print(f"✅ Списано {interest_amount} баллов процентов с кредитных средств пользователя {user_id}")
        else:
            # Если средств не хватает, начисляем штраф
            penalty = interest_amount * 0.1  # 10% штраф
            print(f"⚠️ Недостаточно средств для оплаты процентов по кредиту #{loan_id}. Штраф: {penalty}")

        if success:
            # Обновляем данные по кредиту
            cursor.execute('''
                UPDATE loans 
                SET total_paid_interest = COALESCE(total_paid_interest, 0) + ?,
                    next_interest_date = ?
                WHERE id = ?
            ''', (interest_amount,
                  (next_interest_date + timedelta(hours=504)).isoformat(),  # +21 день
                  loan_id))

        conn.commit()
        conn.close()
        return success

    except Exception as e:
        print(f"❌ Ошибка обработки платежа по процентам: {e}")
        return False


def start_loan_scheduler():
    """Запускает планировщик для автоматического списания платежей"""

    def scheduler():
        while True:
            try:
                print("🔄 Проверка платежей по кредитам...")
                process_loan_payments()
                time.sleep(3600)
            except Exception as e:
                print(f"❌ Ошибка в планировщике кредитов: {e}")
                time.sleep(300)

    scheduler_thread = threading.Thread(target=scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Планировщик платежей по кредитам запущен")


start_loan_scheduler()


# ================== ОСНОВНЫЕ ФУНКЦИИ ==================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users(users_dict):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователей: {e}")


def send_suggestion_to_channel(user_info, suggestion_text):
    try:
        message_text = f"💡 НОВОЕ ПРЕДЛОЖЕНИЕ\n\n👤 От: {user_info['first_name']}\n🆔 ID: {user_info['user_id']}\n"
        if user_info.get('username'):
            message_text += f"📱 Username: @{user_info['username']}\n"
        message_text += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n📝 Предложение:\n{suggestion_text}"

        bot.send_message(SUGGESTIONS_CHANNEL, message_text)
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки в канал: {e}")
        return False


def send_purchase_notification(user_id, product, user, amount_from_balance, amount_from_credit, new_balance,
                               new_credit):
    """Отправляет уведомление о покупке в канал"""
    try:
        payment_parts = []
        if amount_from_balance > 0:
            payment_parts.append(f"{amount_from_balance} из основных баллов")
        if amount_from_credit > 0:
            payment_parts.append(f"{amount_from_credit} из кредитных средств")

        payment_description = " + ".join(payment_parts)

        message_text = f"""🛒 НОВАЯ ПОКУПКА В МАГАЗИНЕ

👤 Покупатель: {user.first_name or 'Неизвестно'}
🆔 ID: {user_id}
📱 Username: @{user.username or 'не указан'}

🎁 Товар: {product['name']}
💰 Стоимость: {product['price']} баллов
💸 Списание: {payment_description}

📊 Новые балансы покупателя:
• Основные баллы: {new_balance}
• Кредитные средства: {new_credit}
• Всего: {new_balance + new_credit} баллов

📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

✅ Баллы автоматически списаны
⚠️ Необходимо выдать товар пользователю"""

        bot.send_message(SUGGESTIONS_CHANNEL, message_text)
        print(f"✅ Уведомление о покупке отправлено в канал для пользователя {user_id}")
        return True

    except Exception as e:
        print(f"❌ Ошибка отправки уведомления о покупке: {e}")
        return False


# ================== ЗАГРУЗКА ДАННЫХ ==================
print("📂 Загружаем данные...")
users = load_users()
print("✅ Данные загружены")


# ================== ОСНОВНЫЕ ОБРАБОТЧИКИ ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or "Пользователь"

    if user_id not in users:
        users[user_id] = {
            'first_name': first_name,
            'username': message.from_user.username or "не указан",
            'is_new': True,
            'visit_count': 1,
            'registered_at': datetime.now().isoformat()
        }
    else:
        users[user_id]['visit_count'] += 1
        users[user_id]['is_new'] = False

    save_users(users)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "👤 Профиль", "📊 История зачислений", "💡 Предложения",
        "⭐ Отзывы", "📋 Правила", "⚡ Штрафы", "🛒 Покупки",
        "📋 Список ID", "💰 Кредит", "🎯 Викторины", "🎁 Ежедневный бонус",
        "🎪 Лотерея", "🏆 Уровни"
    ]

    # Всегда показываем админ-панель админам
    if is_admin(message.from_user.id):
        buttons.append("⚙️ Админ-панель")

    for btn_text in buttons:
        markup.add(types.KeyboardButton(btn_text))

    welcome_text = f"""👋 Привет, {first_name}!

Добро пожаловать в систему мотивации нооFuck'а! 🚀

💡 Баланс автоматически синхронизируется с Google Таблицей.
🔄 Изменения в таблице сразу отображаются в боте.

Выберите раздел:"""

    bot.send_message(user_id, welcome_text, reply_markup=markup)


def show_profile(message):
    user_id = str(message.from_user.id)

    try:
        current_balance = get_user_balance(user_id)
        credit_balance = get_user_credit_balance(user_id)
        total_available = current_balance + credit_balance

        transactions = get_user_transactions(user_id, 5)

        level_info = get_user_level_info(user_id)

        profile_text = f"👤 Ваш профиль\n\n"
        profile_text += f"🆔 ID: {user_id}\n"
        profile_text += f"👤 Имя: {message.from_user.first_name or 'Не указано'}\n"
        profile_text += f"📱 Username: @{message.from_user.username or 'не указан'}\n"

        if level_info:
            profile_text += f"🏆 Уровень: {level_info['level']} ({level_info['level_name']})\n"
            profile_text += f"⭐ Опыт: {level_info['xp']}/{level_info['xp_required']}\n"

        profile_text += f"\n💼 Ваши средства:\n"
        profile_text += f"   💰 Основные баллы: {current_balance}\n"
        profile_text += f"   🏦 Кредитные средства: {credit_balance}\n"
        profile_text += f"   💳 Всего доступно: {total_available} баллов\n"

        bonus_info = get_daily_bonus_info(user_id)
        if bonus_info and bonus_info['last_claim_date']:
            last_claim = datetime.fromisoformat(bonus_info['last_claim_date'])
            today = datetime.now().date()

            if last_claim.date() == today:
                profile_text += f"\n🎁 Ежедневный бонус: уже получен сегодня! 🎉\n"
            else:
                profile_text += f"\n🎁 Ежедневный бонус: готов к получению! 🎁\n"

            profile_text += f"   📅 Текущая серия: {bonus_info['streak_count']} дней\n"
            profile_text += f"   💰 Всего бонусов: {bonus_info['total_bonus_received']} баллов\n"
        else:
            profile_text += f"\n🎁 Ежедневный бонус: еще не получал\n"

        users_data = load_google_sheets_data()
        user_data = users_data.get(user_id, {})

        if user_data:
            count_3_4 = user_data.get('count_3_4', 0)
            penalty_applied = user_data.get('penalty_applied', 0)

            profile_text += f"\n⚠️ Количество просроченных ДД: {count_3_4}\n"
            if penalty_applied > 0:
                profile_text += f"🚫 Штрафов применено: {penalty_applied}\n"

        if transactions:
            profile_text += "\n📊 Последние операции:\n"
            for amount, t_type, description, date in transactions:
                sign = "➕" if amount > 0 else "➖"
                if isinstance(date, datetime):
                    date_str = date.strftime('%d.%m')
                elif isinstance(date, str):
                    try:
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        date_str = date_obj.strftime('%d.%m')
                    except:
                        date_str = date[:5]
                else:
                    date_str = str(date)[:5]

                profile_text += f"{sign} {abs(amount)} - {description} ({date_str})\n"
        else:
            profile_text += "\n📊 История операций пуста\n"

        bot.send_message(user_id, profile_text)

    except Exception as e:
        print(f"❌ Ошибка показа профиля: {e}")
        bot.send_message(user_id, "❌ Ошибка загрузки профиля")


@bot.message_handler(content_types=['text'])
def handle_messages(message):
    user_id = str(message.from_user.id)

    # Обработка отмены для всех состояний
    if message.text in ["🔙 Отмена", "🔙 Назад", "🔙 В меню", "Отмена"]:
        user_states[user_id] = None
        start(message)
        return

    # Проверяем состояния пользователя
    if user_id in user_states:
        current_state = user_states[user_id]

        # Обработка конкретных состояний
        if current_state == 'waiting_suggestion':
            handle_suggestion(message)
            return
        elif current_state == 'waiting_password':
            handle_password(message)
            return
        elif current_state == 'waiting_credit_amount':
            handle_credit_amount(message)
            return
        elif current_state == 'shopping':
            handle_shop_selection(message)
            return
        elif current_state == 'creating_lottery':
            handle_admin_lottery_creation(message)
            return
        elif current_state == 'creating_broadcast':
            handle_admin_broadcast_creation(message)
            return
        elif current_state == 'selecting_lottery_to_draw':
            handle_lottery_selection_for_draw(message)
            return
        elif current_state == 'creating_quiz_code':  # НОВЫЙ ОБРАБОТЧИК
            handle_quiz_code_creation(message)
            return

    # Обработка обычных команд
    handlers = {
        "👤 Профиль": show_profile,
        "📊 История зачислений": show_history,
        "💡 Предложения": show_suggestions_menu,
        "⭐ Отзывы": show_reviews,
        "📋 Правила": show_rules,
        "⚡ Штрафы": show_penalties,
        "🛒 Покупки": lambda msg: enter_shop(msg),
        "📋 Список ID": show_password_prompt,
        "💰 Кредит": show_credit_menu,
        "🎯 Викторины": show_quizzes_menu,
        "🎁 Ежедневный бонус": handle_daily_bonus,
        "🎪 Лотерея": show_lottery_menu,
        "🏆 Уровни": show_levels_menu,
        "⚙️ Админ-панель": admin_broadcast_menu,
        "📊 Мои викторины": show_my_quizzes,
        "📢 Создать рассылку": lambda msg: start_broadcast_creation(msg),
        "📊 Статистика рассылок": handle_admin_broadcast_stats,
        "📋 История рассылок": handle_admin_broadcast_history,
        "🎪 Создать лотерею": lambda msg: start_lottery_creation(msg),
        "🔤 Создать код викторины": lambda msg: start_quiz_code_creation(msg),  # НОВАЯ КНОПКА
        "📊 Статистика викторин": lambda msg: show_quiz_stats(msg),  # НОВАЯ КНОПКА
        "🗑️ Удалить активные лотереи": handle_admin_delete_active_lotteries,
        "🧹 Удалить завершенные лотереи": handle_admin_delete_finished_lotteries,
        "🎰 Запустить розыгрыш": handle_admin_draw_lottery,
        "🔄 Обновить кэш Google": handle_admin_refresh_cache,
    }

    if message.text in handlers:
        handlers[message.text](message)
    elif message.text in ["📝 Взять кредит", "📊 Мои кредиты"]:
        show_credit_menu(message)
    elif message.text.startswith("🎰 ") and " (билетов: " in message.text:
        handle_lottery_selection_for_draw(message)
    else:
        # Обработка кодовых слов викторин
        handle_quiz_code(message)


def show_history(message):
    user_id = str(message.from_user.id)

    try:
        bot.send_message(user_id, "🔄 Загружаем историю из Google Sheets...")
        history = get_user_history(user_id)

        current_balance = get_user_balance(user_id)
        credit_balance = get_user_credit_balance(user_id)
        total_available = current_balance + credit_balance

        if history:
            history_text = f"📊 Полная история начислений\n\n"
            history_text += f"Всего записей: {len(history)}\n"
            history_text += f"Общий балл: {total_available}\n\n"

            for i, record in enumerate(history, 1):
                task = record.get('task', 'Неизвестное задание')
                score = record.get('score', 0)
                description = record.get('description', '')
                original_value = record.get('original_value', '')

                if score > 0:
                    emoji = "🟢"
                elif score < 0:
                    emoji = "🔴"
                else:
                    emoji = "⚪"

                history_text += f"{i}. {emoji} {task}\n"
                history_text += f"   ⭐ Баллы: {score:+.0f}\n"

                if description:
                    history_text += f"   📝 {description}\n"

                history_text += "\n"

        else:
            history_text = "📊 История начислений\n\n"
            history_text += "Данные не найдены.\n\n"
            history_text += f"🆔 Ваш ID: {user_id}\n"
            history_text += f"💳 Текущий баланс: {total_available} баллов\n"
            history_text += "💡 Используйте кнопку '📋 Список ID' чтобы увидеть доступные ID"

        if len(history_text) > 4000:
            parts = [history_text[i:i + 4000] for i in range(0, len(history_text), 4000)]
            for part in parts:
                bot.send_message(user_id, part)
                time.sleep(0.5)
        else:
            bot.send_message(user_id, history_text)

    except Exception as e:
        logger.error(f"Ошибка в show_history: {e}")
        bot.send_message(user_id, "❌ Произошла ошибка при загрузке истории. Попробуйте позже.")


def get_user_history(user_id):
    """Получает историю конкретного пользователя из Google таблицы и локальной БД"""
    users_data = load_google_sheets_data()
    user_id_str = str(user_id)

    history = []

    if user_id_str in users_data:
        user_data = users_data[user_id_str]

        for task_name, score_info in user_data['scores'].items():
            if task_name == 'penalty_info':
                history.append({
                    'task': 'Штраф за просроченные ДД',
                    'score': score_info['points'],
                    'date': '2024-2025',
                    'description': score_info.get('description', 'Штраф за просроченные ДД'),
                    'source': 'google'
                })
            elif isinstance(score_info, dict) and 'points' in score_info:
                history.append({
                    'task': task_name,
                    'score': score_info['points'],
                    'date': '2024-2025',
                    'description': score_info.get('description', ''),
                    'original_value': score_info.get('value', ''),
                    'source': 'google'
                })

    transactions = get_user_transactions(user_id, 100)

    for amount, t_type, description, date in transactions:
        if t_type == 'initial':
            continue

        if t_type == 'purchase':
            task_name = f"🛒 Покупка: {description}"
        elif t_type == 'credit_operation':
            if amount < 0:
                task_name = f"💸 Списание кредитных средств: {description}"
            else:
                task_name = f"🏦 Кредитные средства: {description}"
        elif 'credit' in t_type:
            task_name = f"🏦 Кредитная операция: {description}"
        else:
            task_name = f"📊 Операция: {description}"

        if isinstance(date, datetime):
            date_str = date.strftime('%d.%m.%Y')
        elif isinstance(date, str):
            try:
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                date_str = date_obj.strftime('%d.%m.%Y')
            except:
                date_str = date
        else:
            date_str = str(date)

        history.append({
            'task': task_name,
            'score': amount,
            'date': date_str,
            'description': '',
            'source': 'local_db'
        })

    history.sort(key=lambda x: x['date'] if x['source'] == 'local_db' else '2024-2025', reverse=True)
    return history


def show_suggestions_menu(message):
    user_id = str(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    user_states[user_id] = 'waiting_suggestion'
    bot.send_message(user_id, "💡 Напишите ваше предложение:", reply_markup=markup)


def handle_suggestion(message):
    user_id = str(message.from_user.id)
    suggestion_text = message.text

    if suggestion_text in ["🔙 Назад", "🔙 Отмена"]:
        user_states[user_id] = None
        start(message)
        return

    if len(suggestion_text.strip()) < 10:
        bot.send_message(user_id, "❌ Предложение слишком короткое.")
        return

    user_info = {
        'user_id': user_id,
        'first_name': message.from_user.first_name or "Неизвестно",
        'username': message.from_user.username or "не указан"
    }

    if send_suggestion_to_channel(user_info, suggestion_text):
        add_xp(user_id, XP_REWARDS["suggestion"], "suggestion")

        bot.send_message(user_id, "✅ Спасибо! Ваше предложение отправлено.")
    else:
        bot.send_message(user_id, "❌ Ошибка отправки.")

    user_states[user_id] = None
    start(message)


def show_password_prompt(message):
    user_id = str(message.from_user.id)
    user_states[user_id] = 'waiting_password'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    bot.send_message(user_id, "🔐 Для доступа к списку ID введите пароль:", reply_markup=markup)


def handle_password(message):
    user_id = str(message.from_user.id)
    password_attempt = message.text

    if password_attempt in ["🔙 Назад", "🔙 Отмена"]:
        user_states[user_id] = None
        start(message)
        return

    if password_attempt == PASSWORD:
        user_states[user_id] = None
        show_available_ids(message)
    else:
        bot.send_message(user_id, "❌ Неверный пароль. Попробуйте еще раз:")


def show_available_ids(message):
    """Показывает все ID которые есть в таблице с актуальными балансами"""
    user_id = str(message.from_user.id)

    bot.send_message(user_id, "🔄 Загружаем список ID из таблицы...")

    users_data = load_google_sheets_data()

    if users_data:
        ids_text = "📋 ПОЛНЫЙ СПИСОК ID В ТАБЛИЦЕ:\n\n"

        sorted_users = sorted(users_data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)

        for i, (uid, data) in enumerate(sorted_users, 1):
            name = data.get('name', 'Неизвестно')

            try:
                user_id_num = int(uid)
                current_balance = get_user_balance(user_id_num)
                credit_balance = get_user_credit_balance(user_id_num)
                total_available = current_balance + credit_balance
            except (ValueError, TypeError):
                total_available = data.get('total_score', 0)
                current_balance = total_available
                credit_balance = 0

            count_3_4 = data.get('count_3_4', 0)
            penalty_applied = data.get('penalty_applied', 0)

            ids_text += f"{i}. 🆔 {uid} - {name}\n"
            ids_text += f"   💰 Всего баллов: {total_available}\n"
            ids_text += f"   ⚠️ Просроченных ДД: {count_3_4}\n"
            if penalty_applied > 0:
                ids_text += f"   🚫 Штрафов: {penalty_applied}\n"
            ids_text += "\n"

        ids_text += f"🔍 Всего пользователей: {len(users_data)}\n"
        ids_text += f"👤 Ваш ID: {user_id}\n"
        user_current_balance = get_user_balance(int(user_id))
        user_credit_balance = get_user_credit_balance(int(user_id))
        user_total = user_current_balance + user_credit_balance
        ids_text += f"💳 Ваши баллы: {user_total} (основные: {user_current_balance} + кредитные: {user_credit_balance})"

    else:
        ids_text = "❌ Не удалось загрузить данные из таблицы"

    if len(ids_text) > 4000:
        parts = []
        current_part = ""
        lines = ids_text.split('\n')

        for line in lines:
            if len(current_part + line + '\n') > 4000:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'

        if current_part:
            parts.append(current_part)

        for part in parts:
            bot.send_message(user_id, part)
            time.sleep(0.5)
    else:
        bot.send_message(user_id, ids_text)

    start(message)


def show_reviews(message):
    user_id = str(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("⭐ Оставить отзыв", url="https://t.me/noofuck_feedback")
    markup.add(btn)
    bot.send_message(user_id, "⭐ Отзывы\n\nОставьте отзыв о нашей системе:", reply_markup=markup)


def show_rules(message):
    rules_text = "📋 Правила начисления баллов\n\n 🚀  Правила начисления баллов \n\n Здесь ты узнаешь, как зарабатывать очки в нашей системе мотивации. Активничай, учись и получай за это заслуженные баллы!\n\n --- ✨ ---\n\n 📚 Учеба и дисциплина\n\n→ Прислал(а) ДЗ в дедлайн →  + 10 баллов \n\n → Сдал(а) ДЗ после дедлайна → + 5 баллов \n\n → Пробник сдан в срок → + 15 баллов \n\n → Пробник сдан после дедлайна → + 8 баллов \n\n 🏆 Достижения и активность \n\n → Успешно закрыл(а) зачёт → + 20 баллов \n\n → Пришёл(шла) на сходку → + 15 баллов \n\n → Победил(а) в викторине → + 15 баллов \n\n → Участвовал(а) в викторине → + 8 баллов \n\n 💎 Фирменные активности от Никиты \n\n → Решил(а) авторский пробник → + 30 баллов \n\n → Посетил(а) и активно участвовал(а) на доп. вебинаре → + 15 баллов \n\n 🪅 Фирменные активности от Гели \n\n → Решил(а) авторский пробник → + 30 баллов \n\n → Посетил(а) и активно участвовал(а) на доп. вебинаре → + 15 баллов \n\n → Решил(а) домашнее задание повышенного уровня верно → + 5 баллов \n\n Решил(а) домашнее задание повышенного уровня неверно → + 3 балла \n\n 🚀 Крупные победы \n\n → Успешно сдал(а) рубежную аттестация →  + 25 баллов \n\n --- ✨ --- \n\n Участвуй, действуй и покоряй новые высоты! 💪"
    bot.send_message(message.from_user.id, rules_text)


def show_penalties(message):
    penalties_text = """⚡ Штрафы

🔴 НАРУШЕНИЯ И ШТРАФЫ 

*В этом разделе вы сможете посмотреть за что начисляются штрафные санкции в системе мотивации 🚀 нооFuck'а*

━━━━━━━━━━━━━━━━━━━━

📋 КАТЕГОРИИ ШТРАФОВ:

❌ Просроченные ДД:
   • Первые 2 просрочки → 0 баллов
   • Каждая последующая → 🔴 -20 баллов

🚫 Серьезные нарушения:
   • Несданный зачет → 🔴 -20 баллов
   • Несданный авторский пробник → 🔴 -30 баллов
   • Пропущен дедлайн от куратора → 🔴 -15 баллов
   • Перенос дедлайна ДЗ без предупреждения → 🔴 -10 баллов
   • Перенос дедлайна пробника без предупреждения → 🔴 -15 баллов
   • Нет ответа в ЛС за 24 часа → 🔴 -20 баллов
   • Перенос ДЗ более двух раз → 🔴 -20 баллов
   • Неверная кодовая фраза → 🔴 -10 баллов
   • Не сдана рубежная аттестация → 🔴 -25 баллов

━━━━━━━━━━━━━━━━━━━━

💡 ПОЛЕЗНАЯ ИНФОРМАЦИЯ:

✅ Как избежать штрафов?
   • Своевременно выполнять ДЗ
   • Следить за дедлайнами
   • Консультироваться при трудностях

📊 Где посмотреть историю?
   • Раздел "История зачислений"
   • В вашем профиле "Профиль"""
    bot.send_message(message.from_user.id, penalties_text)


def show_credit_menu(message):
    """Меню кредита"""
    user_id = str(message.from_user.id)

    if message.text == "📝 Взять кредит":
        user_states[user_id] = 'waiting_credit_amount'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(user_id, "💳 Введите сумму кредита (максимум 250 баллов):", reply_markup=markup)
        return

    if message.text == "📊 Мои кредиты":
        loan_info = get_loan_info(user_id)
        bot.send_message(user_id, loan_info)
        return

    if message.text == "🔙 Назад":
        user_states[user_id] = None
        start(message)
        return

    credit_info = """💰 СИСТЕМА КРЕДИТОВ 💰

Условия кредита:
• 🏦 Максимальная сумма: 250 баллов
• 📈 Проценты: 14% каждые 504 часа (21 день)
• 💸 Платеж: 1/12 от суммы каждые 168 часов (7 дней)
• ⏱️ Полное погашение: 12 недель

Пример расчета:
Кредит 120 баллов:
• Еженедельный платеж: 10 баллов
• Проценты каждые 3 недели: 16.8 баллов

⚠️ Внимание: Кредит списывается автоматически!"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Взять кредит"))
    markup.add(types.KeyboardButton("📊 Мои кредиты"))
    markup.add(types.KeyboardButton("🔙 Назад"))

    bot.send_message(user_id, credit_info, reply_markup=markup)


def handle_credit_amount(message):
    """Обработка ввода суммы кредита"""
    user_id = str(message.from_user.id)

    if message.text in ["🔙 Назад", "🔙 Отмена"]:
        user_states[user_id] = None
        show_credit_menu(message)
        return

    try:
        amount = int(message.text)

        if amount <= 0:
            bot.send_message(user_id, "❌ Сумма должна быть положительной!")
            return

        if amount > 250:
            bot.send_message(user_id, "❌ Максимальная сумма кредита - 250 баллов!")
            return

        processing_msg = bot.send_message(user_id, "⏳ Создаем кредит...")

        balance_before = get_user_balance(user_id)
        credit_before = get_user_credit_balance(user_id)

        loan_id = create_loan(user_id, amount)

        balance_after = get_user_balance(user_id)
        credit_after = get_user_credit_balance(user_id)

        bot.delete_message(user_id, processing_msg.message_id)

        if loan_id:
            user_states[user_id] = None
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("🔙 В меню"))

            loan_info = f"""✅ КРЕДИТ ОДОБРЕН!

📋 Детали кредита:
• 💳 Сумма: {amount} баллов
• 🆔 Номер кредита: #{loan_id}
• 💸 Еженедельный платеж: {amount // 12} баллов
• 📈 Проценты: 14% каждые 21 день
• ⏱️ Срок: 12 недель

💰 Балансы:
   • Основные баллы: {balance_before} → {balance_after}
   • Кредитные средства: {credit_before} → {credit_after}

✅ Кредитные средства начислены на ваш счет!

⚠️ Платежи будут списываться автоматически."""

            bot.send_message(user_id, loan_info, reply_markup=markup)
        else:
            bot.send_message(user_id, "❌ Ошибка при создании кредита. Попробуйте позже.")

    except ValueError:
        bot.send_message(user_id, "❌ Пожалуйста, введите число!")
    except Exception as e:
        bot.send_message(user_id, "❌ Ошибка при обработке заявки")
        print(f"Credit error: {e}")


# ================== СИСТЕМА МАГАЗИНА ==================
def enter_shop(message):
    user_id = str(message.from_user.id)
    user_states[user_id] = 'shopping'
    show_purchases(message)


def show_purchases(message):
    user_id = str(message.from_user.id)
    balance = get_user_balance(user_id)
    credit_balance = get_user_credit_balance(user_id)
    total_available = balance + credit_balance

    shop_text = f"""🛒 МАГАЗИН БАЛЛОВ

Здесь вы можете обменять баллы на полезные товары и услуги!

💼 Ваши средства:
💰 Основные баллы: {balance}
🏦 Кредитные средства: {credit_balance}
💳 Всего доступно: {total_available} баллов

Выберите категорию:"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    categories = set(product["category"] for product in PRODUCTS.values())
    for category in categories:
        markup.add(types.KeyboardButton(category))

    markup.add(types.KeyboardButton("🔙 Назад"))

    bot.send_message(user_id, shop_text, reply_markup=markup)


def handle_shop_selection(message):
    user_id = str(message.from_user.id)

    if message.text in ["🔙 Назад", "🔙 Отмена"]:
        user_states[user_id] = None
        start(message)
        return

    categories = set(product["category"] for product in PRODUCTS.values())
    if message.text in categories:
        show_products_in_category(message, message.text)
        return

    for product_id, product in PRODUCTS.items():
        if message.text == product["name"]:
            show_product_details(message, product_id)
            return

    if message.text.startswith("💳 Оплатить"):
        product_id = message.text.replace("💳 Оплатить ", "")
        process_payment(message, product_id)
        return

    show_purchases(message)


def show_products_in_category(message, category):
    user_id = str(message.from_user.id)

    category_products = {pid: prod for pid, prod in PRODUCTS.items() if prod["category"] == category}

    products_text = f"{category}\n\n"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    for product_id, product in category_products.items():
        products_text += f"{product['name']} - {product['price']} баллов\n"
        markup.add(types.KeyboardButton(product['name']))

    markup.add(types.KeyboardButton("🔙 В магазин"))

    bot.send_message(user_id, products_text, reply_markup=markup)


def show_product_details(message, product_id):
    user_id = str(message.from_user.id)
    product = PRODUCTS[product_id]
    balance = get_user_balance(user_id)
    credit_balance = get_user_credit_balance(user_id)
    total_available = balance + credit_balance

    product_text = f"""🎁 {product['name']}

{product['description']}

💰 Цена: {product['price']} баллов

💼 Ваши средства:
• Основные баллы: {balance}
• Кредитные средства: {credit_balance}
• Всего доступно: {total_available}"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if total_available >= product['price']:
        amount_from_balance = min(balance, product['price'])
        amount_from_credit = product['price'] - amount_from_balance

        product_text += f"\n\n✅ Достаточно средств для покупки!"
        product_text += f"\n💸 Будет списано:"

        if amount_from_balance > 0:
            product_text += f"\n   • {amount_from_balance} из основных баллов"
        if amount_from_credit > 0:
            product_text += f"\n   • {amount_from_credit} из кредитных средств"

        markup.add(types.KeyboardButton(f"💳 Оплатить {product_id}"))
    else:
        product_text += f"\n\n❌ Недостаточно средств. Не хватает: {product['price'] - total_available} баллов"

    markup.add(types.KeyboardButton("🔙 В магазин"))

    bot.send_message(user_id, product_text, reply_markup=markup)


def process_payment(message, product_id):
    """Обработка платежа за товары с улучшенной стабильностью"""
    user_id = str(message.from_user.id)
    product = PRODUCTS[product_id]

    # Получаем актуальные балансы
    balance = get_user_balance(user_id)
    credit_balance = get_user_credit_balance(user_id)
    total_available = balance + credit_balance

    if total_available < product['price']:
        bot.send_message(user_id, "❌ Недостаточно средств для покупки!")
        show_purchases(message)
        return

    processing_msg = bot.send_message(user_id, "⏳ Обрабатываем платеж...")

    amount_from_balance = min(balance, product['price'])
    amount_from_credit = product['price'] - amount_from_balance

    success = True
    description_parts = []

    # Списание основных баллов
    if amount_from_balance > 0:
        success_balance = update_user_balance(
            user_id,
            -amount_from_balance,
            f"Покупка: {product['name']}",
            product_id
        )
        success = success and success_balance
        description_parts.append(f"{amount_from_balance} из основных баллов")

    # Списание кредитных средств
    if amount_from_credit > 0:
        success_credit = update_user_credit_balance(
            user_id,
            -amount_from_credit,
            f"Покупка: {product['name']}"
        )
        success = success and success_credit
        description_parts.append(f"{amount_from_credit} из кредитных средств")

    bot.delete_message(user_id, processing_msg.message_id)

    if success:
        # Получаем обновленные балансы
        new_balance = get_user_balance(user_id)
        new_credit = get_user_credit_balance(user_id)

        payment_description = " и ".join(description_parts)

        # Начисляем опыт за покупку
        xp_for_purchase = (product['price'] // 100) * XP_REWARDS["purchase"]
        level_up, new_level, reward = add_xp(user_id, xp_for_purchase, "purchase")

        success_message = f"✅ Покупка успешно совершена!\n\n"
        success_message += f"🎁 Товар: {product['name']}\n"
        success_message += f"💰 Стоимость: {product['price']} баллов\n"
        success_message += f"💸 Списание: {payment_description}\n"
        success_message += f"💳 Новый баланс: {new_balance} основных + {new_credit} кредитных\n"
        success_message += f"🎯 Получено опыта: +{xp_for_purchase}\n"

        if level_up:
            success_message += f"🏆 Поздравляем! Вы достигли {new_level} уровня! +{reward} баллов\n"

        success_message += f"📦 Товар будет выдан в ближайшее время"

        bot.send_message(user_id, success_message)

        # Отправляем уведомление в канал
        send_purchase_notification(
            user_id, product, message.from_user,
            amount_from_balance, amount_from_credit,
            new_balance, new_credit
        )
    else:
        bot.send_message(user_id, "❌ Ошибка при списании баллов. Попробуйте позже.")

    show_purchases(message)


# ================== КОМАНДЫ ДЛЯ АДМИНИСТРАТОРОВ ==================
@bot.message_handler(commands=['admin'])
@admin_required
def admin_panel(message):
    """Панель администратора"""
    user_id = message.from_user.id

    admin_text = """⚙️ ПАНЕЛЬ АДМИНИСТРАТОРА

Доступные команды:
• /stats - Статистика бота
• /users - Список пользователей
• /loans - Активные кредиты
• /broadcast - Быстрая рассылка
• /createlottery - Создать лотерею
• /refresh_cache - Обновить кэш Google
• /create_quiz_code - Создать код викторины
• /quiz_stats - Статистика викторин"""

    bot.send_message(user_id, admin_text)


@bot.message_handler(commands=['stats'])
@admin_required
def show_stats(message):
    """Показывает статистику бота"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM transactions')
        total_transactions = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM loans WHERE status = "active"')
        active_loans = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(amount) FROM loans WHERE status = "active"')
        total_loans_amount = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM daily_bonuses')
        total_bonus_users = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(total_bonus_received) FROM daily_bonuses')
        total_bonus_given = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM user_levels')
        total_level_users = cursor.fetchone()[0]

        cursor.execute('SELECT AVG(level) FROM user_levels')
        avg_level = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM lotteries WHERE status = "active"')
        active_lotteries = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM lottery_tickets')
        total_tickets_sold = cursor.fetchone()[0]

        # Статистика викторин
        cursor.execute('SELECT COUNT(*) FROM quiz_codes')
        total_quiz_codes = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM quiz_code_usage')
        total_quiz_completions = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(xp_earned) FROM quiz_code_usage')
        total_quiz_xp = cursor.fetchone()[0] or 0

        # Статистика рассылок
        cursor.execute('SELECT COUNT(*) FROM broadcasts WHERE status = "sent"')
        total_broadcasts = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(sent_count) FROM broadcasts WHERE status = "sent"')
        total_messages_sent = cursor.fetchone()[0] or 0

        conn.close()

        stats_text = f"""📊 СТАТИСТИКА БОТА

👥 Пользователей: {total_users}
💳 Транзакций: {total_transactions}
🏦 Активных кредитов: {active_loans}
💰 Сумма активных кредитов: {total_loans_amount} баллов
🎁 Пользователей с бонусами: {total_bonus_users}
🎊 Всего выдано бонусов: {total_bonus_given} баллов
🏆 Пользователей с уровнями: {total_level_users}
⭐ Средний уровень: {avg_level:.1f}
🎪 Активных лотерей: {active_lotteries}
🎫 Продано лотерейных билетов: {total_tickets_sold}
🎯 Кодов викторин: {total_quiz_codes}
📝 Пройдено викторин: {total_quiz_completions}
💫 Опыта за викторины: {total_quiz_xp}
📢 Рассылок отправлено: {total_broadcasts}
📨 Сообщений рассылки: {total_messages_sent}
⏰ Время работы: {datetime.now().strftime('%d.%m.%Y %H:%M')}"""

        bot.send_message(message.chat.id, stats_text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка получения статистики: {e}")


@bot.message_handler(commands=['broadcast'])
@admin_required
def quick_broadcast(message):
    """Быстрая рассылка для админов"""
    user_id = message.from_user.id
    parts = message.text.split(' ', 1)

    if len(parts) < 2:
        bot.send_message(user_id, "❌ Использование: /broadcast [текст рассылки]")
        return

    broadcast_text = parts[1]

    # Создаем рассылку в базе данных
    broadcast_id = create_broadcast(user_id, broadcast_text)

    if broadcast_id:
        success, result = send_broadcast(broadcast_id)

        if success:
            bot.send_message(user_id, f"✅ Рассылка отправлена!\n\n{result}")
        else:
            bot.send_message(user_id, f"❌ Ошибка при отправке рассылки:\n{result}")
    else:
        bot.send_message(user_id, "❌ Ошибка создания рассылки")


@bot.message_handler(commands=['createlottery'])
@admin_required
def quick_create_lottery(message):
    """Быстрое создание лотереи для админов с поддержкой продолжительности"""
    user_id = message.from_user.id
    parts = message.text.split(' ', 1)

    if len(parts) < 2:
        bot.send_message(user_id,
                         "❌ Использование: /createlottery Название|Описание|Цена|Макс_билетов|Продолжительность_дней\n\n"
                         "Пример: /createlottery Тестовая|Описание лотереи|10|100|14")
        return

    lottery_data = parts[1]

    try:
        data_parts = lottery_data.split('|')
        if len(data_parts) == 4:
            name = data_parts[0].strip()
            description = data_parts[1].strip()
            ticket_price = int(data_parts[2].strip())
            max_tickets = int(data_parts[3].strip())
            duration_days = 7
        elif len(data_parts) == 5:
            name = data_parts[0].strip()
            description = data_parts[1].strip()
            ticket_price = int(data_parts[2].strip())
            max_tickets = int(data_parts[3].strip())
            duration_days = int(data_parts[4].strip())
        else:
            bot.send_message(user_id,
                             "❌ Неверный формат. Используйте:\n"
                             "• Название|Описание|Цена|Макс_билетов\n"
                             "• Название|Описание|Цена|Макс_билетов|Продолжительность_дней")
            return

        # Проверяем валидность продолжительности
        if duration_days <= 0:
            duration_days = 7
        elif duration_days > 365:
            duration_days = 365

        lottery_id = create_lottery(name, description, ticket_price, max_tickets, duration_days)

        if lottery_id:
            bot.send_message(user_id,
                             f"✅ Лотерея '{name}' создана успешно!\n"
                             f"🆔 ID: {lottery_id}\n"
                             f"⏰ Продолжительность: {duration_days} дней\n"
                             f"🎫 Цена билета: {ticket_price} баллов\n"
                             f"📊 Макс. билетов: {max_tickets}")
        else:
            bot.send_message(user_id, "❌ Ошибка создания лотереи")

    except ValueError:
        bot.send_message(user_id, "❌ Ошибка в числах. Убедитесь, что цена, макс. билеты и продолжительность - числа")
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['create_quiz_code'])
@admin_required
def create_quiz_code_command(message):
    """Быстрое создание кода викторины через команду"""
    user_id = message.from_user.id
    parts = message.text.split(maxsplit=3)

    if len(parts) < 4:
        bot.send_message(user_id,
                         "❌ Использование: /create_quiz_code [код] [название] [XP] [макс_использований]\n\n"
                         "Пример: /create_quiz_code CHEM001 Химия_викторина 20 50\n\n"
                         "Или используйте кнопку '🔤 Создать код викторины' в админ-панели")
        return

    try:
        code = parts[1].upper()
        quiz_name = parts[2]
        xp_reward = int(parts[3])
        max_uses = int(parts[4]) if len(parts) > 4 else 50

        # Валидация
        if not code.isalnum():
            bot.send_message(user_id, "❌ Код должен содержать только буквы и цифры")
            return

        if xp_reward < 10 or xp_reward > 50:
            bot.send_message(user_id, "❌ XP должен быть от 10 до 50")
            return

        success = create_quiz_code(code, quiz_name, xp_reward, max_uses, str(user_id))

        if success:
            bot.send_message(user_id,
                             f"✅ Код создан!\n"
                             f"🔤 {code}\n"
                             f"📝 {quiz_name}\n"
                             f"⭐ {xp_reward} XP\n"
                             f"🎫 {max_uses} использований")
        else:
            bot.send_message(user_id, "❌ Ошибка: код уже существует")

    except ValueError:
        bot.send_message(user_id, "❌ Ошибка: XP и макс. использований должны быть числами")
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['quiz_codes'])
@admin_required
def list_quiz_codes_command(message):
    """Показывает все активные коды"""
    show_quiz_stats(message)


@bot.message_handler(commands=['quiz_stats'])
@admin_required
def quiz_stats_command(message):
    """Статистика по викторинам"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Статистика по кодам
        cursor.execute('''
            SELECT COUNT(*) as total_codes,
                   SUM(used_count) as total_uses,
                   AVG(used_count) as avg_uses
            FROM quiz_codes
        ''')
        code_stats = cursor.fetchone()

        # Статистика по пользователям
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as unique_users,
                   SUM(xp_earned) as total_xp_given
            FROM quiz_code_usage
        ''')
        user_stats = cursor.fetchone()

        # Активные коды
        active_codes = get_active_quiz_codes()

        conn.close()

        stats_text = "📊 СТАТИСТИКА ВИКТОРИН\n\n"
        stats_text += f"🔤 Всего кодов: {code_stats[0]}\n"
        stats_text += f"🎫 Всего использований: {code_stats[1]}\n"
        stats_text += f"👥 Уникальных участников: {user_stats[0]}\n"
        stats_text += f"💫 Всего выдано опыта: {user_stats[1]}\n\n"

        if active_codes:
            stats_text += "🟢 Активные коды:\n"
            for code, quiz_name, xp_reward, max_uses, used_count, expires_at in active_codes[:5]:
                stats_text += f"• {code}: {quiz_name} ({used_count}/{max_uses})\n"

        bot.send_message(message.chat.id, stats_text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка получения статистики: {e}")


@bot.message_handler(commands=['refresh_cache'])
@admin_required
def refresh_cache_command(message):
    """Команда для обновления кэша Google таблицы"""
    handle_admin_refresh_cache(message)


# ================== ЗАПУСК БОТА ==================
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БОТ ЗАПУЩЕН")
    print("=" * 50)
    print("✅ Все системы активированы:")
    print("   • 💰 Балансы и транзакции (с автоматической синхронизацией Google)")
    print("   • 🏆 Система уровней и опыта")
    print("   • 🎪 Лотереи и розыгрыши")
    print("   • 📢 Система уведомлений и рассылок")
    print("   • 🎁 Ежедневные бонусы")
    print("   • 💸 Кредитная система")
    print("   • 🛒 Магазин товаров")
    print("   • 🎯 Система викторин с кодовыми словами")
    print("=" * 50)

    test_data = load_google_sheets_data()
    print(f"📊 Загружено пользователей из Google Sheets: {len(test_data)}")

    # Создаем тестовые коды викторин
    create_initial_quiz_codes()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM lotteries WHERE status = "active"')
        active_lotteries = cursor.fetchone()[0]
        conn.close()

        if active_lotteries == 0:
            create_lottery(
                "🎉 Приветственная лотерея",
                "Участвуйте и выигрывайте баллы! Первая лотерея в нашем боте!",
                10,
                100
            )
            print("✅ Создана тестовая лотерея")
    except Exception as e:
        print(f"⚠️ Не удалось создать тестовую лотерею: {e}")

    print("🔄 Запускаем поллинг...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ Ошибка поллинга: {e}")
        print("🔄 Перезапускаем бота...")
        time.sleep(5)
        bot.infinity_polling(timeout=60, long_polling_timeout=60)

# ================== ЗАПУСК ДЛЯ AMVERA ==================
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 БОТ ЗАПУСКАЕТСЯ НА AMVERA (Python 3.14)")
    print("=" * 50)

    while True:
        try:
            print("🔄 Запускаем бота...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")

            time.sleep(10)
