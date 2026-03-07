import os
import aiosqlite
from datetime import datetime, timedelta

DATABASE_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_hunter.db")


class Database:
    def __init__(self):
        self.database_name = DATABASE_NAME

    async def init_db(self):
        async with aiosqlite.connect(self.database_name) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    agreement_accepted BOOLEAN DEFAULT FALSE,
                    agreement_date TEXT,
                    application_count_daily INTEGER DEFAULT 0,
                    application_count_weekly INTEGER DEFAULT 0,
                    last_applied_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT,
                    skills TEXT,
                    experience_years INTEGER,
                    desired_roles TEXT,
                    desired_locations TEXT,
                    salary_min INTEGER,
                    salary_max INTEGER,
                    salary_currency TEXT,
                    resume_text TEXT,
                    languages TEXT,
                    education TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    job_id INTEGER,
                    job_title TEXT,
                    company TEXT,
                    job_url TEXT,
                    status TEXT DEFAULT 'New',
                    resume_pdf_path TEXT,
                    cover_letter TEXT,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    follow_up_info TEXT,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,
                    salary TEXT,
                    description TEXT,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT,
                    match_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS follow_ups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    message_text TEXT,
                    scheduled_date TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    sent_date TEXT,
                    follow_up_number INTEGER NOT NULL,
                    FOREIGN KEY (application_id) REFERENCES applications (id)
                )
            ''')
            await conn.commit()

    async def user_exists(self, telegram_id):
        async with aiosqlite.connect(self.database_name) as conn:
            cursor = await conn.execute(
                "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            return await cursor.fetchone() is not None

    async def add_user(self, telegram_id, username=None, full_name=None):
        async with aiosqlite.connect(self.database_name) as conn:
            await conn.execute(
                "INSERT INTO users (telegram_id, username, full_name, agreement_accepted, agreement_date, last_applied_date) VALUES (?, ?, ?, ?, ?, ?)",
                (telegram_id, username, full_name, True, datetime.now().isoformat(), datetime.now().isoformat())
            )
            await conn.execute(
                "INSERT INTO profiles (user_id) VALUES ((SELECT id FROM users WHERE telegram_id = ?))",
                (telegram_id,)
            )
            await conn.commit()

    async def get_user(self, telegram_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            return await cursor.fetchone()

    async def get_profile(self, telegram_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT p.* FROM profiles p JOIN users u ON p.user_id = u.id WHERE u.telegram_id = ?",
                (telegram_id,)
            )
            return await cursor.fetchone()

    async def update_profile(self, telegram_id, **kwargs):
        async with aiosqlite.connect(self.database_name) as conn:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)

            if set_clauses:
                query = f"UPDATE profiles SET {', '.join(set_clauses)} WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)"
                values.append(telegram_id)
                await conn.execute(query, tuple(values))
                await conn.commit()

    async def create_job(self, title, company, location, salary, description, url, source, match_score=None):
        async with aiosqlite.connect(self.database_name) as conn:
            cursor = await conn.execute(
                "INSERT INTO jobs (title, company, location, salary, description, url, source, match_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, company, location, salary, description, url, source, match_score)
            )
            await conn.commit()
            return cursor.lastrowid

    async def get_job(self, job_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM jobs WHERE id = ?", (job_id,)
            )
            return await cursor.fetchone()

    async def get_job_by_url(self, url):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM jobs WHERE url = ?", (url,)
            )
            return await cursor.fetchone()

    async def update_job_match_score(self, job_id, match_score):
        async with aiosqlite.connect(self.database_name) as conn:
            await conn.execute(
                "UPDATE jobs SET match_score = ? WHERE id = ?",
                (match_score, job_id)
            )
            await conn.commit()

    async def create_application(self, user_id, job_id, job_title, company, job_url, resume_pdf_path=None, cover_letter=None, status='New', follow_up_info=None):
        async with aiosqlite.connect(self.database_name) as conn:
            cursor = await conn.execute(
                "INSERT INTO applications (user_id, job_id, job_title, company, job_url, resume_pdf_path, cover_letter, status, follow_up_info) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, job_id, job_title, company, job_url, resume_pdf_path, cover_letter, status, follow_up_info)
            )
            await conn.commit()
            return cursor.lastrowid

    async def get_application_by_id(self, application_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM applications WHERE id = ?", (application_id,)
            )
            return await cursor.fetchone()

    async def get_applications_by_user(self, user_id, status=None):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            if status:
                cursor = await conn.execute(
                    "SELECT * FROM applications WHERE user_id = ? AND status = ? ORDER BY applied_at DESC",
                    (user_id, status)
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM applications WHERE user_id = ? ORDER BY applied_at DESC",
                    (user_id,)
                )
            return await cursor.fetchall()

    async def update_application(self, application_id, **kwargs):
        async with aiosqlite.connect(self.database_name) as conn:
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)

            if set_clauses:
                query = f"UPDATE applications SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(application_id)
                await conn.execute(query, tuple(values))
                await conn.commit()

    async def delete_application(self, application_id):
        async with aiosqlite.connect(self.database_name) as conn:
            # Also delete related follow-ups
            await conn.execute(
                "DELETE FROM follow_ups WHERE application_id = ?", (application_id,)
            )
            await conn.execute(
                "DELETE FROM applications WHERE id = ?", (application_id,)
            )
            await conn.commit()

    async def create_follow_up(self, application_id, message_text, scheduled_date, follow_up_number):
        async with aiosqlite.connect(self.database_name) as conn:
            cursor = await conn.execute(
                "INSERT INTO follow_ups (application_id, message_text, scheduled_date, follow_up_number) VALUES (?, ?, ?, ?)",
                (application_id, message_text, scheduled_date, follow_up_number)
            )
            await conn.commit()
            return cursor.lastrowid

    async def get_follow_ups_by_application(self, application_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM follow_ups WHERE application_id = ? ORDER BY follow_up_number ASC",
                (application_id,)
            )
            return await cursor.fetchall()

    async def get_pending_follow_ups(self):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            today = datetime.now().isoformat()
            cursor = await conn.execute(
                "SELECT * FROM follow_ups WHERE sent = FALSE AND scheduled_date <= ?", (today,)
            )
            return await cursor.fetchall()

    async def get_follow_up_by_id(self, follow_up_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM follow_ups WHERE id = ?", (follow_up_id,)
            )
            return await cursor.fetchone()

    async def update_follow_up_status(self, follow_up_id, sent=True):
        async with aiosqlite.connect(self.database_name) as conn:
            sent_date = datetime.now().isoformat() if sent else None
            await conn.execute(
                "UPDATE follow_ups SET sent = ?, sent_date = ? WHERE id = ?",
                (sent, sent_date, follow_up_id)
            )
            await conn.commit()

    async def get_user_application_counts(self, user_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT application_count_daily, application_count_weekly, last_applied_date FROM users WHERE id = ?",
                (user_id,)
            )
            return await cursor.fetchone()

    async def increment_application_counts(self, user_id):
        async with aiosqlite.connect(self.database_name) as conn:
            now = datetime.now()
            user_data = await self.get_user_application_counts(user_id)

            daily_count = user_data['application_count_daily']
            weekly_count = user_data['application_count_weekly']
            last_applied_date_str = user_data['last_applied_date']

            last_applied_date = datetime.fromisoformat(last_applied_date_str) if last_applied_date_str else now

            if now.date() > last_applied_date.date():
                daily_count = 0

            if now.isocalendar()[1] > last_applied_date.isocalendar()[1] or now.year > last_applied_date.year:
                weekly_count = 0

            daily_count += 1
            weekly_count += 1

            await conn.execute(
                "UPDATE users SET application_count_daily = ?, application_count_weekly = ?, last_applied_date = ? WHERE id = ?",
                (daily_count, weekly_count, now.isoformat(), user_id)
            )
            await conn.commit()
            return daily_count, weekly_count

    # ── Admin methods ──

    async def get_all_users(self):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT u.*, p.full_name as profile_name, p.skills, p.desired_roles "
                "FROM users u LEFT JOIN profiles p ON p.user_id = u.id "
                "ORDER BY u.created_at DESC"
            )
            return await cursor.fetchall()

    async def get_stats(self):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            total_users = (await (await conn.execute("SELECT COUNT(*) as c FROM users")).fetchone())["c"]
            total_apps = (await (await conn.execute("SELECT COUNT(*) as c FROM applications")).fetchone())["c"]
            total_jobs = (await (await conn.execute("SELECT COUNT(*) as c FROM jobs")).fetchone())["c"]
            total_offers = (await (await conn.execute("SELECT COUNT(*) as c FROM applications WHERE status = 'Offer'")).fetchone())["c"]
            total_interviews = (await (await conn.execute("SELECT COUNT(*) as c FROM applications WHERE status = 'Interview'")).fetchone())["c"]
            return {
                "total_users": total_users,
                "total_applications": total_apps,
                "total_jobs": total_jobs,
                "total_offers": total_offers,
                "total_interviews": total_interviews,
            }

    async def get_recent_applications(self, limit=20):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT a.*, u.telegram_id, u.username "
                "FROM applications a JOIN users u ON a.user_id = u.id "
                "ORDER BY a.applied_at DESC LIMIT ?",
                (limit,)
            )
            return await cursor.fetchall()

    async def get_users_with_offers(self):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT DISTINCT u.telegram_id, u.username, u.full_name, a.job_title, a.company, a.applied_at "
                "FROM applications a JOIN users u ON a.user_id = u.id "
                "WHERE a.status = 'Offer' ORDER BY a.applied_at DESC"
            )
            return await cursor.fetchall()

    async def get_all_telegram_ids(self):
        async with aiosqlite.connect(self.database_name) as conn:
            cursor = await conn.execute("SELECT telegram_id FROM users")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def get_user_detail_admin(self, telegram_id):
        async with aiosqlite.connect(self.database_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT u.*, p.full_name as profile_name, p.skills, p.experience_years, "
                "p.desired_roles, p.desired_locations, p.salary_min, p.salary_max, "
                "p.salary_currency, p.languages, p.education "
                "FROM users u LEFT JOIN profiles p ON p.user_id = u.id "
                "WHERE u.telegram_id = ?",
                (telegram_id,)
            )
            user = await cursor.fetchone()
            if not user:
                return None
            # Count applications
            apps_cursor = await conn.execute(
                "SELECT COUNT(*) as c FROM applications WHERE user_id = ?",
                (user["id"],)
            )
            apps_count = (await apps_cursor.fetchone())["c"]
            offers_cursor = await conn.execute(
                "SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND status = 'Offer'",
                (user["id"],)
            )
            offers_count = (await offers_cursor.fetchone())["c"]
            return {**dict(user), "total_applications": apps_count, "total_offers": offers_count}

    async def delete_user(self, telegram_id):
        async with aiosqlite.connect(self.database_name) as conn:
            user = await self.get_user(telegram_id)
            if user:
                user_id = user['id']
                await conn.execute(
                    "DELETE FROM follow_ups WHERE application_id IN (SELECT id FROM applications WHERE user_id = ?)",
                    (user_id,)
                )
                await conn.execute("DELETE FROM applications WHERE user_id = ?", (user_id,))
                await conn.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
                await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                await conn.commit()


db = Database()
