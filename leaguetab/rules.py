"""Tie-break rule parsing and team keys."""

from collections.abc import Mapping

RULES = ("gd", "gf", "wins", "away", "h2h")


def parse_rules(text: str) -> list[str]:
    """Parse an ordered comma-separated list of unique tie-break rules.

    The syntax is deliberately strict: whitespace, empty names, and repeated
    rules are not accepted.
    """
    if not text:
        raise ValueError("invalid rules")

    parsed = text.split(",")
    seen: set[str] = set()
    for rule in parsed:
        if rule not in RULES or rule in seen:
            raise ValueError("invalid rules")
        seen.add(rule)
    return parsed


def key(
    rule: str,
    team: str,
    stats: Mapping[str, Mapping[str, int]],
    subgroup_stats: Mapping[str, Mapping[str, int]] | None = None,
) -> int | tuple[int, int, int]:
    """Return a team's descending-sort key for a tie-break rule."""
    if rule == "h2h":
        selected_stats = stats if subgroup_stats is None else subgroup_stats
        record = selected_stats.get(team)
        if record is None:
            return (0, 0, 0)
        return (record["PTS"], record["GD"], record["GF"])

    record = stats[team]
    if rule == "gd":
        return record["GD"]
    if rule == "gf":
        return record["GF"]
    if rule == "wins":
        return record["W"]
    if rule == "away":
        return record["away"]
    raise ValueError("unknown rule")
