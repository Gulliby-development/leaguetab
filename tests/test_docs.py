import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USAGE = """usage: leaguetab table [--win N] [--draw N] [--rules LIST] RESULTS
       leaguetab why [--win N] [--draw N] [--rules LIST] RESULTS TEAM TEAM
       leaguetab todo [--legs N] RESULTS"""

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
Benfica | Celtic | 2-1"""

DEFAULT_TABLE = """POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Celtic     4  2  1  1   8   7  +1    7
2    Eintracht  5  2  1  2  10  10   0    7
3    Benfica    5  2  1  2   7   7   0    7
4    Dinamo     5  1  3  1   7   7   0    6
5    Ajax       5  1  2  2   6   7  -1    5"""

HEAD_TO_HEAD_TABLE = """POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Eintracht  5  2  1  2  10  10   0    7
2    Benfica    5  2  1  2   7   7   0    7
3    Celtic     4  2  1  1   8   7  +1    7
4    Dinamo     5  1  3  1   7   7   0    6
5    Ajax       5  1  2  2   6   7  -1    5"""

WHY_OUTPUT = """points: Benfica 7, Celtic 7
h2h (3 teams): Benfica 3/0/4, Celtic 3/0/4
h2h (2 teams): Benfica 3/+1/2, Celtic 0/-1/1
Benfica is ahead of Celtic on h2h"""

TODO_OUTPUT = """Ajax - Dinamo
Ajax - Eintracht
Benfica - Eintracht
Celtic - Ajax
Celtic - Benfica
Dinamo - Benfica
Dinamo - Celtic
Eintracht - Celtic
8 fixtures missing"""

EXPECTED_TEXT_FENCES = [
    "python -m venv .venv",
    "python -m leaguetab",
    USAGE,
    SEASON,
    DEFAULT_TABLE,
    HEAD_TO_HEAD_TABLE,
    WHY_OUTPUT,
    TODO_OUTPUT,
    "ruff check .\npytest -q",
]


def test_readme_has_the_six_required_sections():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## .+$", readme, flags=re.MULTILINE)

    assert headings == [
        "## Install",
        "## Usage",
        "## Results file",
        "## Ranking",
        "## Exit codes",
        "## Development",
    ]


def test_readme_documents_required_commands_and_behavior():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for required in (
        "python -m venv .venv",
        "python -m leaguetab",
        "ruff check .",
        "pytest -q",
        "gd",
        "gf",
        "wins",
        "away",
        "h2h",
        "HOME | AWAY | HG-AG",
    ):
        assert required in readme

    exit_codes = re.findall(
        r"^- \x60([012])\x60: (.+)$",
        readme,
        flags=re.MULTILINE,
    )

    assert [number for number, _ in exit_codes] == ["0", "1", "2"]
    assert "success" in exit_codes[0][1]
    assert "missing fixtures" in exit_codes[1][1]
    assert "usage or input error" in exit_codes[2][1]


def test_readme_contains_only_the_required_text_fences():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    fences = re.findall(r"\x60{3}text\n(.*?)\n\x60{3}", readme, flags=re.DOTALL)

    assert fences == EXPECTED_TEXT_FENCES


def test_mit_license_has_the_required_holder_and_terms():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    for required in (
        "MIT License",
        "Copyright (c) 2026 Gulliby-development",
        "Permission is hereby granted, free of charge, to any person obtaining a copy",
        "including without limitation the rights",
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell",
        "The above copyright notice and this permission notice shall be included",
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND',
        "IN NO EVENT SHALL THE",
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE",
    ):
        assert required in license_text
