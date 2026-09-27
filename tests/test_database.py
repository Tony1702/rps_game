import sqlite3
from database import db


def test_get_all_participants(monkeypatch):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            voting_credential TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.executemany(
        """
        INSERT INTO participants (
            telegram_user_id,
            voting_credential
        )
        VALUES (?, ?)
        """,
        [
            (1001, "VC-AAA"),
            (1002, "VC-BBB"),
            (1003, "VC-CCC"),
        ],
    )

    def fake_connect_identity():
        return connection

    monkeypatch.setattr(
        db,
        "connect_identity",
        fake_connect_identity,
    )

    participants = db.get_all_participants()

    assert len(participants) == 3

    assert participants[0]["telegram_user_id"] == 1001
    assert participants[0]["voting_credential"] == "VC-AAA"

    assert participants[1]["telegram_user_id"] == 1002
    assert participants[1]["voting_credential"] == "VC-BBB"

    assert participants[2]["telegram_user_id"] == 1003
    assert participants[2]["voting_credential"] == "VC-CCC"

    connection.close()

def test_init_db_creates_voting_tables(monkeypatch, tmp_path):
    identity_db = tmp_path / "identity.db"
    voting_db = tmp_path / "voting.db"

    def connect_identity_test():
        conn = sqlite3.connect(identity_db)
        conn.row_factory = sqlite3.Row
        return conn

    def connect_voting_test():
        conn = sqlite3.connect(voting_db)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(db, "connect_identity", connect_identity_test)
    monkeypatch.setattr(db, "connect_voting", connect_voting_test)

    db.init_db()

    with connect_voting_test() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

    assert "votes" in tables
    assert "voting_state" in tables
    assert "voting_config" in tables
    assert "voting_rounds" in tables

