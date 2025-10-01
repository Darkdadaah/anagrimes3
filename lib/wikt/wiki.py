"""Basic Wiki parsing."""

from __future__ import annotations
import logging
import re
from typing import Self


MAX_UNAMED = 50


class WikiParserError(Exception):
    """Raised when parsing the wiki code fails."""


class Template:
    """Generic Wiki Template representation.

    Attributes:
        title: Template name.
        unnamed: An ordered list of unnamed parameters.
        named: A dictionary of named parameters.
    """

    _template_inside_regex = re.compile(r"^ *\{\{ *([^\}]+) *\}\} *$")
    _template_parts_regex = re.compile(r"^ *(.+?) *= *(.*?) *$")

    def __init__(
        self, title: str, unnamed: None | list[str] = None, named: None | dict[str, str] = None
    ) -> None:
        self.title = title
        self.unnamed = []
        self.named = {}
        if unnamed:
            self.unnamed = unnamed
        if named:
            self.named = named

    def __repr__(self):
        return "{{ " + f"{self.title} | {self.unnamed} || {self.named} " + "}}"

    @classmethod
    def from_string(cls, template_str: str) -> Template:
        """Parse a template string."""
        title = ""
        named: dict[str, str] = {}
        unnamed: list[str] = [""] * MAX_UNAMED

        ordered_index = 0
        max_index = 0
        if templ_match := cls._template_inside_regex.search(template_str):
            templ_content = templ_match.group(1)
            templ_parts = templ_content.split("|")
            title = templ_parts.pop(0)  # First part = named of template

            for part in templ_parts:
                # key-value pair
                if part_match := cls._template_parts_regex.search(part):
                    pkey = part_match.group(1)
                    pval = part_match.group(2)
                    if not pval:
                        continue
                    if pkey.isdigit():
                        try:
                            pindex = int(pkey) - 1
                            unnamed[pindex] = pval
                            max_index = pindex
                        except IndexError:
                            print("WARNING: Template too many arguments past max {MAX_UNAMED}. Ignoring more")
                    else:
                        named[pkey] = pval
                else:
                    pval = part.strip()
                    unnamed[ordered_index] = pval
                    ordered_index += 1

        # TODO: should throw if no title or parsing failed somehow

        # Trim unnamed
        last_index = max_index if max_index > ordered_index else ordered_index
        unnamed = unnamed[0:last_index + 1]

        return Template(title, unnamed, named)


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


class Section:
    """A wiki section."""

    def __init__(self, title: str, level: int):
        self.title = title
        self.level = level
        self.text: list[str] = []
        self.subsections: list[Self] = []

    def __str__(self) -> str:
        sub_str = ",".join([str(sec) for sec in self.subsections])
        return f"{self.title}({sub_str})"

    def add_text(self, text: str) -> None:
        """Add a line of text to the section."""
        self.text.append(text)

    def add_subsection(self, sec: Self) -> None:
        """Add a subsection to the section."""
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
                cur_section.add_text("")

        return self._top_section
