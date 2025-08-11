from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import sqlite3
from aiogram.fsm.state import State, StatesGroup


router = Router()

admins = [1307231822, 1122341470,6943220622]

class Admin(StatesGroup):
    admin = State()
    user = State()
    waiting_for_request_id = State()

@router.message(Command('admin'))
async def menu(message: types.Message, state: FSMContext):
    global u_id
    u_id = message.from_user.id
    if (u_id in admins):
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Посмотреть пользователей")],
                [types.KeyboardButton(text="Все заявки")],
                [types.KeyboardButton(text="Удалить заявку")]
            ],
            resize_keyboard=True
        )
        await message.answer("Что на этот раз?", reply_markup=keyboard)

@router.message(F.text.lower() == 'посмотреть пользователей')
async def show_users(message: types.Message):
    u_id = message.from_user.id
    if (u_id in admins):
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users" 
            )
        users = cur.fetchall()
        info = '' 
        for el in users:
            info += f'ФИО: {el[1]}, Телефон: {el[2]}, tg: {el[3]}\n'

        cur.close()
        conn.close()

        await message.answer(info)
    else:
        await message.answer("Недостаточно прав")

@router.message(F.text.lower() == 'все заявки')
async def show_requests(message: types.Message, bot: Bot):
    u_id = message.from_user.id
    if (u_id in admins):
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM requests" 
            )
        request = cur.fetchall()
        for el in request:
            info = f'район: {el[7]}\nФИО: {el[1]}, Телефон: {el[2]}, телеграмм id: {el[3]}, заявка: №{el[0]} {el[4]}\n'
            await bot.send_photo(chat_id=u_id, photo=el[5])
            await message.answer(info)
        cur.close()
        conn.close()
    else:
        await message.answer("Недостаточно прав")
    return 0

@router.message(F.text.lower() == 'удалить заявку')
async def start_delete_request(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in admins:
        await message.answer("Недостаточно прав")
        return
    
    await message.answer("Введите номер заявки для удаления:")
    await state.set_state(Admin.waiting_for_request_id)

@router.message(Admin.waiting_for_request_id)
async def process_request_id(message: types.Message, state: FSMContext):
    try:
        request_id = int(message.text)  # Преобразуем введенный текст в число
        
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()
        
        # Безопасный запрос с параметрами
        cur.execute("DELETE FROM requests WHERE id = ?", (request_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            await message.answer(f"Заявка #{request_id} успешно удалена")
        else:
            await message.answer("Заявка с таким ID не найдена")
            
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер заявки (только цифры)")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        await state.clear()
        if 'conn' in locals():
            conn.close()