from tournament.rules import validate_move, determine_winner

class GameManager:
    def __init__(self):
        self.matches = {}

    def create_match(self, match_id, player_a, player_b):
        if match_id in self.matches:
            raise ValueError("El match ya existe.")

        if player_a == player_b:
            raise ValueError(
                "Un participante no puede enfrentarse contra sí mismo."
            )

        self.matches[match_id] = {
            "player_a": player_a,
            "player_b": player_b,
            "round": 1,
            "moves": {},
            "results": [],
            "wins_a": 0,
            "wins_b": 0,
            "finished": False,
            "winner": None,
        }

        return self.matches[match_id]

    def get_match(self, match_id):
        if match_id not in self.matches:
            raise ValueError("El match no existe.")

        return self.matches[match_id]

    def submit_move(self, match_id, player, move):
        if match_id not in self.matches:
            raise ValueError("El match no existe.")

        match = self.matches[match_id]

        if match["finished"]:
            raise ValueError("El match ya terminó.")

        if player not in (
            match["player_a"],
            match["player_b"],
        ):
            raise ValueError(
                "El participante no pertenece al match."
            )

        if not validate_move(move):
            raise ValueError("La jugada no es válida.")

        if player in match["moves"]:
            raise ValueError(
                "El participante ya envió su jugada en esta ronda."
            )

        match["moves"][player] = move

        if len(match["moves"]) < 2:
            return None

        return self.resolve_round(match_id)

    def has_submitted_move(self, match_id, player):
        match = self.get_match(match_id)

        return player in match["moves"]

    def resolve_round(self, match_id):
        if match_id not in self.matches:
            raise ValueError("El match no existe.")

        match = self.matches[match_id]

        player_a = match["player_a"]
        player_b = match["player_b"]

        if player_a not in match["moves"] or player_b not in match["moves"]:
            raise ValueError(
                "Todavía no han jugado ambos participantes."
            )

        move_a = match["moves"][player_a]
        move_b = match["moves"][player_b]

        result = determine_winner(move_a, move_b)

        match["results"].append(
            (move_a, move_b)
        )

        if result == "A":
            match["wins_a"] += 1
        elif result == "B":
            match["wins_b"] += 1

        if match["wins_a"] == 2:
            match["finished"] = True
            match["winner"] = player_a

        elif match["wins_b"] == 2:
            match["finished"] = True
            match["winner"] = player_b

        else:
            match["round"] += 1
            match["moves"] = {}

        return result

    def is_finished(self, match_id):
        match = self.get_match(match_id)

        return match["finished"]