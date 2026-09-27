from tournament.match import play_match
from tournament.bye import ByeManager
from tournament.pairing import PairingManager

class Tournament:
    def __init__(self, participants):
        if len(participants) < 2:
            raise ValueError(
                "Se necesitan al menos 2 participantes."
            )

        self.participants = list(participants)
        self.current_round = self.participants
        self.prepared_round = None
        self.bye_manager = ByeManager(self.participants)
        self.pairing_manager = PairingManager()

    def create_matches(self):
        if self.prepared_round is None:
            raise ValueError(
                "La ronda todavía no ha sido preparada."
            )

        matches = []

        for i in range(0, len(self.prepared_round), 2):
            player_a = self.prepared_round[i]
            player_b = self.prepared_round[i + 1]

            if player_a is None or player_b is None:
                continue

            matches.append((player_a, player_b))

        return matches

    def advance(self, winners):
        self.current_round = list(winners)
        self.prepared_round = None

    def is_finished(self):
        return len(self.current_round) == 1

    def get_winner(self):
        if not self.is_finished():
            return None

        return self.current_round[0]

    def play_round(self, match_rounds):
        self.prepare_round()
        matches = self.create_matches()
        bye_players = self.get_bye_players()

        if len(match_rounds) != len(matches):
            raise ValueError(
                "La cantidad de resultados de matches no coincide "
                "con la cantidad de enfrentamientos."
            )

        winners = list(bye_players)

        for (player_a, player_b), rounds in zip(matches, match_rounds):
            result = play_match(rounds)

            if result == "A":
                winners.append(player_a)

            elif result == "B":
                winners.append(player_b)

            else:
                raise ValueError(
                    f"El match entre {player_a} y {player_b} terminó en empate."
                )

        self.advance(winners)

        return winners

    def run_tournament(self, match_rounds):
        round_index = 0

        while not self.is_finished():
            if round_index >= len(match_rounds):
                raise ValueError(
                    "No hay suficientes resultados para completar el torneo."
                )

            self.play_round(match_rounds[round_index])
            round_index += 1

        return self.get_winner()

    def prepare_round(self):
        participants = list(self.current_round)

        if len(participants) < 2:
            raise ValueError(
                "Se necesitan al menos 2 participantes para preparar una ronda."
            )

        number_of_byes = len(participants) % 2

        if number_of_byes == 0:
            pairs = self.pairing_manager.create_pairs(participants)

            prepared = []

            for player_a, player_b in pairs:
                prepared.append(player_a)
                prepared.append(player_b)

            self.prepared_round = prepared
            return prepared

        bye_players = self.bye_manager.select_byes(
            participants,
            number_of_byes,
        )

        players_without_bye = [
            participant
            for participant in participants
            if participant not in bye_players
        ]

        pairs = self.pairing_manager.create_pairs(
            players_without_bye
        )

        prepared = []

        for player_a, player_b in pairs:
            prepared.append(player_a)
            prepared.append(player_b)

        for bye_player in bye_players:
            prepared.append(bye_player)
            prepared.append(None)

        self.prepared_round = prepared
        return prepared

    def get_bye_players(self):
        if self.prepared_round is None:
            raise ValueError(
                "La ronda todavía no ha sido preparada."
            )

        bye_players = []

        for i in range(0, len(self.prepared_round), 2):
            player_a = self.prepared_round[i]
            player_b = self.prepared_round[i + 1]

            if player_a is not None and player_b is None:
                bye_players.append(player_a)

            elif player_b is not None and player_a is None:
                bye_players.append(player_b)

        return bye_players
    

def next_power_of_two(number):
    if number < 1:
        raise ValueError("El número de participantes debe ser positivo.")

    size = 1

    while size < number:
        size *= 2

    return size

def create_bracket(participants):
    if len(participants) < 2:
        raise ValueError("Se necesitan al menos 2 participantes.")

    bracket_size = next_power_of_two(len(participants))

    return list(participants) + [None] * (
        bracket_size - len(participants)
    )

