RULE_SETS = {
    1: {
        "name": "Rock, Paper, Scissors, Well",
        "moves": {
            1: "Rock",
            2: "Paper",
            3: "Scissors",
            4: "Well",
        },
        "wins_against": {
            1: {3},       # Rock vence a Scissors
            2: {1, 4},    # Paper vence a Rock y Well
            3: {2},       # Scissors vence a Paper
            4: {1, 3},    # Well vence a Rock y Scissors
        },
    },

    2: {
        "name": "Rock, Paper, Scissors, Lizard, Spock",
        "moves": {
            1: "Rock",
            2: "Paper",
            3: "Scissors",
            4: "Lizard",
            5: "Spock",
        },
        "wins_against": {
            1: {3, 4},    # Rock vence a Scissors y Lizard
            2: {1, 5},    # Paper vence a Rock y Spock
            3: {2, 4},    # Scissors vence a Paper y Lizard
            4: {2, 5},    # Lizard vence a Paper y Spock
            5: {1, 3},    # Spock vence a Rock y Scissors
        },
    },

    3: {
        "name": "Rock, Paper, Scissors, Fire, Water",
        "moves": {
            1: "Rock",
            2: "Paper",
            3: "Scissors",
            4: "Fire",
            5: "Water",
        },
        "wins_against": {
            1: {3, 5},       # Rock vence a Scissors y Water
            2: {1, 5},       # Paper vence a Rock y Water
            3: {2, 5},       # Scissors vence a Paper y Water
            4: {1, 2, 3},    # Fire vence a Rock, Paper y Scissors
            5: {4},          # Water vence a Fire
        },
    },
}


# La variante 2 sigue siendo la predeterminada
# para mantener compatibilidad con el código y tests existentes.
DEFAULT_RULE_SET = 2

MOVES = RULE_SETS[DEFAULT_RULE_SET]["moves"]
WINS_AGAINST = RULE_SETS[DEFAULT_RULE_SET]["wins_against"]


def get_rule_set(rule_set=DEFAULT_RULE_SET):
    if rule_set not in RULE_SETS:
        raise ValueError("La variante de juego no es válida.")

    return RULE_SETS[rule_set]


def validate_move(move, rule_set=DEFAULT_RULE_SET):
    rules = get_rule_set(rule_set)
    return move in rules["moves"]


def determine_winner(
    move_a,
    move_b,
    rule_set=DEFAULT_RULE_SET,
):
    rules = get_rule_set(rule_set)

    if not validate_move(move_a, rule_set):
        raise ValueError(
            "La jugada del jugador A no es válida."
        )

    if not validate_move(move_b, rule_set):
        raise ValueError(
            "La jugada del jugador B no es válida."
        )

    if move_a == move_b:
        return "tie"

    if move_b in rules["wins_against"][move_a]:
        return "A"

    return "B"
