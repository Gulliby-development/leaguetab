"""Examples for ranking groups and their recorded tie-break history."""

import pytest

from leaguetab.ranking import rank
from leaguetab.stats import calculate


def _rank(matches, rules, win=3, draw=1):
    stats = calculate(matches, win=win, draw=draw)
    return rank(matches, stats, rules, win=win, draw=draw)


@pytest.mark.parametrize(
    ("matches", "win", "draw", "expected_points", "expected_groups"),
    [
        ([("a", "b", 1, 0)], 3, 1, {"a": 3, "b": 0}, [["a"], ["b"]]),
        ([("b", "a", 2, 0)], 3, 1, {"a": 0, "b": 3}, [["b"], ["a"]]),
        ([("a", "b", 1, 1)], 3, 1, {"a": 1, "b": 1}, [["a", "b"]]),
        ([("a", "b", 0, 0)], 3, 0, {"a": 0, "b": 0}, [["a", "b"]]),
        ([("a", "b", 1, 0)], 0, 1, {"a": 0, "b": 0}, [["a", "b"]]),
        (
            [("a", "b", 2, 0), ("a", "b", 1, 0)],
            3,
            1,
            {"a": 6, "b": 0},
            [["a"], ["b"]],
        ),
        ([("a", "b", 0, 3)], 9, 1, {"a": 0, "b": 9}, [["b"], ["a"]]),
        (
            [("a", "b", 1, 1), ("b", "c", 1, 0)],
            3,
            1,
            {"a": 1, "b": 4, "c": 0},
            [["b"], ["a"], ["c"]],
        ),
        ([("a", "b", 2, 1)], 1, 0, {"a": 1, "b": 0}, [["a"], ["b"]]),
        (
            [("a", "b", 1, 0), ("b", "c", 2, 0)],
            3,
            1,
            {"a": 3, "b": 3, "c": 0},
            [["a", "b"], ["c"]],
        ),
    ],
)
def test_points_order_ten_explicit_leagues(
    matches, win, draw, expected_points, expected_groups
):
    groups, applications = _rank(matches, [], win=win, draw=draw)

    assert groups == expected_groups
    assert [application.rule for application in applications] == ["points"]
    assert applications[0].keys == expected_points


def test_goal_difference_rule_orders_equal_point_teams():
    matches = [("a", "b", 2, 0), ("b", "c", 3, 0), ("c", "a", 1, 0)]

    groups, applications = _rank(matches, ["gd"])

    assert groups == [["a", "b"], ["c"]]
    assert [application.rule for application in applications] == ["points", "gd"]
    assert applications[1].teams == ("a", "b", "c")
    assert applications[1].keys == {"a": 1, "b": 1, "c": -2}


def test_goals_for_rule_orders_equal_difference_teams():
    matches = [("a", "b", 1, 1), ("b", "c", 2, 2), ("c", "a", 3, 3)]

    groups, applications = _rank(matches, ["gf"])

    assert groups == [["c"], ["a"], ["b"]]
    assert [application.rule for application in applications] == ["points", "gf"]
    assert applications[1].keys == {"a": 4, "b": 3, "c": 5}


def test_wins_rule_orders_equal_point_teams():
    matches = [
        ("a", "x", 1, 0),
        ("y", "a", 1, 0),
        ("z", "a", 1, 0),
        ("b", "e", 0, 0),
        ("b", "f", 0, 0),
        ("b", "g", 0, 0),
    ]

    groups, applications = _rank(matches, ["wins"])

    assert groups == [["a", "y", "z"], ["b"], ["e", "f", "g"], ["x"]]
    assert [application.rule for application in applications] == [
        "points",
        "wins",
        "wins",
    ]
    assert applications[1].teams == ("a", "b", "y", "z")
    assert applications[1].keys == {"a": 1, "b": 0, "y": 1, "z": 1}
    assert applications[2].teams == ("e", "f", "g")
    assert applications[2].keys == {"e": 0, "f": 0, "g": 0}


def test_away_goals_rule_counts_only_away_goals():
    matches = [("a", "b", 1, 1), ("b", "a", 3, 3)]

    groups, applications = _rank(matches, ["away"])

    assert groups == [["a"], ["b"]]
    assert [application.rule for application in applications] == ["points", "away"]
    assert applications[1].keys == {"a": 3, "b": 1}


def test_head_to_head_rule_uses_only_matches_between_tied_teams():
    matches = [("a", "b", 1, 0), ("b", "c", 1, 0)]

    groups, applications = _rank(matches, ["h2h"])

    assert groups == [["a"], ["b"], ["c"]]
    assert [application.rule for application in applications] == ["points", "h2h"]
    assert applications[1].teams == ("a", "b")
    assert applications[1].keys == {"a": (3, 1, 1), "b": (0, -1, 0)}


def test_combined_rules_keep_order_and_advance_after_an_unsplit_rule():
    matches = [("a", "b", 1, 1), ("b", "c", 2, 2), ("c", "a", 3, 3)]

    groups, applications = _rank(matches, ["gd", "gf", "wins", "away", "h2h"])

    assert groups == [["c"], ["a"], ["b"]]
    assert [application.rule for application in applications] == [
        "points",
        "gd",
        "gf",
    ]
    assert applications[1].keys == {"a": 0, "b": 0, "c": 0}
    assert applications[2].keys == {"a": 4, "b": 3, "c": 5}


def test_head_to_head_recomputes_after_a_three_team_split():
    matches = [("a", "b", 3, 2), ("b", "c", 3, 1), ("c", "a", 4, 1)]

    groups, applications = _rank(matches, ["h2h"])

    assert groups == [["b"], ["c"], ["a"]]
    assert [application.rule for application in applications] == [
        "points",
        "h2h",
        "h2h",
    ]
    assert applications[1].teams == ("a", "b", "c")
    assert applications[1].keys == {
        "a": (3, -2, 4),
        "b": (3, 1, 5),
        "c": (3, 1, 5),
    }
    assert applications[2].teams == ("b", "c")
    assert applications[2].keys == {"b": (3, 2, 3), "c": (0, -2, 1)}


def test_exhausted_rules_leave_a_tie_and_record_unsplit_applications():
    matches = [("a", "b", 1, 1)]

    groups, applications = _rank(matches, ["gd", "gf"])

    assert groups == [["a", "b"]]
    assert [application.rule for application in applications] == ["points", "gd", "gf"]
    assert applications[1].keys == {"a": 0, "b": 0}
    assert applications[2].keys == {"a": 1, "b": 1}


def test_singleton_point_groups_do_not_apply_remaining_rules():
    matches = [("a", "b", 1, 0)]

    groups, applications = _rank(matches, ["gd", "gf", "wins", "away", "h2h"])

    assert groups == [["a"], ["b"]]
    assert [application.rule for application in applications] == ["points"]
