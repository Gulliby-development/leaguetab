"""The --top option of the table command."""

from io import BytesIO, StringIO

import pytest

from leaguetab.cli import main

SEASON = """# a five-team league, played so far
Celtic | Dinamo | 2-2
Ajax | Celtic | 1-2
Dinamo | Ajax | 1-1
Eintracht | Benfica | 3-2
Celtic | Eintracht | 3-2
Dinamo | Eintracht | 1-1
Benfica | Ajax | 1-1
Eintracht | Ajax | 1-2
Ajax | Benfica | 1-2
Benfica | Dinamo | 0-1
Eintracht | Dinamo | 3-2
Benfica | Celtic | 2-1
"""

TIED = """Red | Blue | 1-1
Blue | Green | 1-1
Green | Red | 1-1
Gold | Red | 0-1
"""

TOP_THREE = """POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Celtic     4  2  1  1   8   7  +1    7
2    Eintracht  5  2  1  2  10  10   0    7
3    Benfica    5  2  1  2   7   7   0    7
"""


def _run(argv, text=SEASON):
    stdout = StringIO()
    stderr = StringIO()
    status = main(argv, BytesIO(text.encode("utf-8")), stdout, stderr)
    return status, stdout.getvalue(), stderr.getvalue()


def test_top_prints_only_the_first_rows():
    assert _run(["table", "--top", "3", "-"]) == (0, TOP_THREE, "")


def test_top_one_prints_the_leader_only():
    status, stdout, stderr = _run(["table", "--top=1", "-"])

    assert (status, stderr) == (0, "")
    assert (
        stdout
        == "POS  TEAM    P  W  D  L  GF  GA  GD  PTS\n1    Celtic  4  2  1  1   8   7  +1    7\n"
    )


@pytest.mark.parametrize("value", ["5", "6", "999999999"])
def test_top_at_or_above_the_team_count_prints_every_row(value):
    status, stdout, stderr = _run(["table", "--top", value, "-"])
    _, full, _ = _run(["table", "-"])

    assert (status, stderr) == (0, "")
    assert stdout == full


def test_top_keeps_the_positions_of_the_full_table():
    status, stdout, stderr = _run(["table", "--top", "2", "-"], TIED)

    assert (status, stderr) == (0, "")
    assert stdout == (
        "POS  TEAM  P  W  D  L  GF  GA  GD  PTS\n"
        "1    Red   3  1  2  0   3   2  +1    5\n"
        "2=   Blue  2  0  2  0   2   2   0    2\n"
    )


def test_top_applies_after_the_rules_and_points():
    status, stdout, stderr = _run(["table", "--rules", "h2h,gd,gf", "--top", "2", "-"])

    assert (status, stderr) == (0, "")
    assert [line.split()[1] for line in stdout.splitlines()[1:]] == ["Eintracht", "Benfica"]


def test_the_last_top_wins_in_both_forms():
    assert _run(["table", "--top", "1", "--top=3", "-"]) == (0, TOP_THREE, "")
    assert _run(["table", "--top=2", "--top", "3", "-"]) == (0, TOP_THREE, "")


def test_top_works_with_custom_points():
    status, stdout, stderr = _run(["table", "--win", "2", "--draw", "0", "--top", "1", "-"])

    assert (status, stderr) == (0, "")
    assert len(stdout.splitlines()) == 2


@pytest.mark.parametrize(
    "value", ["0", "00", "01", "-1", "+1", "1.5", "abc", "", "1000000000", " 1"]
)
def test_invalid_top_values_are_refused(value):
    status, stdout, stderr = _run(["table", "--top", value, "-"])

    shown = "".join(c if "!" <= c <= "~" else "?" for c in value)
    assert (status, stdout) == (2, "")
    assert stderr == (
        f'leaguetab: invalid --top "{shown}" (expected a whole number from 1 to 999999999)\n'
    )


def test_top_needs_a_value():
    assert _run(["table", "-", "--top"]) == (2, "", "leaguetab: --top needs a value\n")


@pytest.mark.parametrize(
    "argv",
    [
        ["why", "--top", "2", "-", "Celtic", "Ajax"],
        ["todo", "--top", "2", "-"],
    ],
)
def test_top_is_only_valid_for_table(argv):
    assert _run(argv) == (2, "", "leaguetab: --top is only valid for table\n")


def test_top_value_errors_come_before_the_table_only_error():
    assert _run(["todo", "--top", "0", "-"]) == (
        2,
        "",
        'leaguetab: invalid --top "0" (expected a whole number from 1 to 999999999)\n',
    )


def test_top_table_only_error_comes_before_the_other_todo_errors():
    assert _run(["todo", "--rules", "gd", "--top", "2", "-"]) == (
        2,
        "",
        "leaguetab: --top is only valid for table\n",
    )


def test_top_does_not_change_the_exit_status_or_the_input(tmp_path):
    results = tmp_path / "season.txt"
    results.write_bytes(SEASON.encode("utf-8"))
    before = results.read_bytes()
    stdout = StringIO()

    status = main(["table", "--top", "2", str(results)], BytesIO(b""), stdout, StringIO())

    assert status == 0
    assert results.read_bytes() == before
    assert len(stdout.getvalue().splitlines()) == 3
