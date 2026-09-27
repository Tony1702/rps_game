import pytest

from tournament.bracket import (
    Tournament,
    next_power_of_two,
    create_bracket,
)

from unittest.mock import patch

def test_tournament_requires_at_least_two_participants():
    with pytest.raises(ValueError):
        Tournament(["Alice"])


def test_create_matches():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    tournament.prepare_round()

    matches = tournament.create_matches()

    assert len(matches) == 2

    matched_players = {
        player
        for match in matches
        for player in match
    }

    assert matched_players == {
        "Alice",
        "Bob",
        "Carol",
        "David",
    }


def test_advance_to_next_round():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    tournament.advance(["Alice", "Carol"])

    assert tournament.current_round == [
        "Alice",
        "Carol",
    ]


def test_tournament_is_finished():
    tournament = Tournament(["Alice", "Bob"])

    assert tournament.is_finished() is False

    tournament.advance(["Alice"])

    assert tournament.is_finished() is True
    assert tournament.get_winner() == "Alice"


def test_get_winner_before_tournament_finishes():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    assert tournament.get_winner() is None


def test_play_round():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    match_rounds = [
        [
            (1, 3),
            (2, 1),
        ],
        [
            (3, 1),
            (3, 1),
        ],
    ]

    with patch(
        "tournament.bracket.PairingManager.create_pairs"
    ) as mock_create_pairs:

        mock_create_pairs.return_value = [
            ("Alice", "Bob"),
            ("Carol", "David"),
        ]

        winners = tournament.play_round(match_rounds)

    assert winners == [
        "Alice",
        "David",
    ]


def test_play_round_requires_correct_number_of_matches():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    with pytest.raises(ValueError):
        tournament.play_round([
            [
                (1, 3),
                (2, 1),
            ]
        ])


def test_run_tournament():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    match_rounds = [
        [
            [
                (1, 3),
                (2, 1),
            ],
            [
                (3, 1),
                (3, 1),
            ],
        ],
        [
            [
                (1, 3),
                (1, 3),
            ],
        ],
    ]

    with patch(
        "tournament.bracket.PairingManager.create_pairs"
    ) as mock_create_pairs:

        mock_create_pairs.side_effect = [
            [
                ("Alice", "Bob"),
                ("Carol", "David"),
            ],
            [
                ("Alice", "David"),
            ],
        ]

        winner = tournament.run_tournament(match_rounds)

    assert winner == "Alice"


def test_create_matches_with_bye():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        None,
    ])

    tournament.prepare_round()

    matches = tournament.create_matches()

    assert len(matches) == 1

    matched_players = {
        player
        for match in matches
        for player in match
    }

    assert len(matched_players) == 2

    assert matched_players.issubset({
        "Alice",
        "Bob",
        "Carol",
    })

    bye_players = {
        "Alice",
        "Bob",
        "Carol",
    } - matched_players

    assert len(bye_players) == 1


def test_next_power_of_two():
    assert next_power_of_two(2) == 2
    assert next_power_of_two(3) == 4
    assert next_power_of_two(4) == 4
    assert next_power_of_two(5) == 8
    assert next_power_of_two(7) == 8
    assert next_power_of_two(8) == 8


def test_create_bracket_with_three_participants():
    participants = [
        "Alice",
        "Bob",
        "Carol",
    ]

    bracket = create_bracket(participants)

    assert bracket == [
        "Alice",
        "Bob",
        "Carol",
        None,
    ]


def test_create_bracket_with_five_participants():
    participants = [
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ]

    bracket = create_bracket(participants)

    assert bracket == [
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
        None,
        None,
        None,
    ]


def test_create_bracket_requires_two_participants():
    with pytest.raises(ValueError):
        create_bracket(["Alice"])


def test_prepare_round_distributes_byes():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    first_round = tournament.prepare_round()

    first_bye = first_round[first_round.index(None) - 1]

    tournament.current_round = [
        participant
        for participant in first_round
        if participant is not None
    ]

    second_round = tournament.prepare_round()

    second_bye = second_round[second_round.index(None) - 1]

    assert first_bye != second_bye


def test_play_round_with_bye():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    match_rounds = [
        [
            (1, 3),
            (2, 1),
        ],
    ]

    winners = tournament.play_round(match_rounds)

    assert len(winners) == 2


def test_get_bye_players():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    tournament.prepare_round()

    bye_players = tournament.get_bye_players()

    assert len(bye_players) == 1
    assert bye_players[0] in {
        "Alice",
        "Bob",
        "Carol",
    }


def test_play_round_with_five_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ])

    match_rounds = [
        [
            (1, 3),
            (2, 1),
        ],
        [
            (3, 1),
            (3, 1),
        ],
    ]

    winners = tournament.play_round(match_rounds)

    assert len(winners) == 3


def test_prepare_round_with_bye():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    prepared = tournament.prepare_round()

    assert len(prepared) == 4
    assert prepared.count(None) == 1

    matches = tournament.create_matches()

    assert len(matches) == 1


def test_prepare_round_with_odd_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    prepared = tournament.prepare_round()

    assert len(prepared) == 4
    assert prepared.count(None) == 1

    bye_player = [
        participant
        for participant in prepared
        if participant is not None
    ]

    assert set(bye_player) == {
        "Alice",
        "Bob",
        "Carol",
    }


def test_prepare_round_with_three_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    prepared = tournament.prepare_round()

    assert len(prepared) == 4
    assert prepared.count(None) == 1

    matches = tournament.create_matches()

    assert len(matches) == 1


