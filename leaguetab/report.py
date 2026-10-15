"""Human-readable table and tie-break explanations."""

from collections.abc import Mapping, Sequence

from .ranking import RuleApplication, Score
from .text import table as render_table


def _signed(value: int) -> str:
    """Format a goal difference with an explicit positive sign."""
    return f"+{value}" if value > 0 else str(value)


def _format_key(rule: str, value: Score) -> str:
    if rule == "gd":
        if isinstance(value, tuple):
            raise ValueError("goal difference keys must be integers")
        return _signed(value)
    if rule == "h2h":
        if isinstance(value, int):
            raise ValueError("head-to-head keys must be triples")
        points, goal_difference, goals_for = value
        return f"{points}/{_signed(goal_difference)}/{goals_for}"
    return str(value)


def table_report(
    stats: Mapping[str, Mapping[str, int]], tie_groups: Sequence[Sequence[str]]
) -> str:
    """Return the complete standings table, without a trailing newline."""
    rows: list[list[str]] = [["POS", "TEAM", "P", "W", "D", "L", "GF", "GA", "GD", "PTS"]]
    position = 1
    for group in tie_groups:
        tied = len(group) > 1
        place = f"{position}=" if tied else str(position)
        for team in group:
            record = stats[team]
            rows.append(
                [
                    place,
                    team,
                    str(record["P"]),
                    str(record["W"]),
                    str(record["D"]),
                    str(record["L"]),
                    str(record["GF"]),
                    str(record["GA"]),
                    _signed(record["GD"]),
                    str(record["PTS"]),
                ]
            )
        position += len(group)
    alignment = ("left", "left", "right", "right", "right", "right", "right", "right", "right", "right")
    return render_table(rows, alignment)


def why_report(
    first_team: str,
    second_team: str,
    tie_groups: Sequence[Sequence[str]],
    applications: Sequence[RuleApplication],
) -> list[str]:
    """Return explanation lines for two known, distinct teams."""
    team_groups = {team: index for index, group in enumerate(tie_groups) for team in group}
    if team_groups[first_team] < team_groups[second_team] or (
        team_groups[first_team] == team_groups[second_team] and first_team < second_team
    ):
        ahead, behind = first_team, second_team
    else:
        ahead, behind = second_team, first_team

    lines: list[str] = []
    deciding_rule: str | None = None
    for application in applications:
        if ahead not in application.teams or behind not in application.teams:
            continue
        ahead_key = application.keys[ahead]
        behind_key = application.keys[behind]
        if application.rule == "points":
            lines.append(f"points: {ahead} {ahead_key}, {behind} {behind_key}")
        else:
            lines.append(
                f"{application.rule} ({len(application.teams)} teams): "
                f"{ahead} {_format_key(application.rule, ahead_key)}, "
                f"{behind} {_format_key(application.rule, behind_key)}"
            )
        if ahead_key != behind_key:
            deciding_rule = application.rule
            break

    if deciding_rule is None:
        lines.append(f"{ahead} and {behind} are level")
    else:
        lines.append(f"{ahead} is ahead of {behind} on {deciding_rule}")
    return lines
