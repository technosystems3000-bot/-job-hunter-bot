from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from services.referral import ReferralService
from keyboards import get_main_menu_keyboard

router = Router()
referral_service = ReferralService()


class ReferralStates(StatesGroup):
    waiting_for_company = State()
    waiting_for_contact_name = State()


@router.callback_query(F.data == "find_referrals")
async def find_referrals_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await db.user_exists(user_id):
        await callback.message.edit_text("Please accept the agreement first using /start.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    await callback.message.edit_text(
        "Enter the company name where you'd like to find referrals:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu")]
        ])
    )
    await state.set_state(ReferralStates.waiting_for_company)
    await callback.answer()


@router.message(ReferralStates.waiting_for_company)
async def process_company_for_referral(message: Message, state: FSMContext):
    company = message.text
    user_id = message.from_user.id
    profile = await db.get_profile(user_id)

    if not profile:
        await message.answer("Please set up your profile first.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    await state.update_data(referral_company=company)
    await message.answer("⏳ Finding referral strategies...")

    advice = await referral_service.find_potential_referrals(company, profile)

    await message.answer(
        f"Referral Strategies for {company}:\n\n{advice}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Generate Referral Request", callback_data="generate_referral_request")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
        ])
    )
    await state.clear()
    await state.update_data(referral_company=company)


@router.callback_query(F.data == "generate_referral_request")
async def generate_referral_request_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter the name of the person you'd like to request a referral from:")
    await state.set_state(ReferralStates.waiting_for_contact_name)
    await callback.answer()


@router.message(ReferralStates.waiting_for_contact_name)
async def process_contact_name(message: Message, state: FSMContext):
    contact_name = message.text
    user_id = message.from_user.id
    data = await state.get_data()
    company = data.get("referral_company", "the company")

    profile = await db.get_profile(user_id)
    if not profile:
        await message.answer("Please set up your profile first.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    await message.answer("⏳ Generating referral request message...")

    referral_message = await referral_service.generate_referral_request(profile, company, contact_name)

    await message.answer(
        f"Referral Request for {contact_name} at {company}:\n\n{referral_message}",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()
