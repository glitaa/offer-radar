import pathlib

DB_PATH = pathlib.Path(__file__).parent.parent / "data" / "offer_radar.db"

if DB_PATH.exists():
    DB_PATH.unlink()
    print(f"Removed database at {DB_PATH}")
else:
    print(f"Database at {DB_PATH} not found.")
