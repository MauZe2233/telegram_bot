from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from handlers.menu import Menu
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile
import sqlite3
router = Router()



class Request(StatesGroup):
    request_info = State()
    request_photo = State()

@router.message(Menu.menu, F.text.lower() == "оставить заявку")
async def ans1(message: types.Message, state: FSMContext):
    await message.answer("Подробно опишите проблему", reply_markup=types.ReplyKeyboardRemove())
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar(50), phone varchar(50), tg int(255), text varchar(1000), photo BLOB(1))'
        )
    conn.commit()
    cur.close()
    conn.close()
    await state.set_state(Request.request_info)

@router.message(Request.request_info, F.text)
async def info(message: types.Message, state: FSMContext):
    global request 
    request = message.text
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
        info = f'{el[4]}\n'
        await bot.send_photo(chat_id=u_id, photo=el[5])
        await message.answer(info)

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
    
    for el in list:
        cur.execute(
            "INSERT INTO requests (name, phone, tg, text, photo) VALUES ('%s', '%s' ,'%s', '%s', '%s')" % (el[1], el[2], el[3], request, photo_file_id)
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
