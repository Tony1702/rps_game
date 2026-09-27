MOVES = {
    1: "Rock",
    2: "Paper",
    3: "Scissors",
    4: "Lizard",
    5: "Spock",
}


# Cada movimiento vence a los dos movimientos indicados.
WINS_AGAINST = {
    1: {3, 4},  # Rock vence a Scissors y Lizard
    2: {1, 5},  # Paper vence a Rock y Spock
    3: {2, 4},  # Scissors vence a Paper y Lizard
    4: {2, 5},  # Lizard vence a Paper y Spock
    5: {1, 3},  # Spock vence a Rock y Scissors
}


def validate_move(move):
    return move in MOVES


def determine_winner(move_a, move_b):
    if not validate_move(move_a):
        raise ValueError("La jugada del jugador A no es válida.")

    if not validate_move(move_b):
        raise ValueError("La jugada del jugador B no es válida.")

    if move_a == move_b:
        return "tie"

    if move_b in WINS_AGAINST[move_a]:
        return "A"

    return "B"