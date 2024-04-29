import datetime
import logging
import sqlite3

import pymorphy3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

bot = Bot(token="6708597721:AAFD7j11zXiqwtgycnjqnEnpDcFzDWxpEIQ")
dp = Dispatcher(bot, storage=storage)

menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
profile = types.KeyboardButton("Мой профиль👤")
blok = types.KeyboardButton("Мои заметки📄")
menu.add(blok, profile)

prof = types.ReplyKeyboardMarkup(resize_keyboard=True)
back = types.KeyboardButton("Назад⬅")
photo = types.KeyboardButton("Фото📷")
prof.add(back, photo)

remove = types.ReplyKeyboardRemove()

choice = types.ReplyKeyboardMarkup(resize_keyboard=True)
choice_btnd = types.KeyboardButton("Удалить заметку")
back_bttn = types.KeyboardButton("Назад⬅")
read_btn = types.KeyboardButton("Читать заметки")
choice_btny = types.KeyboardButton("Добавить заметку")
choice.add(back_bttn, choice_btnd, read_btn, choice_btny)

back_to_choice = types.ReplyKeyboardMarkup()
back_btn = types.KeyboardButton("К заметкам")
back_to_choice.add(back_btn)


def generator(names, mode):
    tmp_kb = types.InlineKeyboardMarkup(row_width=1)
    for row in names:
        btn = types.InlineKeyboardButton(text=row[0], callback_data=f"{mode}{row[0]}")
        tmp_kb.add(btn)
    return tmp_kb


class States(StatesGroup):
    blok_name = State()
    blok = State()


class Base:
    def __init__(self, file):
        self.conn = sqlite3.connect(file)
        self.cur = self.conn.cursor()

    def add_user_to_base(self, id, username):
        with self.conn:
            return self.cur.execute("INSERT INTO users (tgid, username) VALUES (?, ?)",
                                    (id, username))

    def user_have(self, id):
        with self.conn:
            result = self.cur.execute("SELECT * FROM users WHERE tgid = ?",
                                      (id,)).fetchall()
            return result

    def get_photo(self, id):
        with self.conn:
            result = self.cur.execute("SELECT photo FROM users WHERE tgid = ?",
                                      (id,)).fetchall()
            for row in result:
                photo = row[0]
            return photo

    def set_photo(self, id, photo):
        with self.conn:
            return self.cur.execute("UPDATE users SET photo = ? WHERE tgid = ?",
                                    (photo, id))

    def add_to_blok(self, id, name):
        with self.conn:
            return self.cur.execute("INSERT INTO blok (tgid, name) VALUES (?, ?)",
                                    (id, name))

    def add_text(self, name, text):
        with self.conn:
            return self.cur.execute("UPDATE blok SET text = ? WHERE name = ?",
                                    (text, name))

    def add_time(self, name, time):
        with self.conn:
            return self.cur.execute("UPDATE blok SET time = ? WHERE name = ?",
                                    (time, name))

    def delete(self, name):
        with self.conn:
            return self.cur.execute("DELETE FROM blok WHERE name = ?",
                                    (name,))

    def get_info(self, name):
        with self.conn:
            result = self.cur.execute("SELECT * FROM blok WHERE name = ?",
                                      (name,)).fetchall()
            return result[0]

    def get_blok(self, id):
        with self.conn:
            result = self.cur.execute("SELECT * FROM blok WHERE tgid = ?",
                                      (id,)).fetchall()
            info = []
            for row in result:
                info.append([row[4], row[2], row[3]])
            return info


database = Base("reminder.db")


@dp.message_handler(commands=["start"])
async def hello(message: types.Message):
    id = message.from_user.id

    if not bool(len(database.user_have(id))):
        await bot.send_message(id,
                               text="Добро пожаловать, я твой блокнот!",
                               reply_markup=menu)
        database.add_user_to_base(id, message.from_user.username)
    else:
        await bot.send_message(id,
                               text="Вы меня перезагрузили",
                               reply_markup=menu)


