"""Example-based tests for score whitespace around the dash."""

from io import BytesIO, StringIO

import pytest

from leaguetab.cli import main
from leaguetab.results import ResultsError, parse_results

WORKED_EXAMPLE = (
    "Ajax | Celtic | 1 - 2\n"
    "Celtic | Ajax | 0 -0\n"
    "Dinamo | Ajax | 3- 3\n"
    "Celtic | Dinamo | 2 -1\n"
)

WORKED_TABLE = (
    "POS  TEAM    P  W  D  L  GF  GA  GD  PTS\n"
    "1    Celtic  3  2  1  0   4   2  +2    7\n"
    "2    Ajax    3  0  2  1   4   5  -1    2\n"
    "3    Dinamo  2  0  1  1   4   5  -1    1\n"
)


def _run(argv, contents=b""):
    stdout = StringIO()
    stderr = StringIO()
    status = main(
        argv,
        stdin=BytesIO(contents),
        stdout=stdout,
        stderr=stderr,
    )
    return status, stdout.getvalue(), stderr.getvalue()


@pytest.mark.parametrize(
    "score",
    [
        "2 - 1",
        "2- 1",
        "2 -1",
        "2\t-\t1",
        "2\t- 1",
    ],
)
def test_score_parts_allow_space_and_tab_padding(score):
    assert parse_results("<stdin>", f"Ajax | Celtic | {score}") == [
        ("Ajax", "Celtic", 2, 1)
    ]


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        ("Ajax | Celtic | 0 - 0", [("Ajax", "Celtic", 0, 0)]),
        (
            "Ajax | Celtic | 999999999 - 0\nCeltic | Ajax | 0 - 999999999",
            [("Ajax", "Celtic", 999999999, 0), ("Celtic", "Ajax", 0, 999999999)],
        ),
    ],
)
def test_zero_and_nine_digit_boundaries_are_valid(results, expected):
    assert parse_results("<stdin>", results) == expected


def test_crlf_lines_allow_tabs_around_the_dash():
    assert parse_results(
        "<stdin>",
        "# comment\r\nAjax | Celtic | 2 \t- \t1\r\n",
    ) == [("Ajax", "Celtic", 2, 1)]


def test_spaced_and_plain_scores_produce_the_same_matches_and_table():
    plain = b"A | B | 1-0\nB | C | 0-0\n"
    spaced = b"A | B | 1 - 0\nB | C | 0 -0\n"

    assert parse_results("<stdin>", plain.decode()) == parse_results(
        "<stdin>", spaced.decode()
    )
    assert _run(["table", "-"], spaced) == _run(["table", "-"], plain)


def test_worked_example_produces_the_exact_supplied_table():
    status, stdout, stderr = _run(["table", "-"], WORKED_EXAMPLE.encode())

    assert (status, stdout, stderr) == (0, WORKED_TABLE, "")


def test_why_accepts_a_spaced_score():
    status, stdout, stderr = _run(
        ["why", "-", "Ajax", "Celtic"],
        b"Ajax | Celtic | 2 - 1\n",
    )

    assert (status, stdout, stderr) == (
        0,
        "points: Ajax 3, Celtic 0\nAjax is ahead of Celtic on points\n",
        "",
    )


def test_todo_accepts_a_spaced_score():
    status, stdout, stderr = _run(
        ["todo", "--legs", "1", "-"],
        b"Ajax | Celtic | 2 - 1\n",
    )

    assert (status, stdout, stderr) == (0, "all fixtures played\n", "")


@pytest.mark.parametrize(
    ("score", "quoted"),
    [
        ("21", "21"),
        ("2 -- 1", "2?--?1"),
        ("- 1", "-?1"),
        ("2 -", "2?-"),
        ("+2 - -1", "+2?-?-1"),
        ("2 3 - 1", "2?3?-?1"),
        ("2x - 1", "2x?-?1"),
        ("2 - 1 extra", "2?-?1?extra"),
        ("01 - 01", "01?-?01"),
        ("1000000000 - 1", "1000000000?-?1"),
        ("2 : 1", "2?:?1"),
        ("2\u00a0-\u00a01", "2?-?1"),
    ],
)
def test_invalid_scores_keep_the_exact_error(score, quoted):
    expected = (
        f'results.txt:1: invalid score "{quoted}" '
        "(expected HG-AG, for example 2-1)"
    )

    with pytest.raises(ResultsError) as error:
        parse_results("results.txt", f"A | B | {score}")

    assert str(error.value) == expected


def test_error_line_number_advances_after_a_spaced_score():
    with pytest.raises(ResultsError) as error:
        parse_results(
            "season.txt",
            "# comment\nAjax | Celtic | 2 - 1\nA | B | 2 -- 1",
        )

    assert str(error.value) == (
        'season.txt:3: invalid score "2?--?1" '
        "(expected HG-AG, for example 2-1)"
    )


def test_self_play_error_follows_a_valid_spaced_score():
    with pytest.raises(ResultsError) as error:
        parse_results("<stdin>", "same | same | 2 \t- 1")

    assert str(error.value) == '<stdin>:1: team "same" plays itself'


def test_stdin_error_has_exit_two_empty_stdout_and_exact_stderr():
    status, stdout, stderr = _run(
        ["table", "-"],
        b"Ajax | Celtic | 1 -- 2\n",
    )

    assert (status, stdout, stderr) == (
        2,
        "",
        (
            'leaguetab: <stdin>:1: invalid score "1?--?2" '
            "(expected HG-AG, for example 2-1)\n"
        ),
    )
