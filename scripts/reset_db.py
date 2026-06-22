import os
import pathlib

DB_PATH = pathlib.Path(__file__).parent.parent / "offer_radar.db"

if DB_PATH.exists():
    os.remove(DB_PATH)
    print(f"Removed database at {DB_PATH}")
else:
    print(f"Database at {DB_PATH} not found.")
