from .text import is_whole_number, quote

Match = tuple[str, str, int, int]


class ResultsError(ValueError):
    """A syntax or validation error in a results file."""


def parse_results(display: str, text: str) -> list[Match]:
    """Parse result lines, raising ResultsError for the first malformed match."""
    text = text.removeprefix("\ufeff")

    lines = text.split("\n")
    matches: list[Match] = []
    for line_number, line in enumerate(lines, start=1):
        if line_number < len(lines) and line.endswith("\r"):
            line = line[:-1]
        line = line.strip(" \t")
        if not line or line.startswith("#"):
            continue

        fields = line.split("|")
        if len(fields) != 3:
            raise ResultsError(
                f'{display}:{line_number}: expected "HOME | AWAY | HG-AG"'
            )
        home, away, score = [field.strip(" \t") for field in fields]
        for team in (home, away):
            invalid_name = not team
            for character in team:
                if ord(character) < 0x20 or ord(character) == 0x7F:
                    invalid_name = True
                    break
            if invalid_name:
                raise ResultsError(
                    f"{display}:{line_number}: invalid team name {quote(team)}"
                )

        score_parts = [part.strip(" \t") for part in score.split("-")]
        if (
            len(score_parts) != 2
            or not is_whole_number(score_parts[0])
            or not is_whole_number(score_parts[1])
        ):
            raise ResultsError(
                f"{display}:{line_number}: invalid score {quote(score)} "
                "(expected HG-AG, for example 2-1)"
            )
        home_goals, away_goals = int(score_parts[0]), int(score_parts[1])
        if home == away:
            raise ResultsError(
                f"{display}:{line_number}: team {quote(home)} plays itself"
            )
        matches.append((home, away, home_goals, away_goals))
    return matches
