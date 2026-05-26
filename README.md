# Job Application Tracker

Terminal UI to track every job you apply to.

## Run

```bash
cd Projects/Career/job_tracker
python3 tracker.py
```

## Commands

| Key | Action |
|-----|--------|
| `a` | Add a new application |
| `u` | Update status + optional note |
| `s` | Search by company / role / notes |
| `f` | Filter by status |
| `d` | Delete an entry |
| `q` | Quit |
| Enter | List all applications |

## Statuses

Applied → Phone Screen → Interview → Final Round → Offer / Rejected / Withdrawn

Data is stored in `applications.json` next to the script.
