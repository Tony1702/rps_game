from tournament.match import play_round, play_match


def test_match_player_a_wins():
    rounds = [
        (1, 3),  # A gana
        (2, 1),  # A gana
    ]

    assert play_match(rounds) == "A"


def test_match_player_b_wins():
    rounds = [
        (3, 1),  # B gana
        (1, 2),  # B gana
    ]

    assert play_match(rounds) == "B"


def test_match_with_tie_round():
    rounds = [
        (1, 1),  # empate
        (1, 3),  # A gana
        (2, 3),  # B gana
        (5, 3),  # A gana
    ]

    assert play_match(rounds) == "A"