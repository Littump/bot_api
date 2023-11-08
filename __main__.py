from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from FSMFillForm import FSMFillForm
import io
from PIL import Image
import requests

TOKEN = '6958394463:AAGdb7GJy7bJsGqNkOn8v0-8hoiU9DnlWAA'
storage = MemoryStorage()
bot = Bot(TOKEN)
dp = Dispatcher(storage=storage)
user_dict: dict[int, dict[str, any]] = {}


@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def cancel(message: Message, state: FSMContext):
    await message.answer(
        text=('Запрос отменен. Чтобы начать сначала, '
              'введите /get_price')
    )
    await state.clear()


@dp.message(Command(commands='clear'), StateFilter(default_state))
async def clear(message: Message, state: FSMContext):
    await state.clear()


@dp.message(CommandStart(), StateFilter(default_state))
async def start(message: Message):
    await message.answer(
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
                text='Кирпичный',
                callback_data='brc',
            ),
            InlineKeyboardButton(
                text='Монолитный',
                callback_data='mnl',
            ),
        ],
        [
            InlineKeyboardButton(
                text='Панельный',
                callback_data='pnl',
            ),
            InlineKeyboardButton(
                text='Блочный',
                callback_data='blc',
            ),
        ],
        [
            InlineKeyboardButton(
                text='Деревянный',
                callback_data='wdn',
            ),
            InlineKeyboardButton(
                text='Сталинский',
                callback_data='stl',
            ),
        ],
        [
            InlineKeyboardButton(
                text='Кирпично-монолитный',
                callback_data='brm',
            ),
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        text='Выберите тип здания',
        reply_markup=markup,
    )
    await state.set_state(FSMFillForm.house_material)


@dp.callback_query(StateFilter(FSMFillForm.house_material),
                   F.data.in_(['brc', 'mnl', 'pnl', 'blc',
                               'wdn', 'stl', 'brm']))
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
        text='Введите количество этажей в доме'
    )
    await state.set_state(FSMFillForm.floors)


@dp.message(StateFilter(FSMFillForm.floors))
async def floors(message: Message, state: FSMContext):
    await state.update_data(floors=message.text)
    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text='первичка',
                callback_data='1_1',
            ),
            InlineKeyboardButton(
                text='вторичка',
                callback_data='2_2',
            ),
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        text=('Выбрать тип недвижимости'),
        reply_markup=markup
    )
    await state.set_state(FSMFillForm.object_type)


@dp.callback_query(StateFilter(FSMFillForm.object_type),
                   F.data.in_(['1_1', "2_2"]))
async def object_type(callback: CallbackQuery, state: FSMFillForm):
    transform_123 = {'1_1': "1", "2_2": '2'}
    await state.update_data(object_type=transform_123[callback.data])
    await callback.message.answer(
        text=('Введите площадь квартиры'),
    )
    await state.set_state(FSMFillForm.area)


@dp.message(StateFilter(FSMFillForm.area))
async def area(message: Message, state: FSMContext):
    await state.update_data(area=message.text)
    keyboard: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text='Выбрать ремонт при помощи клавиатуры',
                callback_data='repair_button',
            ),
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        text=('В нашей модели встроена оценка ремонта квартиры '
              'по фотографиям. Чтобы ей воспользоваться, вы можете '
              'прислать нам в следующем сообщении фотографии своей '
              'квартиры.\n\nВажно: присылать фотографии нужно одним '
              'сообщением!\n\nЕсли вы не хотите присылать фотографии, то '
              'можете выбрать свой ремонт при помощи клавиатуры'),
        reply_markup=markup,
    )
    await state.set_state(FSMFillForm.repair_photo)


