# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KLAR** is an async Telegram bot for selling VPN subscriptions, integrated with the **Remnawave** panel. It supports multiple payment providers (YooKassa, FreeKassa, CryptoPay, Platega, SeverPay, Telegram Stars), referral programs, promo codes, trial periods, and admin tools.

## Commands

```bash
# Install dependencies
uv sync
# or
pip install -r requirements.txt

# Run locally (requires .env)
python main.py

# Docker Compose (standard)
docker compose up -d
docker compose logs -f remnawave-tg-shop

# Database migrations (also run automatically on startup)
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "description"
```

There is no automated test suite. Testing is done manually through Docker Compose with a live database.

## Architecture

**Entry point:** `main.py` → `app/main_bot.py` (bot init, middleware/router registration, webhook server start)

**Layers:**

| Layer | Location | Purpose |
|---|---|---|
| Handlers | `app/handlers/` | Telegram message/callback handlers (user + admin) |
| Services | `app/services/` | Business logic, payment integrations, Remnawave API |
| DAL | `app/database/dal/` | Data Access Layer — all DB queries |
| Models | `app/database/models.py` | SQLAlchemy ORM models |
| Keyboards | `app/keyboards/inline/` | Inline keyboard builders |
| Middlewares | `app/middlewares/` | i18n, ban check, channel subscription, DB session, action logging |
| States | `app/states/` | Aiogram FSM states for multi-step dialogs |
| Web | `app/app/web/` | aiohttp webhook routes for payment providers and Telegram |

**Service factory:** `app/app/factories/build_services.py` instantiates all services at startup.

**Payment flow:** User selects plan → bot creates payment via provider → provider POSTs webhook to `/webhook/<provider>` → `app/handlers/` processes confirmation → DB updated → Remnawave panel synced via `PanelApiService`.

**Key services:**
- `panel_api_service.py` — Remnawave panel REST API integration
- `subscription_service.py` — central subscription creation/renewal logic
- `referral_service.py` / `promo_code_service.py` — discount systems
- `notification_service.py` — admin/user Telegram notifications

## Configuration

Configuration is managed by Pydantic Settings in `app/config.py` (100+ env vars). See `.env.example` for the full list. Critical variables:

- `BOT_TOKEN` — Telegram bot token
- `ADMIN_IDS` — comma-separated Telegram user IDs
- `WEBHOOK_BASE_URL` — public domain (polling mode is disabled; webhooks are required)
- `POSTGRES_*` — PostgreSQL connection (default port 5433 in Docker Compose)
- `PANEL_API_URL`, `PANEL_API_KEY` — Remnawave panel access
- `YOOKASSA_*`, `FREEKASSA_*`, `CRYPTOPAY_*`, `PLATEGA_*`, `SEVERPAY_*`, `STARS_*` — payment provider credentials and toggles
- `TRIAL_*`, `REFERRAL_*` — feature configuration

## Database

PostgreSQL 17 + SQLAlchemy 2.0 async + asyncpg. Alembic migrations run automatically on startup via `init_db()` in `main.py`.

Key tables: `users`, `subscriptions`, `payments`, `promo_codes`, `user_payment_methods`, `user_billing`, `message_logs`, `promo_code_activations`, `active_discounts`.

## Localization

Russian and English strings are in `assets/locales/`. The `i18n` middleware (`app/middlewares/i18n.py`) injects the translator into handler context. Use `_("key")` pattern in handlers.

## Tech Stack

- Python 3.12, Aiogram 3.x, aiohttp
- SQLAlchemy 2.0 async + asyncpg + Alembic
- Pydantic v2 (pydantic-settings)
- Docker + Docker Compose
