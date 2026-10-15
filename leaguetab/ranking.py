"""League ranking and the tie-break applications used to explain it."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .rules import key as rule_key
from .stats import Match, calculate

Score = int | tuple[int, int, int]


@dataclass(frozen=True)
class RuleApplication:
    """A recorded comparison applied to one group of teams."""

    rule: str
    teams: tuple[str, ...]
    keys: Mapping[str, Score]


def rank(
    matches: Sequence[Match],
    stats: Mapping[str, Mapping[str, int]],
    rules: Sequence[str],
    win: int = 3,
    draw: int = 1,
) -> tuple[list[list[str]], list[RuleApplication]]:
    """Return ordered tie groups and the point/rule applications made.

    Applications are recorded before their resulting subgroups are processed.
    The work stack keeps rule evaluation independent of Python's recursion
    limit, even when a tie is split into many nested subgroups.
    """
    team_names = sorted(stats)
    points: dict[int, list[str]] = {}
    for team in team_names:
        points.setdefault(stats[team]["PTS"], []).append(team)

    applications = [
        RuleApplication(
            "points",
            tuple(team_names),
            {team: stats[team]["PTS"] for team in team_names},
        )
    ]
    tie_groups: list[list[str]] = []

    for points_value in sorted(points, reverse=True):
        point_group = points[points_value]
        if len(point_group) == 1:
            tie_groups.append(point_group)
            continue

        pending: list[tuple[list[str], int]] = [(point_group, 0)]
        while pending:
            group, rule_index = pending.pop()
            if len(group) == 1 or rule_index >= len(rules):
                tie_groups.append(sorted(group))
                continue

            rule = rules[rule_index]
            subgroup_stats = (
                calculate(matches, win=win, draw=draw, teams=group)
                if rule == "h2h"
                else None
            )
            group_keys = {
                team: rule_key(rule, team, stats, subgroup_stats)
                for team in group
            }
            applications.append(
                RuleApplication(rule, tuple(sorted(group)), group_keys)
            )

            parts: dict[Score, list[str]] = {}
            for team in group:
                parts.setdefault(group_keys[team], []).append(team)
            ordered_parts = sorted(parts.values(), key=lambda part: group_keys[part[0]], reverse=True)

            if len(ordered_parts) == 1:
                pending.append((group, rule_index + 1))
                continue

            next_rule = rule_index if rule == "h2h" else rule_index + 1
            for part in reversed(ordered_parts):
                pending.append((part, next_rule))

    return tie_groups, applications
