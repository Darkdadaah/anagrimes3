"""Basic Wiki code parsing from a page."""

from __future__ import annotations
import re

from .base import WikiBase
from .error import WikiParserError
from .section import Section


__all__ = ["WikiArticle", "WikiArticleError"]


MAX_UNAMED = 50


class WikiArticleError(WikiParserError):
    """Raised when parsing the wiki code fails."""


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
