"""Basic Wiki code parsing from a page."""

from __future__ import annotations
from dataclasses import dataclass, field
import logging
import re
from typing import Self

from .template import Template


__all__ = ["WikiParserError", "WikiBase", "Template"]


MAX_UNAMED = 50


class WikiParserError(Exception):
    """Raised when parsing the wiki code fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class WikiBase:
    """A base Wiki object with an article title, for easier logging."""

    def __init__(self, title: str) -> None:
        self.title = title

    def log(self, name: str, detail: str = "") -> None:
        """Custom print to log as info."""
        logging.info(f"LOG\t[[{self.title}]]\t{name}\t{detail}")

    def debug(self, name: str, detail: str = "") -> None:
        """Custom print to log as debug."""
        logging.debug(f"DEBUG\t[[{self.title}]]\t{name}\t{detail}")


@dataclass
class Section:
    """A wiki section.

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

    def __str__(self) -> str:
        sub_str = ",".join([str(sec) for sec in self.subsections])
        return f"{self.title}({sub_str})"

    def add_text_line(self, text: str) -> None:
        """Add a line of text to the section."""
        self.text.append(text)

    def add_subsection(self, sec: Self) -> None:
        """Add a subsection to the section."""
        if sec.level >= self.level:
            raise WikiParserError(f"Subsection is higher than its parent: {sec.level} >= {self.level}")
        self.subsections.append(sec)


class WikiArticle(WikiBase):
    """General Wiki page split in wiki sections."""

    text: str

    _section_regex = re.compile(r"^(=+)\s*(.+?)\s*(=+)$")
    _empty_regex = re.compile(r"^\s*$")
    _redirection = re.compile(r"^\s*#REDIRECT", re.IGNORECASE)
    html_comment = re.compile("<!--.*?-->", flags=re.DOTALL)

    def __init__(self, title: str, text: str):
        super().__init__(title)

        text = re.sub(self.html_comment, "", text)
        self.text = text
        self._top_section: Section | None = None

    def parse_section_title(self, section_str: str) -> tuple[int, str]:
        """Extract the level and content of the section title."""
        sec_match = self._section_regex.search(section_str.strip())
        if not sec_match:
            self.log("Can't parse section", section_str)
            return (0, "")

        sec_start = sec_match.group(1)
        sec_title = sec_match.group(2)
        sec_end = sec_match.group(3)

        # Get level
        sec_level = 0
        for nlevel in range(2, 6):
            sec_signs = "=" * nlevel
            if sec_start == sec_signs:
                sec_level = nlevel
                if sec_end != sec_signs:
                    self.log("Section level start and end differ", section_str)

        return (sec_level, sec_title)

    def is_redirect(self) -> bool:
        """Check if a wiki text is a redirection."""
        if re.findall(self._redirection, self.text):
            return True
        return False

    def _parse_sec_title(self, text: str) -> str:
        return text

    def top_section(self) -> Section:
        """Parse out hierarchy of sections from a wiki text."""
        if self._top_section:
            return self._top_section

        self._top_section = Section("TOP", 0)
        cur_section = self._top_section
        cur_sec2: Section | None = None
        cur_sec3: Section | None = None

        for line in self.text.split("\n"):
            # Get title elements
            if line.startswith("=="):
                (level, section_title) = self.parse_section_title(line)

                # New level2
                if level == 2:
                    cur_sec2 = Section(section_title, level)
                    self._top_section.add_subsection(cur_sec2)
                    cur_section = cur_sec2
                if level == 3:
                    cur_sec3 = Section(section_title, level)
                    if cur_sec2:
                        cur_sec2.add_subsection(cur_sec3)
                        cur_section = cur_sec3
                    else:
                        self.log(f"No section2 for {section_title}")
            else:
                cur_section.add_text_line("")

        return self._top_section
