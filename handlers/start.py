from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from config import AGREEMENT_TEXT, WELCOME_MESSAGE, ACCEPT_BUTTON_TEXT
from database import db
from keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if not await db.user_exists(user_id):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text=ACCEPT_BUTTON_TEXT, callback_data="accept_agreement"))
        await message.answer(WELCOME_MESSAGE)
        await message.answer(AGREEMENT_TEXT, reply_markup=builder.as_markup())
    else:
        await message.answer("Welcome back! Use the menu below to navigate.", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "accept_agreement")
async def accept_agreement_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username
    full_name = callback.from_user.full_name
    await db.add_user(user_id, username, full_name)
    await callback.message.edit_text(
        "Thank you for accepting the agreement!\n\n"
        "Let's set up your profile. Send /profile to get started, or use the menu below.",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
