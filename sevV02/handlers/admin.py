from aiogram import Router, types, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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
        await state.set_state(Admin.admin)
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Посмотреть пользователей")],
                [types.KeyboardButton(text="Все заявки")]
            ],
            resize_keyboard=True
        )
        await message.answer("Что на этот раз?", reply_markup=keyboard)

@router.message(Admin.admin, F.text.lower() == 'посмотреть пользователей')
async def show_users(message: types.Message):
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

@router.message(Admin.admin, F.text.lower() == 'все заявки')
async def show_requests(message: types.Message, bot: Bot, state:FSMContext):
    u_id = message.from_user.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("UPDATE requests SET status = ? WHERE status = ?", ("Просмотренно","Ожидает рассмотрения"))
    cur.execute(
        "SELECT * FROM requests" 
        )
    
    conn.commit()
    request = cur.fetchall()
    for el in request:
        info = f'район: {el[7]}\nФИО: {el[1]}\n Телефон: {el[2]}\n\n Заявка: №{el[0]}\n\n {el[4]}\n Статус заявки: {el[6]}'
        try:
            photo_message = await bot.send_photo(chat_id=u_id, photo=el[5])
        except Exception as e:
            photo_message = await bot.send_photo(chat_id=u_id, photo='https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Flag_of_the_New_People_%28political_party%29.svg/2560px-Flag_of_the_New_People_%28political_party%29.svg.png')
        
        photo_message_id = photo_message.message_id
        inline_kb_full = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Удалить', callback_data=f'delete_{el[0]}_{photo_message_id}'),
                InlineKeyboardButton(text='Изменить статус на "Решено"', callback_data=f'change_{el[0]}')
            ]
        ])
        await message.reply(info, reply_markup=inline_kb_full)  
                  
    conn.commit()
    cur.close()
    conn.close()

@router.callback_query(Admin.admin, F.data.startswith("delete_"))
async def delete_request(callback: types.CallbackQuery, bot: Bot):
    request_id = callback.data.split("_")[1]
    photo_id = callback.data.split("_")[2]
    with sqlite3.connect('database.sql') as conn:
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()
        cur.execute("DELETE FROM requests WHERE id = ?", (request_id,))
        conn.commit()
    await callback.answer(f"Заявка № {request_id} удалена!", show_alert=True)
    await callback.message.delete()
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=int(photo_id))
    
    

@router.callback_query(Admin.admin, F.data.startswith("change_"))
async def change_request(callback: types.CallbackQuery):
    request_id = callback.data.split("_")[1]
    with sqlite3.connect('database.sql') as conn:
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()
        cur.execute("UPDATE requests SET status = ? WHERE id = ?", ("Решено", request_id))
        conn.commit()
    await callback.answer("Статус изменен на 'Решено'", show_alert=True)


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