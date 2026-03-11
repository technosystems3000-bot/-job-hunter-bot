import httpx
import asyncio
import logging
import re
import os
import json
import hashlib
from html import unescape
from database import db

logger = logging.getLogger(__name__)

JOOBLE_LIMIT = 500  # Monthly request limit for Jooble
JOOBLE_WARNING_THRESHOLD = 450  # Notify admin at this count


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > 500:
        clean = clean[:500] + "..."
    return clean


def make_cache_key(query: str, location: str = "") -> str:
    """Create a hash key for caching search results."""
    raw = f"{query.lower().strip()}|{location.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


class JobSearchService:
    def __init__(self):
        self.timeout = httpx.Timeout(15.0)
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
        self.jooble_api_key = os.getenv("JOOBLE_API_KEY")
        self._bot_instance = None  # Will be set from bot.py for admin notifications

    def set_bot(self, bot):
        """Set bot instance for sending admin notifications."""
        self._bot_instance = bot

    async def _notify_admin(self, message: str):
        """Send notification to admin via Telegram."""
        from config import ADMIN_TELEGRAM_ID
        if self._bot_instance and ADMIN_TELEGRAM_ID:
            try:
                await self._bot_instance.send_message(ADMIN_TELEGRAM_ID, message)
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")

    # ── Remotive (no key, no limit) ──

    async def search_remotive(self, query: str, limit: int = 10) -> list:
        """Search remote jobs on Remotive (no API key needed)."""
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"search": query, "limit": limit}
                resp = await client.get("https://remotive.com/api/remote-jobs", params=params)
                resp.raise_for_status()
                data = resp.json()
                for j in data.get("jobs", []):
                    jobs.append({
                        "job_id": f"remotive_{j['id']}",
                        "title": j.get("title", ""),
                        "company": j.get("company_name", ""),
                        "location": j.get("candidate_required_location", "Remote"),
                        "description": strip_html(j.get("description", "")),
                        "url": j.get("url", ""),
                        "source": "Remotive",
                        "salary": j.get("salary", ""),
                        "match_score": None,
                    })
        except Exception as e:
            logger.error(f"Remotive API error: {e}")
        return jobs

    # ── Arbeitnow (no key, no limit) ──

    async def search_arbeitnow(self, query: str, limit: int = 10) -> list:
        """Search jobs on Arbeitnow (no API key needed, Europe-focused)."""
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get("https://www.arbeitnow.com/api/job-board-api")
                resp.raise_for_status()
                data = resp.json()
                query_lower = query.lower()
                count = 0
                for j in data.get("data", []):
                    title = j.get("title", "")
                    description = j.get("description", "")
                    tags = " ".join(j.get("tags", []))
                    company = j.get("company_name", "")
                    searchable = f"{title} {description} {tags} {company}".lower()
                    if query_lower and query_lower not in searchable:
                        continue
                    location = j.get("location", "")
                    if j.get("remote"):
                        location = f"{location} (Remote)" if location else "Remote"
                    jobs.append({
                        "job_id": f"arbeitnow_{j.get('slug', '')}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": strip_html(description),
                        "url": j.get("url", ""),
                        "source": "Arbeitnow",
                        "salary": "",
                        "match_score": None,
                    })
                    count += 1
                    if count >= limit:
                        break
        except Exception as e:
            logger.error(f"Arbeitnow API error: {e}")
        return jobs

    # ── Adzuna (key required, generous limits) ──

    async def search_adzuna(self, query: str, location: str = "", page: int = 1, limit: int = 10) -> list:
        """Search jobs on Adzuna (requires API key, 16 countries)."""
        jobs = []
        if not self.adzuna_app_id or not self.adzuna_app_key:
            logger.info("Adzuna API keys not configured, skipping.")
            return jobs

        country_map = {
            "uk": "gb", "united kingdom": "gb", "england": "gb", "london": "gb",
            "us": "us", "usa": "us", "united states": "us", "america": "us",
            "germany": "de", "deutschland": "de", "berlin": "de", "munich": "de",
            "france": "fr", "paris": "fr",
            "netherlands": "nl", "holland": "nl", "amsterdam": "nl",
            "canada": "ca", "toronto": "ca",
            "australia": "au", "sydney": "au",
            "india": "in", "poland": "pl", "russia": "ru",
            "brazil": "br", "austria": "at", "new zealand": "nz",
            "south africa": "za", "singapore": "sg", "italy": "it",
            "spain": "es", "switzerland": "ch", "belgium": "be",
            "czech": "cz", "slovakia": "sk",
        }

        country = "us"
        if location:
            loc_lower = location.lower().strip()
            for key, code in country_map.items():
                if key in loc_lower:
                    country = code
                    break

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
                params = {
                    "app_id": self.adzuna_app_id,
                    "app_key": self.adzuna_app_key,
                    "what": query,
                    "results_per_page": limit,
                    "content-type": "application/json",
                }
                if location:
                    params["where"] = location
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                for j in data.get("results", []):
                    jobs.append({
                        "job_id": f"adzuna_{j.get('id', '')}",
                        "title": j.get("title", ""),
                        "company": j.get("company", {}).get("display_name", ""),
                        "location": j.get("location", {}).get("display_name", ""),
                        "description": strip_html(j.get("description", "")),
                        "url": j.get("redirect_url", ""),
                        "source": "Adzuna",
                        "salary": "",
                        "match_score": None,
                    })
        except Exception as e:
            logger.error(f"Adzuna API error: {e}")
        return jobs

    # ── Jooble (key required, 500 requests/month limit) ──

    async def search_jooble(self, query: str, location: str = "", limit: int = 10) -> list:
        """Search jobs on Jooble (limited API — used as last resort)."""
        jobs = []
        if not self.jooble_api_key:
            logger.info("Jooble API key not configured, skipping.")
            return jobs

        # Check usage limit before making request
        usage = await db.get_api_usage("jooble")
        current_count = usage["request_count"] if usage else 0

        if current_count >= JOOBLE_LIMIT:
            logger.warning(f"Jooble API limit reached: {current_count}/{JOOBLE_LIMIT}")
            # Notify admin (only once per day)
            if usage:
                last_notified = usage.get("last_notified_at", "")
                from datetime import datetime
                should_notify = True
                if last_notified:
                    try:
                        last_dt = datetime.fromisoformat(last_notified)
                        if (datetime.now() - last_dt).total_seconds() < 86400:
                            should_notify = False
                    except Exception:
                        pass
                if should_notify:
                    await self._notify_admin(
                        "⚠️ JOOBLE API LIMIT REACHED\n\n"
                        f"Monthly requests used: {current_count}/{JOOBLE_LIMIT}\n\n"
                        "The bot has stopped using Jooble API to avoid errors.\n"
                        "Please contact Jooble to request higher limits or a new API key.\n\n"
                        "Other search sources (Remotive, Arbeitnow, Adzuna) continue to work normally."
                    )
                    await db.update_api_notified("jooble")
            return jobs

        # Warn admin when approaching limit
        if current_count >= JOOBLE_WARNING_THRESHOLD and current_count < JOOBLE_LIMIT:
            remaining = JOOBLE_LIMIT - current_count
            if usage:
                last_notified = usage.get("last_notified_at", "")
                from datetime import datetime
                should_notify = True
                if last_notified:
                    try:
                        last_dt = datetime.fromisoformat(last_notified)
                        if (datetime.now() - last_dt).total_seconds() < 86400:
                            should_notify = False
                    except Exception:
                        pass
                if should_notify:
                    await self._notify_admin(
                        "⚠️ JOOBLE API WARNING\n\n"
                        f"Monthly requests used: {current_count}/{JOOBLE_LIMIT}\n"
                        f"Remaining: {remaining} requests\n\n"
                        "Consider contacting Jooble for higher limits."
                    )
                    await db.update_api_notified("jooble")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"https://jooble.org/api/{self.jooble_api_key}"
                payload = {
                    "keywords": query,
                    "location": location if location else "",
                    "page": 1,
                }
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

                # Track usage
                new_count = await db.increment_api_usage("jooble")
                logger.info(f"Jooble API usage: {new_count}/{JOOBLE_LIMIT}")

                count = 0
                for j in data.get("jobs", []):
                    jobs.append({
                        "job_id": f"jooble_{j.get('id', '')}",
                        "title": j.get("title", ""),
                        "company": j.get("company", ""),
                        "location": j.get("location", ""),
                        "description": strip_html(j.get("snippet", "")),
                        "url": j.get("link", ""),
                        "source": "Jooble",
                        "salary": j.get("salary", ""),
                        "match_score": None,
                    })
                    count += 1
                    if count >= limit:
                        break
        except Exception as e:
            logger.error(f"Jooble API error: {e}")
        return jobs

    # ── Smart Search with Cache and Priority Queue ──

    async def search_jobs(self, query: str, location: str = "", page: int = 1) -> list:
        """
        Smart job search with caching and priority queue:
        1. Check cache first (5 days TTL)
        2. Search free unlimited APIs (Remotive, Arbeitnow)
        3. Search Adzuna (generous limits)
        4. Only use Jooble if other sources gave < 5 results
        5. Cache all results
        """
        # Step 1: Check cache
        cache_key = make_cache_key(query, location)
        cached = await db.get_cached_search(cache_key, max_age_hours=120)  # 5 days
        if cached:
            logger.info(f"Cache HIT for query='{query}', location='{location}'")
            return json.loads(cached)

        logger.info(f"Cache MISS for query='{query}', location='{location}' — searching APIs")

        # Step 2: Search free unlimited APIs first
        limit_per_source = 5
        free_tasks = [
            self.search_remotive(query, limit=limit_per_source),
            self.search_arbeitnow(query, limit=limit_per_source),
        ]
        free_results = await asyncio.gather(*free_tasks, return_exceptions=True)

        all_jobs = []
        source_names = ["Remotive", "Arbeitnow"]
        for i, result in enumerate(free_results):
            if isinstance(result, Exception):
                logger.error(f"Error from {source_names[i]}: {result}")
            elif isinstance(result, list):
                all_jobs.extend(result)
                logger.info(f"Got {len(result)} jobs from {source_names[i]}")

        # Step 3: Search Adzuna (generous limits)
        try:
            adzuna_jobs = await self.search_adzuna(query, location, page, limit=limit_per_source)
            all_jobs.extend(adzuna_jobs)
            logger.info(f"Got {len(adzuna_jobs)} jobs from Adzuna")
        except Exception as e:
            logger.error(f"Adzuna error: {e}")

        # Step 4: Only use Jooble if we have < 5 results (save precious requests)
        if len(all_jobs) < 5:
            logger.info(f"Only {len(all_jobs)} results from free APIs — trying Jooble")
            try:
                jooble_jobs = await self.search_jooble(query, location, limit=limit_per_source)
                all_jobs.extend(jooble_jobs)
                logger.info(f"Got {len(jooble_jobs)} jobs from Jooble")
            except Exception as e:
                logger.error(f"Jooble error: {e}. Skipping Jooble for this search.")
                jooble_jobs = [] # Ensure an empty list is returned on error
        else:
            logger.info(f"Got {len(all_jobs)} results from free APIs — skipping Jooble to save quota")

        # Step 5: Cache results if we got any
        if all_jobs:
            await db.save_search_cache(cache_key, json.dumps(all_jobs, ensure_ascii=False))
            logger.info(f"Cached {len(all_jobs)} jobs for query='{query}'")

        # Cleanup old cache periodically
        await db.cleanup_old_cache(max_age_hours=120)

        if not all_jobs:
            logger.warning(f"No jobs found for query='{query}', location='{location}'")

        return all_jobs


job_search_service = JobSearchService()
