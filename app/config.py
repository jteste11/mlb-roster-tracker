import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import date

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Folder where daily folders will be created
DATA_ROOT = Path(os.getenv("DATA_ROOT", BASE_DIR / "data"))

# SQLite DB path
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "roster_tracker.db"))

# MLB season (you can override via env if needed)
DEFAULT_SEASON = int(os.getenv("MLB_SEASON", date.today().year))

def get_today_folder(today: date | None = None) -> Path:
    if today is None:
        today = date.today()
    folder = DATA_ROOT / today.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    return folder