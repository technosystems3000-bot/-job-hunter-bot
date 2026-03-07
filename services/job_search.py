import httpx
import asyncio
import logging
import re
import os
from html import unescape

logger = logging.getLogger(__name__)


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    # Limit description length for Telegram messages
    if len(clean) > 500:
        clean = clean[:500] + "..."
    return clean


class JobSearchService:
    def __init__(self):
        self.timeout = httpx.Timeout(15.0)
        # Adzuna credentials (optional — set in .env)
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

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

                    # Filter by query keywords
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

    async def search_adzuna(self, query: str, location: str = "", page: int = 1, limit: int = 10) -> list:
        """Search jobs on Adzuna (requires API key, 16 countries)."""
        jobs = []
        if not self.adzuna_app_id or not self.adzuna_app_key:
            logger.info("Adzuna API keys not configured, skipping.")
            return jobs

        # Map common location names to Adzuna country codes
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
        }

        country = "us"  # default
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

    async def search_jobs(self, query: str, location: str = "", page: int = 1) -> list:
        """Search all sources in parallel and combine results."""
        limit_per_source = 5

        # Run all searches concurrently
        tasks = [
            self.search_remotive(query, limit=limit_per_source),
            self.search_arbeitnow(query, limit=limit_per_source),
            self.search_adzuna(query, location, page, limit=limit_per_source),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        source_names = ["Remotive", "Arbeitnow", "Adzuna"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error from {source_names[i]}: {result}")
            elif isinstance(result, list):
                all_jobs.extend(result)
                logger.info(f"Got {len(result)} jobs from {source_names[i]}")

        if not all_jobs:
            logger.warning(f"No jobs found for query='{query}', location='{location}'")

        return all_jobs


job_search_service = JobSearchService()
