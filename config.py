import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "technosystems3000@gmail.com")

DAILY_APPLICATION_LIMIT = 10
WEEKLY_APPLICATION_LIMIT = 50

WELCOME_MESSAGE = (
    "Welcome to Global Job Hunter AI!\n\n"
    "This bot helps you find jobs worldwide, generates tailored resumes and cover letters, "
    "tracks your applications, and helps you follow up with recruiters.\n\n"
    "Please read and accept the agreement below to continue."
)

AGREEMENT_TEXT = (
    "SERVICE AGREEMENT\n\n"
    "By using this bot, you agree to the following terms:\n\n"
    "1. The bot is free to use for job searching, resume generation, and application tracking.\n\n"
    "2. If you successfully find a job through our service, you commit to paying ONE MONTHLY SALARY "
    "as a service fee within 30 days of your first paycheck.\n\n"
    "3. Your personal data is used solely for the purpose of helping you find employment and will "
    "not be shared with third parties.\n\n"
    "4. To prevent spam, the bot limits applications to 10 per day and 50 per week.\n\n"
    "By clicking the button below, you confirm that you have read, understood, and agree to these terms."
)

ACCEPT_BUTTON_TEXT = "✅ I Accept the Agreement"