@dp.message_handler(text=["Мой профиль👤"])
async def profile(message: types.Message):
    id = message.from_user.id

    if database.get_photo(id):
        await bot.send_photo(id,
                             database.get_photo(id),
                             reply_markup=prof)
    else:
        await bot.send_message(id,
                               text="У вас нет фото",
                               reply_markup=prof)

    blok = len(database.get_blok(id))
    morph = pymorphy3.MorphAnalyzer()
    bloks = morph.parse("заметка")[0]
    much = bloks.make_agree_with_number(blok).word
    await bot.send_message(id,
                           text=f"У вас - {blok} {much}")


@dp.message_handler(text=["Фото📷"])
async def photo(message: types.Message):
    id = message.from_user.id
    await bot.send_message(chat_id=id,
                           text="Отправьте ваше фото (используйте функцию сжать фото)",
                           reply_markup=remove)


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def process_photo(message: types.Message):
    photo = message.photo[-1]
    id = message.from_user.id

    await bot.send_message(id,
                           text="Ваше фото загружено",
                           reply_markup=prof)
    database.set_photo(id, photo.file_id)


@dp.message_handler(text=["Назад⬅"])
async def back(message: types.Message):
    id = message.from_user.id
    await bot.send_message(id,
                           text="Вы вернулись назад",
                           reply_markup=menu)


@dp.message_handler(text=["Мои заметки📄"])
async def blok(message: types.Message):
    id = message.from_user.id
    await bot.send_message(id,
                           text="Выберите действие:",
                           reply_markup=choice)


@dp.message_handler(text=["Читать заметки"])
async def read(message: types.Message):
    id = message.from_user.id
    blok = database.get_blok(id)

    if blok:
        kb = generator(blok, "read")
        await bot.send_message(id,
                               text="Выберите заметку",
                               reply_markup=kb)
    else:
        await bot.send_message(id,
                               text="У вас нет заметок")


@dp.callback_query_handler(lambda message: message.data[:4] == "read")
async def read_blok(callback: types.CallbackQuery):
    id = callback.from_user.id
    name = callback.data[4:]
    blok = database.get_info(name)
    text = f"Название - {blok[4]}\nДата - {blok[3]}\n\n{blok[2]}"
    await bot.send_message(id,
                           text=text)


@dp.message_handler(text=["Добавить заметку"])
async def add(message: types.Message):
    id = message.from_user.id
    await States.blok_name.set()
    await bot.send_message(id,
                           text="Введите название заметки, длинна не более 10 символов",
                           reply_markup=remove)


@dp.message_handler(state=States.blok_name, content_types=types.ContentType.TEXT)
async def blok_name(message: types.Message, state: FSMContext):
    name = message.text
    id = message.from_user.id

    if len(name) <= 10:
        await state.finish()
        database.add_to_blok(id, name)
        async with state.proxy() as data:
            data['name'] = name
        await bot.send_message(id,
                               text="Введите текст заметки")
        await States.blok.set()

    else:
        await bot.send_message(id,
                               text="Название заметки не должно превышать 10 символов")


@dp.message_handler(state=States.blok, content_types=types.ContentType.TEXT)
async def blok_text(message: types.Message, state: FSMContext):
    id = message.from_user.id
    text = message.text
    time_blok = datetime.datetime.now()

    async with state.proxy() as data:
        database.add_text(data['name'], text)
        database.add_time(data['name'], time_blok)

    await bot.send_message(id,
                           text="Заметка добавлена",
                           reply_markup=choice)
    await state.finish()


@dp.message_handler(text=["Удалить заметку"])
async def delete(message: types.Message):
    id = message.from_user.id
    if not bool(database.get_blok(id)):
        await bot.send_message(id,
                               text="Вам нечего удалять")
    else:
        bloks = database.get_blok(id)

        gen = generator(bloks, "del")
        await bot.send_message(id,
                               text="Выберите что удалить",
                               reply_markup=gen)


@dp.callback_query_handler(lambda message: message.data[:3] == "del")
async def dele(callback: types.CallbackQuery):
    id = callback.from_user.id
    name = callback.data[3:]
    database.delete(name)

    await bot.delete_message(id,
                             message_id=callback.message.message_id)
    await bot.send_message(id,
                           text="Заметка удалена")


@dp.message_handler(text=["К заметка"])
async def back_to_choice(message: types.Message):
    id = message.from_user.id

    await bot.send_message(id,
                           text="Вы вернулись к заметкам",
                           reply_markup=choice)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
