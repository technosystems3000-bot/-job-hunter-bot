from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import get_main_menu_keyboard

router = Router()


class ProfileStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_skills = State()
    waiting_for_experience = State()
    waiting_for_desired_roles = State()
    waiting_for_desired_locations = State()
    waiting_for_salary_range = State()
    waiting_for_education = State()
    waiting_for_languages = State()
    waiting_for_resume_text = State()


@router.message(F.text == "/profile")
async def cmd_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await db.user_exists(user_id):
        await message.answer("Please accept the agreement first using the /start command.")
        return

    profile = await db.get_profile(user_id)
    if not profile:
        await message.answer("An error occurred while loading your profile. Please try again later.")
        return

    await message.answer("Let's set up your profile. Enter your full name:")
    await state.set_state(ProfileStates.waiting_for_full_name)


@router.message(ProfileStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.update_profile(user_id, full_name=message.text)
    await message.answer("Great! Now enter your skills (comma separated, e.g., Python, SQL, Docker):")
    await state.set_state(ProfileStates.waiting_for_skills)


@router.message(ProfileStates.waiting_for_skills)
async def process_skills(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.update_profile(user_id, skills=message.text)
    await message.answer("How many years of experience do you have? (Enter a number):")
    await state.set_state(ProfileStates.waiting_for_experience)


@router.message(ProfileStates.waiting_for_experience)
async def process_experience(message: Message, state: FSMContext):
    try:
        experience = int(message.text)
        user_id = message.from_user.id
        await db.update_profile(user_id, experience_years=experience)
        await message.answer("What roles are you looking for? (Comma separated, e.g., Data Scientist, ML Engineer):")
        await state.set_state(ProfileStates.waiting_for_desired_roles)
    except ValueError:
        await message.answer("Please enter a numeric value for years of experience.")


@router.message(ProfileStates.waiting_for_desired_roles)
async def process_desired_roles(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.update_profile(user_id, desired_roles=message.text)
    await message.answer("In what locations are you looking for a job? (Comma separated, e.g., Remote, London, Berlin):")
    await state.set_state(ProfileStates.waiting_for_desired_locations)


@router.message(ProfileStates.waiting_for_desired_locations)
async def process_desired_locations(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.update_profile(user_id, desired_locations=message.text)
    await message.answer("Enter your desired salary range (e.g., 50000-70000 USD):")
    await state.set_state(ProfileStates.waiting_for_salary_range)


@router.message(ProfileStates.waiting_for_salary_range)
async def process_salary_range(message: Message, state: FSMContext):
    user_id = message.from_user.id
    salary_parts = message.text.split()
    salary_min = None
    salary_max = None
    salary_currency = None

    if len(salary_parts) >= 1:
        if '-' in salary_parts[0]:
            min_max = salary_parts[0].split('-')
            try:
                salary_min = int(min_max[0])
                salary_max = int(min_max[1])
            except ValueError:
                pass
        else:
            try:
                salary_min = int(salary_parts[0])
            except ValueError:
                pass
    if len(salary_parts) > 1:
        salary_currency = salary_parts[-1]

    await db.update_profile(user_id, salary_min=salary_min, salary_max=salary_max, salary_currency=salary_currency)
    await message.answer("What is your education? (e.g., Master's Degree, Bachelor of Computer Science):")
    await state.set_state(ProfileStates.waiting_for_education)


@router.message(ProfileStates.waiting_for_education)
async def process_education(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.update_profile(user_id, education=message.text)
    await message.answer("What languages do you know? (Comma separated, e.g., English (B2), German (A1)):")
    await state.set_state(ProfileStates.waiting_for_languages)


@router.message(ProfileStates.waiting_for_languages)
async def process_languages(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db.update_profile(user_id, languages=message.text)
    await message.answer("Paste your current resume text. If you don't have one, send \"-\".")
    await state.set_state(ProfileStates.waiting_for_resume_text)


@router.message(ProfileStates.waiting_for_resume_text)
async def process_resume_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    resume_text = None
    if message.text != "-":
        resume_text = message.text
    await db.update_profile(user_id, resume_text=resume_text)
    await message.answer("✅ Profile successfully updated!", reply_markup=get_main_menu_keyboard())
    await state.clear()
