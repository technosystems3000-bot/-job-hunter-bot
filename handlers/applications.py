from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import get_main_menu_keyboard, get_applications_keyboard, get_application_detail_keyboard, get_application_filter_keyboard
from database import db
from services.follow_up import FollowUpService
from datetime import datetime

router = Router()


class ApplicationStates(StatesGroup):
    VIEWING_APPLICATIONS = State()
    VIEWING_APPLICATION_DETAIL = State()
    UPDATING_STATUS = State()
    CONFIRM_WITHDRAW = State()
    SENDING_FOLLOW_UP = State()


@router.callback_query(F.data == "my_applications")
async def my_applications_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ApplicationStates.VIEWING_APPLICATIONS)
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("User not found. Please /start first.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    applications = await db.get_applications_by_user(user["id"])

    if not applications:
        await callback.message.edit_text(
            "You haven't submitted any applications yet.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return

    await display_applications(callback.message, applications, user["id"])
    await callback.answer()


async def display_applications(message, applications, user_id, filter_status=None):
    text = "Your Job Applications:\n\n"
    if filter_status:
        text = f"Your Job Applications (Status: {filter_status}):\n\n"

    for app in applications:
        company = app["company"]
        title = app["job_title"]
        status = app["status"]
        app_id = app["id"]
        text += f"• {company} - {title} (Status: {status})\n"

    await message.edit_text(
        text,
        reply_markup=get_applications_keyboard(applications, filter_status)
    )


@router.callback_query(F.data.startswith("filter_applications_"))
async def filter_applications_handler(callback: CallbackQuery, state: FSMContext):
    # Extract status after "filter_applications_"
    status_filter = callback.data[len("filter_applications_"):]
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("User not found.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    if status_filter == "all":
        applications = await db.get_applications_by_user(user["id"])
        await display_applications(callback.message, applications, user["id"])
    else:
        applications = await db.get_applications_by_user(user["id"], status=status_filter)
        await display_applications(callback.message, applications, user["id"], filter_status=status_filter)

    await callback.answer()


@router.callback_query(F.data.startswith("view_app_detail_"))
async def application_detail_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    application_id = int(parts[-1])
    await show_application_detail(callback.message, application_id, state)
    await callback.answer()


async def show_application_detail(message, application_id: int, state: FSMContext):
    application = await db.get_application_by_id(application_id)
    if not application:
        await message.edit_text("Application not found.", reply_markup=get_main_menu_keyboard())
        return

    await state.set_state(ApplicationStates.VIEWING_APPLICATION_DETAIL)
    await state.update_data(current_application_id=application_id)

    app_id = application["id"]
    company = application["company"]
    title = application["job_title"]
    status = application["status"]
    applied_at = datetime.fromisoformat(application["applied_at"]).strftime("%Y-%m-%d")
    follow_info = application["follow_up_info"]
    job_url = application["job_url"]

    text = f"Application Details (ID: {app_id})\n\n"
    text += f"Company: {company}\n"
    text += f"Position: {title}\n"
    text += f"Status: {status}\n"
    text += f"Applied On: {applied_at}\n"
    if follow_info:
        text += f"Follow-up Info: {follow_info}\n"
    text += f"Job URL: {job_url}\n"

    await message.edit_text(
        text,
        reply_markup=get_application_detail_keyboard(app_id, status)
    )


@router.callback_query(F.data.startswith("update_status_"))
async def update_status_prompt(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    application_id = int(parts[-1])
    await state.set_state(ApplicationStates.UPDATING_STATUS)
    await state.update_data(current_application_id=application_id)
    await callback.message.edit_text(
        "Select new status:",
        reply_markup=get_application_filter_keyboard(prefix="set_status")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_status_"), ApplicationStates.UPDATING_STATUS)
async def set_new_status(callback: CallbackQuery, state: FSMContext):
    new_status = callback.data[len("set_status_"):]
    data = await state.get_data()
    application_id = data["current_application_id"]

    await db.update_application(application_id, status=new_status)
    application = await db.get_application_by_id(application_id)

    if new_status == "Offer":
        company = application["company"]
        title = application["job_title"]
        await callback.message.edit_text(
            f"Congratulations on the offer from {company} for {title}!\n\n"
            "Remember, our agreement is a one monthly salary fee upon successful placement. We'll be in touch to finalize details.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        company = application["company"]
        title = application["job_title"]
        await callback.message.edit_text(
            f"Status for {company} - {title} updated to {new_status}.",
            reply_markup=get_application_detail_keyboard(application_id, new_status)
        )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_status_update")
async def cancel_status_update(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    application_id = data.get("current_application_id")
    if application_id:
        await show_application_detail(callback.message, application_id, state)
    else:
        await callback.message.edit_text("Cancelled.", reply_markup=get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("withdraw_app_"))
async def confirm_withdraw_application(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    application_id = int(parts[-1])
    await state.set_state(ApplicationStates.CONFIRM_WITHDRAW)
    await state.update_data(current_application_id=application_id)
    await callback.message.edit_text(
        "Are you sure you want to withdraw this application? This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Yes, Withdraw", callback_data=f"execute_withdraw_{application_id}")],
            [InlineKeyboardButton(text="No, Cancel", callback_data=f"view_app_detail_{application_id}")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("execute_withdraw_"), ApplicationStates.CONFIRM_WITHDRAW)
async def execute_withdraw_application(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    application_id = data["current_application_id"]
    application = await db.get_application_by_id(application_id)

    if application:
        company = application["company"]
        title = application["job_title"]
        await db.delete_application(application_id)
        await callback.message.edit_text(
            f"Application for {company} - {title} has been withdrawn.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text("Application not found.", reply_markup=get_main_menu_keyboard())

    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("send_follow_up_"))
async def send_follow_up_prompt(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    application_id = int(parts[-1])
    await state.set_state(ApplicationStates.SENDING_FOLLOW_UP)
    await state.update_data(current_application_id=application_id)

    follow_up_service = FollowUpService(db)
    user = await db.get_user(callback.from_user.id)
    application = await db.get_application_by_id(application_id)
    profile = await db.get_profile(callback.from_user.id)

    if not application or not user or not profile:
        await callback.message.edit_text("Error retrieving application or user data.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        await callback.answer()
        return

    # Generate follow-up message
    follow_up_message = await follow_up_service.generate_follow_up_message(profile, application)

    # Schedule next follow-up
    await follow_up_service.schedule_follow_up(application_id, days=3, message_text=follow_up_message, follow_up_number=1)

    await callback.message.edit_text(
        "Here is your personalized follow-up message. You can copy it and send it to the recruiter.\n\n"
        f"{follow_up_message}\n\n"
        "We've also scheduled the next follow-up for you.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Application", callback_data=f"view_app_detail_{application_id}")]
        ])
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "back_to_applications")
async def back_to_applications_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ApplicationStates.VIEWING_APPLICATIONS)
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("User not found.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return
    applications = await db.get_applications_by_user(user["id"])
    if not applications:
        await callback.message.edit_text("No applications found.", reply_markup=get_main_menu_keyboard())
    else:
        await display_applications(callback.message, applications, user["id"])
    await callback.answer()
