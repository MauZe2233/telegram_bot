from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from handlers.menu import Menu
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import sqlite3
import time

router = Router()



class Request(StatesGroup):
    request_loc = State()
    request_info = State()
    request_photo = State()

@router.callback_query(Request.request_loc, lambda c: c.data)
async def process_callback_button1(callback_query: types.CallbackQuery, bot : Bot, state:FSMContext):
    await callback_query.message.delete()
    u_id = callback_query.from_user.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar(50), phone varchar(50), tg int(255), text varchar(1000), photo BLOB(1), status varchar(50), zone varchar(50))'
        )
    conn.commit()
    cur.close()
    conn.close()
    
    await bot.send_message(chat_id=u_id, text = "Подробно опишите проблему", reply_markup=types.ReplyKeyboardRemove())
    await state.update_data(zone=callback_query.data)
    await state.set_state(Request.request_info)



@router.message(Menu.menu, F.text.lower() == "оставить заявку")
async def ans2(message: types.Message, state:FSMContext, bot: Bot):
    
    inline_kb_full = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Гагаринский', callback_data='Гагаринский'),
            InlineKeyboardButton(text='Ленинский', callback_data='Ленинский')
        ]
    ])
    
    await message.reply("Выберите район", reply_markup=inline_kb_full)
    await state.set_state(Request.request_loc)


@router.message(Request.request_info, F.text)
async def info(message: types.Message, state: FSMContext):
    await state.update_data(request=message.text)
    await message.delete()

    await message.answer("Прикрепите фото проблемы")
    await state.set_state(Request.request_photo)

    
    
@router.message(Menu.menu, F.text.lower() == "мои заявки")
async def ans2(message: types.Message, state: FSMContext, bot: Bot):
    u_id = message.from_user.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM requests WHERE tg LIKE '%s'" % (u_id)
        )
    my_reqs = cur.fetchall()
    for el in my_reqs:
        info = f'{el[4]}\n{el[6]}'
        await bot.send_photo(chat_id=u_id, photo=el[5])
        await message.answer(info)
        time.sleep(0.5)

    cur.close()
    conn.close()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("Чтобы вернуться нажмите 'Главное меню'", reply_markup=keyboard)
    if(F.text == "Главное меню"):
        await state.set_state(Menu.wait)

@router.message(Request.request_photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):

    try:
        # Получаем фото с самым высоким разрешением (последний элемент в списке)
        photo = message.photo[-1]
        u_id = message.from_user.id
        # Скачиваем фото
        file = await message.bot.get_file(photo.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        await message.delete()
        
        
        # Можно сохранить file_id для дальнейшего использования
        photo_file_id = photo.file_id
        await state.update_data(photo_file_id=photo_file_id)
        
    except Exception as e:
        await message.answer(f"Ошибка обработки фото: {str(e)}")

    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    
    cur.execute(
        "SELECT * FROM users WHERE tg LIKE '%s'" % (u_id)
        )
    list = cur.fetchall()
    data = await state.get_data()
    for el in list:
        cur.execute(
            "INSERT INTO requests (name, phone, tg, text, photo, status, zone) VALUES ('%s', '%s' ,'%s', '%s', '%s', 'Ожидает рассмотрения', '%s')" % (el[1], el[2], el[3], data["request"], data["photo_file_id"], data["zone"])
        )
    
    
    conn.commit()

    cur.close()
    conn.close()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("Спасибо за оставленную заявку", reply_markup=keyboard)

    await state.set_state(Menu.wait)
