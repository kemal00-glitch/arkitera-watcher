# Arkitera Kariyer Job Watcher

Watches https://www.arkitera.com/kariyer/ and emails you whenever a new job
posting appears. Runs automatically every hour on GitHub's free servers —
your computer doesn't need to be on.

## How it works

- `scraper.py` fetches the career page and pulls out every job posting link.
- It compares that list against `seen_jobs.json` (the jobs it's seen before).
- Anything new gets emailed to you, then gets added to `seen_jobs.json`.
- `.github/workflows/check-jobs.yml` runs `scraper.py` every hour and
  commits the updated `seen_jobs.json` back to the repo, so state carries
  over between runs.

**First run:** it saves the ~100 jobs currently on the site as a baseline
and does **not** email you — otherwise you'd get one huge email listing
every job that already exists. From the second run onward, you'll only
hear about genuinely new postings.

## Setup (10 minutes)

### 1. Create a GitHub repository

Create a new **private** repository on GitHub, then upload all the files
in this folder, keeping the folder structure exactly as-is (the
`.github/workflows/check-jobs.yml` path matters — GitHub only recognizes
workflows in that exact location).

### 2. Create a Gmail App Password

You'll send the notification email from a Gmail account using an "App
Password" (a 16-character code, not your real Gmail password — Google
requires this for scripts).

1. Go to your Google Account → **Security**.
2. Turn on **2-Step Verification** if it isn't already on.
3. Go to **Security → 2-Step Verification → App passwords**
   (or search "App Passwords" in your Google Account settings).
4. Create one (name it something like "arkitera-watcher") and copy the
   16-character password shown.

*(Using a different email provider? The script uses Gmail's SMTP server —
swap `smtp.gmail.com` in `scraper.py` for your provider's SMTP host and
adjust accordingly.)*

### 3. Add secrets to your GitHub repo

In your repo: **Settings → Secrets and variables → Actions → New
repository secret**. Add three:

| Secret name     | Value                                              |
|------------------|-----------------------------------------------------|
| `MAIL_USERNAME`  | Your Gmail address                                  |
| `MAIL_PASSWORD`  | The 16-character App Password from step 2           |
| `MAIL_TO`        | Where you want the alerts sent (can be the same address, or a different inbox) |

### 4. Test it

Go to the **Actions** tab in your repo → **Arkitera Job Watcher** →
**Run workflow**. This does the first (baseline) run. Check the run's log
to confirm it says something like "First run: saved 100 existing jobs as
baseline."

After that, run it manually once more — if nothing's changed on the site
you'll see "No new jobs." From here it just runs itself every hour.

## Adjusting the check frequency

Edit the `cron` line in `.github/workflows/check-jobs.yml`. Some examples:

- Every 30 minutes: `*/30 * * * *`
- Every 6 hours: `0 */6 * * *`
- Once a day at 9am UTC: `0 9 * * *`

GitHub Actions cron schedules can run a few minutes late during busy
periods — that's expected and not a bug.

## Notes / limitations

- Only checks page 1 of the listings, which is where new postings appear
  first (the site orders by newest by default). If Arkitera changes their
  page layout significantly, the scraper may need updating — if it stops
  finding jobs, the workflow log will say so explicitly.
- If you'd rather monitor another Turkish architecture magazine's career
  page too, this can be extended to check multiple URLs in the same run —
  just ask and I can add that.
