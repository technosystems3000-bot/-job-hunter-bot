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


class ReferralService:
    def __init__(self):
        self.openai_client = OpenAI()

    async def find_potential_referrals(self, company: str, user_profile):
        p = to_dict(user_profile)
        skills = p.get("skills") or "various skills"
        desired_roles = p.get("desired_roles") or "various roles"

        prompt = (
            f"Given the user's profile (skills: {skills}, desired roles: {desired_roles}) "
            f"and target company {company}, suggest strategies or types of people to look for "
            f"to get a referral. Focus on networking advice and how to identify potential referrers "
            f"on platforms like LinkedIn. Do not provide specific names or direct contact information."
        )
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides advice on finding potential referrals."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error finding potential referrals: {e}"

    async def generate_referral_request(self, user_profile, company: str, contact_name: str):
        p = to_dict(user_profile)
        full_name = p.get("full_name") or "the applicant"
        desired_roles = p.get("desired_roles") or "various roles"
        skills = p.get("skills") or "various skills"

        prompt = (
            f"Generate a personalized message for {contact_name} at {company} requesting a referral. "
            f"The user's name is {full_name}. They are interested in roles related to {desired_roles} "
            f"and have skills in {skills}. The message should be polite, concise, and clearly state "
            f"the request for a referral, explaining why they are a good fit for {company}."
        )
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates professional referral request messages."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating referral request: {e}"
