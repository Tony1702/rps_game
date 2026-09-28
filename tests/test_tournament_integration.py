from unittest.mock import patch

from tournament.bracket import Tournament

from tournament.game_manager import GameManager

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


def test_tournament_match_with_game_manager():
    participants = ["Alice", "Bob"]

    tournament = Tournament(participants)

    tournament.prepare_round()

    matches = tournament.create_matches()

    assert len(matches) == 1

    player_a, player_b = matches[0]

    game_manager = GameManager()

    match_id = "match-1"

    game_manager.create_match(
        match_id,
        player_a,
        player_b,
    )

    # Ronda 1: gana A.
    game_manager.submit_move(
        match_id,
        player_a,
        1,
    )

    result = game_manager.submit_move(
        match_id,
        player_b,
        3,
    )

    assert result == "A"

    # Ronda 2: gana A nuevamente.
    game_manager.submit_move(
        match_id,
        player_a,
        1,
    )

    result = game_manager.submit_move(
        match_id,
        player_b,
        3,
    )

    assert result == "A"

    assert game_manager.is_finished(match_id)

    match = game_manager.get_match(match_id)

    assert match["winner"] == player_a


def test_tournament_match_is_registered_in_game_manager():
    participants = ["Alice", "Bob"]

    tournament = Tournament(participants)
    tournament.prepare_round()

    matches = tournament.create_matches()

    assert len(matches) == 1

    player_a, player_b = matches[0]

    game_manager = GameManager()

    game_manager.create_match(
        "match-1",
        player_a,
        player_b,
    )

    match = game_manager.get_match("match-1")

    assert match["player_a"] == player_a
    assert match["player_b"] == player_b
    assert match["round"] == 1
    assert match["wins_a"] == 0
    assert match["wins_b"] == 0
    assert match["finished"] is False
    assert match["winner"] is None


def test_three_player_tournament_with_bye():
    participants = [
        "VC-PLAYER-A",
        "VC-PLAYER-B",
        "VC-PLAYER-C",
    ]

    tournament = Tournament(participants)
    game_manager = GameManager()

    # Primera ronda
    tournament.prepare_round()

    matches = tournament.create_matches()
    bye_players = tournament.get_bye_players()

    assert len(matches) == 1
    assert len(bye_players) == 1

    player_a, player_b = matches[0]
    bye_player = bye_players[0]

    assert bye_player not in (player_a, player_b)

    # Crear el match en GameManager
    match_id = "match-1"

    game_manager.create_match(
        match_id,
        player_a,
        player_b,
    )

    # Jugador A gana 2-0
    game_manager.submit_move(match_id, player_a, 1)
    game_manager.submit_move(match_id, player_b, 3)

    game_manager.submit_move(match_id, player_a, 1)
    result = game_manager.submit_move(match_id, player_b, 3)

    assert result == "A"

    match_state = game_manager.get_match(match_id)

    assert match_state["finished"] is True
    assert match_state["winner"] == player_a

    winner = player_a

    tournament.advance([
        winner,
        bye_player,
    ])

    assert len(tournament.current_round) == 2
    assert winner in tournament.current_round
    assert bye_player in tournament.current_round

    # Segunda ronda: ambos deben enfrentarse
    tournament.prepare_round()

    next_matches = tournament.create_matches()
    next_byes = tournament.get_bye_players()

    assert len(next_matches) == 1
    assert len(next_byes) == 0

    next_player_a, next_player_b = next_matches[0]

    assert {
        next_player_a,
        next_player_b,
    } == {
        winner,
        bye_player,
    }


def test_three_player_tournament_complete():
    participants = [
        "VC-PLAYER-A",
        "VC-PLAYER-B",
        "VC-PLAYER-C",
    ]

    tournament = Tournament(participants)
    game_manager = GameManager()

    # Primera ronda
    tournament.prepare_round()

    matches = tournament.create_matches()
    bye_players = tournament.get_bye_players()

    assert len(matches) == 1
    assert len(bye_players) == 1

    player_a, player_b = matches[0]
    bye_player = bye_players[0]

    assert bye_player not in (player_a, player_b)

    # Crear el match
    match_id = "match-1"

    game_manager.create_match(
        match_id,
        player_a,
        player_b,
    )

    # El jugador A gana 2-0
    game_manager.submit_move(match_id, player_a, 1)
    game_manager.submit_move(match_id, player_b, 3)

    game_manager.submit_move(match_id, player_a, 1)
    result = game_manager.submit_move(match_id, player_b, 3)

    assert result == "A"

    match_state = game_manager.get_match(match_id)

    assert match_state["finished"] is True
    assert match_state["winner"] == player_a

    match_winner = match_state["winner"]

    # El ganador y el jugador con bye avanzan a la final
    tournament.advance([
        match_winner,
        bye_player,
    ])

    assert len(tournament.current_round) == 2
    assert tournament.is_finished() is False

    # Segunda ronda: final
    tournament.prepare_round()

    final_matches = tournament.create_matches()
    final_byes = tournament.get_bye_players()

    assert len(final_matches) == 1
    assert len(final_byes) == 0

    final_player_a, final_player_b = final_matches[0]

    assert {
        final_player_a,
        final_player_b,
    } == {
        match_winner,
        bye_player,
    }

    # Crear la final
    final_match_id = "match-final"

    game_manager.create_match(
        final_match_id,
        final_player_a,
        final_player_b,
    )

    # El jugador A de la final gana 2-0
    game_manager.submit_move(final_match_id, final_player_a, 1)
    game_manager.submit_move(final_match_id, final_player_b, 3)

    game_manager.submit_move(final_match_id, final_player_a, 1)
    final_result = game_manager.submit_move(
        final_match_id,
        final_player_b,
        3,
    )

    assert final_result == "A"

    final_state = game_manager.get_match(final_match_id)

    assert final_state["finished"] is True
    assert final_state["winner"] == final_player_a

    # El ganador de la final se convierte en campeón
    tournament.advance([
        final_state["winner"],
    ])

    assert tournament.is_finished() is True
    assert tournament.get_winner() == final_player_a


