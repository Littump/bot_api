from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)
from dotenv import load_dotenv
import os
from FSMFillForm import FSMFillForm
import requests

load_dotenv()
TOKEN = os.getenv('TOKEN')
storage = MemoryStorage()
bot = Bot(TOKEN)
dp = Dispatcher(storage=storage)
user_dict: dict[int, dict[str, any]] = {}


@dp.message(CommandStart(), StateFilter(default_state))
async def start(message: Message):
    await message.anser(
        text=('Привет! Чтобы начать работу, введите '
              'команду /get_price')
    )


@dp.message(Command(commands='get_price'), StateFilter(default_state))
async def get_price(message: Message, state: FSMContext):
    await message.answer(
        text='Пожалуйста, введите адрес'
    )
    await state.set_state(FSMFillForm.address)


@dp.message(StateFilter(FSMFillForm.address))
async def address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
        ],
        [
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
        ],
        [
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        text='Выберите тип здания',
        reply_markup=markup,
    )
    await state.set_state(FSMFillForm.house_material)


@dp.callback_query(StateFilter(FSMFillForm.house_material),
                   F.data.in_([]))
async def house_material(callback: CallbackQuery, state: FSMFillForm):
    await state.update_data(house_material=callback.data)
    await callback.message.answer(
        text='Введите количество комнат'
    )
    await state.set_state(FSMFillForm.cnt_rooms)


@dp.message(StateFilter(FSMFillForm.cnt_rooms))
async def cnt_rooms(message: Message, state: FSMContext):
    await state.update_data(cnt_rooms=message.text)
    await message.answer(
        text='Введите номер этажа'
    )
    await state.set_state(FSMFillForm.floor)


@dp.message(StateFilter(FSMFillForm.floor))
async def floor(message: Message, state: FSMContext):
    await state.update_data(floor=message.text)
    await message.answer(
        text='Укажите площадь квартиры'
    )
    await state.set_state(FSMFillForm.area)

@dp.message(StateFilter(FSMFillForm.area))
async def area(message: Message, state: FSMContext):
    await state.update_data(area=message.text)
    ...
    await state.set_state(FSMFillForm.repair)


@dp.callback_query(StateFilter(FSMFillForm.repair),
                   F.data.in_([]))
async def repair(callback: CallbackQuery, state: FSMFillForm):
    await state.update_data(repair=callback.data)
    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text='Да',
                callback_data='1',
            ),
            InlineKeyboardButton(
                text='Нет',
                callback_data='0',
            ),
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(
        text='В доме есть лифт?',
        reply_markup=markup,
    )
    await state.set_state(FSMFillForm.has_lift)


@dp.callback_query(StateFilter(FSMFillForm.has_lift),
                   F.data.in_(['0', '1']))
async def has_lift(callback: CallbackQuery, state: FSMFillForm):
    await state.update_data(has_lift=callback.data)
    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
        ],
        [
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
        ],
        [
            InlineKeyboardButton(
                text='',
                callback_data='',
            ),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(
        text='Выберите тип парковки',
        reply_markup=markup,
    )
    await state.set_state(FSMFillForm.parking_type)


@dp.callback_query(StateFilter(FSMFillForm.parking_type),
                   F.data.in_([]))
async def parking_type(callback: CallbackQuery, state: FSMFillForm):
    await state.update_data(parking_type=callback.data)
    await callback.message.answer(
        text=('Напишите описнаие вашей квартиры. '
              'Чем подробнее напишите, тем точнее '
              'мы укажем реальную стоимость.')
    )
    await state.set_state(FSMFillForm.text)


@dp.message(StateFilter(FSMFillForm.text))
async def text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    await message.answer(
        text=('Ваши данные успещно получены. '
              'Через несколько секунд вы узнаете стоимость.')
    )
    await request(message.from_user.id)


async def request(user_id):
    url = 'http://localhost:8000/api/property/get_price/'
    data = user_dict[user_id]
    response = request.post(
        url=url,
        data=data
    )
    price = response['price']
    await bot.send_message(
        chat_id=user_id,
        text=(f'Реальная стоимость квартиры: {price}'
              f'Чтобы попробовать снова - введите /get_price')
    )


@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def cancel(message: Message, state: FSMContext):
    await message.answer(
        text=('Запрос отменен. Чтобы начать сначала, '
              'введите /get_price')
    )
    await state.clear()


if __name__ == '__main__':
    dp.run_polling(bot)