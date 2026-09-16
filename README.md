# Job Search Customizations

A small, independent Python project that turns a JSON Lines file of job postings into a personalized shortlist. It is designed to make a candidate's manual review faster and more consistent—not to collect jobs, decide work authorization, or submit applications automatically.

## At a glance

| Candidate-side problem | What this demo does |
| --- | --- |
| Repeated or already-applied postings | Normalizes common tracking parameters and suppresses duplicate URLs |
| Stale or uncertain posting dates | Labels a posting `within_7_days` only when its supplied publication date is marked as coming from an employer or ATS; otherwise labels it `unverified` or `older` |
| Roles outside a target search | Filters by preferred locations and excluded seniority terms, then ranks remaining roles by title, skills, and recency |
| Work-authorization ambiguity | Flags explicit OPT/STEM OPT restrictions for exclusion and treats no-sponsorship language as a warning for human review |
| Multiple resume versions | Suggests a resume route from role-title rules in the profile |

The output is a ranked JSON shortlist with a score, recency label, matched skills, resume route, and warnings. Scores are simple rule-based priorities, **not** a prediction of hiring or eligibility.

## Implementation and project scope

This repository implements filtering, URL normalization, recency labeling, authorization warnings, scoring, and resume routing in standard-library Python, together with fictional sample data and unit tests. It is an independent demonstration of candidate-side workflow ideas. It does **not** contain or reproduce a private upstream application, and it has no live job-board or employer integration.

## Try it

Requires Python 3.10 or newer; no third-party packages or API keys are needed.

```bash
python3 pipeline.py example_jobs.jsonl --profile profile.example.json --today 2026-09-16
python3 -m unittest -v
```

The sample run returns two shortlisted postings. `Example Analytics` is labeled `within_7_days`; `Example Finance` remains `unverified` because its date source is a job board, and it carries a sponsorship warning. The fictional posting that explicitly excludes OPT candidates is removed. The example uses a fixed date so the result is reproducible.

## Input and output

Each line of the jobs file is one JSON object. Required fields for a usable result are `company`, `title` (or `role`), `location`, `description`, and `url`. Optional `posted_at` is an ISO-format date; `date_source` can be `employer` or `ats` for the seven-day recency label. A date marked `job_board` is not treated as a verified publication date. The program trusts the supplied source label; it does not independently check the employer website.

The profile JSON controls preferred `locations`, `target_roles`, `skills`, `max_required_years`, `exclude_titles`, `resume_routes`, and `already_applied_urls`. The included `profile.example.json` is fictional and safe to edit locally. Output goes to standard output as JSON, so it can be saved or inspected without sending data to a service.

## Privacy and limitations

- All sample employers and URLs are fictional. Do not commit real resumes, personal profiles, credentials, application logs, or third-party job data you are not authorized to publish.
- This tool does not scrape job boards, verify dates against live websites, contact employers, or apply on anyone's behalf.
- The OPT/STEM OPT and sponsorship checks use phrase matching. They can miss unusual wording or flag language that needs context. A no-H-1B statement is **not** an automatic OPT rejection. Always review work-authorization questions personally and answer them truthfully; this tool is not legal advice.
- Role matching and scores are intentionally simple and may not fit a particular job search without changing the profile rules. Review every shortlisted job before applying.
