from database import db
from datetime import datetime, timedelta
from openai import OpenAI
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


class FollowUpService:
    def __init__(self, db_instance):
        self.db = db_instance
        self.openai_client = OpenAI()

    async def find_recruiter_contacts(self, company: str, job_title: str):
        prompt = (
            f"Find potential recruiter contacts for a {job_title} position at {company}. "
            "Provide names, LinkedIn profiles (if publicly available), and potential email patterns "
            "(e.g., firstname.lastname@company.com). If no specific contacts are found, suggest "
            "general strategies for finding recruiters at this company."
        )
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that finds recruiter contacts and provides strategies."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error finding recruiter contacts: {e}"

    async def generate_follow_up_message(self, user_profile, application):
        p = to_dict(user_profile)
        a = to_dict(application)
        full_name = p.get("full_name") or "the applicant"
        job_title = a.get("job_title", "")
        company = a.get("company", "")
        applied_at_raw = a.get("applied_at", "")
        applied_at = datetime.fromisoformat(applied_at_raw).strftime("%Y-%m-%d") if applied_at_raw else "recently"
        skills = p.get("skills") or "various skills"

        prompt = (
            f"Generate a personalized follow-up email/LinkedIn message for a job application. "
            f"The user's name is {full_name}. They applied for the {job_title} position at {company} "
            f"on {applied_at}. Highlight their skills: {skills}. Keep it concise and professional, "
            f"expressing continued interest and eagerness for the next steps. Ask for an update on "
            f"the application status. Do not include placeholders like [Recruiter Name] or [Your Name]."
        )
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates professional follow-up messages for job applications."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating follow-up message: {e}"

    async def schedule_follow_up(self, application_id: int, days: int, message_text: str, follow_up_number: int):
        scheduled_date = (datetime.now() + timedelta(days=days)).isoformat()
        await self.db.create_follow_up(application_id, message_text, scheduled_date, follow_up_number)

    async def send_follow_up(self, follow_up_id: int, application_id: int):
        await self.db.update_follow_up_status(follow_up_id, sent=True)
        application = await self.db.get_application_by_id(application_id)
        if application:
            a = to_dict(application)
            current_info = a.get("follow_up_info") or ""
            new_info = f"Follow-up {follow_up_id} sent on {datetime.now().strftime('%Y-%m-%d')}.\n"
            await self.db.update_application(application_id, follow_up_info=current_info + new_info)
        return True
