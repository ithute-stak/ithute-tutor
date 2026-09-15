# Ithute Tutor

Ithute Tutor is a standalone, multi-tenant school management and learning system.

## Architecture boundary

Until this repository is deliberately integrated with another service, Tutor owns its own:

- user accounts and authentication;
- access and refresh sessions;
- PostgreSQL database and migrations;
- school tenancy and authorization;
- in-app notifications;
- runtime configuration;
- deployment and infrastructure configuration.

Tutor must not import code, read databases, rely on authentication, share sessions, or require deployment services from another Ithute product. Product-specific third-party integrations such as M-Pesa may be added directly to Tutor when required.

## Current application layout

- `sms_back_end/` — FastAPI backend and Tutor database models.
- `sms-frontend/` — Next.js frontend.
- `.env.example` — Tutor-only runtime configuration template.

Deployment scripts are intentionally absent. They will be designed again for this repository as a standalone deployment when that phase begins.
