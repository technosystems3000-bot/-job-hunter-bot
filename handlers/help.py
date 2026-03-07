from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from config import SUPPORT_EMAIL

router = Router()

HELP_TEXT = f"""🤖 Global Job Hunter AI — Help

Welcome! This bot is your AI-powered job search assistant.

🔍 Search Jobs
Search for jobs worldwide by keywords and location. Each result comes with a Match Score showing how well it fits your profile.

📄 My Resume
View your current resume, generate a tailored resume for a specific job, or optimize it for ATS (Applicant Tracking Systems).

📊 My Applications
Track all your job applications. View statuses, send follow-ups, update statuses, or withdraw.

📧 Scheduled Follow-ups
View and manage scheduled follow-up messages. The bot generates personalized follow-up emails for recruiters.

🤝 Find Referrals
Get AI-powered advice on finding referrals at target companies.

👤 My Profile
Set up your professional profile: skills, experience, roles, locations, salary, etc.

⚙️ Settings
Edit your profile, change preferences, or delete your account.

━━━━━━━━━━━━━━━━━━━━

📋 FAQ

Q: How much does it cost?
A: Free to use. If you find a job through us, you pay one monthly salary as a service fee.

Q: How many applications can I submit?
A: 10 per day, 50 per week (to ensure quality).

Q: How does the follow-up feature work?
A: After applying, the bot generates follow-up messages scheduled at 3 and 10 days.

Q: Is my data safe?
A: Your data is stored securely and never shared with third parties.

Q: How does the Match Score work?
A: AI analyzes your profile vs. job description — score from 0 to 100%.

━━━━━━━━━━━━━━━━━━━━

📬 Contact & Support
Email: {SUPPORT_EMAIL}

Commands:
/start — Start the bot
/menu — Open main menu
/help — Show this help
/search — Quick job search
"""


def get_help_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Search Jobs", callback_data="job_search"),
            InlineKeyboardButton(text="👤 Profile", callback_data="my_profile"),
        ],
        [
            InlineKeyboardButton(text="📩 Contact Support", callback_data="contact_support"),
        ],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=get_help_keyboard())


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.edit_text(HELP_TEXT, reply_markup=get_help_keyboard())
    await callback.answer()


@router.callback_query(F.data == "contact_support")
async def contact_support(callback: CallbackQuery):
    text = (
        f"📩 Contact Support\n\n"
        f"If you need help, have questions, or want to report an issue, "
        f"please email us at:\n\n"
        f"{SUPPORT_EMAIL}\n\n"
        f"We typically respond within 24 hours."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="help")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
