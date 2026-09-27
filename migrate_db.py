import sqlite3

from config import DATABASE_PATH


def migrate():
    conn = sqlite3.connect(DATABASE_PATH)

    try:
        conn.execute("PRAGMA foreign_keys = OFF")

        # 1. Crear las nuevas tablas.
        conn.executescript("""
        CREATE TABLE participants_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            voting_credential TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE votes_new (
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

        # 2. Migrar participantes.
        conn.execute("""
            INSERT INTO participants_new (
                id,
                telegram_user_id,
                voting_credential,
                created_at
            )
            SELECT
                id,
                telegram_user_id,
                anonymous_id,
                created_at
            FROM participants
        """)

        # 3. Migrar votos.
        conn.execute("""
            INSERT INTO votes_new (
                id,
                voting_credential,
                commitment,
                revealed_vote,
                revealed_nonce,
                verified,
                created_at,
                revealed_at
            )
            SELECT
                id,
                anonymous_id,
                commitment,
                revealed_vote,
                revealed_nonce,
                verified,
                created_at,
                revealed_at
            FROM votes
        """)

        # 4. Reemplazar las tablas antiguas.
        conn.execute("DROP TABLE votes")
        conn.execute("DROP TABLE participants")

        conn.execute(
            "ALTER TABLE participants_new RENAME TO participants"
        )

        conn.execute(
            "ALTER TABLE votes_new RENAME TO votes"
        )

        conn.commit()

        print("Migración completada correctamente.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()