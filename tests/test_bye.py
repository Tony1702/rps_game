import pytest

from tournament.bye import ByeManager


def test_bye_manager_initializes_counts():
    manager = ByeManager([
        "Alice",
        "Bob",
        "Carol",
    ])

    assert manager.get_bye_count("Alice") == 0
    assert manager.get_bye_count("Bob") == 0
    assert manager.get_bye_count("Carol") == 0


def test_select_byes():
    manager = ByeManager([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    selected = manager.select_byes(
        ["Alice", "Bob", "Carol", "David"],
        2,
    )

    assert len(selected) == 2

    assert manager.get_bye_count(selected[0]) == 1
    assert manager.get_bye_count(selected[1]) == 1


def test_byes_are_distributed_fairly():
    manager = ByeManager([
        "Alice",
        "Bob",
        "Carol",
        "David",
    ])

    first = manager.select_byes(
        ["Alice", "Bob", "Carol", "David"],
        2,
    )

    second = manager.select_byes(
        ["Alice", "Bob", "Carol", "David"],
        2,
    )

    assert set(first).isdisjoint(set(second))

    for participant in [
        "Alice",
        "Bob",
        "Carol",
        "David",
    ]:
        assert manager.get_bye_count(participant) == 1


def test_participants_with_fewer_byes_have_priority():
    manager = ByeManager([
        "Alice",
        "Bob",
        "Carol",
    ])

    manager.bye_counts["Alice"] = 1
    manager.bye_counts["Bob"] = 0
    manager.bye_counts["Carol"] = 0

    selected = manager.select_byes(
        ["Alice", "Bob", "Carol"],
        1,
    )

    assert selected[0] in {
        "Bob",
        "Carol",
    }


def test_unknown_participant():
    manager = ByeManager(["Alice", "Bob"])

    with pytest.raises(ValueError):
        manager.get_bye_count("Carol")


def test_invalid_number_of_byes():
    manager = ByeManager(["Alice", "Bob"])

    with pytest.raises(ValueError):
        manager.select_byes(
            ["Alice", "Bob"],
            3,
        )


def test_select_bye_only_from_participants_with_fewest_byes():
    manager = ByeManager([
        "A",
        "C",
        "F",
        "G",
        "I",
    ])

    manager.bye_counts["A"] = 1
    manager.bye_counts["I"] = 1

    selected = manager.select_byes(
        ["A", "C", "F", "G", "I"],
        1,
    )

    assert selected[0] in {
        "C",
        "F",
        "G",
    }


def test_debug_bye_counts():
    manager = ByeManager([
        "Alice",
        "Bob",
        "Carol",
    ])

    first = manager.select_byes(
        ["Alice", "Bob", "Carol"],
        1,
    )

    print("PRIMER BYE:", first)
    print("COUNTS 1:", manager.bye_counts)

    second = manager.select_byes(
        ["Alice", "Bob", "Carol"],
        1,
    )

    print("SEGUNDO BYE:", second)
    print("COUNTS 2:", manager.bye_counts)

    assert second[0] != first[0]



