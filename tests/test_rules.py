"""Example-based tests for tie-break rule parsing and keys."""

import pytest

from leaguetab.rules import key, parse_rules


@pytest.mark.parametrize(
    ("rule",),
    [("gd",), ("gf",), ("wins",), ("away",), ("h2h",)],
)
def test_each_rule_is_valid_on_its_own(rule):
    assert parse_rules(rule) == [rule]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("gd,gf", ["gd", "gf"]),
        ("h2h,gd,gf", ["h2h", "gd", "gf"]),
        ("away,wins,gf,gd,h2h", ["away", "wins", "gf", "gd", "h2h"]),
        ("wins,away,h2h,gf,gd", ["wins", "away", "h2h", "gf", "gd"]),
    ],
)
def test_parse_rules_preserves_combined_and_permuted_order(text, expected):
    assert parse_rules(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        ",gd",
        "gd,",
        "gd,,gf",
        "gd,gd",
        "h2h,h2h",
        "unknown",
        "gd, gf",
        " gd",
        "gd ",
    ],
)
def test_invalid_rules_raise_the_exact_parse_error(text):
    with pytest.raises(ValueError, match=r"^invalid rules$"):
        parse_rules(text)


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ("gd", 3),
        ("gf", 8),
        ("wins", 2),
        ("away", 5),
        ("h2h", (7, 3, 8)),
    ],
)
def test_rule_keys_use_the_documented_team_statistics(rule, expected):
    stats = {
        "Alpha": {"PTS": 7, "GD": 3, "GF": 8, "W": 2, "away": 5},
    }

    assert key(rule, "Alpha", stats) == expected


def test_h2h_key_uses_only_the_supplied_subgroup_record():
    stats = {
        "Alpha": {"PTS": 12, "GD": 8, "GF": 20, "W": 4, "away": 7},
        "Beta": {"PTS": 10, "GD": 5, "GF": 14, "W": 3, "away": 6},
    }
    subgroup_stats = {
        "Alpha": {"PTS": 3, "GD": 1, "GF": 2},
        "Beta": {"PTS": 0, "GD": -1, "GF": 1},
    }

    assert key("h2h", "Alpha", stats, subgroup_stats) == (3, 1, 2)
    assert key("h2h", "Beta", stats, subgroup_stats) == (0, -1, 1)


def test_h2h_key_defaults_to_the_team_record_when_no_subgroup_is_given():
    stats = {"Alpha": {"PTS": 7, "GD": 3, "GF": 8}}

    assert key("h2h", "Alpha", stats) == (7, 3, 8)


@pytest.mark.parametrize(
    ("team", "subgroup_stats"),
    [
        ("Beta", {}),
        ("Beta", {"Alpha": {"PTS": 3, "GD": 1, "GF": 2}}),
    ],
)
def test_h2h_key_is_zero_when_team_has_no_subgroup_match(team, subgroup_stats):
    stats = {"Beta": {"PTS": 9, "GD": 4, "GF": 10}}

    assert key("h2h", team, stats, subgroup_stats) == (0, 0, 0)


def test_unknown_rule_key_has_an_exact_error():
    with pytest.raises(ValueError, match=r"^unknown rule$"):
        key("unknown", "Alpha", {"Alpha": {"PTS": 0, "GD": 0, "GF": 0}})
