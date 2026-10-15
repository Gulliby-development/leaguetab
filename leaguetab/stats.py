"""League statistics for match results."""

from collections.abc import Iterable, Sequence

Match = tuple[str, str, int, int]

_FIELDS = ("P", "W", "D", "L", "GF", "GA", "GD", "PTS", "away")


def _empty_record() -> dict[str, int]:
    """Return a fresh zeroed statistics record."""
    return dict.fromkeys(_FIELDS, 0)


def calculate(
    matches: Sequence[Match],
    win: int = 3,
    draw: int = 1,
    teams: Iterable[str] | None = None,
) -> dict[str, dict[str, int]]:
    """Calculate match and goal counts for each team.

    If teams is supplied, every listed team is included even when it has no
    qualifying matches, and only matches between two listed teams count.
    """
    totals: dict[str, dict[str, int]] = {}
    selected: set[str] | None = None

    if teams is not None:
        selected = set()
        for team in teams:
            if team not in totals:
                totals[team] = _empty_record()
                selected.add(team)

    for home, away, home_goals, away_goals in matches:
        if selected is not None and (home not in selected or away not in selected):
            continue

        if home not in totals:
            totals[home] = _empty_record()
        if away not in totals:
            totals[away] = _empty_record()

        home_stats = totals[home]
        away_stats = totals[away]

        home_stats["P"] += 1
        away_stats["P"] += 1
        home_stats["GF"] += home_goals
        home_stats["GA"] += away_goals
        away_stats["GF"] += away_goals
        away_stats["GA"] += home_goals
        away_stats["away"] += away_goals

        if home_goals > away_goals:
            home_stats["W"] += 1
            home_stats["PTS"] += win
            away_stats["L"] += 1
        elif home_goals < away_goals:
            away_stats["W"] += 1
            away_stats["PTS"] += win
            home_stats["L"] += 1
        else:
            home_stats["D"] += 1
            away_stats["D"] += 1
            home_stats["PTS"] += draw
            away_stats["PTS"] += draw

    for record in totals.values():
        record["GD"] = record["GF"] - record["GA"]

    return totals
