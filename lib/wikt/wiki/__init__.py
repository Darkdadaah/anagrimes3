"""Basic Wiki code parsing from a page."""

from __future__ import annotations
from dataclasses import dataclass, field
import logging
import re
from typing import Self

from .template import Template
from .section import Section

logger = logging.getLogger(__name__)


__all__ = ["WikiParserError", "WikiBase", "Template"]


MAX_UNAMED = 50


class WikiParserError(Exception):
    """Raised when parsing the wiki code fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass
class WikiContext:
    """Context for parsing a wiki page. for logging."""

    title: str
    section: str = ""

    def __str__(self) -> str:
        s = f"[[{self.title}]]"
        if self.section:
            s += f" #{self.section}"
        return s


def parser_log(context: WikiContext, name: str, details: str = "", debug=False) -> None:
    """Log a message with the current wiki context."""
    s = f"{str(context):<20}\t{name:<40}\t{details}"
    if debug:
        logger.debug(s)
    else:
        logger.info(s)


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


class WikiArticle:
    """General Wiki page split in wiki sections."""

    title: str
    text: str

    _section_regex = re.compile(r"^(=+)\s*(.+?)\s*(=+)$")
    _empty_regex = re.compile(r"^\s*$")
    _redirection = re.compile(r"^\s*#REDIRECT", re.IGNORECASE)
    html_comment = re.compile("<!--.*?-->", flags=re.DOTALL)

    def __init__(self, title: str, text: str):
        self.title = title
        text = re.sub(self.html_comment, "", text)
        self.text = text
        self._top_section: Section | None = None

    def parse_section_title(self, section_str: str) -> tuple[int, str]:
        """Extract the level and content of the section title."""

        sec_match = self._section_regex.search(section_str.strip())
        if not sec_match:
            context = WikiContext(self.title)
            parser_log(context, "Can't parse section", section_str)
            return (0, "")

        sec_start = sec_match.group(1)
        sec_title = sec_match.group(2)
        sec_end = sec_match.group(3)

        # Get level
        sec_level = 0
        for nlevel in range(2, 7):
            sec_signs = "=" * nlevel
            if sec_start == sec_signs:
                sec_level = nlevel
                if sec_end != sec_signs:
                    context = WikiContext(self.title, sec_title)
                    parser_log(context, "Section level start and end differ", section_str)

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
                        context = WikiContext(self.title, section_title)
                        parser_log(context, "No section2", line)
            else:
                cur_section.add_text_line("")

        return self._top_section
