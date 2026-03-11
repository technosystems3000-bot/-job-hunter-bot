import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import db
from handlers import start, profile, menu, jobs, resume, applications, follow_up, help, settings, referral, admin
from services.job_search import job_search_service


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is not set in environment variables.")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Pass bot instance to job_search_service for admin notifications
    job_search_service.set_bot(bot)

    # Register routers in order of priority
    dp.include_router(admin.router)  # Admin first (restricted access)
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(settings.router)
    dp.include_router(menu.router)
    dp.include_router(help.router)
    dp.include_router(jobs.router)
    dp.include_router(resume.router)
    dp.include_router(applications.router)
    dp.include_router(follow_up.router)
    dp.include_router(referral.router)

    await db.init_db()
    logging.info("Database initialized.")

    # Drop pending updates to ensure bot starts fresh
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot is starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
