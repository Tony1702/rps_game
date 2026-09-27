import random


class ByeManager:
    def __init__(self, participants):
        if len(participants) < 1:
            raise ValueError("Se necesita al menos un participante.")

        self.participants = list(participants)
        self.bye_counts = {
            participant: 0
            for participant in self.participants
        }

    def get_bye_count(self, participant):
        if participant not in self.bye_counts:
            raise ValueError(
                "El participante no pertenece al torneo."
            )

        return self.bye_counts[participant]

    def select_byes(self, participants, number_of_byes):
        if number_of_byes < 0:
            raise ValueError(
                "La cantidad de byes no puede ser negativa."
            )

        if number_of_byes > len(participants):
            raise ValueError(
                "No puede haber más byes que participantes."
            )

        for participant in participants:
            if participant not in self.bye_counts:
                raise ValueError(
                    "El participante no pertenece al torneo."
                )

        min_byes = min(
            self.bye_counts[participant]
            for participant in participants
        )

        eligible = [
            participant
            for participant in participants
            if self.bye_counts[participant] == min_byes
        ]

        selected = random.sample(
            eligible,
            number_of_byes,
        )

        for participant in selected:
            self.bye_counts[participant] += 1

        return selected