from unittest.mock import patch

from tournament.bracket import Tournament


def test_nine_participant_tournament_reduces_9_to_5_to_3_to_2_to_1():
    participants = [
        "A", "B", "C", "D", "E",
        "F", "G", "H", "I"
    ]

    tournament = Tournament(participants)

    pairings = [
        # Ronda 1: 9 -> 5
        [
            ("A", "B"),
            ("C", "D"),
            ("E", "F"),
            ("G", "H"),
        ],

        # Ronda 2: 5 -> 3
        [
            ("C", "E"),
            ("G", "I"),
        ],

        # Ronda 3: 3 -> 2
        [
            ("A", "I"),
        ],

        # Ronda 4: 2 -> 1
        [
            ("E", "A"),
        ],
    ]

    bye_sequence = [
        "I",
        "A",
        "E",
    ]

    match_results = [
        # Ronda 1
        [
            [(1, 3), (1, 3)],  # A vence a B
            [(1, 2), (1, 2)],  # C vence a D
            [(1, 2), (1, 2)],  # E vence a F
            [(1, 3), (1, 3)],  # G vence a H
        ],

        # Ronda 2
        [
            [(1, 2), (1, 2)],  # E vence a C
            [(1, 2), (1, 2)],  # I vence a G
        ],

        # Ronda 3
        [
            [(1, 3), (1, 3)],  # A vence a I
        ],

        # Ronda 4
        [
            [(3, 1), (3, 1)],
        ],
    ]

    expected_sizes = [5, 3, 2, 1]

    for round_index in range(4):

        with patch(
            "tournament.bracket.PairingManager.create_pairs",
            return_value=pairings[round_index],
        ):

            if round_index < 3:
                with patch(
                    "tournament.bracket.ByeManager.select_byes",
                    return_value=[bye_sequence[round_index]],
                ):
                    winners = tournament.play_round(
                        match_results[round_index]
                    )
            else:
                winners = tournament.play_round(
                    match_results[round_index]
                )

        assert len(winners) == expected_sizes[round_index]

    assert tournament.is_finished()
    assert tournament.get_winner() == "A"