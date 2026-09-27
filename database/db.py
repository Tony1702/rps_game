import sqlite3

from config import (
    IDENTITY_DATABASE_PATH,
    VOTING_DATABASE_PATH,
)


def connect_identity():
    conn = sqlite3.connect(IDENTITY_DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def connect_voting():
    conn = sqlite3.connect(VOTING_DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_identity() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            voting_credential TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

    with connect_voting() as conn:
        # Crear la tabla inicial si todavía no existe.
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voting_credential TEXT NOT NULL,
            commitment TEXT NOT NULL,
            revealed_vote INTEGER,
            revealed_nonce TEXT,
            verified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            revealed_at TEXT,
            round_number INTEGER NOT NULL DEFAULT 1
        );
        """)

        # --------------------------------------------------------
        # Migración de votos:
        # cambiar UNIQUE(voting_credential)
        # por UNIQUE(voting_credential, round_number)
        # --------------------------------------------------------

        columns = conn.execute(
            "PRAGMA table_info(votes)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        # La migración anterior ya agregó round_number.
        if "round_number" not in column_names:
            conn.execute(
                """
                ALTER TABLE votes
                ADD COLUMN round_number INTEGER NOT NULL DEFAULT 1
                """
            )

        # Comprobar si todavía existe la restricción UNIQUE
        # individual sobre voting_credential.
        indexes = conn.execute(
            "PRAGMA index_list(votes)"
        ).fetchall()

        has_old_unique = False

        for index in indexes:
            index_name = index["name"]
            is_unique = index["unique"]

            if not is_unique:
                continue

            index_columns = conn.execute(
                f'PRAGMA index_info("{index_name}")'
            ).fetchall()

            indexed_columns = [
                row["name"]
                for row in index_columns
            ]

            if indexed_columns == ["voting_credential"]:
                has_old_unique = True
                break

        if has_old_unique:
            conn.execute("BEGIN")

            try:
                conn.execute("""
                    CREATE TABLE votes_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        voting_credential TEXT NOT NULL,
                        commitment TEXT NOT NULL,
                        revealed_vote INTEGER,
                        revealed_nonce TEXT,
                        verified INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        revealed_at TEXT,
                        round_number INTEGER NOT NULL DEFAULT 1,
                        UNIQUE(voting_credential, round_number)
                    )
                """)

                conn.execute("""
                    INSERT INTO votes_new (
                        id,
                        voting_credential,
                        commitment,
                        revealed_vote,
                        revealed_nonce,
                        verified,
                        created_at,
                        revealed_at,
                        round_number
                    )
                    SELECT
                        id,
                        voting_credential,
                        commitment,
                        revealed_vote,
                        revealed_nonce,
                        verified,
                        created_at,
                        revealed_at,
                        round_number
                    FROM votes
                """)

                conn.execute("DROP TABLE votes")

                conn.execute(
                    "ALTER TABLE votes_new RENAME TO votes"
                )

                conn.commit()

            except Exception:
                conn.rollback()
                raise

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS voting_rounds (
                round_number INTEGER PRIMARY KEY,
                allowed_options TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('active', 'tie', 'winner')),
                winner INTEGER,
                tied_options TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );
            """)

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS voting_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                phase TEXT NOT NULL
                    CHECK (phase IN ('commitment', 'reveal', 'closed'))
            );

            INSERT OR IGNORE INTO voting_state (id, phase)
            VALUES (1, 'commitment');

            CREATE TABLE IF NOT EXISTS voting_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                round_number INTEGER NOT NULL,
                allowed_options TEXT NOT NULL
            );

            INSERT OR IGNORE INTO voting_config (
                id,
                round_number,
                allowed_options
            )
            VALUES (1, 1, '1,2,3');
            """)

        config = conn.execute(
            """
            SELECT round_number, allowed_options
            FROM voting_config
            WHERE id = 1
            """
        ).fetchone()

        if config:
            conn.execute(
                """
                INSERT OR IGNORE INTO voting_rounds (
                    round_number,
                    allowed_options,
                    status
                )
                VALUES (?, ?, 'active')
                """,
                (
                    config["round_number"],
                    config["allowed_options"],
                )
            )


# ============================================================
# IDENTIDAD
# ============================================================

def get_participant(telegram_user_id):
    with connect_identity() as conn:
        return conn.execute(
            """SELECT * FROM participants
               WHERE telegram_user_id = ?""",
            (telegram_user_id,)
        ).fetchone()


def create_participant(telegram_user_id, voting_credential):
    with connect_identity() as conn:
        conn.execute(
            """INSERT INTO participants
               (telegram_user_id, voting_credential)
               VALUES (?, ?)""",
            (telegram_user_id, voting_credential)
        )


def get_all_participants():
    with connect_identity() as conn:
        return conn.execute(
            """
            SELECT *
            FROM participants
            ORDER BY id
            """
        ).fetchall()

# ============================================================
# VOTACIÓN
# ============================================================

def save_commitment(voting_credential, commitment, round_number):
    with connect_voting() as conn:
        try:
            conn.execute(
                """
                INSERT INTO votes (
                    voting_credential,
                    commitment,
                    round_number
                )
                VALUES (?, ?, ?)
                """,
                (
                    voting_credential,
                    commitment,
                    round_number
                )
            )
            return True

        except sqlite3.IntegrityError:
            return False


def get_vote(voting_credential, round_number):
    with connect_voting() as conn:
        return conn.execute(
            """
            SELECT *
            FROM votes
            WHERE voting_credential = ?
              AND round_number = ?
            """,
            (
                voting_credential,
                round_number
            )
        ).fetchone()
    

def save_reveal(
    voting_credential,
    round_number,
    vote,
    nonce,
    verified
):
    if not verified:
        return

    with connect_voting() as conn:
        conn.execute(
            """
            UPDATE votes
            SET revealed_vote = ?,
                revealed_nonce = ?,
                verified = 1,
                revealed_at = CURRENT_TIMESTAMP
            WHERE voting_credential = ?
              AND round_number = ?
              AND verified = 0
            """,
            (
                vote,
                nonce,
                voting_credential,
                round_number
            )
        )


def reset_invalid_reveal(voting_credential, round_number):
    with connect_voting() as conn:
        conn.execute(
            """
            UPDATE votes
            SET revealed_vote = NULL,
                revealed_nonce = NULL,
                verified = 0,
                revealed_at = NULL
            WHERE voting_credential = ?
              AND round_number = ?
              AND verified = 0
            """,
            (
                voting_credential,
                round_number
            )
        )


def count_verified_votes(round_number):
    with connect_voting() as conn:
        rows = conn.execute(
            """
            SELECT revealed_vote,
                   COUNT(*) AS total
            FROM votes
            WHERE verified = 1
              AND round_number = ?
            GROUP BY revealed_vote
            ORDER BY revealed_vote
            """,
            (round_number,)
        ).fetchall()

        return [
            (row["revealed_vote"], row["total"])
            for row in rows
        ]


def get_voting_phase():
    with connect_voting() as conn:
        row = conn.execute(
            "SELECT phase FROM voting_state WHERE id = 1"
        ).fetchone()

        return row["phase"]


def set_voting_phase(phase):
    if phase not in {"commitment", "reveal", "closed"}:
        raise ValueError("Fase de votación no válida.")

    with connect_voting() as conn:
        conn.execute(
            """UPDATE voting_state
               SET phase = ?
               WHERE id = 1""",
            (phase,)
        )


def get_voting_config():
    with connect_voting() as conn:
        row = conn.execute(
            """SELECT round_number, allowed_options
               FROM voting_config
               WHERE id = 1"""
        ).fetchone()

        if not row:
            return None

        options = [
            int(option)
            for option in row["allowed_options"].split(",")
            if option
        ]

        return {
            "round_number": row["round_number"],
            "allowed_options": options,
        }


def get_current_round():
    config = get_voting_config()

    if not config:
        return 1

    return config["round_number"]


def save_round_result(
    round_number,
    status,
    winner=None,
    tied_options=None
):
    if status not in {"tie", "winner"}:
        raise ValueError(
            "Estado de ronda no válido."
        )

    encoded_tied_options = None

    if tied_options:
        encoded_tied_options = ",".join(
            str(option)
            for option in tied_options
        )

    with connect_voting() as conn:
        conn.execute(
            """
            UPDATE voting_rounds
            SET status = ?,
                winner = ?,
                tied_options = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE round_number = ?
            """,
            (
                status,
                winner,
                encoded_tied_options,
                round_number
            )
        )


def set_voting_config(round_number, allowed_options):
    valid_options = {1, 2, 3}

    if not allowed_options:
        raise ValueError(
            "Debe existir al menos una opción disponible."
        )

    if not set(allowed_options).issubset(valid_options):
        raise ValueError(
            "Existe una opción de reglas no válida."
        )

    encoded_options = ",".join(
        str(option)
        for option in allowed_options
    )

    with connect_voting() as conn:
        conn.execute(
            """UPDATE voting_config
               SET round_number=?,
                   allowed_options=?
               WHERE id=1""",
            (
                round_number,
                encoded_options,
            )
        )


def start_new_round(round_number, allowed_options):
    if round_number < 1:
        raise ValueError(
            "El número de ronda debe ser mayor o igual a 1."
        )

    if not allowed_options:
        raise ValueError(
            "Debe existir al menos una opción disponible."
        )

    set_voting_config(
        round_number,
        allowed_options
    )

    encoded_options = ",".join(
        str(option)
        for option in allowed_options
    )

    with connect_voting() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO voting_rounds (
                round_number,
                allowed_options,
                status
            )
            VALUES (?, ?, 'active')
            """,
            (
                round_number,
                encoded_options
            )
        )

    set_voting_phase("commitment")


def get_vote_counts(round_number):
    with connect_voting() as conn:
        rows = conn.execute(
            """
            SELECT revealed_vote,
                   COUNT(*) AS total
            FROM votes
            WHERE verified = 1
              AND round_number = ?
            GROUP BY revealed_vote
            ORDER BY revealed_vote
            """,
            (round_number,)
        ).fetchall()

        return {
            row["revealed_vote"]: row["total"]
            for row in rows
        }


def determine_rule_result(round_number):
    counts = get_vote_counts(round_number)

    if not counts:
        return {
            "status": "no_votes",
            "winner": None,
            "counts": counts,
            "round_number": round_number,
        }

    max_votes = max(counts.values())

    winners = [
        option
        for option, total in counts.items()
        if total == max_votes
    ]

    if len(winners) > 1:
        return {
            "status": "tie",
            "winner": None,
            "counts": counts,
            "tied_options": winners,
            "round_number": round_number,
        }

    return {
        "status": "winner",
        "winner": winners[0],
        "counts": counts,
        "round_number": round_number,
    }

