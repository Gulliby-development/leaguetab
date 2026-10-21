"""Regression tests for web-table score dash characters."""

from io import BytesIO, StringIO

import pytest

from leaguetab.cli import main
from leaguetab.results import ResultsError, parse_results


@pytest.mark.parametrize(
    "score",
    [
        "2\u20131",
        "2 \u2013 1",
        "2\t\u2212\t1",
        "2\u22121",
        "2-1",
    ],
)
def test_web_table_dashes_parse_as_score_separators(score):
    assert parse_results("<stdin>", "Ajax | Celtic | " + score) == [("Ajax", "Celtic", 2, 1)]


@pytest.mark.parametrize(
    ("score", "quoted"),
    [
        ("2\u20132\u20131", "2?2?1"),
        ("2\u20141", "2?1"),
        ("2\u20101", "2?1"),
        ("\u20131", "?1"),
        ("1\u2013", "1?"),
        ("2-\u20131", "2-?1"),
        ("2\u2013 \u22121", "2???1"),
        ("-\u2212", "-?"),
    ],
)
def test_other_dash_forms_remain_invalid_with_original_diagnostics(score, quoted):
    expected = f'results.txt:1: invalid score "{quoted}" (expected HG-AG, for example 2-1)'

    with pytest.raises(ResultsError) as error:
        parse_results("results.txt", "A | B | " + score)

    assert str(error.value) == expected


def test_table_command_accepts_web_table_dashes_from_utf8_stdin():
    stdin = BytesIO(("Ajax | Celtic | 1\u20132\nCeltic | Ajax | 0 \u2212 0\n").encode())
    stdout = StringIO()
    stderr = StringIO()

    status = main(["table", "-"], stdin=stdin, stdout=stdout, stderr=stderr)

    assert status == 0
    assert stderr.getvalue() == ""
    assert stdout.getvalue() == (
        "POS  TEAM    P  W  D  L  GF  GA  GD  PTS\n"
        "1    Celtic  2  1  1  0   2   1  +1    4\n"
        "2    Ajax    2  0  1  1   1   2  -1    1\n"
    )
