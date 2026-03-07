from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import get_main_menu_keyboard

router = Router()


class SettingsStates(StatesGroup):
    editing_full_name = State()
    editing_skills = State()
    editing_experience = State()
    editing_desired_roles = State()
    editing_desired_locations = State()
    editing_salary_range = State()
    editing_education = State()
    editing_languages = State()
    editing_resume_text = State()
    confirm_delete_account = State()


def get_settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Edit Full Name", callback_data="edit_full_name")],
        [InlineKeyboardButton(text="🛠 Edit Skills", callback_data="edit_skills")],
        [InlineKeyboardButton(text="📅 Edit Experience", callback_data="edit_experience")],
        [InlineKeyboardButton(text="🎯 Edit Desired Roles", callback_data="edit_desired_roles")],
        [InlineKeyboardButton(text="📍 Edit Desired Locations", callback_data="edit_desired_locations")],
        [InlineKeyboardButton(text="💰 Edit Salary Range", callback_data="edit_salary_range")],
        [InlineKeyboardButton(text="🎓 Edit Education", callback_data="edit_education")],
        [InlineKeyboardButton(text="🌐 Edit Languages", callback_data="edit_languages")],
        [InlineKeyboardButton(text="📝 Edit Resume Text", callback_data="edit_resume_text")],
        [InlineKeyboardButton(text="🗑 Delete Account", callback_data="delete_account")],
        [
            InlineKeyboardButton(text="ℹ️ Help", callback_data="help"),
            InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"),
        ],
    ])


def get_edit_cancel_keyboard():
    """Keyboard shown during editing — user can cancel."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="my_profile")],
    ])


@router.callback_query(F.data == "settings")
async def settings_redirect(callback: CallbackQuery, state: FSMContext):
    """Settings button redirects to profile view with edit options."""
    await state.clear()
    # Reuse the my_profile handler
    user_id = callback.from_user.id
    profile = await db.get_profile(user_id)

    if not profile:
        await callback.message.edit_text(
            "Profile not found. Please set up your profile first using /start.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return

    text = build_profile_text(profile)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback.answer()


@router.callback_query(F.data == "my_profile")
async def show_profile_settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    profile = await db.get_profile(user_id)

    if not profile:
        await callback.message.edit_text(
            "Profile not found. Please set up your profile first using /start.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return

    text = build_profile_text(profile)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback.answer()


def build_profile_text(profile):
    text = "👤 Your Profile\n\n"
    text += f"Name: {profile['full_name'] or 'Not set'}\n"
    text += f"Skills: {profile['skills'] or 'Not set'}\n"
    text += f"Experience: {profile['experience_years'] or 'Not set'} years\n"
    text += f"Desired Roles: {profile['desired_roles'] or 'Not set'}\n"
    text += f"Desired Locations: {profile['desired_locations'] or 'Not set'}\n"
    salary = ""
    if profile['salary_min'] and profile['salary_max']:
        salary = f"{profile['salary_min']}-{profile['salary_max']} {profile['salary_currency'] or ''}"
    elif profile['salary_min']:
        salary = f"{profile['salary_min']}+ {profile['salary_currency'] or ''}"
    text += f"Salary Range: {salary or 'Not set'}\n"
    text += f"Education: {profile['education'] or 'Not set'}\n"
    text += f"Languages: {profile['languages'] or 'Not set'}\n"
    text += f"Resume: {'Saved' if profile['resume_text'] else 'Not set'}\n"
    return text


# --- Edit handlers ---

@router.callback_query(F.data == "edit_full_name")
async def edit_full_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your new full name:", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_full_name)
    await callback.answer()


@router.message(SettingsStates.editing_full_name)
async def save_full_name(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, full_name=message.text)
    await message.answer("✅ Full name updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_skills")
async def edit_skills(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your skills (comma separated, e.g., Python, SQL, Docker):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_skills)
    await callback.answer()


@router.message(SettingsStates.editing_skills)
async def save_skills(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, skills=message.text)
    await message.answer("✅ Skills updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_experience")
async def edit_experience(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your years of experience (number):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_experience)
    await callback.answer()


@router.message(SettingsStates.editing_experience)
async def save_experience(message: Message, state: FSMContext):
    try:
        exp = int(message.text)
        await db.update_profile(message.from_user.id, experience_years=exp)
        await message.answer("✅ Experience updated!", reply_markup=get_settings_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("Please enter a valid number.", reply_markup=get_edit_cancel_keyboard())


@router.callback_query(F.data == "edit_desired_roles")
async def edit_desired_roles(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your desired roles (comma separated, e.g., Data Scientist, ML Engineer):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_desired_roles)
    await callback.answer()


@router.message(SettingsStates.editing_desired_roles)
async def save_desired_roles(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, desired_roles=message.text)
    await message.answer("✅ Desired roles updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_desired_locations")
async def edit_desired_locations(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your desired locations (comma separated, e.g., Remote, London, Berlin):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_desired_locations)
    await callback.answer()


@router.message(SettingsStates.editing_desired_locations)
async def save_desired_locations(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, desired_locations=message.text)
    await message.answer("✅ Desired locations updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_salary_range")
async def edit_salary_range(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your desired salary range (e.g., 50000-70000 USD):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_salary_range)
    await callback.answer()


@router.message(SettingsStates.editing_salary_range)
async def save_salary_range(message: Message, state: FSMContext):
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

    await db.update_profile(
        message.from_user.id,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency
    )
    await message.answer("✅ Salary range updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_education")
async def edit_education(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your education (e.g., Master's Degree in Computer Science):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_education)
    await callback.answer()


@router.message(SettingsStates.editing_education)
async def save_education(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, education=message.text)
    await message.answer("✅ Education updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_languages")
async def edit_languages(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your languages (comma separated, e.g., English (C1), German (B2)):", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_languages)
    await callback.answer()


@router.message(SettingsStates.editing_languages)
async def save_languages(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, languages=message.text)
    await message.answer("✅ Languages updated!", reply_markup=get_settings_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_resume_text")
async def edit_resume_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Paste your updated resume text:", reply_markup=get_edit_cancel_keyboard())
    await state.set_state(SettingsStates.editing_resume_text)
    await callback.answer()


@router.message(SettingsStates.editing_resume_text)
async def save_resume_text(message: Message, state: FSMContext):
    await db.update_profile(message.from_user.id, resume_text=message.text)
    await message.answer("✅ Resume text updated!", reply_markup=get_settings_keyboard())
    await state.clear()


# --- Delete Account ---

@router.callback_query(F.data == "delete_account")
async def delete_account_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.confirm_delete_account)
    await callback.message.edit_text(
        "⚠️ Are you sure you want to delete your account?\n\n"
        "This will remove all your data including profile, applications, and follow-ups. "
        "This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Yes, Delete My Account", callback_data="confirm_delete_yes")],
            [InlineKeyboardButton(text="❌ No, Cancel", callback_data="my_profile")],
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_delete_yes", SettingsStates.confirm_delete_account)
async def confirm_delete_account(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if user:
        await db.delete_user(user_id)
    await callback.message.edit_text(
        "Your account has been deleted. If you want to use the bot again, send /start."
    )
    await state.clear()
    await callback.answer()
