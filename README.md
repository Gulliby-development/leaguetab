<p align="center"><img src="docs/logo.svg" width="96" alt="leaguetab logo"></p>

# leaguetab

[![CI](https://github.com/Gulliby-development/leaguetab/actions/workflows/ci.yml/badge.svg)](https://github.com/Gulliby-development/leaguetab/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

leaguetab is an offline command-line tool for league organizers at clubs, schools and esports competitions. It prints standings, explains why one team is ahead of another, and lists fixtures still to be played. It reads results without changing the input and produces deterministic output.

## Install

Create a virtual environment:

```text
python -m venv .venv
```

Run leaguetab from the repository root with Python 3.11 or newer:

```text
python -m leaguetab
```

## Usage

The three commands are `table` for the standings, `why` for a comparison between two teams, and `todo` for missing fixtures. Use `-` instead of a path to read results from standard input. The help output is:

```text
usage: leaguetab table [--win N] [--draw N] [--rules LIST] RESULTS
       leaguetab why [--win N] [--draw N] [--rules LIST] RESULTS TEAM TEAM
       leaguetab todo [--legs N] RESULTS
```

The examples below use this `season.txt` file:

```text
# a five-team league, played so far
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
```

With the default tie-breaks, `python -m leaguetab table season.txt` prints:

```text
POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Celtic     4  2  1  1   8   7  +1    7
2    Eintracht  5  2  1  2  10  10   0    7
3    Benfica    5  2  1  2   7   7   0    7
4    Dinamo     5  1  3  1   7   7   0    6
5    Ajax       5  1  2  2   6   7  -1    5
```

Use `--rules h2h,gd,gf` to order level teams by head-to-head, then goal difference, then goals scored. `python -m leaguetab table --rules h2h,gd,gf season.txt` prints:

```text
POS  TEAM       P  W  D  L  GF  GA  GD  PTS
1    Eintracht  5  2  1  2  10  10   0    7
2    Benfica    5  2  1  2   7   7   0    7
3    Celtic     4  2  1  1   8   7  +1    7
4    Dinamo     5  1  3  1   7   7   0    6
5    Ajax       5  1  2  2   6   7  -1    5
```

`python -m leaguetab why --rules h2h,gd,gf season.txt Benfica Celtic` explains the comparison:

```text
points: Benfica 7, Celtic 7
h2h (3 teams): Benfica 3/0/4, Celtic 3/0/4
h2h (2 teams): Benfica 3/+1/2, Celtic 0/-1/1
Benfica is ahead of Celtic on h2h
```

`python -m leaguetab todo season.txt` lists the fixtures still missing:

```text
Ajax - Dinamo
Ajax - Eintracht
Benfica - Eintracht
Celtic - Ajax
Celtic - Benfica
Dinamo - Benfica
Dinamo - Celtic
Eintracht - Celtic
8 fixtures missing
```

## Results file

Results are UTF-8 text, one match per line, in the form `HOME | AWAY | HG-AG`. Spaces and tabs around fields are ignored, and so are those around the dash of the score, so `2 - 1` is the score `2-1`. Blank lines and lines beginning with `#` are ignored. Team names are case-sensitive. A UTF-8 byte-order mark is allowed at the start of the file, and either LF or CRLF line endings can be used.

## Ranking

Teams are ranked first by points. Tied teams use the selected rules in order:

- `gd`: goal difference
- `gf`: goals scored
- `wins`: matches won
- `away`: goals scored while playing away
- `h2h`: points, goal difference and goals scored in matches among the teams still tied

The default rules are `gd,gf`. Set `--rules` to a comma-separated list with no repeated key. Set `--win` and `--draw` to change the points awarded for wins and draws.

## Exit codes

- `0`: success
- `1`: missing fixtures were found by `todo`
- `2`: usage or input error

## Development

Install the checkers into your virtual environment (`python -m pip install pytest ruff`), then run the checks from the repository root:

```text
ruff check .
pytest -q
```

**License.**

MIT, see [LICENSE](LICENSE).

---

Built with BAKED.
