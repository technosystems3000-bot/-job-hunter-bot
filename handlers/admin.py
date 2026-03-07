from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_TELEGRAM_ID
from database import db
from keyboards import get_admin_menu_keyboard, get_main_menu_keyboard

router = Router()


def is_admin(telegram_id: int) -> bool:
    return telegram_id == ADMIN_TELEGRAM_ID


class AdminStates(StatesGroup):
    waiting_broadcast_message = State()
    waiting_user_id_lookup = State()


@router.message(Command("admin"))
async def admin_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("You don't have admin access.")
        return
    await message.answer(
        "Admin Panel\n\nSelect an option below:",
        reply_markup=get_admin_menu_keyboard()
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    await callback.message.edit_text(
        "Admin Panel\n\nSelect an option below:",
        reply_markup=get_admin_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    stats = await db.get_stats()
    text = (
        "Dashboard Statistics\n\n"
        f"Total Users: {stats['total_users']}\n"
        f"Total Applications: {stats['total_applications']}\n"
        f"Total Jobs in DB: {stats['total_jobs']}\n"
        f"Interviews Scheduled: {stats['total_interviews']}\n"
        f"Offers Received: {stats['total_offers']}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    users = await db.get_all_users()
    if not users:
        await callback.message.edit_text(
            "No users registered yet.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
            ])
        )
        await callback.answer()
        return

    text = f"All Users ({len(users)} total)\n\n"
    keyboard_rows = []
    for u in users[:20]:  # Show max 20
        name = u["profile_name"] or u["full_name"] or u["username"] or "Unknown"
        tg_id = u["telegram_id"]
        skills = u["skills"] or "No skills"
        text += f"• {name} (@{u['username'] or 'N/A'}) — {skills[:40]}\n"
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"👤 {name}",
                callback_data=f"admin_view_user_{tg_id}"
            )
        ])

    keyboard_rows.append([InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")])
    keyboard_rows.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")])

    await callback.message.edit_text(
        text[:4000],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_user_"))
async def admin_view_user(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    tg_id = int(callback.data.split("_")[-1])
    user = await db.get_user_detail_admin(tg_id)

    if not user:
        await callback.message.edit_text("User not found.")
        await callback.answer()
        return

    text = (
        f"User Detail\n\n"
        f"Telegram ID: {user['telegram_id']}\n"
        f"Username: @{user.get('username') or 'N/A'}\n"
        f"Name: {user.get('profile_name') or user.get('full_name') or 'N/A'}\n"
        f"Skills: {user.get('skills') or 'N/A'}\n"
        f"Experience: {user.get('experience_years') or 'N/A'} years\n"
        f"Desired Roles: {user.get('desired_roles') or 'N/A'}\n"
        f"Desired Locations: {user.get('desired_locations') or 'N/A'}\n"
        f"Salary: {user.get('salary_min') or '?'}-{user.get('salary_max') or '?'} {user.get('salary_currency') or ''}\n"
        f"Languages: {user.get('languages') or 'N/A'}\n"
        f"Education: {user.get('education') or 'N/A'}\n"
        f"Registered: {user.get('created_at', 'N/A')}\n\n"
        f"Total Applications: {user.get('total_applications', 0)}\n"
        f"Total Offers: {user.get('total_offers', 0)}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Send Message to User", callback_data=f"admin_msg_user_{tg_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Users", callback_data="admin_users")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text[:4000], reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_msg_user_"))
async def admin_msg_user_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    tg_id = int(callback.data.split("_")[-1])
    await state.update_data(admin_msg_target=tg_id)
    await callback.message.edit_text(
        f"Type the message you want to send to user {tg_id}:\n\n"
        "Send /cancel to cancel."
    )
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.answer()


@router.callback_query(F.data == "admin_recent_apps")
async def admin_recent_apps(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    apps = await db.get_recent_applications(limit=15)
    if not apps:
        await callback.message.edit_text(
            "No applications yet.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
            ])
        )
        await callback.answer()
        return

    text = "Recent Applications\n\n"
    for a in apps:
        username = a["username"] or "N/A"
        text += (
            f"• @{username}: {a['job_title']} at {a['company']} "
            f"[{a['status']}] ({a['applied_at'][:10]})\n"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text[:4000], reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_offers")
async def admin_offers(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    offers = await db.get_users_with_offers()
    if not offers:
        await callback.message.edit_text(
            "No offers received yet.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
            ])
        )
        await callback.answer()
        return

    text = "Users with Job Offers\n\n"
    for o in offers:
        username = o["username"] or "N/A"
        name = o["full_name"] or "N/A"
        text += (
            f"• @{username} ({name})\n"
            f"  Position: {o['job_title']} at {o['company']}\n"
            f"  Date: {o['applied_at'][:10]}\n\n"
        )

    text += "These users should be contacted for payment reminder."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Send Payment Reminders", callback_data="admin_send_payment_reminders")],
        [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text[:4000], reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_send_payment_reminders")
async def admin_send_payment_reminders(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    offers = await db.get_users_with_offers()
    sent = 0
    for o in offers:
        try:
            await bot.send_message(
                o["telegram_id"],
                f"Congratulations on your new job as {o['job_title']} at {o['company']}!\n\n"
                f"As per our service agreement, a one-month salary service fee is due "
                f"within 30 days of your first paycheck.\n\n"
                f"Please contact us at technosystems3000@gmail.com to arrange payment.\n\n"
                f"Thank you for using Global Job Hunter AI!"
            )
            sent += 1
        except Exception:
            pass

    await callback.message.edit_text(
        f"Payment reminders sent to {sent}/{len(offers)} users with offers.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")],
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    await state.update_data(admin_msg_target="all")
    await callback.message.edit_text(
        "Type the message you want to broadcast to ALL users:\n\n"
        "Send /cancel to cancel."
    )
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_message)
async def admin_send_message(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer("Cancelled.", reply_markup=get_admin_menu_keyboard())
        return

    data = await state.get_data()
    target = data.get("admin_msg_target")

    if target == "all":
        # Broadcast to all users
        user_ids = await db.get_all_telegram_ids()
        sent = 0
        for uid in user_ids:
            try:
                await bot.send_message(uid, f"Message from Admin:\n\n{message.text}")
                sent += 1
            except Exception:
                pass
        await message.answer(
            f"Broadcast sent to {sent}/{len(user_ids)} users.",
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        # Send to specific user
        try:
            await bot.send_message(int(target), f"Message from Support:\n\n{message.text}")
            await message.answer(
                f"Message sent to user {target}.",
                reply_markup=get_admin_menu_keyboard()
            )
        except Exception as e:
            await message.answer(
                f"Failed to send message: {e}",
                reply_markup=get_admin_menu_keyboard()
            )

    await state.clear()
