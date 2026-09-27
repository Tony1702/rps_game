from tournament.pairing import PairingManager

import pytest


def test_create_pairs_with_four_participants():
    manager = PairingManager()

    pairs = manager.create_pairs([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    assert len(pairs) == 2

    participants = [
        participant
        for pair in pairs
        for participant in pair
    ]

    assert set(participants) == {
        "Alice",
        "Bob",
        "Carol",
        "David",
    }


def test_create_pairs_rejects_odd_number_of_participants():
    manager = PairingManager()

    with pytest.raises(ValueError):
        manager.create_pairs([
            "Alice",
            "Bob",
            "Carol",
        ])


def test_create_pairs_rejects_duplicate_participants():
    manager = PairingManager()

    with pytest.raises(ValueError):
        manager.create_pairs([
            "Alice",
            "Bob",
            "Alice",
            "David",
        ])


def test_create_pairs_can_generate_different_pairings():
    manager = PairingManager()

    participants = [
        "Alice",
        "Bob",
        "Carol",
        "David",
    ]

    pairings = {
        tuple(manager.create_pairs(participants))
        for _ in range(20)
    }

    assert len(pairings) > 1




