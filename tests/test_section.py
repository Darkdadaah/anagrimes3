#!/usr/bin/env python
"""
Unit tests for the Section class.
"""

import pytest
from wikt.wiki.section import Section, SectionError, MAX_LEVEL


def test_repr():
    """Test __repr__ method."""
    sec = Section(title="Section1", level=2, text=["line1"], subsections=[])
    assert repr(sec) == "Section1()"
    sec2 = Section(title="Section2", level=3, text=["line2"], subsections=[])
    sec.add_subsection(sec2)
    assert repr(sec) == "Section1(Section2())"


def test_level():
    """Test level constraints."""
    with pytest.raises(SectionError):
        Section(title="Section1", level=0)
    with pytest.raises(SectionError):
        Section(title="Section1", level=MAX_LEVEL + 1)


def test_subsection_addition():
    """Test adding a subsection to the section."""
    sec = Section(title="Parent", level=2)
    sub_sec = Section(title="Child", level=3, text=["line1"])
    sec.add_subsection(sub_sec)
    assert sec.subsections == [sub_sec]


def test_text_line_addition():
    """Test adding a line of text to the section."""
    sec = Section(title="Section1", level=2)
    text_lines = ["This is a line", "Another line"]
    sec.add_text_line(text_lines[0])
    assert sec.text == [text_lines[0]]
    sec.add_text_line(text_lines[1])
    assert sec.text == text_lines
