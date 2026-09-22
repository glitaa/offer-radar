# Offer-Radar Roadmap

Offer-Radar is a local aggregator of classifieds listings, built with Clean Architecture to support CLI workflows today and seamless GUI transitions in the future.

---

## Completed Capabilities

### ✅ Core Aggregation & Initial CLI (June 2026)
- Scraper for OLX.pl (Jobs & Real Estate).
- SQLite storage for retrieved listings.
- Fundamental CLI for syncing and viewing offers.

### ✅ Offer Deduplication & Structured Pricing (June 2026)
- Offer hash and URL deduplication to filter previously seen listings.
- Structured pricing domain model (`OfferPrice`) with currency, total, and per-sqm calculations.
- Rate offers with user status tracking (Save, Reject, Skip).

### ✅ Interactive CLI Entry Point (July 2026)
- Migration of main entry point to Typer with Questionary interactive menus.
- Support for managing search sessions (create new search, list existing, run, delete with cascade).
- Interactive browsing loop with formatted terminal output (`rich`).

### ✅ Settings & Localization (July 2026)
- Domain settings model with TOML storage (`config.toml`).
- Full internationalization (i18n) via Babel with English and Polish locale catalogs.
- Dynamic interactive Settings menu (language toggle, browser auto-open preferences).

### ✅ Maintenance & CI/CD (July 2026)
- Cross-platform keyboard input handling using `click`.
- GitHub Actions CI workflow (ruff linter/formatter, pytest, babel translation check).
- Automated dependency maintenance via Dependabot and `uv`.

---

## Upcoming Initiatives

### 🎯 Scraper Extensibility & Portal Expansion
- [ ] Abstract scraper interface into pluggable portal modules (`BasePortalScraper`).
- [ ] Implement additional portals (e.g., Otodom, Gratka, NoFluffJobs).
- [ ] Configurable request throttling, user-agent rotation, and robust error recovery.

### 🎯 Advanced Filtering & Query Presets
- [ ] Flexible criteria filtering (price range, price per m², location radius, excluded keywords).
- [ ] Saved search presets with custom refresh intervals.
- [ ] Offer status filtering in CLI (review rejected or saved offers, re-evaluate).

### 🎯 Notification Dispatcher
- [ ] Background scheduled scans for saved search sessions.
- [ ] Instant notification channels for new matching listings (Desktop OS notifications, Telegram bot, webhook).

### 🎯 Desktop GUI Application
- [ ] Dedicated desktop presentation layer (e.g. PySide6 / PyQt or lightweight local web dashboard).
- [ ] Reuses existing `domain` and `application` layers without modification.
- [ ] Split-view offer inspector, embedded image previews, and direct one-click rating.
