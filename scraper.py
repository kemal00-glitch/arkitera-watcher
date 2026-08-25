"""
Arkitera Kariyer (career page) watcher.

Checks https://www.arkitera.com/kariyer/ for new job postings and emails
you when new ones appear. Designed to be run on a schedule (see the
GitHub Actions workflow in .github/workflows/check-jobs.yml), but you can
also run it locally with `python scraper.py`.

State (which jobs we've already seen) is kept in seen_jobs.json, sitting
next to this script.
"""

import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.arkitera.com/kariyer/"
STATE_FILE = Path(__file__).parent / "seen_jobs.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_jobs():
    """Return a list of {title, url} dicts for jobs currently listed on page 1."""
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = {}
    prefix = "https://www.arkitera.com/kariyer/"
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # Job posting permalinks look like https://www.arkitera.com/kariyer/<slug>/
        # Pagination links look like .../kariyer/page/2/ -- those get skipped.
        if not href.startswith(prefix):
            continue
        remainder = href[len(prefix):].strip("/")
        if not remainder or remainder.startswith("page"):
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        jobs.setdefault(href, title)  # keep first non-empty title seen for a URL

    return [{"title": t, "url": u} for u, t in jobs.items()]


def load_seen():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return None  # None means "first run, no baseline yet"


def save_seen(urls):
    STATE_FILE.write_text(
        json.dumps(sorted(urls), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def send_email(new_jobs):
    username = os.environ["MAIL_USERNAME"]
    password = os.environ["MAIL_PASSWORD"]
    to_addr = os.environ.get("MAIL_TO", username)

    lines = [f"{j['title']}\n{j['url']}\n" for j in new_jobs]
    body = (
        f"{len(new_jobs)} new job posting(s) on Arkitera Kariyer:\n\n"
        + "\n".join(lines)
        + f"\nFull page: {URL}"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"Arkitera Kariyer: {len(new_jobs)} new job(s)"
    msg["From"] = username
    msg["To"] = to_addr

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(username, [to_addr], msg.as_string())


def main():
    try:
        current_jobs = fetch_jobs()
    except requests.RequestException as e:
        print(f"Failed to fetch page: {e}", file=sys.stderr)
        sys.exit(1)

    if not current_jobs:
        print(
            "No job links found on the page -- the site structure may have "
            "changed and the scraper needs updating.",
            file=sys.stderr,
        )
        sys.exit(1)

    current_urls = {j["url"] for j in current_jobs}
    seen_urls = load_seen()

    if seen_urls is None:
        # First run: just establish a baseline. Without this, you'd get one
        # giant email listing every job currently on the site.
        save_seen(current_urls)
        print(f"First run: saved {len(current_urls)} existing jobs as baseline. No email sent.")
        return

    new_urls = current_urls - set(seen_urls)

    if new_urls:
        new_jobs = [j for j in current_jobs if j["url"] in new_urls]
        print(f"Found {len(new_jobs)} new job(s). Sending email...")
        send_email(new_jobs)
    else:
        print("No new jobs.")

    save_seen(current_urls)


if __name__ == "__main__":
    main()
