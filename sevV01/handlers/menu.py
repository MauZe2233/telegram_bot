from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


router = Router()

class Menu(StatesGroup):
    wait = State()
    menu = State()

@router.message(F.text.lower() == 'главное меню')
async def menu(message: types.Message, state: FSMContext):
    await message.delete()
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Профиль")],
            [types.KeyboardButton(text="Оставить заявку")],
            [types.KeyboardButton(text="Мои заявки")],
            [types.KeyboardButton(text="Карта обращений")]
        ],
        resize_keyboard=True
    )
    await state.set_state(Menu.menu)
    await message.answer("📋 Выбереите подходящую опцию", reply_markup=keyboard)


@router.message(Menu.menu, F.text.lower() == "карта обращений")
async def ans3(message: types.Message, state: FSMContext):
    await state.set_state(Menu.map)
    await message.answer("Мы работаем над этим))))", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Menu.wait)
    