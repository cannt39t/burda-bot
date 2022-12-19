import asyncio
import logging

from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import BotBlocked

from tabulate import tabulate
import numpy as np

from aiogram import Bot, Dispatcher, executor, types

from db_new import user_make_spin, init_db, user_balance, user_can_make_a_spin, get_top_10_of_group, \
    get_top_10_of_world, info_about_user, set_user_balance, user_make_spin_bonus, user_can_make_a_bonus_spin

API_TOKEN = ''

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

init_db()

list_of_chats_where_bonus_game_playing = list()


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    chat_id = message.chat.id
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Burda 🎰", "Balance 💰"]
    keyboard.add(*buttons)
    buttons = ["Profile 👤", "Group top 👥", "World top 🌎"]
    keyboard.add(*buttons)
    buttons = ["🚨 Bonus games 🚨"]
    keyboard.add(*buttons)
    await message.answer("What do you want?", reply_markup=keyboard, )


@dp.message_handler(Text(equals="Burda 🎰"))
@dp.message_handler(commands=['burda'])
async def burda(message: types.Message):
    chat_id = message.chat.id
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    spin_or_not = user_can_make_a_spin(chat_id=chat_id, user_id=user_id)
    if spin_or_not[0] is True:
        res = await message.reply_dice("🎰")
        res_1_64 = int(res.dice.value)
        size_of_win = dice_value_into_balance(res_1_64)
        user_make_spin(chat_id=chat_id, user_id=user_id, size_of_win=size_of_win, user_name=user_name)
        await asyncio.sleep(2)
        await message.reply("<b>YOU WON: " + str(size_of_win) + str("💲") + "</b>", parse_mode=types.ParseMode.HTML)
    else:
        await message.reply("<b>You already made spin\nCome here in " + spin_or_not[1] + "</b>",
                            parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="◀️ Main menu"))
@dp.message_handler(commands=['/main_menu'])
async def top_group(message: types.Message):
    chat_id = message.chat.id
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    await cmd_start(message=message)


@dp.message_handler(Text(equals="Balance 💰"))
@dp.message_handler(commands=['balance'])
async def balance(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    balance = user_balance(chat_id=chat_id, user_id=user_id)
    await message.reply("<b>Your balance is: " + str(balance) + str(" 💵") + "</b>", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="Group top 👥"))
@dp.message_handler(commands=['top_group'])
async def top_group(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.full_name
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    top_10 = get_top_10_of_group(chat_id=chat_id, user_id=user_id, user_name=user_name)
    table = np.asarray(top_10)
    headers = ["№", "User", "Balance"]
    res = tabulate(table, headers, tablefmt="simple", showindex=range(1, len(table) + 1), maxcolwidths=10)
    await message.answer(f"<code>{res}</code>", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="World top 🌎"))
@dp.message_handler(commands=['top'])
async def top_group(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.full_name
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    top_10 = get_top_10_of_world(chat_id=chat_id, user_id=user_id, user_name=user_name)
    table = np.asarray(top_10)
    headers = ["№", "User", "Balance"]
    res = tabulate(table, headers, tablefmt="simple", showindex=range(1, len(table) + 1), maxcolwidths=10)
    await message.answer(f"<code>{res}</code>", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="Profile 👤"))
@dp.message_handler(commands=['profile'])
async def top_group(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if chat_id in list_of_chats_where_bonus_game_playing:
        return
    user_name = message.from_user.full_name
    info_user = info_about_user(chat_id=chat_id, user_id=user_id, user_name=user_name)
    profile = profile_info(info_user)
    res = tabulate(tabular_data=profile, tablefmt="plain")
    await message.reply(f"<code>{res}</code>", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="🚨 Bonus Game 1️⃣ 🚨"))
