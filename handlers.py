from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from functools import lru_cache
import text, kb, sqlite3


router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    # Отправляем приветственное сообщение с именем пользователя и меню
    await msg.answer(text.greet .format(name=msg.from_user.full_name), reply_markup=kb.menu)

@router.message(F.text == "admin")
async def admin_handler(msg: Message):
    await msg.answer("Для входа в панель администратора введите пароль")

@router.message(Command("players"))
async def players_handler(msg: Message):
    conn = sqlite3.connect('mbr1.db')
    cursor = conn.cursor()
    @lru_cache(maxsize=None)
    def get_player_list():
        cursor.execute("SELECT last_name FROM players")
        return cursor.fetchall()
    player_list = get_player_list()
    cursor.close()
    conn.close()
    buttons = []
    for row in player_list:
        last_name = row[0]
        buttons.append(types.InlineKeyboardButton(text=last_name, callback_data=f"player_{last_name}"))
    columns = 2
    inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+columns] for i in range(0, len(buttons), columns)])
    await msg.answer("Выберите игрока:", reply_markup=inline_keyboard)


@router.callback_query(lambda c: c.data.startswith('player_'))
async def player_callback_handler(query: types.CallbackQuery):
    last_name = query.data.split('_')[1]
    cursor = sqlite3.connect('mbr1.db').cursor()

    # Извлекаем данные игрока из таблицы player
    cursor.execute("SELECT first_name, birthday FROM players WHERE last_name = ?", (last_name,))
    player_data = cursor.fetchone()
    if player_data is None:
        await query.message.answer("Данные об игроке не найдены")
        return
    first_name, birthday = player_data

    # Извлекаем данные о голах игрока из таблицы goal_detail
    cursor.execute(
        "SELECT count(*) FROM goal_details WHERE who_score = (SELECT player_id FROM players WHERE last_name = ?)",
        (last_name,))
    goals_scored = cursor.fetchone()[0]

    # Извлекаем данные о сыгранных матчах из таблицы match_player
    cursor.execute(
        "SELECT count(*) FROM matches_players WHERE player_id = (SELECT player_id FROM players WHERE last_name = ?)",
        (last_name,))
    match_player = cursor.fetchone()[0]

    # Извлекаем данные о голевых передачах из таблицы goal_detail
    cursor.execute(
        "SELECT count(*) FROM goal_details WHERE who_assist = (SELECT player_id FROM players WHERE last_name = ?)",
        (last_name,))
    goal_assists = cursor.fetchone()[0]

    # Извлекаем данные о номере на футболке из таблицы json_mbr
    cursor.execute(
        "SELECT json_extract(data, '$.jersey') FROM json_mbr WHERE player_id = (SELECT player_id FROM players WHERE last_name = ?)",
        (last_name,))
    jersey_number = cursor.fetchone()[0]

    # Извлекаем данные о позиции из таблицы json_mbr
    cursor.execute(
        "SELECT json_extract(data, '$.position') FROM json_mbr WHERE player_id = (SELECT player_id FROM players WHERE last_name = ?)",
        (last_name,))
    position = cursor.fetchone()[0]

    # Извлекаем данные о стране из таблицы json_mbr
    cursor.execute(
        "SELECT json_extract(data, '$.country') FROM json_mbr WHERE player_id = (SELECT player_id FROM players WHERE last_name = ?)",
        (last_name,))
    country = cursor.fetchone()[0]

    # Формируем сообщение с данными игрока
    message = f"Досье игрока:\n\n"
    message += f"Имя - {last_name}, {first_name}\n"
    message += f"Номер - {jersey_number} \n"
    message += f"Позиция - {position} \n"
    message += f"Дата рождения - {birthday}\n"
    message += f"Страна - {country} \n"
    message += f"Сыграно матчей - {match_player} \n"
    message += f"Голов забито - {goals_scored}\n"
    message += f"Голевых передач - {goal_assists}\n"

    # Отправляем сообщение с досье игрока
    await query.message.answer(message)