def test_prepare_round_with_five_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ])

    prepared = tournament.prepare_round()

    assert len(prepared) == 6
    assert prepared.count(None) == 1

    matches = tournament.create_matches()

    assert len(matches) == 2


def test_prepare_round_with_six_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
        "Frank",
    ])

    prepared = tournament.prepare_round()

    assert len(prepared) == 6
    assert prepared.count(None) == 0

    matches = tournament.create_matches()

    assert len(matches) == 3


def test_prepare_round_with_seven_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
        "Frank",
        "Grace",
    ])

    prepared = tournament.prepare_round()

    assert len(prepared) == 8
    assert prepared.count(None) == 1

    matches = tournament.create_matches()

    assert len(matches) == 3


def test_byes_are_not_repeated_before_others_receive_one():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    first_round = tournament.prepare_round()
    first_bye = tournament.get_bye_players()[0]

    tournament.current_round = [
        participant
        for participant in first_round
        if participant is not None
    ]

    second_round = tournament.prepare_round()
    second_bye = tournament.get_bye_players()[0]

    assert first_bye != second_bye


def test_bye_player_advances_without_playing():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    tournament.prepare_round()

    bye_players = tournament.get_bye_players()

    assert len(bye_players) == 1

    matches = tournament.create_matches()

    assert len(matches) == 1


def test_run_tournament_with_two_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
    ])

    match_rounds = [
        [
            [(1, 3), (1, 3)],
        ]
    ]

    with patch(
        "tournament.bracket.PairingManager.create_pairs"
    ) as mock_create_pairs:

        mock_create_pairs.return_value = [
            ("Alice", "Bob"),
        ]

        winner = tournament.run_tournament(match_rounds)

    assert winner == "Alice"


def test_run_tournament_with_three_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    match_rounds = [
        [
            [(1, 3), (1, 3)],
        ],
        [
            [(1, 3), (1, 3)],
        ],
    ]

    winner = tournament.run_tournament(match_rounds)

    assert winner in {
        "Alice",
        "Bob",
        "Carol",
    }


def test_run_tournament_with_five_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ])

    match_rounds = [
        [
            [(1, 3), (1, 3)],
            [(2, 3), (2, 3)],
        ],
        [
            [(1, 3), (1, 3)],
        ],
        [
            [(1, 3), (1, 3)],
        ],
    ]

    winner = tournament.run_tournament(match_rounds)

    assert winner in {
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    }


def test_bye_is_not_repeated_before_other_participants():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ])

    first_prepared = tournament.prepare_round()
    first_bye = tournament.get_bye_players()

    assert len(first_bye) == 1

    first_bye_player = first_bye[0]

    # Simulamos que el bye y los demás participantes
    # continúan disponibles para la siguiente preparación.
    tournament.current_round = [
        participant
        for participant in first_prepared
        if participant is not None
    ]

    second_prepared = tournament.prepare_round()
    second_bye = tournament.get_bye_players()

    assert len(second_bye) == 1

    second_bye_player = second_bye[0]

    assert second_bye_player != first_bye_player


def test_tournament_preserves_bye_counts():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    tournament.prepare_round()

    first_bye = tournament.get_bye_players()[0]

    first_count = tournament.bye_manager.get_bye_count(
        first_bye
    )

    assert first_count == 1

    tournament.current_round = [
        participant
        for participant in tournament.current_round
        if participant is not None
    ]

    tournament.prepare_round()

    second_count = tournament.bye_manager.get_bye_count(
        first_bye
    )

    assert second_count == 1


def test_debug_bye_assignment_between_rounds():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
    ])

    first_round = tournament.prepare_round()

    print("\nPRIMERA RONDA:", first_round)
    print("PRIMER BYE:", tournament.get_bye_players())
    print("COUNTS:", tournament.bye_manager.bye_counts)

    tournament.current_round = [
        participant
        for participant in first_round
        if participant is not None
    ]

    second_round = tournament.prepare_round()

    print("\nSEGUNDA RONDA:", second_round)
    print("SEGUNDO BYE:", tournament.get_bye_players())
    print("COUNTS:", tournament.bye_manager.bye_counts)

    assert True


def test_prepare_round_uses_random_pairing_with_bye():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ])

    prepared = tournament.prepare_round()

    bye_players = tournament.get_bye_players()
    matches = tournament.create_matches()

    assert len(bye_players) == 1
    assert len(matches) == 2

    bye_player = bye_players[0]

    # El jugador con bye no puede aparecer
    # en ninguno de los matches.
    for player_a, player_b in matches:
        assert bye_player not in {
            player_a,
            player_b,
        }

    # Los cuatro jugadores restantes deben
    # aparecer exactamente una vez en los matches.
    matched_players = [
        player
        for pair in matches
        for player in pair
    ]

    assert len(matched_players) == 4
    assert len(set(matched_players)) == 4

    assert set(matched_players) == (
        set(tournament.participants) - {bye_player}
    )

    # El participante con bye debe estar representado
    # en la estructura preparada junto con None.
    assert bye_player in prepared
    assert None in prepared


def test_prepare_round_uses_pairing_manager():
    tournament = Tournament([
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Eve",
    ])

    with patch(
        "tournament.bracket.PairingManager.create_pairs"
    ) as mock_create_pairs:

        mock_create_pairs.return_value = [
            ("Alice", "Bob"),
            ("Carol", "David"),
        ]

        prepared = tournament.prepare_round()

        mock_create_pairs.assert_called_once()

        assert prepared[-2:] in [
            ["Eve", None],
            ["Alice", None],
            ["Bob", None],
            ["Carol", None],
            ["David", None],
        ]



