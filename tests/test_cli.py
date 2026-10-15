"""In-memory CLI integration examples for leaguetab."""

import ast
from io import BytesIO, StringIO
from pathlib import Path

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

TABLE = """POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Celtic     4  2  1  1   8   7  +1    7
2    Eintracht  5  2  1  2  10  10   0    7
3    Benfica    5  2  1  2   7   7   0    7
4    Dinamo     5  1  3  1   7   7   0    6
5    Ajax       5  1  2  2   6   7  -1    5
"""

TABLE_H2H = """POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Eintracht  5  2  1  2  10  10   0    7
2    Benfica    5  2  1  2   7   7   0    7
3    Celtic     4  2  1  1   8   7  +1    7
4    Dinamo     5  1  3  1   7   7   0    6
5    Ajax       5  1  2  2   6   7  -1    5
"""

WHY_H2H = """points: Benfica 7, Celtic 7
h2h (3 teams): Benfica 3/0/4, Celtic 3/0/4
h2h (2 teams): Benfica 3/+1/2, Celtic 0/-1/1
Benfica is ahead of Celtic on h2h
"""

TODO = """Ajax - Dinamo
Ajax - Eintracht
Benfica - Eintracht
Celtic - Ajax
Celtic - Benfica
Dinamo - Benfica
Dinamo - Celtic
Eintracht - Celtic
8 fixtures missing
"""


def _run(argv, input_bytes=b""):
    stdout = StringIO()
    stderr = StringIO()
    status = main(
        argv,
        stdin=BytesIO(input_bytes),
        stdout=stdout,
        stderr=stderr,
    )
    return status, stdout.getvalue(), stderr.getvalue()


def _write_results(tmp_path, contents):
    path = tmp_path / "season.txt"
    if isinstance(contents, bytes):
        path.write_bytes(contents)
    else:
        path.write_text(contents, encoding="utf-8", newline="")
    return str(path)


def _package_directory():
    return Path(__file__).resolve().parents[1] / "leaguetab"


def test_package_has_exactly_the_requested_python_modules_and_empty_initializer():
    package = _package_directory()

    assert sorted([path.name for path in package.glob("*.py")]) == [
        "__init__.py",
        "__main__.py",
        "args.py",
        "cli.py",
        "fixtures.py",
        "ranking.py",
        "report.py",
        "results.py",
        "rules.py",
        "stats.py",
        "text.py",
    ]
    assert package.joinpath("__init__.py").read_text(encoding="utf-8") == ""


def test_entry_point_reconfigures_both_standard_streams_for_utf8_lf():
    entry_point = _package_directory().joinpath("__main__.py").read_text(encoding="utf-8")

    assert r'sys.stdout.reconfigure(encoding="utf-8", newline="\n")' in entry_point
    assert r'sys.stderr.reconfigure(encoding="utf-8", newline="\n")' in entry_point
    assert "sys.exit(main(sys.argv[1:]))" in entry_point


def test_production_source_avoids_prohibited_imports_and_environment_reads():
    forbidden_modules = {"argparse", "subprocess", "random"}
    package = _package_directory()

    for source_path in package.glob("*.py"):
        source = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(source):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules
            elif isinstance(node, ast.ImportFrom):
                assert node.module not in forbidden_modules
            elif isinstance(node, ast.Attribute):
                assert node.attr not in {"environ", "getenv", "putenv"}


def test_help_as_the_only_argument_has_exact_usage_and_status():
    status, stdout, stderr = _run(["--help"])

    assert (status, stdout, stderr) == (
        0,
        (
            "usage: leaguetab table [--win N] [--draw N] [--rules LIST] RESULTS\n"
            "       leaguetab why [--win N] [--draw N] [--rules LIST] RESULTS TEAM TEAM\n"
            "       leaguetab todo [--legs N] RESULTS\n"
        ),
        "",
    )


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "missing command (table, why or todo)"),
        (["tabel"], 'unknown command "tabel"'),
        (["--help", "table"], 'unknown command "--help"'),
    ],
)
def test_command_selection_errors_are_exact(argv, message):
    status, stdout, stderr = _run(argv)

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["table", "--help", "-"], 'unknown option "--help"'),
        (["table", "--unknown", "-"], 'unknown option "--unknown"'),
        (["todo", "-abc", "-"], 'unknown option "-abc"'),
    ],
)
def test_help_elsewhere_and_unknown_options_are_scan_errors(argv, message):
    status, stdout, stderr = _run(argv, b"A | B | 1-0\n")

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


