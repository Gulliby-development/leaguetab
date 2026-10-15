"""Example-based tests for text formatting and primitive validation."""

import pytest

from leaguetab.text import is_whole_number, quote, table


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", '""'),
        ("!~", '"!~"'),
        (" ", '"?"'),
        ("\x00", '"?"'),
        ("\x7f", '"?"'),
        ("é", '"?"'),
        ("😀", '"?"'),
        ("aé😀!", '"a??!"'),
    ],
)
def test_quote_preserves_only_printable_ascii(value, expected):
    assert quote(value) == expected


@pytest.mark.parametrize("value", ["0", "1", "9", "999999999"])
def test_whole_number_accepts_zero_and_one_to_nine_digit_boundaries(value):
    assert is_whole_number(value)


@pytest.mark.parametrize(
    "value",
    ["", "00", "01", "-1", "+1", "1.5", "١", "１００", "1000000000", " 1"],
)
def test_whole_number_rejects_noncanonical_or_overlong_values(value):
    assert not is_whole_number(value)


def test_table_aligns_using_code_point_widths_for_unicode_cells():
    rendered = table(
        [("Team", "P"), ("e\u0301", "12"), ("😀", "3")],
        ("left", "right"),
    )

    assert rendered == "Team   P\ne\u0301    12\n😀      3"


def test_table_left_and_right_alignment_have_exact_padding():
    assert table(
        [("A", "N"), ("long", 2), ("x", 30)],
        ("left", "right"),
    ) == "A      N\nlong   2\nx     30"


def test_table_does_not_pad_the_last_left_aligned_column():
    assert table(
        [("x", "last"), ("long", "z")],
        ("left", "left"),
    ) == "x     last\nlong  z"


def test_table_uses_lf_between_rows_and_never_adds_trailing_spaces():
    rendered = table(
        [("Name", "P"), ("Ajax", 2), ("B", 10)],
        ("left", "right"),
    )

    assert rendered == "Name   P\nAjax   2\nB     10"
    assert "\r" not in rendered
    assert not rendered.endswith("\n")
    for line in rendered.split("\n"):
        assert line == line.rstrip(" ")


def test_table_of_no_rows_is_empty():
    assert table([], ("left", "right")) == ""


@pytest.mark.parametrize(
    ("rows", "align"),
    [
        ([("A",)], ("left", "right")),
        ([("A",)], ()),
    ],
)
def test_table_rejects_rows_that_do_not_match_column_count(rows, align):
    with pytest.raises(ValueError, match="each table row must match the alignment width"):
        table(rows, align)


def test_table_rejects_unknown_alignment():
    with pytest.raises(ValueError, match="alignment must be left or right"):
        table([("A",)], ("center",))
