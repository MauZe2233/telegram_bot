from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.menu import Menu
import sqlite3
import re

router = Router()
global u_id
class Registration(StatesGroup):
    fio = State()
    phone = State()
    agreed = State()
    done = State()

#Начало
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    u_id = message.from_user.id

    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), phone varchar(50), tg int(255))'
    )
    conn.commit()
    cur.execute(
        "SELECT tg FROM users" 
    )
    tg = cur.fetchall()
    # Не работает праивльно логика проверки пользователя
    for el in tg:
        if (u_id == el[0]):
            await message.answer("Вы уже зарегистрированны!")
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="Главное меню")]
                ],
                resize_keyboard=True
            )
            await message.answer("Можете перейти к выбору опции - 'Главное меню'", reply_markup=keyboard)        
            await state.set_state(Menu.wait)
            return 0
        
    cur.close()
    conn.close()

    await message.answer('Привет, сейчас тебя зарегистрируем!')
    await message.answer('Введите ваше ФИО:')
    await state.set_state(Registration.fio)

#Начало регистрации
@router.message(Registration.fio)
async def get_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer("📱 Теперь отправьте ваш номер телефона (можно вручную или кнопкой).",
                         reply_markup=types.ReplyKeyboardMarkup(
                             keyboard=[[types.KeyboardButton(text="📲 Отправить мой номер", request_contact=True)]],
                             resize_keyboard=True
                         ))
    await state.set_state(Registration.phone)

@router.message(Registration.phone)
async def get_phone(message: types.Message, state: FSMContext):

    if message.contact:  
        phone = message.contact.phone_number
        result = re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone)
    else:
        phone = message.text
        result = re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone)

    if(not bool(result)):
        await message.answer("Телефон введен неверно! Попробуйте ещё раз")
        get_phone()
        return 0
       
    await state.update_data(phone=phone)

    await message.answer("Подтвердите согласие на обработку персональных данных (просто формальность)", 
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Согласен")]],
            resize_keyboard=True
        )
    )
    await state.set_state(Registration.agreed)

@router.message(Registration.agreed, F.text.lower() == "согласен")
async def agreed(message: types.Message, state: FSMContext):
    await state.update_data(tg_id = message.from_user.id)
    data = await state.get_data()
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (name, phone, tg) VALUES ('%s', '%s' ,'%s')" % (data["fio"], data["phone"], data["tg_id"])
        )
    conn.commit()
    cur.close()
    conn.close()
    await message.answer(
        f"✅ Регистрация завершена!\n\n👤 ФИО: {data['fio']}\n📱 Телефон: {data['phone']}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Главное меню")]
        ],
        resize_keyboard=True
    )
    await message.answer(f"Добро пожаловать, {data['fio']}! ", reply_markup=keyboard)
    await state.set_state(Registration.done)
    await state.set_state(Menu.wait)

    


