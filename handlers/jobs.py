from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from services.job_search import job_search_service
from services.ai_service import ai_service
from keyboards import get_main_menu_keyboard

router = Router()


class JobSearchStates(StatesGroup):
    waiting_for_keywords = State()
    waiting_for_location = State()
    showing_results = State()


@router.callback_query(F.data == "job_search")
async def job_search_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await db.user_exists(user_id):
        await callback.message.edit_text("Please accept the agreement first using /start.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    await callback.message.edit_text("Please enter keywords for job search (e.g., 'Python developer', 'Data Scientist'):")
    await state.set_state(JobSearchStates.waiting_for_keywords)
    await callback.answer()


@router.message(JobSearchStates.waiting_for_keywords)
async def process_keywords(message: Message, state: FSMContext):
    await state.update_data(keywords=message.text)
    await message.answer("Please enter the desired location (e.g., 'Remote', 'London', 'Berlin'):")
    await state.set_state(JobSearchStates.waiting_for_location)


@router.message(JobSearchStates.waiting_for_location)
async def process_location(message: Message, state: FSMContext):
    user_data = await state.get_data()
    keywords = user_data.get("keywords")
    location = message.text
    user_id = message.from_user.id

    await message.answer("🔍 Searching for jobs...")

    jobs = await job_search_service.search_jobs(keywords, location)
    profile = await db.get_profile(user_id)

    if not jobs:
        await message.answer("No jobs found matching your criteria.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    processed_jobs = []
    for job in jobs:
        if profile:
            match_score = await ai_service.calculate_match_score(profile, job)
            job["match_score"] = round(match_score, 2)
        processed_jobs.append(job)

    await state.update_data(jobs=processed_jobs, current_job_index=0)
    await show_job_result(message, state)


async def show_job_result(message: Message, state: FSMContext):
    user_data = await state.get_data()
    jobs = user_data.get("jobs")
    current_job_index = user_data.get("current_job_index", 0)

    if not jobs or current_job_index >= len(jobs):
        await message.answer("No more jobs to show.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return

    job = jobs[current_job_index]
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "N/A")
    url = job.get("url", "#")
    description = job.get("description", "N/A")[:200]
    match_score = job.get("match_score")

    match_text = f"Match Score: {match_score}%\n" if match_score is not None else ""
    source = job.get("source", "")
    source_text = f"Source: {source}\n" if source else ""
    salary = job.get("salary", "")
    salary_text = f"Salary: {salary}\n" if salary else ""

    job_text = (
        f"Job Title: {title}\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"{salary_text}"
        f"{match_text}"
        f"{source_text}"
        f"URL: {url}\n\n"
        f"Description: {description}..."
    )

    job_id = job.get("job_id", current_job_index)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 View Job", url=url))
    builder.row(
        InlineKeyboardButton(text="🚀 Apply", callback_data=f"quick_apply_{current_job_index}"),
        InlineKeyboardButton(text="⏭ Next", callback_data="next_job"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu"))

    await message.answer(job_text, reply_markup=builder.as_markup())
    await state.set_state(JobSearchStates.showing_results)


@router.callback_query(F.data == "next_job", JobSearchStates.showing_results)
async def next_job_callback(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    current_job_index = user_data.get("current_job_index", 0)
    await state.update_data(current_job_index=current_job_index + 1)
    await show_job_result(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("quick_apply_"), JobSearchStates.showing_results)
async def quick_apply_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    job_index = int(parts[-1])
    user_data = await state.get_data()
    jobs = user_data.get("jobs", [])

    if job_index >= len(jobs):
        await callback.message.answer("Job not found.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    job = jobs[job_index]
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    profile = await db.get_profile(user_id)

    if not user or not profile:
        await callback.message.answer("Please set up your profile first.", reply_markup=get_main_menu_keyboard())
        await callback.answer()
        return

    await callback.message.answer("⏳ Generating tailored resume and cover letter...")

    # Generate resume and cover letter
    resume = await ai_service.generate_resume(profile, job)
    cover_letter = await ai_service.generate_cover_letter(profile, job)

    # Save job to DB if not exists
    existing_job = await db.get_job_by_url(job.get("url", ""))
    if existing_job:
        db_job_id = existing_job["id"]
    else:
        db_job_id = await db.create_job(
            title=job.get("title", ""),
            company=job.get("company", ""),
            location=job.get("location", ""),
            salary=job.get("salary", ""),
            description=job.get("description", ""),
            url=job.get("url", ""),
            source=job.get("source", ""),
            match_score=job.get("match_score")
        )

    # Create application
    app_id = await db.create_application(
        user_id=user["id"],
        job_id=db_job_id,
        job_title=job.get("title", ""),
        company=job.get("company", ""),
        job_url=job.get("url", ""),
        cover_letter=cover_letter,
        status="Applied"
    )

    # Increment counts
    await db.increment_application_counts(user["id"])

    company = job.get("company", "N/A")
    title = job.get("title", "N/A")

    await callback.message.answer(
        f"✅ Application submitted for {title} at {company}!\n\n"
        f"Your tailored resume and cover letter have been generated.\n\n"
        f"Generated Cover Letter:\n{cover_letter[:500]}...\n\n"
        f"You can track this application in 'My Applications'.",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