@pytest.mark.parametrize(
    ("option", "message"),
    [
        ("--win", "--win needs a value"),
        ("--draw", "--draw needs a value"),
        ("--rules", "--rules needs a value"),
        ("--legs", "--legs needs a value"),
    ],
)
def test_each_option_requires_a_value(option, message):
    status, stdout, stderr = _run(["table", "-", option])

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        (
            "--win",
            "03",
            'invalid --win "03" (expected a whole number of at most 9 digits)',
        ),
        (
            "--draw",
            "-1",
            'invalid --draw "-1" (expected a whole number of at most 9 digits)',
        ),
        (
            "--rules",
            "gd,gd",
            'invalid --rules "gd,gd" (expected a comma-separated list of gd, gf, wins, away and h2h without repeats)',
        ),
        ("--legs", "3", 'invalid --legs "3" (expected 1 or 2)'),
    ],
)
def test_invalid_option_values_have_exact_messages(option, value, message):
    status, stdout, stderr = _run(["table", option, value, "-"])

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (
            ["table", "--win", "03", "--draw", "00", "--rules", "bad", "--legs", "4", "-"],
            'invalid --win "03" (expected a whole number of at most 9 digits)',
        ),
        (
            ["table", "--draw", "00", "--rules", "bad", "--legs", "4", "-"],
            'invalid --draw "00" (expected a whole number of at most 9 digits)',
        ),
        (
            ["table", "--rules", "gd,,gf", "--legs", "4", "-"],
            'invalid --rules "gd,,gf" (expected a comma-separated list of gd, gf, wins, away and h2h without repeats)',
        ),
        (
            ["table", "--legs", "4", "--win", "0"],
            'invalid --legs "4" (expected 1 or 2)',
        ),
    ],
)
def test_option_validation_precedes_compatibility_and_arity(argv, message):
    status, stdout, stderr = _run(argv)

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["table", "--legs", "1"], "--legs is only valid for todo"),
        (["why", "--legs=2", "-"], "--legs is only valid for todo"),
        (["todo", "--win", "3", "-"], "--win is only valid for table and why"),
        (["todo", "--draw=1", "-"], "--draw is only valid for table and why"),
        (["todo", "--rules", "gd", "-"], "--rules is only valid for table and why"),
        (
            ["todo", "--win", "3", "--draw", "1", "--rules", "gd", "-"],
            "--win is only valid for table and why",
        ),
        (
            ["table", "--legs", "2", "--win", "3"],
            "--legs is only valid for todo",
        ),
    ],
)
def test_option_compatibility_errors_precede_arity_and_file_access(argv, message):
    status, stdout, stderr = _run(argv)

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["table"], "missing RESULTS"),
        (["todo"], "missing RESULTS"),
        (["why"], "missing RESULTS"),
        (["why", "-"], "missing TEAM"),
        (["why", "-", "A"], "missing TEAM"),
        (["why", "-", "A", "B", "C"], "too many arguments"),
        (["table", "-", "extra"], "too many arguments"),
        (["todo", "-", "extra"], "too many arguments"),
    ],
)
def test_command_arity_messages_are_exact(argv, message):
    status, stdout, stderr = _run(argv)

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


