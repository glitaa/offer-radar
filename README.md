# Offer Radar

[![CI](https://github.com/glitaa/offer-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/glitaa/offer-radar/actions/workflows/ci.yml)

Offer Radar is a local command-line tool that helps you review classifieds listings without repeatedly processing offers you have already seen. It fetches listings, stores your decisions locally, and presents unseen offers for review, making recurring searches faster and easier to manage.

Currently supports: **OLX.pl** (Jobs and Real Estate)

## Motivation

I originally built Offer Radar while searching for accommodation. Repeatedly encountering the same listings made it annoying and time-consuming to identify new offers.

Offer Radar solved that problem by keeping a local history of my decisions and showing me unreviewed listings. I used the tool to process hundreds of offers and eventually find a suitable room.

## Features
- **Interactive CLI:** Quickly review listings directly in your terminal.
- **Cross-platform:** Works natively on Windows, macOS, and Linux.
- **Local Database:** Stores which listings were saved, rejected or temporarily skipped.
- **Search Sessions**: Preserve progress separately for different searches and resume them later.
- **Multi-language Support:** The interface is currently available in English and Polish.

## Demo

```text
$ uv run offer-radar --query "pokój kraków"
Starting session for: pokój kraków
  Syncing offers... (Found 520 offers so far) ━━ 100% 0:00:50
╭─────────── Pokój jednoosobowy Kraków Bronowice ───────────╮
│ Price: 1200.00 PLN                                        │
│ Location: Małopolskie, Kraków, Bronowice                  │
│ URL: https://www.olx.pl/d/oferta/pokoj...                 │
│                                                           │
│ (s) Save  (r) Reject  (k) Skip  (q) Quit                  │
╰───────────────────────────────────────────────────────────╯
```

## Prerequisites
- [uv](https://github.com/astral-sh/uv) installed on your system (Python is managed automatically by uv).

## Getting Started

Clone the repository:

```bash
git clone https://github.com/glitaa/offer-radar.git
cd offer-radar
```

Display the available commands:

```bash
uv run offer-radar --help
```

Start a search:

```bash
uv run offer-radar --query "pokój kraków"
```

On the first run, `uv` automatically downloads the required Python version and installs dependencies before starting the application.

## Usage

You can run the application without arguments to open the interactive main menu, which allows you to resume previous sessions, configure settings, or start new searches:

```bash
uv run offer-radar
```

Alternatively, you can bypass the menu and start a session directly using a search query or a direct OLX URL:

```bash
# Search by query
uv run offer-radar --query "python developer kraków"

# Search using an OLX search URL
uv run offer-radar --url "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/krakow/?search%5Bfilter_float_price%3Ato%5D=3000"
```

*Query-based searches use the default OLX search configuration. For category, location, price and other advanced filters, configure the search on OLX and pass the resulting URL using `--url`.*

The application fetches the matching listings, filters out offers that have already been reviewed and presents the first unseen listing.

### Keyboard controls
- `(s) Save`: Marks the listing as saved in your local database.
- `(r) Reject`: Marks the listing as rejected and hides it from future sessions.
- `(k) Skip`: Skips the listing for now (it may appear again in future sessions).
- `(q) Quit`: Exits the current review session.

## Technology Stack

- **Language**: [Python](https://www.python.org/) managed by [uv](https://github.com/astral-sh/uv)
- **CLI & UI**: [Typer](https://typer.tiangolo.com/) for commands, [Questionary](https://questionary.readthedocs.io/) for interactive menus, [Rich](https://rich.readthedocs.io/) for terminal output, and [Click](https://click.palletsprojects.com/) for cross-platform single-key input.
- **Web Scraping**: [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) and [HTTPX](https://www.python-httpx.org/) (for asynchronous requests).
- **Database**: [SQLite](https://www.sqlite.org/) with [SQLAlchemy](https://www.sqlalchemy.org/) and `aiosqlite` for asynchronous database operations.
- **Testing**: [pytest](https://docs.pytest.org/) and `pytest-asyncio`.
- **Linting & Formatting**: [Ruff](https://docs.astral.sh/ruff/) for blazingly fast Python linting and formatting.
- **Localization**: [Babel](https://babel.pocoo.org/) for managing and compiling translation files.
- **CI/CD**: GitHub Actions (for automated tests, linting, and translation integrity checks) and Dependabot.

## Architecture

The application separates domain models and repository interfaces from application services and infrastructure implementations. This ensures the core workflow remains independent of SQLite, SQLAlchemy, and the scraper.

The codebase is structured as follows:

- [src/domain](src/domain) – models, rules, and repository interfaces,
- [src/application](src/application) – search synchronization and session workflows,
- [src/infrastructure](src/infrastructure) – database, settings and scraper implementations,
- [src/cli](src/cli) – commands, menus and terminal presentation.

## Development

To run the automated test suite, use `uv` to execute `pytest`:

```bash
uv run pytest
```

To run the linter and code formatter:

```bash
uv run ruff check .
uv run ruff format .
```

To compile the latest translation files:

```bash
uv run pybabel compile -d locales
```

## Data Storage

Offer Radar stores its data locally in an SQLite database named `offer_radar.db`, located in the directory from which you run the application.

The database stores:
- **Offers**: Basic details of the listings you have processed (ID, URL, status).
- **Search Sessions**: Your progress for specific URLs or queries, ensuring you don't review the same offers again.

**Resetting Data:**
To reset all your data and start fresh, simply delete the `offer_radar.db` file:
```bash
rm offer_radar.db
```

## Roadmap

- [x] Interactive CLI listing review
- [x] Local database persistence
- [x] Offer deduplication via content fingerprinting
- [x] Search session management
- [x] In-app settings
- [x] Multi-language support (English/Polish)
- [x] Cross-platform compatibility
- [ ] Web interface
- [ ] Semantic analysis of descriptions
- [ ] Advanced filtering
- [ ] Additional classifieds sources

## Responsible Use

Offer Radar is intended for personal and educational use. Use it responsibly, avoid excessive request rates, and make sure your usage complies with the terms and policies of the supported platform.

To reduce load on the supported platform, requests are sent sequentially with random delays. Transient network failures are retried with exponential backoff, and synchronization stops gracefully after an HTTP 429 response while preserving listings collected so far.

## License

This project is available under the MIT License. See [LICENSE](LICENSE) for details.