"""Manual command-line argument parsing for leaguetab."""

from collections.abc import Sequence
from dataclasses import dataclass

from leaguetab.rules import parse_rules
from leaguetab.text import is_whole_number, quote

USAGE = (
    "usage: leaguetab table [--win N] [--draw N] [--rules LIST] RESULTS\n"
    "       leaguetab why [--win N] [--draw N] [--rules LIST] RESULTS TEAM TEAM\n"
    "       leaguetab todo [--legs N] RESULTS"
)

_OPTION_NAMES = ("win", "draw", "rules", "legs")
_RULES_ERROR = (
    "invalid --rules {value} (expected a comma-separated list of gd, gf, "
    "wins, away and h2h without repeats)"
)


class UsageError(ValueError):
    """A command-line usage error with the exact user-facing message."""


@dataclass(frozen=True)
class Arguments:
    """Validated command-line values returned by :func:`parse_args`."""

    command: str | None
    results: str | None
    teams: tuple[str, ...]
    win: int
    draw: int
    rules: tuple[str, ...]
    legs: int
    supplied: frozenset[str]
    help: bool = False

    @property
    def options(self) -> dict[str, object]:
        """Return validated option values keyed by their option names."""
        return {
            "win": self.win,
            "draw": self.draw,
            "rules": self.rules,
            "legs": self.legs,
        }


def _option_error(name: str, value: str) -> UsageError:
    return UsageError(
        f'invalid --{name} {quote(value)} (expected a whole number of at most 9 digits)'
    )


def _scan_options(argv: Sequence[str]) -> tuple[dict[str, str], set[str], list[str]]:
    values = {"win": "3", "draw": "1", "rules": "gd,gf", "legs": "2"}
    supplied: set[str] = set()
    positional: list[str] = []
    index = 0

    while index < len(argv):
        argument = argv[index]
        if argument == "-" or not argument.startswith("-"):
            positional.append(argument)
            index += 1
            continue

        if argument.startswith("--"):
            option, separator, inline_value = argument[2:].partition("=")
            if option in _OPTION_NAMES:
                supplied.add(option)
                if separator:
                    values[option] = inline_value
                    index += 1
                elif index + 1 < len(argv):
                    values[option] = argv[index + 1]
                    index += 2
                else:
                    raise UsageError(f"--{option} needs a value")
                continue

        raise UsageError(f"unknown option {quote(argument)}")

    return values, supplied, positional


def parse_args(argv: Sequence[str]) -> Arguments:
    """Parse arguments and raise :class:`UsageError` for invalid input."""
    if not argv:
        raise UsageError("missing command (table, why or todo)")

    command = argv[0]
    if command == "--help" and len(argv) == 1:
        return Arguments(
            command=None,
            results=None,
            teams=(),
            win=3,
            draw=1,
            rules=("gd", "gf"),
            legs=2,
            supplied=frozenset(),
            help=True,
        )
    if command not in ("table", "why", "todo"):
        raise UsageError(f"unknown command {quote(command)}")

    values, supplied, positional = _scan_options(argv[1:])

    parsed_numbers: dict[str, int] = {}
    for name in ("win", "draw"):
        value = values[name]
        if not is_whole_number(value):
            raise _option_error(name, value)
        parsed_numbers[name] = int(value)

    try:
        rules = parse_rules(values["rules"])
    except ValueError as error:
        raise UsageError(_RULES_ERROR.format(value=quote(values["rules"]))) from error

    legs_value = values["legs"]
    if legs_value not in ("1", "2"):
        raise UsageError(f"invalid --legs {quote(legs_value)} (expected 1 or 2)")
    legs = int(legs_value)

    if command in ("table", "why") and "legs" in supplied:
        raise UsageError("--legs is only valid for todo")
    if command == "todo":
        for name in ("win", "draw", "rules"):
            if name in supplied:
                raise UsageError(f"--{name} is only valid for table and why")

    if not positional:
        raise UsageError("missing RESULTS")

    if command == "why":
        if len(positional) < 3:
            raise UsageError("missing TEAM")
        if len(positional) > 3:
            raise UsageError("too many arguments")
        return Arguments(
            command=command,
            results=positional[0],
            teams=(positional[1], positional[2]),
            win=parsed_numbers["win"],
            draw=parsed_numbers["draw"],
            rules=tuple(rules),
            legs=legs,
            supplied=frozenset(supplied),
        )

    if len(positional) > 1:
        raise UsageError("too many arguments")

    return Arguments(
        command=command,
        results=positional[0],
        teams=(),
        win=parsed_numbers["win"],
        draw=parsed_numbers["draw"],
        rules=tuple(rules),
        legs=legs,
        supplied=frozenset(supplied),
    )
