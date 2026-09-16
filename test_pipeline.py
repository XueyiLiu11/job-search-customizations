import unittest
from datetime import date

from pipeline import assess, canonical_url, shortlist


PROFILE = {
    "locations": ["New York", "Long Island City"],
    "target_roles": ["Data Analyst", "Financial Analyst"],
    "skills": ["SQL", "Python"],
    "max_required_years": 3,
    "exclude_titles": ["Senior"],
    "resume_routes": {"finance": ["Financial Analyst"]},
    "already_applied_urls": [],
}
TODAY = date(2026, 9, 16)


def job(**overrides):
    result = {
        "company": "Acme",
        "title": "Data Analyst",
        "location": "New York, NY",
        "description": "Use SQL and Python. 2+ years of experience.",
        "url": "https://example.org/role?utm_source=board",
        "posted_at": "2026-09-15",
        "date_source": "employer",
    }
    result.update(overrides)
    return result


class PipelineTests(unittest.TestCase):
    def test_verified_recent_date(self):
        self.assertEqual(assess(job(), PROFILE, TODAY)["recency"], "within_7_days")
        self.assertEqual(assess(job(date_source="board"), PROFILE, TODAY)["recency"], "unverified")

    def test_opt_exclusion_but_no_h1b_warning(self):
        self.assertTrue(assess(job(description="OPT candidates are not eligible."), PROFILE, TODAY)["excluded"])
        result = assess(job(description="No future H-1B sponsorship."), PROFILE, TODAY)
        self.assertFalse(result["excluded"])
        self.assertTrue(result["warnings"])

    def test_title_and_location_filters(self):
        self.assertTrue(assess(job(title="Senior Data Analyst"), PROFILE, TODAY)["excluded"])
        self.assertTrue(assess(job(location="Boston, MA"), PROFILE, TODAY)["excluded"])

    def test_deduplicate_tracking_links(self):
        jobs = [job(), job(url="https://example.org/role?utm_medium=email")]
        self.assertEqual(len(shortlist(jobs, PROFILE, TODAY)), 1)
        self.assertEqual(canonical_url(jobs[0]["url"]), "https://example.org/role")

    def test_resume_routing(self):
        result = assess(job(title="Financial Analyst"), PROFILE, TODAY)
        self.assertEqual(result["resume_route"], "finance")

    def test_future_date_is_not_recent(self):
        self.assertEqual(assess(job(posted_at="2026-09-17"), PROFILE, TODAY)["recency"], "older")

    def test_already_applied_url_is_suppressed(self):
        profile = {**PROFILE, "already_applied_urls": ["https://example.org/role?ref=email"]}
        self.assertEqual(shortlist([job()], profile, TODAY), [])

    def test_explicit_opt_restriction_is_not_shortlisted(self):
        restricted = job(description="STEM OPT candidates are not considered.")
        self.assertEqual(shortlist([restricted], PROFILE, TODAY), [])


if __name__ == "__main__":
    unittest.main()