def test_last_option_value_wins_and_inline_and_separate_forms_work(tmp_path):
    path = _write_results(tmp_path, "A | B | 1-0\n")

    status, stdout, stderr = _run(
        ["table", "--win", "7", "--win=4", "--draw=0", str(path)]
    )

    assert status == 0
    assert stderr == ""
    assert "1    A     1  1  0  0   1   0  +1    4\n" in stdout


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("--win", "-1", 'invalid --win "-1" (expected a whole number of at most 9 digits)'),
        (
            "--rules",
            "-x",
            'invalid --rules "-x" (expected a comma-separated list of gd, gf, wins, away and h2h without repeats)',
        ),
        ("--legs", "-1", 'invalid --legs "-1" (expected 1 or 2)'),
    ],
)
def test_option_consumes_a_dash_prefixed_separate_value(option, value, message):
    status, stdout, stderr = _run(["table", option, value, "-"])

    assert (status, stdout, stderr) == (2, "", f"leaguetab: {message}\n")


def test_nonexistent_results_file_reports_slash_normalized_path():
    display_path = "folder\\missing-season.txt"

    status, stdout, stderr = _run(["table", display_path])

    assert (status, stdout, stderr) == (
        2,
        "",
        "leaguetab: folder/missing-season.txt: cannot read the file\n",
    )


def test_invalid_utf8_file_has_exact_error_and_no_stdout(tmp_path):
    path = _write_results(tmp_path, b"A | B | \xff\n")

    status, stdout, stderr = _run(["table", path])

    assert (status, stdout, stderr) == (
        2,
        "",
        f"leaguetab: {path.replace(chr(92), '/')}: input is not valid UTF-8\n",
    )


@pytest.mark.parametrize(
    "contents",
    ["", "  \t\n", "# comment only\n# another comment\n"],
)
def test_empty_results_have_no_matches_error(tmp_path, contents):
    path = _write_results(tmp_path, contents)

    status, stdout, stderr = _run(["table", path])

    assert (status, stdout, stderr) == (
        2,
        "",
        f"leaguetab: {path.replace(chr(92), '/')}: no matches\n",
    )


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("A | B", 'expected "HOME | AWAY | HG-AG"'),
        ("A | B | 1-0 | extra", 'expected "HOME | AWAY | HG-AG"'),
        ("A\tX | B | 1-0", 'invalid team name "A?X"'),
        ("A | B\x7f | 1-0", 'invalid team name "B?"'),
        ("A | B | 2:1", 'invalid score "2:1" (expected HG-AG, for example 2-1)'),
        ("same | same | 2:1", 'invalid score "2:1" (expected HG-AG, for example 2-1)'),
        ("same | same | 2-1", 'team "same" plays itself'),
    ],
)
def test_first_bad_results_line_is_reported_exactly(line, message):
    status, stdout, stderr = _run(["table", "-"], line.encode("utf-8"))

    assert (status, stdout, stderr) == (
        2,
        "",
        f"leaguetab: <stdin>:1: {message}\n",
    )


def test_line_error_counts_blank_and_comment_physical_lines():
    status, stdout, stderr = _run(["table", "-"], b"# comment\n \t\nA | B")

    assert (status, stdout, stderr) == (
        2,
        "",
        'leaguetab: <stdin>:3: expected "HOME | AWAY | HG-AG"\n',
    )


def test_first_team_name_error_precedes_away_name_and_score_errors():
    status, stdout, stderr = _run(["table", "-"], b"\t | B\x7f | 01-0\n")

    assert (status, stdout, stderr) == (
        2,
        "",
        'leaguetab: <stdin>:1: invalid team name ""\n',
    )


def test_unknown_team_checks_first_query_team_before_second(tmp_path):
    path = _write_results(tmp_path, "A | B | 1-0\n")

    status, stdout, stderr = _run(["why", path, "missing-first", "missing-second"])

    assert (status, stdout, stderr) == (2, "", 'leaguetab: unknown team "missing-first"\n')


def test_unknown_second_team_is_reported_after_known_first_team(tmp_path):
    path = _write_results(tmp_path, "A | B | 1-0\n")

    status, stdout, stderr = _run(["why", path, "A", "missing"])

    assert (status, stdout, stderr) == (2, "", 'leaguetab: unknown team "missing"\n')


