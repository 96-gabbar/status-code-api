# W3-06 Portfolio migrations evidence

Date: 12 November 2026

- Independent configuration: `portfolio_alembic.ini`
- Independent migration tree: `portfolio_alembic/`
- Independent version table: `portfolio_alembic_version`
- Dedicated database used for validation: `portfolio_service`
- Live `upgrade head`: passed.
- Live `downgrade base`: passed.
- Live re-upgrade to head: passed.
- Current revision: `20261112_0001 (head)`.