@router.message(Command("lastm"))
async def lastmatch_handler(msg: Message):
    conn = sqlite3.connect('mbr1.db')
    cursor = conn.cursor()
    @lru_cache(maxsize=None)
    def get_results_list(cursor):
        cursor.execute("SELECT scored, missed, opponent, play_date FROM matches")
        return cursor.fetchall()
    results_list = get_results_list(cursor)

    # Формируем текстовый список результатов
    results_list_text = "Последние матчи команды:\n" + "\n".join(
        f"Marlboro  ( {scored}:{missed} )  {opponent}  -  {play_date}" for scored, missed, opponent, play_date in
        results_list
    )

    # Создаем список кнопок с оппонентами
    buttons = [
        types.InlineKeyboardButton(text=f"({scored}:{missed}) - {opponent}", callback_data=f"lastm_{play_date}")
        for scored, missed, opponent, play_date in results_list
    ]

    # Разбиваем список кнопок на две колонки
    columns = 2
    inline_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[buttons[i:i + columns] for i in range(0, len(buttons), columns)]
    )

    # Отправляем сообщение с результатами и inline клавиатурой
    await msg.answer("Выберите матч:\n\n" + results_list_text, reply_markup=inline_keyboard)

@router.callback_query(lambda c: c.data.startswith('lastm_'))
async def lastm_callback_handler(query: types.CallbackQuery):
    # Получаем данные из callback-запроса
    match_id = query.data.split('_')[1]

    # Подключаемся к базе данных
    conn = sqlite3.connect('mbr1.db')
    cursor = conn.cursor()

    # Выбираем данные о матче
    cursor.execute("SELECT scored, missed, opponent, play_date, ref FROM matches WHERE play_date = ?", (match_id,))
    result = cursor.fetchone()

    if result:
        # Формируем сообщение с датой матча
        scored, missed, opponent, play_date, ref = result
        message = f"Матч Marlboro - {opponent}\n"
        message += f"Счёт - {scored} : {missed}\n"
        message += f"Стартовый состав - \n"
        message += f"Голы забили - \n"
        message += f"Ссылка на матч - {ref}\n"
        message += f"Дата матча: {play_date}\n"
        message += f"Турнир: - \n"

        # Отправляем сообщение
        await query.message.answer(message)
    else:
        # Если матч не найден, отправляем сообщение об ошибке
        await query.answer("Матч не найден.")

    # Закрываем соединение с базой данных
    conn.close()

@router.message(Command("results"))
async def results_handler(msg: Message):
    conn = sqlite3.connect('mbr1.db')
    cursor = conn.cursor()

    # Извлекаем данные о сыгранных матчах из таблицы matches
    cursor.execute("SELECT count(*) FROM matches")
    matches_played = cursor.fetchone()[0]

    # Извлекаем данные о забитых голах из таблицы goal_details
    cursor.execute("SELECT count(*) FROM goal_details WHERE who_score != 0")
    goal_scored = cursor.fetchone()[0]

    # Извлекаем данные о количестве ассистов из таблицы goal_details
    cursor.execute("SELECT count(*) FROM goal_details WHERE who_assist != 0")
    goal_assists = cursor.fetchone()[0]

    # Так можно посчитать число выигранных матчей
    cursor.execute("SELECT count(match_id) from matches where scored > missed;")
    match_won = cursor.fetchone()[0]

    # Так можно посчитать число выигранных матчей
    cursor.execute("SELECT avg(scored) from matches")
    scored_avg = cursor.fetchone()[0]
    scored_avg = round(scored_avg, 2)

    # Так можно посчитать число выигранных матчей
    cursor.execute("SELECT avg(missed) from matches")
    missed_avg = cursor.fetchone()[0]
    missed_avg = round(missed_avg, 2)

    cursor.execute('SELECT  who_assist, count(*) FROM goal_details GROUP BY who_assist ORDER BY count(*) DESC limit 3')
    res1 = cursor.fetchall()

    # Формируем сообщение с данными команды
    message = f"Результаты ФК 🚬Marlboro🚬:\n\n"
    message += f"Число сыгранных матчей - {matches_played}\n"
    message += f"Забито голов - {goal_scored}\n"
    message += f"Число ассистов - {goal_assists}\n"
    message += f"Матчей выиграно - {match_won}\n"
    message += f"Забито в среднем за игру - {scored_avg}\n"
    message += f"Пропущено в среднем за игру - {missed_avg}\n"

    # Отправляем сообщение с результатами команды
    await msg.answer(message)

    cursor.close()
    conn.close()

@router.callback_query(lambda c: c.data == "lastm")
async def lastmatch_callback_handler(query: types.CallbackQuery):
    await lastmatch_handler(query.message)

@router.callback_query(lambda c: c.data == "players")
async def player_callback_handler(query: types.CallbackQuery):
    await players_handler(query.message)

@router.callback_query(lambda c: c.data == "results")
async def results_callback_handler(query: types.CallbackQuery):
    await results_handler(query.message)
