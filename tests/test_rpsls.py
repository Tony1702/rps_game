import pytest

from tournament.rules import (
    MOVES,
    determine_winner,
    validate_move,
)


def test_all_moves_are_valid():
    for move in range(1, 6):
        assert validate_move(move)


def test_invalid_moves():
    assert not validate_move(0)
    assert not validate_move(6)
    assert not validate_move(-1)


@pytest.mark.parametrize(
    "move_a, move_b",
    [
        (1, 3),  # Rock > Scissors
        (1, 4),  # Rock > Lizard
        (2, 1),  # Paper > Rock
        (2, 5),  # Paper > Spock
        (3, 2),  # Scissors > Paper
        (3, 4),  # Scissors > Lizard
        (4, 2),  # Lizard > Paper
        (4, 5),  # Lizard > Spock
        (5, 1),  # Spock > Rock
        (5, 3),  # Spock > Scissors
    ],
)
def test_winning_combinations(move_a, move_b):
    assert determine_winner(move_a, move_b) == "A"


@pytest.mark.parametrize(
    "move_a, move_b",
    [
        (3, 1),
        (4, 1),
        (1, 2),
        (5, 2),
        (2, 3),
        (4, 3),
        (2, 4),
        (5, 4),
        (1, 5),
        (3, 5),
    ],
)
def test_losing_combinations(move_a, move_b):
    assert determine_winner(move_a, move_b) == "B"


@pytest.mark.parametrize(
    "move",
    [1, 2, 3, 4, 5],
)
def test_ties(move):
    assert determine_winner(move, move) == "tie"


def test_invalid_move_a():
    with pytest.raises(ValueError):
        determine_winner(0, 1)


def test_invalid_move_b():
    with pytest.raises(ValueError):
        determine_winner(1, 6)