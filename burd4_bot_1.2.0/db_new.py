import datetime
import sqlite3


def ensure_connection(func):
    def inner(*args, **kwargs):
        with sqlite3.connect('anketa.db') as conn:
            kwargs['conn'] = conn
            res = func(*args, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    """ Проверить что нужные таблицы существуют, иначе создать их

        Важно: миграции на такие таблицы вы должны производить самостоятельно!

        :param conn: подключение к СУБД
        :param force: явно пересоздать все таблицы
    """
    c = conn.cursor()

    # Информация о пользователе
    # TODO: создать при необходимости...

    # Сообщения от пользователей
    if force:
        c.execute('DROP TABLE IF EXISTS users_burda')

    c.execute('''CREATE TABLE IF NOT EXISTS users_burda(
                id                               INTEGER PRIMARY KEY,
                chat_id                          INTEGER NOT NULL,
                user_id                          INTEGER NOT NULL,
                user_name                        TEXT,
                balance                          INT DEFAULT 0,
                winning_spins                    INT DEFAULT 0,
                total_spins                      INT DEFAULT 0,
                count_of_available_bonusok       INT DEFAULT 3,
                time_when_can_make_spin DateTime DEFAULT CURRENT_TIMESTAMP,
                time_when_can_make_bonus_game DateTime DEFAULT CURRENT_TIMESTAMP
                )      
        ''')

    # Сохранить изменения
    conn.commit()


@ensure_connection
def user_make_spin(conn, chat_id: int, user_id: int, size_of_win: int, user_name: str):
    c = conn.cursor()

    c.execute('SELECT balance FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (balance_user,) = c.fetchone()
    new_balance = balance_user + size_of_win

    c.execute('SELECT winning_spins FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (winning_spins,) = c.fetchone()
    new_wining_spins = winning_spins + 1 if size_of_win > 0 else winning_spins

    c.execute('SELECT total_spins FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (total_spins,) = c.fetchone()
    new_total_spins = total_spins + 1

    new_time_when_can_make_spin = return_on_6_more()

    c.execute('''UPDATE users_burda 
                 SET balance = ?, 
                     winning_spins = ?,
                     total_spins = ?,
                     time_when_can_make_spin = ?,
                     user_name = ?
                 WHERE chat_id = ? AND user_id = ?''', (
        new_balance, new_wining_spins, new_total_spins, new_time_when_can_make_spin, user_name, chat_id, user_id))
    conn.commit()


@ensure_connection
def user_make_spin_bonus(conn, chat_id: int, user_id: int, win_or_not: bool, user_name: str):
    c = conn.cursor()

    c.execute('SELECT balance FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (balance_user,) = c.fetchone()
    new_balance = balance_user

    c.execute('SELECT winning_spins FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (winning_spins,) = c.fetchone()
    new_wining_spins = winning_spins + 1 if win_or_not is True else winning_spins

    c.execute('SELECT total_spins FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (total_spins,) = c.fetchone()
    new_total_spins = total_spins + 1

    c.execute('''UPDATE users_burda 
                 SET balance = ?, 
                     winning_spins = ?,
                     total_spins = ?,
                     user_name = ?
                 WHERE chat_id = ? AND user_id = ?''', (
        new_balance, new_wining_spins, new_total_spins, user_name, chat_id, user_id))
    conn.commit()


@ensure_connection
def user_balance(conn, chat_id: int, user_id: int):
    c = conn.cursor()

    c.execute('SELECT * FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users_burda (chat_id, user_id) VALUES (?, ?)', (chat_id, user_id))

    c.execute('SELECT balance FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id,))
    (balance_user,) = c.fetchone()
    return int(balance_user)


@ensure_connection
def user_can_make_a_spin(conn, chat_id: int, user_id: int):
    c = conn.cursor()

    c.execute('SELECT * FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users_burda (chat_id, user_id) VALUES (?, ?)', (chat_id, user_id))

    c.execute('SELECT time_when_can_make_spin FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1',
              (chat_id, user_id))
    (time_when_can_make_spin,) = c.fetchone()

    if str_to_date(time_when_can_make_spin) <= datetime.datetime.utcnow():
        return True, None
    else:
        return False, str(str_to_date(time_when_can_make_spin) - datetime.datetime.utcnow()).split(".")[0]


@ensure_connection
def get_top_10_of_group(conn, chat_id: int, user_id: int, user_name: str):
    c = conn.cursor()

    c.execute('SELECT * FROM users_burda WHERE chat_id = ? AND user_id = ?', (chat_id, user_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users_burda (chat_id, user_id, user_name) VALUES (?, ?, ?)', (chat_id, user_id, user_name))
        conn.commit()
    c.execute('SELECT user_name, balance FROM users_burda WHERE chat_id = ? ORDER BY balance DESC LIMIT 10',
              (chat_id,))
    return c.fetchall()


@ensure_connection
def get_top_10_of_world(conn, chat_id: int, user_id: int, user_name: str):
    c = conn.cursor()
    c.execute('SELECT * FROM users_burda')
    if c.fetchone() is None:
        c.execute('INSERT INTO users_burda (chat_id, user_id, user_name) VALUES (?, ?, ?)',
                  (chat_id, user_id, user_name))
        conn.commit()
    c.execute('SELECT user_name, balance FROM users_burda ORDER BY balance DESC LIMIT 10')
    return c.fetchall()


@ensure_connection
def info_about_user(conn, chat_id: int, user_id: int, user_name: str):
    c = conn.cursor()
    c.execute('SELECT * FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id,))
    if c.fetchone() is None:
        c.execute('INSERT INTO users_burda (chat_id, user_id, user_name) VALUES (?, ?, ?)',
                  (chat_id, user_id, user_name))

    c.execute(
        'SELECT count_of_available_bonusok, time_when_can_make_bonus_game FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1',
        (chat_id, user_id))
    (count_of_bonusok_in_day, time_last_bonus_game,) = c.fetchone()

    if count_of_bonusok_in_day < 3:
        if datetime.datetime.utcnow() > str_to_date(time_last_bonus_game):
            c.execute('''UPDATE users_burda 
                             SET count_of_available_bonusok = ?
                             WHERE chat_id = ? AND user_id = ?''', (
                3, chat_id, user_id))
            conn.commit()

    c.execute(
        'SELECT user_id, user_name, balance, winning_spins, total_spins, time_when_can_make_spin, count_of_available_bonusok FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1',
        (chat_id, user_id))
    return c.fetchall()[0]


@ensure_connection
def set_user_balance(conn, chat_id: int, user_id: int, size_of_change: int):
    c = conn.cursor()

    c.execute('SELECT balance FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1', (chat_id, user_id))
    (balance_user,) = c.fetchone()
    new_balance = balance_user + size_of_change
    c.execute('''UPDATE users_burda 
                     SET balance = ?
                     WHERE chat_id = ? AND user_id = ?''', (new_balance, chat_id, user_id))
    conn.commit()

@ensure_connection
def user_can_make_a_bonus_spin(conn, chat_id: int, user_id: int):
    c = conn.cursor()

    c.execute('SELECT count_of_available_bonusok, time_when_can_make_bonus_game FROM users_burda WHERE chat_id = ? AND user_id = ? LIMIT 1',
              (chat_id, user_id))
    (count_of_bonusok_in_day, time_last_bonus_game,) = c.fetchone()

    if 0 < count_of_bonusok_in_day <= 3:
        c.execute('''UPDATE users_burda 
                             SET count_of_available_bonusok = ?, 
                                 time_when_can_make_bonus_game = ?
                             WHERE chat_id = ? AND user_id = ?''', (
            count_of_bonusok_in_day - 1, return_on_1_day_more(), chat_id, user_id))
        conn.commit()
        return True
    else:
        if datetime.datetime.utcnow() > str_to_date(time_last_bonus_game):
            c.execute('''UPDATE users_burda 
                         SET count_of_available_bonusok = ?, 
                             time_when_can_make_bonus_game = ?
                         WHERE chat_id = ? AND user_id = ?''', (
                2, return_on_1_day_more(), chat_id, user_id))
            conn.commit()
            return True
        else:
            return False

def str_to_date(time: str):
    year_month_day = time.split(" ")[0]
    hour_minute_seconds = time.split(" ")[1]

    year = int(year_month_day.split("-")[0])
    month = int(year_month_day.split("-")[1])
    day = int(year_month_day.split("-")[2])

    hours = int(hour_minute_seconds.split(":")[0])
    minutes = int(hour_minute_seconds.split(":")[1])
    seconds = int(hour_minute_seconds.split(":")[2].split(".")[0])

    date = datetime.datetime(year, month, day, hours, minutes, seconds)

    return date


def return_on_6_more():
    date = datetime.datetime.utcnow()
    date += datetime.timedelta(hours=3)
    return str(date) + '.000'

def return_on_1_day_more():
    date = datetime.datetime.utcnow()
    date += datetime.timedelta(hours=24)
    new_date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    return str(new_date) + '.000'
