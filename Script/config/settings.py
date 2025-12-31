from pathlib import Path

# base
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# directories
CHECKIN_DIR = BASE_DIR / "checkin"
MEDIA_DIR   = BASE_DIR / "media"
MONOQLO_DIR = BASE_DIR / "monoqlo"
TEMP_DIR = BASE_DIR / "temp"
THUMBNAIL_DIR = BASE_DIR / "thumbnail"

# database
VIDEO_DB_PATH = BASE_DIR / "database" / "videos.db"
MEDIA_DB_PATH  = BASE_DIR / "database" / "media.db"