@dp.message(StateFilter(FSMFillForm.repair_photo))
async def repair_photo(message: Message, state: FSMContext):
    try:
        photos = message.photo
        photo = photos[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path

        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

        response = requests.get(file_url)

        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            bytes = io.BytesIO()
            image.save(bytes, format='PNG')
            await state.update_data(photos=("photo.jpeg",
                                            bytes.getvalue(), 'image/jpeg'))
        else:
            await state.update_data(photos=())

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
        await message.answer(
            text='В доме есть лифт?',
            reply_markup=markup,
        )
        await state.update_data(asked_lift=True)
        await state.set_state(FSMFillForm.has_lift)
    except Exception:
        await message.answer(
            text='Не удалось обработать изображение, повторите попытку'
        )
        await state.clear()


@dp.callback_query(StateFilter(FSMFillForm.repair_photo),
                   F.data.in_(['repair_button']))
async def repair_text(callback: CallbackQuery, state: FSMFillForm):
    keyboard: list[InlineKeyboardButton] = [
        [InlineKeyboardButton(
            text='Черновая отделка без ремонта',
            callback_data='0;0',
        )],
        [InlineKeyboardButton(
            text='Средняя отделка без ремонта',
            callback_data='1;0',
        )],
        [InlineKeyboardButton(
            text='Предчистовая отделка без ремонта',
            callback_data='2;0',
        )],
        [InlineKeyboardButton(
            text='Старый ремонт без мебели',
            callback_data='0;1',
        )],
        [InlineKeyboardButton(
            text='Косметический ремонт без мебели',
            callback_data='1;1',
        )],
        [InlineKeyboardButton(
            text='Евроремонт ремонт без мебели',
            callback_data='2;1',
        )],
        [InlineKeyboardButton(
            text='Дизайнерский ремонт без мебели',
            callback_data='3;1',
        )],
        [InlineKeyboardButton(
            text='Старый ремонт с мебелью',
            callback_data='0;2',
        )],
        [InlineKeyboardButton(
            text='Косметический ремонт с мебелью',
            callback_data='1;2',
        )],
        [InlineKeyboardButton(
            text='Евроремонт ремонт с мебелью',
            callback_data='2;2',
        )],
        [InlineKeyboardButton(
            text='Дизайнерский ремонт с мебелью',
            callback_data='3;2',
        )],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(
        text=('Выберите тип ремонта'),
        reply_markup=markup,
    )
    await state.set_state(FSMFillForm.repair_button)


@dp.callback_query(StateFilter(FSMFillForm.repair_button),
                   F.data.in_(['0;0', '1;0', '2;0', '0;1', '1;1', '2;1', '3;1',
                               '0;2', '1;2', '2;2', '3;2']))
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
                text='парковка на крыше',
                callback_data='orf',
            ),
            InlineKeyboardButton(
                text='наземная парковка',
                callback_data='grn',
            ),
        ],
        [
            InlineKeyboardButton(
                text='подземная парковка',
                callback_data='und',
            ),
            InlineKeyboardButton(
                text='многоуровневая парковка',
                callback_data='mlt',
            ),
        ],
        [
            InlineKeyboardButton(
                text='нет парковки',
                callback_data='0',
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
                   F.data.in_(['0', 'mlt', 'und', 'grn', 'orf']))
async def parking_type(callback: CallbackQuery, state: FSMFillForm):
    await state.update_data(parking_type=callback.data)
    await callback.message.answer(
        text=('Напишите описание вашей квартиры. '
              'Чем подробнее напишите, тем точнее '
              'мы укажем реальную стоимость.')
    )
    await state.set_state(FSMFillForm.text)


@dp.message(StateFilter(FSMFillForm.text))
async def text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    await message.answer(
        text=('Ваши данные успешно получены.\n'
              'Через несколько секунд вы узнаете стоимость.')
    )
    try:
        await request(message.from_user.id)
    except Exception:
        await message.answer(
            text=('Ошибка ввода\n'
                  'Повторите попытку')
        )
    await state.clear()


def get_repair(pil_array, user_id):
    url = 'https://estate-valuation.tech/api/property/calculate_repair/'
    data = user_dict[user_id]
    a = {}
    a['photos'] = data['photos']
    response = requests.post(
        url=url,
        files=a
    )
    return response.json()['repair']


async def request(user_id):
    url = 'https://estate-valuation.tech/api/property/get_price/'
    data = user_dict[user_id]
    data['repair'] = get_repair(data, user_id)
    data.pop('photos', None)
    response = requests.post(
        url=url,
        data=data
    )
    price = round(response.json()['price'])
    price = '{:,.0f}'.format(price).replace(',', ' ')
    await bot.send_message(
        chat_id=user_id,
        text=(f'Реальная стоимость квартиры: {price}\n\n'
              f'Чтобы попробовать снова - введите /get_price')
    )


if __name__ == '__main__':
    dp.run_polling(bot)
