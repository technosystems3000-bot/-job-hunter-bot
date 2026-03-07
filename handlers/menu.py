from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import get_main_menu_keyboard

router = Router()

MENU_TEXT = "🏠 Main Menu\n\nChoose an option below:"


@router.message(Command("menu"))
async def show_main_menu_command(message: Message, state: FSMContext):
    await state.clear()  # Clear any active state so user can start fresh
    await message.answer(MENU_TEXT, reply_markup=get_main_menu_keyboard())


@router.message(Command("search"))
async def search_shortcut(message: Message, state: FSMContext):
    """Quick shortcut to start job search."""
    await state.clear()
    from handlers.jobs import JobSearchStates
    await message.answer("Please enter keywords for job search (e.g., 'Python developer', 'Data Scientist'):")
    await state.set_state(JobSearchStates.waiting_for_keywords)


@router.callback_query(F.data == "main_menu")
async def show_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # Clear any active state
    await callback.message.edit_text(MENU_TEXT, reply_markup=get_main_menu_keyboard())
    await callback.answer()
