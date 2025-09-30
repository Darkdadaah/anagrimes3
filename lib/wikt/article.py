"""Main Wiktionnaire articles representation."""

from __future__ import annotations
import logging
import re
from re import Match
from typing import Any, Self

from wikt.data import word_types, word_attributes


MAX_UNAMED = 50


class WiktParserError(Exception):
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
                            print("WARNING: has too many arguments past max {MAX_UNAMED}. Ignoring more")

                    named[pkey] = pval
                else:
                    pval = part.strip()
                    unnamed[ordered_index] = pval
                    ordered_index += 1

        # TODO: should throw if no title or parsing failed somehow

        # Trim unnamed
        last_index = max_index if max_index > ordered_index else ordered_index
        unnamed = unnamed[0:last_index]

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


class Form(WikiBase):
    """Word form line parsing."""

    form_regex = re.compile(r"^'''(.+?)''' ?(.+)? *$")
    template_regex = re.compile(r"(\{\{[^\}]+?\}\})")

    def __init__(self, title: str, form_line: str) -> None:
        super().__init__(f"{title}-form_line")
        self.form = None
        self.prons: list[str] = []
        self.attributes: list[str] = []

        self.parse_form_line(form_line)

    def parse_form_line(self, line: str) -> None:
        """Parse a form line in the form '''(WORD)''' (PROPERTIES in templates)"""
        templates: dict[str, list[Template]] = self.get_templates(line)

        # Get pronunciations
        if "pron" in templates:
            prons = templates["pron"]

            for pron in prons:
                if pron.unnamed:
                    pron_str = pron.unnamed[0]
                    self.add_pron(pron_str)

        # Get other attributes
        for attr, full_attr_name in word_attributes.items():
            if attr in templates:
                self.add_attribute(full_attr_name)

    def add_pron(self, pron_str: str) -> None:
        """Add a pronunciation for that word."""
        self.prons.append(pron_str)

    def add_attribute(self, attr: str) -> None:
        """Add an attribute for that word."""
        if attr not in self.attributes:
            self.attributes.append(attr)
        else:
            self.log("Attribute written twice", attr)

    def get_templates(self, string: str) -> dict[str, list[Template]]:
        """Retrieve all templates from a wiki string."""
        templates: dict[str, list[Template]] = {}

        if string is None:
            return templates

        template_strings = self.template_regex.findall(string)

        for temp_str in template_strings:
            template = Template.from_string(temp_str)
            if template.title in templates:
                templates[template.title].append(template)
            else:
                templates[template.title] = [template]

        return templates


class Word(WikiBase):
    """A Wiktionnaire word section representation."""

    def __init__(
        self,
        title: str,
        lang: str,
        wtype: str,
        is_flexion: bool = False,
        is_locution: bool = False,
        number: int = 0,
    ) -> None:
        super().__init__(f"{title}#{lang}-{wtype}-{number}")
        self.lang = lang
        self.type = wtype
        self.form: Form = Form(title, "")
        self.defs: list[str] = []
        self.is_flexion = is_flexion
        self.is_locution = is_locution
        self.number = number

    def add_def(self, def_line: str) -> None:
        """Add a definition from a definition line."""
        self.defs.append(def_line)

    def add_form(self, form: Form) -> None:
        """Add a form from a form line."""
        self.form = form

    def __str__(self) -> str:
        lines = [
            f"TITLE = {self.title}",
            f"LANG  = {self.lang}",
            f"TYPE  = {self.type}",
            f"PRONS = {self.form.prons}",
            f"DEFS  = {len(self.defs)}",
        ]
        return "\n\t".join(lines)

    def struct(self) -> dict[str, Any]:
        """Returns a json structure representing the word section."""
        struct = {
            "title": self.title,
            "lang": self.lang,
            "type": self.type,
            "defs": self.defs,
            "is_flexion": self.is_flexion,
            "is_locution": self.is_locution,
            "number": self.number,
        }

        # Add form properties
        if self.form:
            if self.form.prons:
                struct["prons"] = self.form.prons
            if self.form.attributes:
                struct["attributes"] = self.form.attributes
        return struct


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