def test_same_known_team_is_rejected_after_membership_checks(tmp_path):
    path = _write_results(tmp_path, "A | B | 1-0\n")

    status, stdout, stderr = _run(["why", path, "A", "A"])

    assert (status, stdout, stderr) == (2, "", "leaguetab: choose two different teams\n")


def test_stdin_dash_accepts_bom_and_crlf_and_writes_only_lf():
    contents = b"\xef\xbb\xbf1. FC K\xc3\xb6ln |  Bayern M\xc3\xbcnchen  | 0-3\r\n"

    status, stdout, stderr = _run(["table", "-"], contents)

    assert (status, stderr, stdout.count("\r")) == (0, "", 0)
    assert stdout == (
        "POS  TEAM            P  W  D  L  GF  GA  GD  PTS\n"
        "1    Bayern München  1  1  0  0   3   0  +3    3\n"
        "2    1. FC Köln      1  0  0  1   0   3  -3    0\n"
    )


def test_successful_table_does_not_modify_its_input_file(tmp_path):
    original = b"\xef\xbb\xbfA | B | 2-0\r\n"

    path = _write_results(tmp_path, original)
    status, stdout, stderr = _run(["table", path])

    assert status == 0
    assert stderr == ""
    assert "1    A     1  1  0  0   2   0  +2    3\n" in stdout
    assert (tmp_path / "season.txt").read_bytes() == original


def test_default_table_matches_the_supplied_season_output(tmp_path):
    path = _write_results(tmp_path, SEASON)

    status, stdout, stderr = _run(["table", path])

    assert (status, stdout, stderr) == (0, TABLE, "")


def test_table_keeps_shared_positions_and_skips_the_next_rank(tmp_path):
    path = _write_results(tmp_path, "A | D | 1-0\nB | C | 0-0\n")

    status, stdout, stderr = _run(["table", path])

    assert (status, stdout, stderr) == (
        0,
        (
            "POS  TEAM  P  W  D  L  GF  GA  GD  PTS\n"
            "1    A     1  1  0  0   1   0  +1    3\n"
            "2=   B     1  0  1  0   0   0   0    1\n"
            "2=   C     1  0  1  0   0   0   0    1\n"
            "4    D     1  0  0  1   0   1  -1    0\n"
        ),
        "",
    )


def test_h2h_table_matches_the_supplied_season_output(tmp_path):
    path = _write_results(tmp_path, SEASON)

    status, stdout, stderr = _run(["table", "--rules", "h2h,gd,gf", path])

    assert (status, stdout, stderr) == (0, TABLE_H2H, "")


def test_custom_scoring_zero_points_are_rendered(tmp_path):
    path = _write_results(tmp_path, "A | B | 1-0\n")

    status, stdout, stderr = _run(["table", "--win=0", "--draw=0", path])

    assert status == 0
    assert stderr == ""
    assert "1    A     1  1  0  0   1   0  +1    0\n" in stdout
    assert "2    B     1  0  0  1   0   1  -1    0\n" in stdout


