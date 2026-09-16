# Job Search Customizations

An independent, standard-library Python example of a personalized job shortlist.
It captures the candidate-side workflow improvements I wanted: location and
seniority filters, verified seven-day recency, duplicate suppression, OPT/STEM
OPT screening, and resume routing. It does **not** contain or reproduce the
private upstream application, and it never submits applications.

## Run

```bash
python3 pipeline.py example_jobs.jsonl --profile profile.example.json --today 2026-09-16
python3 -m unittest -v
```

Input is JSON Lines with `company`, `title`, `location`, `description`, and
`url`. Include `posted_at` and `date_source` for recency. Only publication
dates verified from an employer or ATS are labeled `within_7_days`; board
scrape/update dates remain `unverified`.

The included employers and URLs are fictional. Keep real profiles, resumes,
credentials, and application logs out of version control. A no-H-1B statement
is a warning, not an automatic OPT rejection; explicit OPT/STEM OPT exclusion
is a hard block. Always review work authorization questions personally and
answer them truthfully.
