from openai import OpenAI
import os


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


class AIService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4.1-mini"

    async def generate_resume(self, profile, job) -> str:
        p = to_dict(profile)
        j = to_dict(job)
        prompt = f"""Generate a resume tailored for the following job description, using the provided user profile. Ensure the resume highlights skills and experiences relevant to the job. The output should be a plain text resume.

User Profile:
Full Name: {p.get('full_name', 'N/A')}
Skills: {p.get('skills', 'N/A')}
Experience: {p.get('experience_years', 'N/A')} years
Desired Roles: {p.get('desired_roles', 'N/A')}
Education: {p.get('education', 'N/A')}
Languages: {p.get('languages', 'N/A')}
Original Resume Text: {p.get('resume_text', 'N/A')}

Job Description:
Title: {j.get('title', 'N/A')}
Company: {j.get('company', 'N/A')}
Location: {j.get('location', 'N/A')}
Description: {j.get('description', 'N/A')}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that generates professional resumes."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    async def generate_cover_letter(self, profile, job) -> str:
        p = to_dict(profile)
        j = to_dict(job)
        prompt = f"""Generate a cover letter tailored for the following job description, using the provided user profile. Highlight relevant skills and experiences and express enthusiasm for the role and company. The output should be a plain text cover letter.

User Profile:
Full Name: {p.get('full_name', 'N/A')}
Skills: {p.get('skills', 'N/A')}
Experience: {p.get('experience_years', 'N/A')} years
Desired Roles: {p.get('desired_roles', 'N/A')}
Education: {p.get('education', 'N/A')}
Languages: {p.get('languages', 'N/A')}

Job Description:
Title: {j.get('title', 'N/A')}
Company: {j.get('company', 'N/A')}
Location: {j.get('location', 'N/A')}
Description: {j.get('description', 'N/A')}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that generates professional cover letters."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    async def optimize_for_ats(self, resume_text: str, job_description: str) -> str:
        prompt = f"""Optimize the following resume text for an Applicant Tracking System (ATS) based on the provided job description. Focus on incorporating keywords and formatting for ATS compatibility. The output should be the optimized resume text.

Original Resume:
{resume_text}

Job Description:
{job_description}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that optimizes resumes for ATS."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    async def calculate_match_score(self, profile, job) -> float:
        p = to_dict(profile)
        j = to_dict(job)
        prompt = f"""Calculate a match score (0-100) between the user's profile and the job description. Consider skills, experience, desired roles, and education. Provide only the score as a number, no additional text.

User Profile:
Skills: {p.get('skills', 'N/A')}
Experience: {p.get('experience_years', 'N/A')} years
Desired Roles: {p.get('desired_roles', 'N/A')}
Education: {p.get('education', 'N/A')}
Languages: {p.get('languages', 'N/A')}

Job Description:
Title: {j.get('title', 'N/A')}
Company: {j.get('company', 'N/A')}
Location: {j.get('location', 'N/A')}
Description: {j.get('description', 'N/A')}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an AI assistant that calculates a match score between a user profile and a job description."},
                {"role": "user", "content": prompt}
            ]
        )
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 0.0

ai_service = AIService()
