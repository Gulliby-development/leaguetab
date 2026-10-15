"""Command-line application for standings, explanations and fixtures."""

import sys
from collections.abc import Sequence
from typing import BinaryIO, TextIO

from .args import USAGE, Arguments, UsageError, parse_args
from .fixtures import missing
from .ranking import rank
from .report import table_report, why_report
from .results import ResultsError, parse_results
from .stats import calculate
from .text import quote


def _read_input(arguments: Arguments, stdin: BinaryIO) -> tuple[str, str]:
    """Read input bytes and return its display name and decoded UTF-8 text."""
    assert arguments.results is not None
    display = "<stdin>" if arguments.results == "-" else arguments.results.replace("\\", "/")
    try:
        if arguments.results == "-":
            contents = stdin.read()
        else:
            with open(arguments.results, "rb") as results_file:
                contents = results_file.read()
    except OSError as error:
        raise ResultsError(f"{display}: cannot read the file") from error

    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ResultsError(f"{display}: input is not valid UTF-8") from error
    return display, text


def _write_error(stderr: TextIO, message: str) -> int:
    stderr.write(f"leaguetab: {message}\n")
    return 2


def main(
    argv: Sequence[str],
    stdin: BinaryIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run leaguetab with injectable streams and return its process status."""
    input_stream = sys.stdin.buffer if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr

    try:
        arguments = parse_args(argv)
    except UsageError as error:
        return _write_error(error_stream, str(error))

    if arguments.help:


        output_stream.write(f"{USAGE}\n")
        return 0

    try:
        display, input_text = _read_input(arguments, input_stream)
        matches = parse_results(display, input_text)
        if not matches:
            raise ResultsError(f"{display}: no matches")
    except ResultsError as error:
        return _write_error(error_stream, str(error))

    if arguments.command == "todo":
        fixtures = missing(matches, arguments.legs)
        if fixtures:
            lines = [f"{home} - {away}" for home, away in fixtures]
            count = len(fixtures)
            noun = "fixture" if count == 1 else "fixtures"
            lines.append(f"{count} {noun} missing")
            status = 1
        else:
            lines = ["all fixtures played"]
            status = 0
        output_stream.write("\n".join(lines) + "\n")
        return status

    stats = calculate(matches, win=arguments.win, draw=arguments.draw)
    tie_groups, applications = rank(
        matches,
        stats,
        arguments.rules,
        win=arguments.win,
        draw=arguments.draw,
    )

    if arguments.command == "table":
        output_stream.write(table_report(stats, tie_groups) + "\n")
        return 0

    first_team, second_team = arguments.teams
    if first_team not in stats:
        return _write_error(error_stream, f"unknown team {quote(first_team)}")
    if second_team not in stats:
        return _write_error(error_stream, f"unknown team {quote(second_team)}")
    if first_team == second_team:
        return _write_error(error_stream, "choose two different teams")

    output_stream.write("\n".join(why_report(first_team, second_team, tie_groups, applications)) + "\n")
    return 0
