import pytest

from tournament.game_manager import GameManager


def test_create_match():
    manager = GameManager()

    match = manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    assert match["player_a"] == "Alice"
    assert match["player_b"] == "Bob"
    assert match["round"] == 1
    assert match["moves"] == {}
    assert match["results"] == []
    assert match["wins_a"] == 0
    assert match["wins_b"] == 0
    assert match["finished"] is False
    assert match["winner"] is None


def test_cannot_create_duplicate_match():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    with pytest.raises(ValueError):
        manager.create_match(
            "match-1",
            "Carol",
            "David",
        )


def test_cannot_create_match_with_same_player():
    manager = GameManager()

    with pytest.raises(ValueError):
        manager.create_match(
            "match-1",
            "Alice",
            "Alice",
        )


def test_first_move_waits_for_second_player():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    result = manager.submit_move(
        "match-1",
        "Alice",
        1,
    )

    assert result is None

    match = manager.matches["match-1"]

    assert match["moves"] == {
        "Alice": 1
    }


def test_round_is_resolved_when_both_players_move():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    manager.submit_move(
        "match-1",
        "Alice",
        1,
    )

    result = manager.submit_move(
        "match-1",
        "Bob",
        3,
    )

    assert result == "A"

    match = manager.matches["match-1"]

    assert match["wins_a"] == 1
    assert match["wins_b"] == 0
    assert match["results"] == [(1, 3)]
    assert match["round"] == 2
    assert match["moves"] == {}


def test_cannot_submit_two_moves_in_same_round():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    manager.submit_move(
        "match-1",
        "Alice",
        1,
    )

    with pytest.raises(ValueError):
        manager.submit_move(
            "match-1",
            "Alice",
            2,
        )


def test_match_finishes_when_player_reaches_two_wins():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    # Primera ronda: Alice gana.
    manager.submit_move(
        "match-1",
        "Alice",
        1,
    )

    manager.submit_move(
        "match-1",
        "Bob",
        3,
    )

    # Segunda ronda: Alice gana nuevamente.
    manager.submit_move(
        "match-1",
        "Alice",
        2,
    )

    result = manager.submit_move(
        "match-1",
        "Bob",
        1,
    )

    assert result == "A"

    match = manager.matches["match-1"]

    assert match["wins_a"] == 2
    assert match["wins_b"] == 0
    assert match["finished"] is True
    assert match["winner"] == "Alice"


def test_get_match():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    match = manager.get_match("match-1")

    assert match["player_a"] == "Alice"
    assert match["player_b"] == "Bob"


def test_has_submitted_move():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    assert manager.has_submitted_move(
        "match-1",
        "Alice",
    ) is False

    manager.submit_move(
        "match-1",
        "Alice",
        1,
    )

    assert manager.has_submitted_move(
        "match-1",
        "Alice",
    ) is True


def test_is_finished():
    manager = GameManager()

    manager.create_match(
        "match-1",
        "Alice",
        "Bob",
    )

    assert manager.is_finished("match-1") is False

    manager.submit_move("match-1", "Alice", 1)
    manager.submit_move("match-1", "Bob", 3)

    manager.submit_move("match-1", "Alice", 2)
    manager.submit_move("match-1", "Bob", 1)

    assert manager.is_finished("match-1") is True


    