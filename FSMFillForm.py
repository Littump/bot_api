from aiogram.fsm.state import State, StatesGroup


class FSMFillForm(StatesGroup):
    address = State()
    house_material = State()
    object_type = State()
    cnt_rooms = State()
    floor = State()
    area = State()
    repair_photo = State()
    repair_button = State()
    has_lift = State()
    parking_type = State()
    text = State()
    object_type = State()
    floors = State()
