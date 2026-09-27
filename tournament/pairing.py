import random


class PairingManager:
    def create_pairs(self, participants):
        participants = list(participants)

        if len(participants) < 2:
            raise ValueError(
                "Se necesitan al menos 2 participantes."
            )

        if len(participants) % 2 != 0:
            raise ValueError(
                "La cantidad de participantes debe ser par."
            )

        if len(set(participants)) != len(participants):
            raise ValueError(
                "No puede haber participantes duplicados."
            )

        random.shuffle(participants)

        pairs = []

        for i in range(0, len(participants), 2):
            pairs.append(
                (
                    participants[i],
                    participants[i + 1],
                )
            )

        return pairs