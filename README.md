# Offer Radar

Offer Radar is a local command-line aggregator of listings from classifieds websites. It fetches, filters, and allows you to rate listings so you only review new offers, saving you time.

Currently supports: **OLX.pl** (Jobs and Real Estate)

## Features
- **Interactive CLI:** Quickly review listings directly in your terminal.
- **Local Database:** Remembers which listings you have already seen, saved, or rejected.
- **Session Management:** Save your progress and resume your search at any time.

## Prerequisites
- Python 3.12+ installed on your system.

## Getting Started

1. Clone or download this repository.
2. Open a terminal in the repository folder.
3. Run the script for your OS:

**Windows:**
```cmd
.\offer-radar.bat --query "laptop"
```

**Linux / macOS:**
```bash
./offer-radar --query "laptop"
```

*(On the first run, the script will automatically create a virtual environment and install all required dependencies before starting the application.)*

## Usage

You can start a session using either a search query or a direct OLX URL:

```bash
# Search by query
./offer-radar --query "recepcjonista kraków"

# Search using a direct OLX URL (useful for complex filters)
./offer-radar --url "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/krakow/?search%5Bfilter_float_price%3Ato%5D=3000"
```

Once running, the application will fetch listings and present you with the first unseen one. Use the following keyboard shortcuts to manage listings:
- `(s) Save`: Marks the listing as saved in your local database.
- `(r) Reject`: Marks the listing as rejected (you won't see it again).
- `(k) Skip`: Skips the listing for now (you will see it again in future sessions).
- `(q) Quit`: Exits the application and saves your progress.
