"""Missing fixture calculations."""

from collections.abc import Sequence

Match = tuple[str, str, int, int]


def missing(matches: Sequence[Match], legs: int) -> list[tuple[str, str]]:
    """Return unplayed directed or undirected fixtures in code-point order."""
    teams: set[str] = set()
    played: set[tuple[str, str]] = set()

    for home, away, _home_goals, _away_goals in matches:
        teams.add(home)
        teams.add(away)
        played.add((home, away))

    ordered_teams = sorted(teams)
    fixtures: list[tuple[str, str]] = []

    if legs == 2:
        for home in ordered_teams:
            for away in ordered_teams:
                if home != away and (home, away) not in played:
                    fixtures.append((home, away))
        return fixtures

    if legs == 1:
        for home_index, home in enumerate(ordered_teams):
            for away in ordered_teams[home_index + 1 :]:
                if (home, away) not in played and (away, home) not in played:
                    fixtures.append((home, away))
        return fixtures

    raise ValueError("legs must be 1 or 2")