@dp.message_handler(commands=['bonuska1'])
async def top_group(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.full_name
    info_user = info_about_user(chat_id=chat_id, user_id=user_id, user_name=user_name)
    if info_user[2] >= 1000:
        if user_can_make_a_bonus_spin(chat_id=chat_id, user_id=user_id) is False:
            await message.reply(f"You have already spinned 3 Bonus Games", parse_mode=types.ParseMode.HTML)
            return
        else:
            await message.answer(f"<b>Your balance: {info_user[2]} - 1000 = {info_user[2] - 1000} 💲</b>",
                                 parse_mode=types.ParseMode.HTML)
        if chat_id in list_of_chats_where_bonus_game_playing:
            return
        else:
            list_of_chats_where_bonus_game_playing.append(chat_id)
        total_win = 0
        set_user_balance(chat_id=chat_id, user_id=user_id, size_of_change=-1000)
        # await balance(message)
        await asyncio.sleep(2)
        await message.answer("<b>💰 Here we go 💰</b>", parse_mode=types.ParseMode.HTML,
                             reply_markup=types.ReplyKeyboardRemove())
        await asyncio.sleep(1)
        times = 10
        for i in range(times):
            res = await message.answer_dice("🎰")
            res_1_64 = int(res.dice.value)
            size_of_win = dice_value_into_balance_bonus_1(res_1_64)
            total_win = total_win + size_of_win
            user_make_spin_bonus(chat_id=chat_id, user_id=user_id, win_or_not=win_or_not(res_1_64), user_name=user_name)
            await asyncio.sleep(3)
            await message.answer("<b>" + str(size_of_win) + str("💲") + "</b>", parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(3)
            if i == times - 1:
                await message.answer(f"<b>TOTAL: {total_win}</b>", parse_mode=types.ParseMode.HTML)
                await asyncio.sleep(3)
                await message.answer("<b>❌ CHOOSING YOUR ❌</b>", parse_mode=types.ParseMode.HTML)
                await asyncio.sleep(3)
                xxx = await message.answer_dice("🎲")
                await asyncio.sleep(5)
                await message.answer(f"<b>YOUR WINNINGS ARE MULTIPLIED BY {xxx.dice.value}</b>",
                                     parse_mode=types.ParseMode.HTML)
                total_win = total_win * xxx.dice.value
                set_user_balance(chat_id=chat_id, user_id=user_id, size_of_change=total_win)
                await asyncio.sleep(3)
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                buttons = ["Burda 🎰", "Balance 💰"]
                keyboard.add(*buttons)
                buttons = ["Profile 👤", "Group top 👥", "World top 🌎"]
                keyboard.add(*buttons)
                buttons = ["🚨 Bonus games 🚨"]
                keyboard.add(*buttons)
                await message.reply("<b>YOU WON: " + str(total_win) + str("💲") + "</b>",
                                    parse_mode=types.ParseMode.HTML, reply_markup=keyboard)
                list_of_chats_where_bonus_game_playing.remove(chat_id)
    else:
        need_to = 1000 - info_user[2]
        await message.reply(f"You can't afford it haha\nYou need: {need_to} 💲", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="🚨 Bonus Game 2️⃣ 🚨"))
@dp.message_handler(commands=['bonuska2'])
async def top_group(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.full_name
    info_user = info_about_user(chat_id=chat_id, user_id=user_id, user_name=user_name)
    if info_user[2] >= 10000:
        if user_can_make_a_bonus_spin(chat_id=chat_id, user_id=user_id) is False:
            await message.reply(f"You have already spinned 3 Bonus Games", parse_mode=types.ParseMode.HTML)
            return
        else:
            await message.answer(f"<b>Your balance: {info_user[2]} - 10000 = {info_user[2] - 10000} 💲</b>",
                                 parse_mode=types.ParseMode.HTML)
        if chat_id in list_of_chats_where_bonus_game_playing:
            return
        else:
            list_of_chats_where_bonus_game_playing.append(chat_id)
        total_spins = 0
        total_win = 0
        set_user_balance(chat_id=chat_id, user_id=user_id, size_of_change=-10000)
        # await balance(message)
        await asyncio.sleep(2)
        await message.answer("<b>💰 Here we go 💰</b>", parse_mode=types.ParseMode.HTML,
                             reply_markup=types.ReplyKeyboardRemove())
        await asyncio.sleep(1)
        times = 3
        await message.answer("<b>The number of $pins: </b>", parse_mode=types.ParseMode.HTML)
        for i in range(times):
            xxx = await message.answer_dice("🎲")
            total_spins += xxx.dice.value
            await asyncio.sleep(5)
        await asyncio.sleep(3)
        await message.answer(f"<b>Total $pins: {total_spins}</b>", parse_mode=types.ParseMode.HTML)
        await asyncio.sleep(3)
        for i in range(total_spins):
            res = await message.answer_dice("🎰")
            res_1_64 = int(res.dice.value)
            size_of_win = dice_value_into_balance_bonus_2(res_1_64)
            total_win = total_win + size_of_win
            user_make_spin_bonus(chat_id=chat_id, user_id=user_id, user_name=user_name, win_or_not=win_or_not(res_1_64))
            await asyncio.sleep(3)
            await message.answer("<b>" + str(size_of_win) + str("💲") + "</b>", parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(3)
            if i == total_spins - 1:
                set_user_balance(chat_id=chat_id, user_id=user_id, size_of_change=total_win)
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                buttons = ["Burda 🎰", "Balance 💰"]
                keyboard.add(*buttons)
                buttons = ["Profile 👤", "Group top 👥", "World top 🌎"]
                keyboard.add(*buttons)
                buttons = ["🚨 Bonus games 🚨"]
                keyboard.add(*buttons)
                await message.reply("<b>YOU WON: " + str(total_win) + str("💲") + "</b>",
                                    parse_mode=types.ParseMode.HTML, reply_markup=keyboard)
                list_of_chats_where_bonus_game_playing.remove(chat_id)
    else:
        need_to = 10000 - info_user[2]
        await message.reply(f"<b>You can't afford it haha\nYou need: {need_to} 💲</b>", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="🚨 Bonus Game 3️⃣ 🚨"))
@dp.message_handler(commands=['bonuska3'])
async def top_group(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.full_name
    info_user = info_about_user(chat_id=chat_id, user_id=user_id, user_name=user_name)
    if info_user[2] >= 100000:
        if user_can_make_a_bonus_spin(chat_id=chat_id, user_id=user_id) is False:
            await message.reply(f"You have already spinned 3 Bonus Games", parse_mode=types.ParseMode.HTML)
            return
        else:
            await message.answer(f"<b>Your balance: {info_user[2]} - 100000 = {info_user[2] - 100000} 💲</b>",
                                 parse_mode=types.ParseMode.HTML)
        if chat_id in list_of_chats_where_bonus_game_playing:
            return
        else:
            list_of_chats_where_bonus_game_playing.append(chat_id)
        total_win = 0
        set_user_balance(chat_id=chat_id, user_id=user_id, size_of_change=-100000)
        # await balance(message)
        await asyncio.sleep(2)
        await message.answer("<b>💰 Here we go 💰</b>", parse_mode=types.ParseMode.HTML,
                             reply_markup=types.ReplyKeyboardRemove())
        await asyncio.sleep(2)
        await message.answer("<b>You have only 3 spins</b>", parse_mode=types.ParseMode.HTML)
        await asyncio.sleep(2)
        times = 3
        while times > 0:
            times = times - 1
            res = await message.answer_dice("🎰")
            res_1_64 = int(res.dice.value)
            size_of_win = dice_value_into_balance_bonus_3(res_1_64)
            total_win = total_win + size_of_win
            user_make_spin_bonus(chat_id=chat_id, user_id=user_id, user_name=user_name, win_or_not=win_or_not(res_1_64))
            await asyncio.sleep(3)
            await message.answer("<b>" + str(size_of_win) + str("💲") + "</b>", parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(3)
            if win_or_not(res_1_64):
                times = 3
                await message.answer("<b>+3 FREE SPINS</b>", parse_mode=types.ParseMode.HTML)
            else:
                if have_2(res_1_64):
                    if times != 3:
                        times += 1
                    await message.answer("<b>+1 FREE SPINS</b>", parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(2)
            await message.answer(f"<b>SPINS: {times}</b>", parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(2)
        await asyncio.sleep(3)
        set_user_balance(chat_id=chat_id, user_id=user_id, size_of_change=total_win)
        await asyncio.sleep(3)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Burda 🎰", "Balance 💰"]
        keyboard.add(*buttons)
        buttons = ["Profile 👤", "Group top 👥", "World top 🌎"]
        keyboard.add(*buttons)
        buttons = ["🚨 Bonus games 🚨"]
        keyboard.add(*buttons)
        await message.reply("<b>YOU WON: " + str(total_win) + str("💲") + "</b>",
                            parse_mode=types.ParseMode.HTML, reply_markup=keyboard)
        list_of_chats_where_bonus_game_playing.remove(chat_id)
    else:
        need_to = 100000 - info_user[2]
        await message.reply(f"<b>You can't afford it haha\nYou need: {need_to} 💲</b>", parse_mode=types.ParseMode.HTML)


@dp.message_handler(Text(equals="🚨 Bonus games 🚨"))
@dp.message_handler(commands=['bonuska'])
async def top_group(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["🚨 Bonus Game 1️⃣ 🚨"]
    keyboard.add(*buttons)
    buttons = ["🚨 Bonus Game 2️⃣ 🚨"]
    keyboard.add(*buttons)
    buttons = ["🚨 Bonus Game 3️⃣ 🚨"]
    keyboard.add(*buttons)
    buttons = ["◀️ Main menu"]
    keyboard.add(*buttons)
    await message.answer("What 🚨 Bonus Game 🚨 do you want?", reply_markup=keyboard)


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    # Update: объект события от Telegram. Exception: объект исключения
    # Здесь можно как-то обработать блокировку, например, удалить пользователя из БД
    print(f"Меня заблокировал пользователь!\nСообщение: {update}\nОшибка: {exception}")

    # Такой хэндлер должен всегда возвращать True,
    # если дальнейшая обработка не требуется.
    return True


def profile_info(info: tuple):
    res = [["Profile", info[1]], ["ID", info[0]], ["Balance:", info[2]], ["Total spins:", info[4]]]
    if info[4] == 0:
        wins = 0
    else:
        wins: float = round(float(info[3] / info[4]) * 100, 2)
    res.append(["Wins:", str(wins) + " %"])
    res.append(["Bonus Games: ", str(info[6]) + "/3"])
    return res


def dice_value_into_balance(dice_value: int):
    in4: str = into_4(dice_value)

    # 3
    if in4.count('3') == 3:
        return 500
    if in4.count('2') == 3:
        return 300
    if in4.count('1') == 3:
        return 200
    if in4.count('0') == 3:
        return 100

    # 2
    """
    if in4.count('3') == 2:
        return 75
    if in4.count('2') == 2:
        return 50
    if in4.count('1') == 2:
        return 25
    if in4.count('0') == 2:
        return 10
    """

    return 0


def into_4(value: int):
    if value == 1:
        return "000"
    num = value - 1
    base = 4
    if not (2 <= base <= 9):
        quit()

    new_num = ''

    while num > 0:
        new_num = str(num % base) + new_num
        num //= base
    if 4 < value < 17:
        new_num = "0" + new_num

    if 2 <= value <= 4:
        new_num = "00" + new_num

    return new_num


def win_or_not(dice_value: int):
    in4: str = into_4(dice_value)

    if in4.count('3') == 3:
        return True
    if in4.count('2') == 3:
        return True
    if in4.count('1') == 3:
        return True
    if in4.count('0') == 3:
        return True
    return False


def dice_value_into_balance_bonus_1(dice_value: int):
    in4: str = into_4(dice_value)

    # 3
    if in4.count('3') == 3:
        return 500
    if in4.count('2') == 3:
        return 300
    if in4.count('1') == 3:
        return 200
    if in4.count('0') == 3:
        return 100

    # 2
    if in4.count('3') == 2:
        return 50
    if in4.count('2') == 2:
        return 25
    if in4.count('1') == 2:
        return 10
    if in4.count('0') == 2:
        return 5

    return 0


def dice_value_into_balance_bonus_2(dice_value: int):
    in4: str = into_4(dice_value)

    # 3
    if in4.count('3') == 3:
        return 50000
    if in4.count('2') == 3:
        return 25000
    if in4.count('1') == 3:
        return 10000
    if in4.count('0') == 3:
        return 5000

    # 2
    if in4.count('3') == 2:
        return 1000
    if in4.count('2') == 2:
        return 500
    if in4.count('1') == 2:
        return 250
    if in4.count('0') == 2:
        return 100

    return 0


def dice_value_into_balance_bonus_3(dice_value: int):
    in4: str = into_4(dice_value)

    # 3
    if in4.count('3') == 3:
        return 500000
    if in4.count('2') == 3:
        return 250000
    if in4.count('1') == 3:
        return 100000
    if in4.count('0') == 3:
        return 50000

    # 2
    if in4.count('3') == 2:
        return 5000
    if in4.count('2') == 2:
        return 2500
    if in4.count('1') == 2:
        return 1000
    if in4.count('0') == 2:
        return 500

    return 0


def have_2(dice_value: int):
    in4: str = into_4(dice_value)

    if in4.count('3') == 2:
        return True
    if in4.count('2') == 2:
        return True
    if in4.count('1') == 2:
        return True
    if in4.count('0') == 2:
        return True

    return False


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
