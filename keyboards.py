from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🔍 Job Search", callback_data="job_search")],
        [InlineKeyboardButton(text="📊 My Applications", callback_data="my_applications")],
        [InlineKeyboardButton(text="📝 My Resume", callback_data="my_resume")],
        [InlineKeyboardButton(text="📧 Scheduled Follow-ups", callback_data="view_scheduled_follow_ups")],
        [InlineKeyboardButton(text="🤝 Find Referrals", callback_data="find_referrals")],
        [InlineKeyboardButton(text="👤 My Profile", callback_data="my_profile")],
        [
            InlineKeyboardButton(text="⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton(text="ℹ️ Help", callback_data="help"),
        ],
        [InlineKeyboardButton(text="📩 Contact Support", callback_data="contact_support")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_menu_keyboard():
    """Simple keyboard with just Back to Main Menu."""
    keyboard = [
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_nav_keyboard(back_callback=None, show_help=True, show_menu=True):
    """Universal navigation row that can be appended to any keyboard."""
    row = []
    if back_callback:
        row.append(InlineKeyboardButton(text="⬅️ Back", callback_data=back_callback))
    if show_help:
        row.append(InlineKeyboardButton(text="ℹ️ Help", callback_data="help"))
    if show_menu:
        row.append(InlineKeyboardButton(text="🏠 Menu", callback_data="main_menu"))
    return row


def get_applications_keyboard(applications, filter_status=None):
    keyboard = []
    if applications:
        for app in applications:
            company = app["company"]
            title = app["job_title"]
            status = app["status"]
            app_id = app["id"]
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{company} - {title} ({status})",
                    callback_data=f"view_app_detail_{app_id}"
                )
            ])

    filter_buttons = [
        InlineKeyboardButton(text="All", callback_data="filter_applications_all"),
        InlineKeyboardButton(text="New", callback_data="filter_applications_New"),
        InlineKeyboardButton(text="Applied", callback_data="filter_applications_Applied"),
    ]
    filter_buttons_2 = [
        InlineKeyboardButton(text="Follow-up", callback_data="filter_applications_Follow-up Sent"),
        InlineKeyboardButton(text="Interview", callback_data="filter_applications_Interview"),
        InlineKeyboardButton(text="Rejected", callback_data="filter_applications_Rejected"),
        InlineKeyboardButton(text="Offer", callback_data="filter_applications_Offer"),
    ]
    keyboard.append(filter_buttons)
    keyboard.append(filter_buttons_2)
    keyboard.append(get_nav_keyboard())
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_application_detail_keyboard(application_id, current_status):
    keyboard = [
        [InlineKeyboardButton(text="📧 Send Follow-up", callback_data=f"send_follow_up_{application_id}")],
        [InlineKeyboardButton(text="🔄 Update Status", callback_data=f"update_status_{application_id}")],
        [InlineKeyboardButton(text="❌ Withdraw", callback_data=f"withdraw_app_{application_id}")],
        [InlineKeyboardButton(text="⬅️ Back to Applications", callback_data="back_to_applications")],
        get_nav_keyboard(show_help=True, show_menu=True),
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_application_filter_keyboard(prefix="filter_applications"):
    statuses = ["New", "Applied", "Follow-up Sent", "Interview", "Rejected", "Offer"]
    keyboard = []
    for status in statuses:
        keyboard.append([InlineKeyboardButton(text=status, callback_data=f"{prefix}_{status}")])
    keyboard.append([
        InlineKeyboardButton(text="Cancel", callback_data="cancel_status_update"),
        InlineKeyboardButton(text="🏠 Menu", callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_agreement_keyboard():
    keyboard = [
        [KeyboardButton(text="✅ I Accept the Agreement")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


# ── Admin keyboards ──

def get_admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="👥 All Users", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Recent Applications", callback_data="admin_recent_apps")],
        [InlineKeyboardButton(text="🏆 Users with Offers", callback_data="admin_offers")],
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
