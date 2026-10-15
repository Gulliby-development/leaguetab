"""Example-based tests for league statistics."""

import pytest

from leaguetab.stats import calculate

_FIELDS = ("P", "W", "D", "L", "GF", "GA", "GD", "PTS", "away")


def _zero_record():
    return dict.fromkeys(_FIELDS, 0)


def test_empty_matches_return_no_teams():
    assert calculate([]) == {}


@pytest.mark.parametrize(
    ("score", "home_expected", "away_expected"),
    [
        (
            (3, 1),
            {"P": 1, "W": 1, "D": 0, "L": 0, "GF": 3, "GA": 1, "GD": 2, "PTS": 3, "away": 0},
            {"P": 1, "W": 0, "D": 0, "L": 1, "GF": 1, "GA": 3, "GD": -2, "PTS": 0, "away": 1},
        ),
        (
            (1, 3),
            {"P": 1, "W": 0, "D": 0, "L": 1, "GF": 1, "GA": 3, "GD": -2, "PTS": 0, "away": 0},
            {"P": 1, "W": 1, "D": 0, "L": 0, "GF": 3, "GA": 1, "GD": 2, "PTS": 3, "away": 3},
        ),
        (
            (2, 2),
            {"P": 1, "W": 0, "D": 1, "L": 0, "GF": 2, "GA": 2, "GD": 0, "PTS": 1, "away": 0},
            {"P": 1, "W": 0, "D": 1, "L": 0, "GF": 2, "GA": 2, "GD": 0, "PTS": 1, "away": 2},
        ),
    ],
)
def test_single_match_counts_each_result(score, home_expected, away_expected):
    goals_for_home, goals_for_away = score
    matches = [("Home", "Away", goals_for_home, goals_for_away)]

    assert calculate(matches) == {"Home": home_expected, "Away": away_expected}


def test_repeated_matches_in_both_directions_are_counted_independently():
    matches = [
        ("A", "B", 2, 0),
        ("B", "A", 1, 3),
        ("A", "B", 0, 0),
    ]

    assert calculate(matches) == {
        "A": {"P": 3, "W": 2, "D": 1, "L": 0, "GF": 5, "GA": 1, "GD": 4, "PTS": 7, "away": 3},
        "B": {"P": 3, "W": 0, "D": 1, "L": 2, "GF": 1, "GA": 5, "GD": -4, "PTS": 1, "away": 0},
    }


def test_custom_win_and_draw_values_change_points_only():
    matches = [("A", "B", 3, 1), ("B", "C", 2, 2)]

    assert calculate(matches, win=5, draw=2) == {
        "A": {"P": 1, "W": 1, "D": 0, "L": 0, "GF": 3, "GA": 1, "GD": 2, "PTS": 5, "away": 0},
        "B": {"P": 2, "W": 0, "D": 1, "L": 1, "GF": 3, "GA": 5, "GD": -2, "PTS": 2, "away": 1},
        "C": {"P": 1, "W": 0, "D": 1, "L": 0, "GF": 2, "GA": 2, "GD": 0, "PTS": 2, "away": 2},
    }


def test_zero_point_values_preserve_results_and_goal_counts():
    matches = [("A", "B", 1, 0), ("B", "C", 1, 1)]

    assert calculate(matches, win=0, draw=0) == {
        "A": {"P": 1, "W": 1, "D": 0, "L": 0, "GF": 1, "GA": 0, "GD": 1, "PTS": 0, "away": 0},
        "B": {"P": 2, "W": 0, "D": 1, "L": 1, "GF": 1, "GA": 2, "GD": -1, "PTS": 0, "away": 0},
        "C": {"P": 1, "W": 0, "D": 1, "L": 0, "GF": 1, "GA": 1, "GD": 0, "PTS": 0, "away": 1},
    }


def test_subgroup_counts_only_internal_matches_and_initializes_empty_teams():
    matches = [
        ("A", "B", 2, 1),
        ("A", "Outside", 5, 0),
        ("Outside", "B", 1, 0),
        ("Outside", "C", 4, 4),
    ]

    assert calculate(matches, teams=("A", "B", "C", "C")) == {
        "A": {"P": 1, "W": 1, "D": 0, "L": 0, "GF": 2, "GA": 1, "GD": 1, "PTS": 3, "away": 0},
        "B": {"P": 1, "W": 0, "D": 0, "L": 1, "GF": 1, "GA": 2, "GD": -1, "PTS": 0, "away": 1},
        "C": _zero_record(),
    }


def test_empty_match_subgroup_keeps_each_requested_team_zeroed():
    assert calculate([], teams=("Zulu", "Alpha")) == {
        "Zulu": _zero_record(),
        "Alpha": _zero_record(),
    }


def test_large_aggregates_and_away_goals_are_not_limited_to_nine_digits():
    matches = [
        ("A", "B", 0, 999_999_999),
        ("C", "B", 0, 999_999_999),
    ]

    assert calculate(matches) == {
        "A": {"P": 1, "W": 0, "D": 0, "L": 1, "GF": 0, "GA": 999_999_999, "GD": -999_999_999, "PTS": 0, "away": 0},
        "B": {"P": 2, "W": 2, "D": 0, "L": 0, "GF": 1_999_999_998, "GA": 0, "GD": 1_999_999_998, "PTS": 6, "away": 1_999_999_998},
        "C": {"P": 1, "W": 0, "D": 0, "L": 1, "GF": 0, "GA": 999_999_999, "GD": -999_999_999, "PTS": 0, "away": 0},
    }
