"""Independent, privacy-conscious job shortlist generator (standard library only)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


EXPLICIT_OPT_BLOCK = re.compile(
    r"(?:stem\s+opt|opt|cpt)\s+(?:candidates?\s+)?(?:are\s+)?(?:not\s+(?:accepted|eligible|considered)|ineligible)"
    r"|(?:do(?:es)?\s+not|cannot|won't|will\s+not)\s+(?:accept|consider|support)"
    r"\s+(?:candidates?\s+(?:on|using)\s+)?(?:opt|stem\s+opt|cpt)"
    r"|(?:u\.?s\.?\s+citizenship|permanent\s+residen(?:cy|t\s+status))\s+(?:is\s+)?required",
    re.I,
)
NO_SPONSORSHIP = re.compile(
    r"(?:no|not\s+eligible\s+for|without|do(?:es)?\s+not\s+provide)\s+"
    r"(?:future\s+)?(?:visa\s+)?sponsorship|will\s+not\s+sponsor|unable\s+to\s+sponsor",
    re.I,
)
H1B_ONLY = re.compile(r"(?:no|not\s+provide|will\s+not\s+sponsor).{0,30}h-?1b", re.I)
EXPERIENCE = re.compile(r"(?:at\s+least\s+)?(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref"}


def canonical_url(raw: str) -> str:
    """Drop common tracking parameters while preserving a job's identity."""
    parts = urlsplit(raw.strip())
    query = urlencode([
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def load_jobs(path: Path) -> list[dict]:
    jobs = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(job, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        jobs.append(job)
    return jobs


def posted_date(job: dict) -> date | None:
    """Only trust an explicitly verified employer/ATS publication date."""
    if job.get("date_source") not in {"employer", "ats"}:
        return None
    raw = job.get("posted_at")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def assess(job: dict, profile: dict, today: date) -> dict:
    title = str(job.get("title") or job.get("role") or "")
    company = str(job.get("company") or "")
    location = str(job.get("location") or "")
    description = str(job.get("description") or "")
    url = canonical_url(str(job.get("url") or ""))
    text = f"{title} {description}".lower()
    reasons: list[str] = []
    warnings: list[str] = []

    if not title or not company or not url:
        reasons.append("missing job identity")
    if any(word.lower() in title.lower() for word in profile.get("exclude_titles", [])):
        reasons.append("seniority outside target range")
    if not any(place.lower() in location.lower() for place in profile.get("locations", [])):
        reasons.append("outside preferred locations")
    if EXPLICIT_OPT_BLOCK.search(description):
        reasons.append("explicit OPT/STEM OPT or permanent-authorization restriction")

    minimums = [int(value) for value in EXPERIENCE.findall(description)]
    if minimums and min(minimums) > profile.get("max_required_years", 3):
        warnings.append(f"asks for {min(minimums)}+ years")
    if NO_SPONSORSHIP.search(description) or H1B_ONLY.search(description):
        warnings.append("no sponsorship stated; verify STEM OPT support before applying")

    published = posted_date(job)
    if published is None:
        recency = "unverified"
    elif today - timedelta(days=7) <= published <= today:
        recency = "within_7_days"
    else:
        recency = "older"

    role_matches = [role for role in profile.get("target_roles", []) if role.lower() in title.lower()]
    skill_matches = [skill for skill in profile.get("skills", []) if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text)]
    score = min(10.0, round(4.0 + 1.2 * bool(role_matches) + 0.65 * len(skill_matches) + (0.5 if recency == "within_7_days" else 0), 1))
    if not role_matches:
        score = round(max(0.0, score - 1.5), 1)
    if warnings:
        score = round(max(0.0, score - 0.5 * len(warnings)), 1)

    resume = "general"
    for name, terms in profile.get("resume_routes", {}).items():
        if any(term.lower() in title.lower() for term in terms):
            resume = name
            break

    return {
        "company": company,
        "title": title,
        "location": location,
        "url": url,
        "score": score,
        "recency": recency,
        "posted_at": published.isoformat() if published else None,
        "resume_route": resume,
        "matched_skills": skill_matches,
        "warnings": warnings,
        "excluded": reasons,
    }


def shortlist(jobs: list[dict], profile: dict, today: date) -> list[dict]:
    seen = {canonical_url(url) for url in profile.get("already_applied_urls", [])}
    results = []
    for job in jobs:
        result = assess(job, profile, today)
        if result["url"] in seen:
            continue
        seen.add(result["url"])
        if not result["excluded"]:
            results.append(result)
    return sorted(results, key=lambda item: (item["recency"] != "within_7_days", -item["score"], item["company"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank job postings without uploading candidate data")
    parser.add_argument("jobs", type=Path, help="JSON Lines file with job postings")
    parser.add_argument("--profile", type=Path, default=Path("profile.example.json"))
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    print(json.dumps(shortlist(load_jobs(args.jobs), profile, args.today), indent=2))


if __name__ == "__main__":
    main()
