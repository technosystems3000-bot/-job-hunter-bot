# 🤖 Global Job Hunter AI — Telegram Bot

An AI-powered Telegram bot that helps you find jobs worldwide, generates tailored resumes and cover letters, tracks applications, sends follow-ups, and finds referrals.

## Features

### 🔍 Job Search
- Search for jobs globally by keywords and location
- AI-powered Match Score showing how well each job fits your profile
- One-click apply with auto-generated resume and cover letter

### 📄 Resume & Cover Letter
- AI-generated tailored resumes for specific job descriptions
- ATS (Applicant Tracking System) optimization
- Cover letter generation personalized to each position

### 📊 Application Tracking
- Track all your applications in one place
- Filter by status: New, Applied, Follow-up Sent, Interview, Rejected, Offer
- Update statuses and withdraw applications

### 📧 Smart Follow-ups
- AI-generated personalized follow-up messages
- Scheduled follow-ups (3 days and 10 days after application)
- Track which follow-ups have been sent

### 🤝 Referral Finder
- AI-powered advice on finding referrals at target companies
- Personalized referral request message generation
- LinkedIn networking strategies

### 👤 Profile Management
- Complete professional profile setup
- Edit any field at any time via Settings
- Skills, experience, education, languages, salary expectations
- Resume text storage
- Account deletion option

### ⚙️ Anti-Spam Protection
- Daily limit: 10 applications per day
- Weekly limit: 50 applications per week
- Ensures quality over quantity

## Monetization Model

**Pay-on-Success:** The bot is completely free to use. If you find a job through the service, you agree to pay one monthly salary as a service fee. Users accept this agreement when they first start the bot.

## Project Structure

```
job_hunter_bot/
├── bot.py                    # Main entry point
├── config.py                 # Configuration and environment variables
├── database.py               # SQLite database with async operations
├── keyboards.py              # Inline and reply keyboard builders
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── handlers/
│   ├── __init__.py
│   ├── start.py              # /start command, agreement acceptance
│   ├── menu.py               # Main menu navigation
│   ├── profile.py            # Initial profile setup wizard
│   ├── settings.py           # Profile editing and account deletion
│   ├── jobs.py               # Job search and quick apply
│   ├── resume.py             # Resume viewing, generation, ATS optimization
│   ├── applications.py       # Application tracking and management
│   ├── follow_up.py          # Follow-up scheduling and tracking
│   ├── help.py               # Help command and FAQ
│   └── referral.py           # Referral finder and message generation
└── services/
    ├── __init__.py
    ├── ai_service.py          # OpenAI integration (resume, cover letter, ATS, match score)
    ├── auto_apply.py          # Auto-apply with rate limiting
    ├── follow_up.py           # Follow-up generation and scheduling
    ├── job_search.py          # Job search API integration
    └── referral.py            # Referral advice and message generation
```

## Installation & Setup

### Prerequisites
- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key (from [OpenAI Platform](https://platform.openai.com/api-keys))

### Steps

1. **Download and extract the project:**
   ```bash
   unzip job_hunter_bot.zip
   cd job_hunter_bot
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your BOT_TOKEN and OPENAI_API_KEY
   ```

   Or export them directly:
   ```bash
   export BOT_TOKEN="your_telegram_bot_token"
   export OPENAI_API_KEY="your_openai_api_key"
   ```

5. **Run the bot:**
   ```bash
   python bot.py
   ```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram Bot API token from @BotFather |
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI features |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot / Accept agreement |
| `/menu` | Open main menu |
| `/help` | Show help and FAQ |
| `/profile` | Set up your profile from scratch |

## Usage Flow

1. **Start** — User sends `/start`, reads and accepts the service agreement
2. **Profile Setup** — User fills in their professional profile (skills, experience, etc.)
3. **Job Search** — User searches for jobs by keywords and location
4. **Apply** — User clicks "Apply" on a job; bot generates tailored resume and cover letter
5. **Track** — User monitors application statuses in "My Applications"
6. **Follow Up** — Bot generates and schedules follow-up messages
7. **Referrals** — User gets AI advice on finding referrals at target companies

## Database

The bot uses SQLite for data storage. Tables:
- **users** — Telegram user data, agreement status, application counters
- **profiles** — Professional profile (skills, experience, education, resume, etc.)
- **jobs** — Cached job listings
- **applications** — User job applications with status tracking
- **follow_ups** — Scheduled and sent follow-up messages

The database file `job_hunter.db` is created automatically in the project directory on first run.

## Extending the Bot

### Real Job Search Integration
The current `services/job_search.py` returns placeholder data. To integrate real job boards:
- Replace `JobSearchService.search_jobs()` with API calls to JSearch (RapidAPI), LinkedIn API, Indeed API, Adzuna, etc.
- Each job should return: `job_id`, `title`, `company`, `location`, `description`, `url`, `source`

### Automated Form Submission
The current apply flow creates a database record. For actual automated submission:
- Integrate with job board APIs that support application submission
- Or use browser automation (Playwright/Selenium) for form filling

### Email Integration
To send actual follow-up emails:
- Add SMTP configuration to `config.py`
- Update `FollowUpService.send_follow_up()` to send emails via `aiosmtplib`

## License

This project is provided as-is for educational and personal use.
