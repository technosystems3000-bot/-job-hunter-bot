from database import db
from datetime import datetime
import config


def to_dict(obj):
    """Convert sqlite3.Row or similar object to a regular dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    try:
        return dict(obj)
    except (TypeError, ValueError):
        return {}


class AutoApplyService:
    def __init__(self, db_instance):
        self.db = db_instance

    async def apply_to_job(self, telegram_id, job, resume_pdf_path=None, cover_letter=None):
        user = await self.db.get_user(telegram_id)
        if not user:
            return False, "User not found."

        user_id = user["id"]
        j = to_dict(job)

        # Check application limits
        daily_exceeded, daily_count = await self.check_daily_limit(user_id)
        weekly_exceeded, weekly_count = await self.check_weekly_limit(user_id)

        if daily_exceeded:
            return False, (
                f"You've reached your daily application limit ({config.DAILY_APPLICATION_LIMIT}). "
                "This helps ensure quality applications. Try again tomorrow!"
            )
        if weekly_exceeded:
            return False, (
                f"You've reached your weekly application limit ({config.WEEKLY_APPLICATION_LIMIT}). "
                "This helps ensure quality applications. Try again next week!"
            )

        # Create application
        application_id = await self.db.create_application(
            user_id=user_id,
            job_id=j.get("id"),
            job_title=j.get("title", ""),
            company=j.get("company", ""),
            job_url=j.get("url", ""),
            resume_pdf_path=resume_pdf_path,
            cover_letter=cover_letter,
            status="Applied"
        )

        if application_id:
            await self.db.increment_application_counts(user_id)
            return True, "Application submitted successfully!"
        else:
            return False, "Failed to submit application."

    async def check_daily_limit(self, user_id):
        counts = await self.db.get_user_application_counts(user_id)
        if not counts:
            return True, 0

        now = datetime.now()
        last_applied_str = counts["last_applied_date"]
        last_applied = datetime.fromisoformat(last_applied_str) if last_applied_str else now

        if now.date() > last_applied.date():
            daily_count = 0
        else:
            daily_count = counts["application_count_daily"]

        return daily_count >= config.DAILY_APPLICATION_LIMIT, daily_count

    async def check_weekly_limit(self, user_id):
        counts = await self.db.get_user_application_counts(user_id)
        if not counts:
            return True, 0

        now = datetime.now()
        last_applied_str = counts["last_applied_date"]
        last_applied = datetime.fromisoformat(last_applied_str) if last_applied_str else now

        if now.isocalendar()[1] > last_applied.isocalendar()[1] or now.year > last_applied.year:
            weekly_count = 0
        else:
            weekly_count = counts["application_count_weekly"]

        return weekly_count >= config.WEEKLY_APPLICATION_LIMIT, weekly_count
