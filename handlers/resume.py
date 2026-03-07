from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from services.ai_service import ai_service
from keyboards import get_main_menu_keyboard

router = Router()


class ResumeStates(StatesGroup):
    waiting_for_job_description_for_generation = State()
    waiting_for_job_description_for_ats = State()


@router.callback_query(F.data == "my_resume")
async def cmd_my_resume(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await db.user_exists(user_id):
        await callback.message.edit_text("Please accept the agreement first using /start.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    profile = await db.get_profile(user_id)
    if not profile or not profile["resume_text"]:
        await callback.message.edit_text(
            "You don't have a resume text saved yet. Please update your profile in 'My Profile'.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return

    resume_text = profile["resume_text"]
    # Truncate if too long for Telegram message
    display_text = resume_text if len(resume_text) <= 3000 else resume_text[:3000] + "...\n(truncated)"

    await callback.message.edit_text(
        f"Your Current Resume:\n\n{display_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Generate Tailored Resume", callback_data="generate_tailored_resume")],
            [InlineKeyboardButton(text="🎯 Optimize for ATS", callback_data="optimize_ats")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "generate_tailored_resume")
async def generate_tailored_resume_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Please paste the job description for which you want to generate a tailored resume:")
    await state.set_state(ResumeStates.waiting_for_job_description_for_generation)
    await callback.answer()


@router.message(ResumeStates.waiting_for_job_description_for_generation)
async def process_job_description_for_generation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    job_description = message.text

    profile = await db.get_profile(user_id)
    if not profile:
        await message.answer("An error occurred while fetching your profile. Please try again later.")
        await state.clear()
        return

    await message.answer("⏳ Generating tailored resume...")
    job_for_ai = {"description": job_description, "title": "", "company": "", "location": ""}
    tailored_resume = await ai_service.generate_resume(profile, job_for_ai)

    display_text = tailored_resume if len(tailored_resume) <= 3500 else tailored_resume[:3500] + "...\n(truncated)"

    await message.answer(
        f"Tailored Resume:\n\n{display_text}",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "optimize_ats")
async def optimize_ats_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Please paste the job description for ATS optimization:")
    await state.set_state(ResumeStates.waiting_for_job_description_for_ats)
    await callback.answer()


@router.message(ResumeStates.waiting_for_job_description_for_ats)
async def process_job_description_for_ats(message: Message, state: FSMContext):
    user_id = message.from_user.id
    job_description = message.text

    profile = await db.get_profile(user_id)
    if not profile or not profile["resume_text"]:
        await message.answer("You don't have a resume text saved yet. Please update your profile first.")
        await state.clear()
        return

    await message.answer("⏳ Optimizing resume for ATS...")
    optimized_resume = await ai_service.optimize_for_ats(profile["resume_text"], job_description)

    display_text = optimized_resume if len(optimized_resume) <= 3500 else optimized_resume[:3500] + "...\n(truncated)"

    await message.answer(
        f"ATS Optimized Resume:\n\n{display_text}",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()
