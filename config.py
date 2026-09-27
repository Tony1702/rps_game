import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

IDENTITY_DATABASE_PATH = Path(
    os.getenv(
        "IDENTITY_DATABASE_PATH",
        BASE_DIR / "data" / "identity.db"
    )
)

VOTING_DATABASE_PATH = Path(
    os.getenv(
        "VOTING_DATABASE_PATH",
        BASE_DIR / "data" / "voting.db"
    )
)

IDENTITY_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
VOTING_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "Falta TELEGRAM_BOT_TOKEN. Copia .env.example como .env y coloca el token."
    )

ADMIN_TELEGRAM_USER_ID = os.getenv("ADMIN_TELEGRAM_USER_ID")

if not ADMIN_TELEGRAM_USER_ID:
    raise RuntimeError(
        "Falta ADMIN_TELEGRAM_USER_ID en el archivo .env."
    )