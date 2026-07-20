from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.parent

DATA_DIR = BASE_DIR / "data"

DATABASE_DIR = DATA_DIR / "database"
DB_FILE = DATABASE_DIR / "db.sqlite3"
AGENT_DB_FILE = DATABASE_DIR / "agent_db.sqlite3"

SECRETS_DIR = BASE_DIR / "secrets"
ENV_FILE = SECRETS_DIR / ".env"

LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

ATTACHMENTS_DIR = BASE_DIR / "attachments"

if not DATABASE_DIR.exists():
    DATABASE_DIR.mkdir(parents=True)
if not SECRETS_DIR.exists():
    SECRETS_DIR.mkdir(parents=True)
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir(parents=True)
if not ATTACHMENTS_DIR.exists():
    ATTACHMENTS_DIR.mkdir(parents=True)
