from tournament.rules import determine_winner


def play_round(move_a, move_b):
    return determine_winner(move_a, move_b)


def play_match(rounds):
    """
    Ejecuta un enfrentamiento entre dos jugadores.

    rounds debe ser una lista de tuplas:
        [(movimiento_a, movimiento_b), ...]

    El jugador que alcance primero 2 victorias gana el match.
    """
    wins_a = 0
    wins_b = 0

    for move_a, move_b in rounds:
        result = play_round(move_a, move_b)

        if result == "A":
            wins_a += 1
        elif result == "B":
            wins_b += 1

        if wins_a == 2:
            return "A"

        if wins_b == 2:
            return "B"

    return "tie"