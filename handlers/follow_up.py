from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from services.follow_up import FollowUpService
from datetime import datetime
from keyboards import get_main_menu_keyboard

router = Router()


class FollowUpStates(StatesGroup):
    VIEWING_SCHEDULED_FOLLOW_UPS = State()
    VIEWING_FOLLOW_UP_MESSAGE = State()


@router.callback_query(F.data == "view_scheduled_follow_ups")
async def view_scheduled_follow_ups_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FollowUpStates.VIEWING_SCHEDULED_FOLLOW_UPS)
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.edit_text("User not found. Please /start first.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    applications = await db.get_applications_by_user(user["id"])

    if not applications:
        await callback.message.edit_text(
            "You have no applications to follow up on.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return

    text = "Your Scheduled Follow-ups:\n\n"
    has_follow_ups = False
    for app in applications:
        app_id = app["id"]
        company = app["company"]
        job_title = app["job_title"]
        follow_ups = await db.get_follow_ups_by_application(app_id)
        for fu in follow_ups:
            if not fu["sent"]:
                has_follow_ups = True
                fu_num = fu["follow_up_number"]
                fu_date = datetime.fromisoformat(fu["scheduled_date"]).strftime("%Y-%m-%d")
                fu_id = fu["id"]
                text += f"• {company} - {job_title} (Follow-up #{fu_num}) on {fu_date}\n"

    if not has_follow_ups:
        text = "You have no pending follow-ups."
        await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    else:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
            ])
        )
    await callback.answer()


@router.callback_query(F.data.startswith("view_follow_up_message_"))
async def follow_up_detail_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    follow_up_id = int(parts[-1])
    await show_follow_up_message(callback.message, follow_up_id, state)
    await callback.answer()


async def show_follow_up_message(message: Message, follow_up_id: int, state: FSMContext):
    follow_up = await db.get_follow_up_by_id(follow_up_id)
    if not follow_up:
        await message.edit_text("Follow-up not found.", reply_markup=get_main_menu_keyboard())
        return

    await state.set_state(FollowUpStates.VIEWING_FOLLOW_UP_MESSAGE)
    await state.update_data(current_follow_up_id=follow_up_id)

    fu_id = follow_up["id"]
    fu_date = datetime.fromisoformat(follow_up["scheduled_date"]).strftime("%Y-%m-%d")
    fu_text = follow_up["message_text"]

    text = f"Follow-up Message (ID: {fu_id})\n\n"
    text += f"Scheduled for: {fu_date}\n\n"
    text += f"{fu_text}\n"

    await message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Mark as Sent", callback_data=f"mark_follow_up_sent_{follow_up_id}")],
            [InlineKeyboardButton(text="⬅️ Back to Follow-ups", callback_data="view_scheduled_follow_ups")]
        ])
    )


@router.callback_query(F.data.startswith("mark_follow_up_sent_"))
async def mark_follow_up_sent(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    follow_up_id = int(parts[-1])
    await db.update_follow_up_status(follow_up_id, sent=True)
    follow_up = await db.get_follow_up_by_id(follow_up_id)
    if follow_up:
        application = await db.get_application_by_id(follow_up["application_id"])
        if application:
            current_info = application["follow_up_info"] if application["follow_up_info"] else ""
            fu_num = follow_up["follow_up_number"]
            new_info = f"Follow-up #{fu_num} sent on {datetime.now().strftime('%Y-%m-%d')}.\n"
            await db.update_application(follow_up["application_id"], follow_up_info=current_info + new_info)

    await callback.message.edit_text(
        "Follow-up marked as sent!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Follow-ups", callback_data="view_scheduled_follow_ups")]
        ])
    )
    await state.clear()
    await callback.answer()
