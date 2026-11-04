# Renewly

An internal admin app for ZcaleUp to manage its ERP clients, subscriptions, licences, payments and renewals.

**Live app:** https://renewly-hwbl.onrender.com

Test login details are provided with the submission. The app runs on Render's free tier, so the first request after a quiet period can take up to a minute.

## Features

- **Clients:** add, edit and view clients, with generated `CL-001` codes and an Active, Inactive or Suspended status. Each client has a profile with its subscriptions and payment history.
- **Subscriptions:** plans, dates, amounts, and licensed, active and available users. Subscriptions can be renewed or cancelled, and each renewal links back to the previous term.
- **Payments:** record several payments per subscription by UPI, NEFT, card, cheque or cash, with balances and full history.
- **Dashboard:** finance, client and subscription figures, plus charts for monthly revenue and subscriptions by status.
- **Alerts:** subscriptions expiring within 30 days, expired, or renewing in 31–90 days, plus overdue and pending payments.
- **Search and filters:** search clients by name, filter clients by status or payment status, and filter subscriptions by status or expiry date. Subscriptions can also be sorted by expiry.
- **Validation:** rejects invalid dates, negative amounts, licence overuse, overpayment, future-dated payments and duplicate transaction references.

## Tech stack

| Area | Technology |
|---|---|
| Backend | Python 3.13, Django 6.1 |
| Frontend | Django templates, Bootstrap 5, Bootstrap Icons, Chart.js |
| Database | PostgreSQL on Neon in production, SQLite locally |
| Hosting | Render, gunicorn, WhiteNoise |

## Run it locally

You need Python 3.13.

```bash
git clone https://github.com/searaaman/renewly.git
cd renewly
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in with the superuser you created.

`seed_demo` loads 15 sample clients, 16 subscriptions and 19 payments. Dates are relative to the day you run it, so every status appears. It does nothing if the sample data is already loaded.

## Configuration

Local development needs no environment variables. Production uses:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Set to `false` in production |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | Test login, created or reset on each deploy |

## Deployment

Render reads `render.yaml` and deploys each push to `main`. `build.sh` installs dependencies, collects static files, runs migrations, creates the login and loads the sample data.

## Project structure

```
clients/         Client records and profiles
subscriptions/   Plans, subscriptions, renewals, status rules
payments/        Payment records and balances
dashboard/       Dashboard, alerts, sample data command
config/          Settings, URLs, shared form base, number format
templates/       Base layout and login page
docs/            Market research
```

Dependencies run one way: `payments` → `subscriptions` → `clients`. The dashboard only reads from them and has no models of its own.

## How it works

Only facts and human decisions are stored. Everything else is calculated when it's needed, so it can't go out of sync:

- **Subscription status** comes from the dates and the cancelled and activated fields.
- **Payment status** comes from the payment total, the subscription amount and the due date.
- **Available licences** are licensed users minus active users.

Key rules are also enforced by the database: the end date must follow the start date, active users can't exceed licensed users, and non-blank transaction references must be unique.

## Known limitations

- **Reminders:** alerts appear on screen, and no emails are sent.
- **Invoicing:** the app doesn't issue GST invoices. This is intentional, as explained in the market research.
- **Payment corrections:** these go through the Django admin panel at `/admin`.
- **Payment gateway:** payments are recorded manually, and no gateway is connected.
- **Concurrent payments:** two people paying into the same subscription at the same moment could get past the overpayment check.
- **Status filters:** these run in Python rather than SQL, which is fine at this scale but would need changing for thousands of subscriptions.
- **Automated tests:** the repo has none yet. Flows have been tested manually.