class Article(WikiArticle):
    """A Wiktionnaire article."""

    def_regex = re.compile("^#+([^#*:] *.+)$")

    temp_def_keep_only_par = ["term", "lien"]
    temp_def_keep_with_par = [
        "cf",
        "variante",
        "variante ortho de",
        "variante orthographique de",
    ]
    temp_def_no_parentheses = temp_def_keep_with_par
    temp_def_no_capitalize = ["cf"]

    def __init__(self, title: str, text: str) -> None:
        super().__init__(title, text)
        self.words: list[Word] = self.parse_words()

    def __str__(self):
        lines = [f"TITLE = {self.title}", f"WORDS = {len(self.words)}"]
        return "\n".join(lines)


    def parse_words(self) -> list[Word]:
        """Parse a Wiktionnaire article into words."""
        words = []

        # Parse language sections
        lang = ""
        cur_word = None
        has_char_section = False

        if not self.text:
            self.debug("No text")
            return []

        if self.is_redirect():
            self.debug("Redirect")
            return []

        # top = self.top_section()
        # print(top)

        for line in self.text.split("\n"):
            # Get title elements
            if line.startswith("=="):
                (level, section_title) = self.parse_section_title(line)

                if not level or not section_title:
                    self.debug("Skip section", line)
                    continue

                # Language section
                if level == 2:
                    section = Template.from_string(section_title)

                    if not section:
                        self.log("Section 2 is not a template", line)
                        continue

                    if section.title == "langue":
                        pars = section.unnamed
                        if pars:
                            lang = pars[0]
                        else:
                            lang = ""
                            self.log("Langue section has no lang parameter", line)
                    elif section.title == "caractère":
                        lang = ""
                        self.debug("Skip Caractere section", line)
                        has_char_section = True
                    else:
                        lang = ""
                        self.log("Unrecognized level 2 section template", line)
                elif lang and level == 3:
                    section = Template.from_string(section_title)

                    if not section:
                        self.log("Section 3 is not a template", line)
                        continue

                    templ_name = section.title

                    # Section template
                    if templ_name == "S":
                        pars = section.unnamed
                        if pars:
                            sname = pars[0]
                            wlang = None
                            wtype = ""
                            add_word = False

                            # Get word lang
                            if len(pars) > 1:
                                wlang = pars[1]

                            # Get controlled type name
                            if sname in word_types:
                                wtype = word_types[sname]
                                add_word = True

                            # Check if this is considered a word section
                            if add_word and wlang is None:
                                wlang = lang
                                self.log("Word has no lang", lang)

                            # Create a word
                            if add_word:
                                if cur_word:
                                    words.append(cur_word)
                                    cur_word = None

                                # Number
                                number = int(section.named.get("num", 1))

                                # Check if flexion
                                is_flexion = False
                                if len(pars) > 2:
                                    if pars[2] == "flexion":
                                        is_flexion = True
                                    else:
                                        self.log("Parameter 3 should be flexion", line)

                                # Check if locution
                                is_locution = False
                                if " " in self.title:
                                    is_locution = True

                                # TODO: check that is a word type

                                cur_word = Word(
                                    self.title,
                                    lang,
                                    wtype,
                                    is_flexion=is_flexion,
                                    is_locution=is_locution,
                                    number=number,
                                )

                                if wlang != lang:
                                    self.log(
                                        "Langue section parameter is different from word section section",
                                        f"{lang} vs {wlang}",
                                    )
                        else:
                            self.log("Level 3 section has no type parameter", line)
                    else:
                        self.log(f"Unrecognized level 3 template from '{section_title}'", line)
                elif cur_word:
                    words.append(cur_word)
                    cur_word = None

            elif line.startswith("'''") and lang and cur_word:
                form = Form(self.title, line)
                cur_word.add_form(form)

            elif line.startswith("#") and lang and cur_word:
                if def_match := self.def_regex.search(line):
                    def_line = def_match.group(1)
                    def_line = self.clean_def(def_line)
                    cur_word.add_def(def_line.strip())

        if cur_word:
            words.append(cur_word)

        if not has_char_section and len(words) == 0:
            self.log("No word parsed")
        return words

    def _template_def(self, match: Match) -> str:
        template_str = match.group(1)
        template = Template.from_string(template_str)
        title = template.title
        par = ""
        if len(template.unnamed) > 0:
            par = template.unnamed[0]

        temp_str = ""
        if title in self.temp_def_keep_with_par and par is not None:
            temp_str = title + " " + par

        elif title in self.temp_def_keep_only_par and par is not None:
            temp_str = par
        else:
            temp_str = title

        if title not in self.temp_def_no_capitalize:
            temp_str = temp_str.capitalize()

        if title not in self.temp_def_no_parentheses:
            temp_str = "(" + temp_str + ")"

        return temp_str

    def clean_def(self, line: str) -> str:
        """Clean up a definition string to only keep the text."""
        # Remove wiki links
        line = re.sub(r"\[\[([^\|\]]+?\|)?([^\|\]]+?)\]\]", r"\2", line)

        # Remove templates links with 1 parameter
        line = re.sub(r"(\{\{.+?\}\})", self._template_def, line)

        # Remove italic and bold
        line = re.sub("'''(.+)'''", r"\1", line)
        line = re.sub("''(.+)''", r"\1", line)

        return line
