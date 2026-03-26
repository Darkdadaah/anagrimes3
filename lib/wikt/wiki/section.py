"""Basic Wiki code parsing from a page."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Self


__all__ = ["Section"]


MAX_LEVEL = 6


class SectionError(Exception):
    """Raised when parsing a section fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class Section:
    """A wiki section, delimited by = signs in the wiki code.

    Attributes:
        title (str): The title of the section.
        level (int): The level of the section (based on the number of =).
        text (list[str]): The text of the section (excluding the section title).
        subsections (list[Section]): A list of subsections within this section (under the text if any).
    """

    title: str
    level: int
    text: list[str] = field(default_factory=list)
    subsections: list[Self] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Post-initialization method to check the input."""
        if self.level < 1:
            raise SectionError("Section level can't be lower than 1")
        if self.level > MAX_LEVEL:
            raise SectionError(f"Section level can't be higher than {MAX_LEVEL}")

    def __str__(self) -> str:
        sub_str = ",".join([str(sec) for sec in self.subsections])
        return f"{self.title}({sub_str})"

    def add_text_line(self, text: str) -> None:
        """Add a line of text to the section."""
        self.text.append(text)

    def add_subsection(self, sec: Self) -> None:
        """Add a subsection to the section."""
        if sec.level >= self.level:
            raise SectionError(f"Subsection is higher than its parent: {sec.level} >= {self.level}")
        self.subsections.append(sec)
