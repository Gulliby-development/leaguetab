from collections.abc import Sequence


def quote(value: object) -> str:
    """Return a double-quoted, printable ASCII representation of value."""
    text = str(value)
    escaped = []
    for character in text:
        if "!" <= character <= "~":
            escaped.append(character)
        else:
            escaped.append("?")
    return '"' + "".join(escaped) + '"'


def is_whole_number(value: str) -> bool:
    """Return whether value is a canonical whole-number token of at most nine digits."""
    if value == "0":
        return True
    if not value or len(value) > 9 or value[0] < "1" or value[0] > "9":
        return False
    for character in value[1:]:
        if character < "0" or character > "9":
            return False
    return True


def table(rows: Sequence[Sequence[object]], align: Sequence[str]) -> str:
    """Render rows as a fixed-width table with left/right column alignment."""
    cells = []
    for row in rows:
        cells.append([str(cell) for cell in row])
    if not cells:
        return ""
    column_count = len(align)
    if column_count == 0:
        raise ValueError("each table row must match the alignment width")
    for row in cells:
        if len(row) != column_count:
            raise ValueError("each table row must match the alignment width")
    for direction in align:
        if direction not in ("left", "right"):
            raise ValueError("alignment must be left or right")

    widths = [0] * column_count
    for row in cells:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    rendered_rows = []
    for row in cells:
        rendered_cells = []
        for index, cell in enumerate(row):
            if align[index] == "right":
                rendered_cells.append(cell.rjust(widths[index]))
            elif index == column_count - 1:
                rendered_cells.append(cell)
            else:
                rendered_cells.append(cell.ljust(widths[index]))
        rendered_rows.append("  ".join(rendered_cells))
    return "\n".join(rendered_rows)
