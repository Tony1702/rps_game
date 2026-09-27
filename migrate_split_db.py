import sqlite3
from pathlib import Path

from config import DATABASE_PATH


BASE_DIR = Path(__file__).resolve().parent
IDENTITY_DB_PATH = BASE_DIR / "data" / "identity.db"
VOTING_DB_PATH = BASE_DIR / "data" / "voting.db"


def migrate():
    source = sqlite3.connect(DATABASE_PATH)
    identity = sqlite3.connect(IDENTITY_DB_PATH)
    voting = sqlite3.connect(VOTING_DB_PATH)

    try:
        # Base de identidad
        identity.executescript("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            voting_credential TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Base de votación
        voting.executescript("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voting_credential TEXT UNIQUE NOT NULL,
            commitment TEXT NOT NULL,
            revealed_vote INTEGER,
            revealed_nonce TEXT,
            verified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            revealed_at TEXT
        );
        """)

        # Copiar participantes
        participants = source.execute("""
            SELECT
                id,
                telegram_user_id,
                voting_credential,
                created_at
            FROM participants
        """).fetchall()

        identity.executemany("""
            INSERT OR IGNORE INTO participants (
                id,
                telegram_user_id,
                voting_credential,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, participants)

        # Copiar votos
        votes = source.execute("""
            SELECT
                id,
                voting_credential,
                commitment,
                revealed_vote,
                revealed_nonce,
                verified,
                created_at,
                revealed_at
            FROM votes
        """).fetchall()

        voting.executemany("""
            INSERT OR IGNORE INTO votes (
                id,
                voting_credential,
                commitment,
                revealed_vote,
                revealed_nonce,
                verified,
                created_at,
                revealed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, votes)

        identity.commit()
        voting.commit()

        print("Migración separada completada correctamente.")
        print(f"Participantes migrados: {len(participants)}")
        print(f"Votos migrados: {len(votes)}")

    except Exception:
        identity.rollback()
        voting.rollback()
        raise

    finally:
        source.close()
        identity.close()
        voting.close()


if __name__ == "__main__":
    migrate()