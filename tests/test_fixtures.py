"""Examples for missing directed and undirected fixtures."""

import pytest

from leaguetab.fixtures import missing


def test_empty_matches_have_no_league_teams_or_missing_fixtures():
    assert missing([], legs=1) == []
    assert missing([], legs=2) == []


def test_two_legs_require_each_home_away_direction():
    matches = [
        ("A", "B", 1, 0),
        ("B", "A", 1, 0),
        ("A", "C", 2, 1),
    ]

    assert missing(matches, legs=2) == [
        ("B", "C"),
        ("C", "A"),
        ("C", "B"),
    ]


def test_one_leg_accepts_a_match_in_either_direction():
    matches = [
        ("B", "A", 1, 0),
        ("A", "C", 2, 1),
    ]

    assert missing(matches, legs=1) == [("B", "C")]


def test_repeated_same_direction_matches_do_not_fill_the_reverse_fixture():
    matches = [
        ("A", "B", 1, 0),
        ("A", "B", 2, 0),
        ("A", "B", 0, 0),
    ]

    assert missing(matches, legs=2) == [("B", "A")]


def test_repeated_and_reversed_results_satisfy_one_unordered_pair_once():
    matches = [
        ("B", "A", 1, 0),
        ("A", "B", 2, 0),
        ("B", "A", 0, 0),
        ("A", "C", 1, 1),
    ]

    assert missing(matches, legs=1) == [("B", "C")]


def test_complete_two_leg_schedule_has_no_missing_fixtures():
    matches = [
        ("A", "B", 1, 0),
        ("A", "C", 2, 0),
        ("B", "A", 1, 1),
        ("B", "C", 0, 2),
        ("C", "A", 0, 1),
        ("C", "B", 3, 2),
    ]

    assert missing(matches, legs=2) == []


def test_complete_one_leg_schedule_has_no_missing_fixtures_in_any_orientation():
    matches = [
        ("A", "B", 1, 0),
        ("C", "A", 2, 0),
        ("B", "C", 0, 2),
    ]

    assert missing(matches, legs=1) == []


def test_one_leg_fixtures_are_sorted_by_code_point_team_names():
    matches = [
        ("A", "a", 1, 0),
        ("Ä", "é", 1, 0),
    ]

    assert missing(matches, legs=1) == [
        ("A", "Ä"),
        ("A", "é"),
        ("a", "Ä"),
        ("a", "é"),
    ]


def test_two_leg_fixtures_are_sorted_by_code_point_home_then_away():
    matches = [
        ("A", "a", 1, 0),
        ("a", "A", 1, 0),
        ("Ä", "é", 1, 0),
    ]

    assert missing(matches, legs=2) == [
        ("A", "Ä"),
        ("A", "é"),
        ("a", "Ä"),
        ("a", "é"),
        ("Ä", "A"),
        ("Ä", "a"),
        ("é", "A"),
        ("é", "a"),
        ("é", "Ä"),
    ]


@pytest.mark.parametrize("legs", [0, 3])
def test_unsupported_leg_counts_are_rejected(legs):
    with pytest.raises(ValueError, match="legs must be 1 or 2"):
        missing([("A", "B", 1, 0)], legs=legs)