@pytest.mark.parametrize(
    ("argv", "contents", "expected"),
    [
        (
            ["why", "-", "A", "B"],
            b"A | B | 1-0\n",
            "points: A 3, B 0\nA is ahead of B on points\n",
        ),
        (
            ["why", "--rules", "gd", "-", "A", "C"],
            b"A | B | 2-0\nB | C | 1-0\nC | A | 1-0\n",
            "points: A 3, C 3\ngd (3 teams): A +1, C 0\nA is ahead of C on gd\n",
        ),
        (
            ["why", "--rules", "gf", "-", "C", "B"],
            b"A | B | 1-1\nB | C | 2-2\nC | A | 3-3\n",
            "points: C 2, B 2\ngf (3 teams): C 5, B 3\nC is ahead of B on gf\n",
        ),
        (
            ["why", "--rules", "wins", "-", "A", "B"],
            (
                b"A | X | 1-0\nA | Y | 1-0\nB | P | 0-0\nB | Q | 0-0\n"
                b"B | R | 0-0\nB | S | 0-0\nB | T | 0-0\nB | U | 0-0\n"
            ),
            "points: A 6, B 6\nwins (2 teams): A 2, B 0\nA is ahead of B on wins\n",
        ),
        (
            ["why", "--rules", "away", "-", "A", "B"],
            b"A | B | 1-1\nB | A | 2-2\n",
            "points: A 2, B 2\naway (2 teams): A 2, B 1\nA is ahead of B on away\n",
        ),
    ],
)
def test_why_explains_each_rule_with_exact_lines(argv, contents, expected):
    status, stdout, stderr = _run(argv, contents)

    assert (status, stdout, stderr) == (0, expected, "")


def test_h2h_why_matches_the_supplied_recomputed_subgroup_output():
    status, stdout, stderr = _run(
        ["why", "--rules", "h2h,gd,gf", "-", "Benfica", "Celtic"],
        SEASON.encode("utf-8"),
    )

    assert (status, stdout, stderr) == (0, WHY_H2H, "")


def test_why_output_is_independent_of_argument_order():
    contents = b"A | B | 1-0\n"
    first = _run(["why", "-", "A", "B"], contents)
    reversed_query = _run(["why", "-", "B", "A"], contents)

    assert first == reversed_query == (
        0,
        "points: A 3, B 0\nA is ahead of B on points\n",
        "",
    )


def test_why_reports_level_teams_and_all_unsplit_rules():
    status, stdout, stderr = _run(
        ["why", "-", "b", "a"],
        b"a | b | 1-1\n",
    )

    assert (status, stdout, stderr) == (
        0,
        (
            "points: a 1, b 1\n"
            "gd (2 teams): a 0, b 0\n"
            "gf (2 teams): a 1, b 1\n"
            "a and b are level\n"
        ),
        "",
    )


def test_why_omits_rule_applications_from_groups_without_both_teams():
    status, stdout, stderr = _run(
        ["why", "--rules", "gd,gf", "-", "A", "B"],
        b"A | X | 2-0\nB | Y | 1-0\n",
    )

    assert (status, stdout, stderr) == (
        0,
        "points: A 3, B 3\ngd (2 teams): A +2, B +1\nA is ahead of B on gd\n",
        "",
    )


def test_todo_default_legs_matches_supplied_schedule_and_status(tmp_path):
    path = _write_results(tmp_path, SEASON)

    status, stdout, stderr = _run(["todo", path])

    assert (status, stdout, stderr) == (1, TODO, "")


def test_todo_one_leg_matches_supplied_complete_schedule(tmp_path):
    path = _write_results(tmp_path, SEASON)

    status, stdout, stderr = _run(["todo", "--legs=1", path])

    assert (status, stdout, stderr) == (0, "all fixtures played\n", "")


def test_todo_reports_singular_missing_fixture(tmp_path):
    path = _write_results(tmp_path, "A | B | 1-0\nB | C | 1-0\n")

    status, stdout, stderr = _run(["todo", "--legs", "1", path])

    assert (status, stdout, stderr) == (1, "A - C\n1 fixture missing\n", "")


def test_todo_one_leg_orders_pairs_and_accepts_either_venue(tmp_path):
    path = _write_results(tmp_path, "Z | A | 1-0\nB | Z | 1-0\n")

    status, stdout, stderr = _run(["todo", "--legs", "1", path])

    assert (status, stdout, stderr) == (1, "A - B\n1 fixture missing\n", "")


def test_todo_two_legs_lists_each_missing_direction(tmp_path):
    path = _write_results(tmp_path, "B | A | 1-0\n")

    status, stdout, stderr = _run(["todo", "--legs", "2", path])

    assert (status, stdout, stderr) == (1, "A - B\n1 fixture missing\n", "")
