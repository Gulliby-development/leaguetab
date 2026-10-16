"""Example-based tests for result-file parsing."""

import pytest

from leaguetab.results import ResultsError, parse_results


def test_bom_crlf_comments_and_surrounding_spaces_are_parsed():
    text = (
        "\ufeff# opening comment\r\n"
        " \t\r\n"
        "  Ajax \t|  FC Porto  | 2-1\r\n"
        "FC Porto | 1. FC Köln | 0-0\r\n"
        "Ajax | FC Porto | 0-0"
    )

    assert parse_results("season.txt", text) == [
        ("Ajax", "FC Porto", 2, 1),
        ("FC Porto", "1. FC Köln", 0, 0),
        ("Ajax", "FC Porto", 0, 0),
    ]


def test_empty_and_comment_only_inputs_have_no_matches():
    for text in ("", "\ufeff", "# comment", " \t\n# first\n \t\n# last\n"):
        assert parse_results("<stdin>", text) == []


def test_non_ascii_names_and_case_sensitive_names_are_distinct():
    assert parse_results(
        "<stdin>",
        "1. FC Köln | Bayern München | 0-3\nAjax | ajax | 1-0",
    ) == [
        ("1. FC Köln", "Bayern München", 0, 3),
        ("Ajax", "ajax", 1, 0),
    ]


def test_unicode_line_separator_is_not_a_physical_line_break():
    assert parse_results("<stdin>", "North\u2028South | East | 1-0") == [
        ("North\u2028South", "East", 1, 0)
    ]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("A | B", 'season.txt:1: expected "HOME | AWAY | HG-AG"'),
        ("A | B | 1-0 | extra", 'season.txt:1: expected "HOME | AWAY | HG-AG"'),
        ("|", 'season.txt:1: expected "HOME | AWAY | HG-AG"'),
        ("A | B | 1-0 | extra | data", 'season.txt:1: expected "HOME | AWAY | HG-AG"'),
    ],
)
def test_wrong_field_count_has_the_exact_error(line, expected):
    with pytest.raises(ResultsError) as error:
        parse_results("season.txt", line)

    assert str(error.value) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (" | B | 1-0", 'results.txt:1: invalid team name ""'),
        ("A |  | 1-0", 'results.txt:1: invalid team name ""'),
        ("A\tB | C | 1-0", 'results.txt:1: invalid team name "A?B"'),
        ("A | B\tC | 1-0", 'results.txt:1: invalid team name "B?C"'),
        ("A\x01B | C | 1-0", 'results.txt:1: invalid team name "A?B"'),
        ("A | B\x1fC | 1-0", 'results.txt:1: invalid team name "B?C"'),
        ("A\x7fB | C | 1-0", 'results.txt:1: invalid team name "A?B"'),
        ("\u00e9 | \u00e9\x00x | 1-0", 'results.txt:1: invalid team name "??x"'),
    ],
)
def test_invalid_team_names_are_checked_home_then_away(line, expected):
    with pytest.raises(ResultsError) as error:
        parse_results("results.txt", line)

    assert str(error.value) == expected


@pytest.mark.parametrize(
    ("score", "quoted"),
    [
        ("2:1", "2:1"),
        ("2 -- 1", "2?--?1"),
        ("-1-2", "-1-2"),
        ("01-1", "01-1"),
        ("1-01", "1-01"),
        ("", ""),
        ("1-", "1-"),
        ("-1", "-1"),
        ("١-1", "?-1"),
        ("1000000000-1", "1000000000-1"),
        ("2-1 extra", "2-1?extra"),
        ("2--1", "2--1"),
    ],
)
def test_invalid_scores_have_the_exact_error(score, quoted):
    line = f"A | B | {score}"
    expected = (
        f'results.txt:1: invalid score "{quoted}" '
        "(expected HG-AG, for example 2-1)"
    )

    with pytest.raises(ResultsError) as error:
        parse_results("results.txt", line)

    assert str(error.value) == expected


@pytest.mark.parametrize(
    ("score", "home_goals", "away_goals"),
    [
        ("0-0", 0, 0),
        ("1-2", 1, 2),
        ("999999999-0", 999999999, 0),
    ],
)
def test_canonical_ascii_scores_include_zero_and_nine_digit_boundary(
    score, home_goals, away_goals
):
    assert parse_results("<stdin>", f"A | B | {score}") == [
        ("A", "B", home_goals, away_goals)
    ]


def test_bad_home_name_precedes_bad_away_name_and_score():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "A\x00 | B\x00 | invalid")

    assert str(error.value) == '<stdin>:1: invalid team name "A?"'


def test_bad_away_name_precedes_invalid_score():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "A | B\x7f | 01-0")

    assert str(error.value) == '<stdin>:1: invalid team name "B?"'


def test_invalid_score_precedes_self_play_error():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "same | same | 2:1")

    assert str(error.value) == (
        '<stdin>:1: invalid score "2:1" (expected HG-AG, for example 2-1)'
    )


def test_valid_score_on_self_play_reports_self_play():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "same | same | 2-1")

    assert str(error.value) == '<stdin>:1: team "same" plays itself'


def test_line_numbers_include_blank_and_comment_lines():
    with pytest.raises(ResultsError) as error:
        parse_results("season.txt", "# comment\n \t\nA | B")

    assert str(error.value) == 'season.txt:3: expected "HOME | AWAY | HG-AG"'


def test_one_cr_before_lf_is_removed():
    assert parse_results("<stdin>", "A | B | 1-0\r\n") == [("A", "B", 1, 0)]


def test_only_one_cr_before_lf_is_removed():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "A | B | 1-0\r\r\n")

    assert str(error.value) == (
        '<stdin>:1: invalid score "1-0?" (expected HG-AG, for example 2-1)'
    )


def test_terminal_cr_is_not_treated_as_a_crlf_terminator():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "A | B | 1-0\r")

    assert str(error.value) == (
        '<stdin>:1: invalid score "1-0?" (expected HG-AG, for example 2-1)'
    )


def test_physical_line_number_advances_only_at_lf():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "A\u2028| B | 1-0\nnot a result")

    assert str(error.value) == '<stdin>:2: expected "HOME | AWAY | HG-AG"'
