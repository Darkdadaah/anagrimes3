"""Main Wiktionnaire articles representation."""

import logging
import re
from re import Match
from typing import Dict, List, Tuple
from wikt.data import word_types, word_attributes


class WikiBase:
    """A wiki page with basic parsing."""

    section_regex = re.compile(r"^(=+) *(.+?) *(=+)$")
    template_inside_regex = re.compile(r"^ *\{\{ *([^\}]+) *\}\} *$")
    template_parts_regex = re.compile(r"^ *(.+?) *= *(.*?) *$")
    empty_regex = re.compile(r"^ *$")

    def __init__(self, title: str) -> None:
        self.title = title

    def log(self, name: str, detail: str = "") -> None:
        """Custom print to log as info."""
        logging.info(f"LOG\t[[{self.title}]]\t{name}\t{detail}")

    def debug(self, name: str, detail: str = "") -> None:
        """Custom print to log as debug."""
        logging.debug(f"DEBUG\t[[{self.title}]]\t{name}\t{detail}")

    def parse_section(self, section_str: str) -> Tuple[int, str]:
        """Extract the level and content of the section title."""
        sec_match = self.section_regex.search(section_str.strip())
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

    def parse_template(self, template_str: str) -> Dict[str, str]:
        """Parse a template string."""
        template = {}

        if templ_match := self.template_inside_regex.search(template_str):
            templ_content = templ_match.group(1)
            templ_parts = templ_content.split("|")

            part_i = 0
            for part in templ_parts:
                if part_match := self.template_parts_regex.search(part):
                    pkey = part_match.group(1)
                    pval = part_match.group(2)
                    if pval != "":
                        template[pkey] = pval
                else:
                    pval = part.strip()
                    if pval != "":
                        template[str(part_i)] = pval
                    part_i += 1

        return template


class Article(WikiBase):
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
        super().__init__(title)
        self.words: List[str] = self.parse(title, text)

    def __str__(self):
        lines = [f"TITLE = {self.title}", f"WORDS = {len(self.words)}"]
        return "\n".join(lines)

    def parse(self, title: str, text: str) -> List[str]:
        """Parse a Wiktionnaire article."""
        words = []

        # Parse language sections
        lang = ""
        cur_word = None
        if text is None:
            return words
        for line in text.split("\n"):
            # Get title elements
            if line.startswith("=="):
                (level, sec_title) = self.parse_section(line)

                if level is None or self.empty_regex.search(sec_title):
                    self.debug("Skip section", line)
                    continue

                # Language section
                if level == 2:
                    section = self.parse_template(sec_title)

                    if not section:
                        self.log("Section 2 is not a template", line)
                        continue

                    if section and "0" in section:
                        templ_name = section["0"]

                        if templ_name == "langue":
                            if "1" in section:
                                lang = section["1"]
                            else:
                                lang = None
                                self.log("Langue section has no lang parameter", line)
                        elif templ_name == "caractère":
                            lang = None
                            self.debug("Skip Caractere section", line)
                        else:
                            lang = None
                            self.log("Unrecognized level 2 section template", line)
                    else:
                        lang = None
                        self.log("Unrecognized level 2 section", line)
                elif lang and level == 3:
                    section = self.parse_template(sec_title)

                    if not section:
                        self.log("Section 3 is not a template", line)
                        continue

                    if section and "0" in section:
                        templ_name = section["0"]

                        # Section template
                        if templ_name == "S":
                            if "1" in section:
                                sname = section["1"]
                                wlang = None
                                wtype = None
                                add_word = False

                                # Get word lang
                                wlang = section.get("2")

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
                                    number = section.get("num", 1)

                                    # Check if flexion
                                    is_flexion = False
                                    if "3" in section:
                                        if section["3"] == "flexion":
                                            is_flexion = True
                                        else:
                                            self.log("Parameter 3 should be flexion", line)

                                    # Check if locution
                                    is_locution = False
                                    if " " in self.title:
                                        is_locution = True

                                    cur_word = Word(
                                        title,
                                        lang,
                                        wtype,
                                        is_flexion=is_flexion,
                                        is_locution=is_locution,
                                        number=number,
                                    )

                                    # TODO: check that is a word type
                                    if wlang != lang:
                                        self.log(
                                            "Langue section parameter is different from word section section",
                                            f"{lang} vs {wlang}",
                                        )
                            else:
                                self.log("Level 3 section has no type parameter", line)
                        else:
                            self.log("Unrecognized level 3 template", line)
                    else:
                        self.log("Unrecognized level 3 section", line)
                elif cur_word:
                    words.append(cur_word)
                    cur_word = None

            elif line.startswith("'''") and lang and cur_word:
                form = Form(title, line)
                cur_word.add_form(form)

            elif line.startswith("#") and lang and cur_word:
                if def_match := self.def_regex.search(line):
                    def_line = def_match.group(1)
                    def_line = self.clean_def(def_line)
                    cur_word.add_def(def_line.strip())

        if cur_word:
            words.append(cur_word)

        if len(words) == 0 and not re.match("#REDIRECT", text):
            self.log("No word parsed")
        return words

    def _template_def(self, match: Match) -> str:
        template_str = match.group(1)
        parts = self.parse_template(template_str)

        title = parts.get("0")
        par = parts.get("1")

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
        super().__init__(title)
        self.lang = lang
        self.type = wtype
        self.form = None
        self.defs = []
        self.is_flexion = is_flexion
        self.is_locution = is_locution
        self.number = number

    def add_def(self, def_line: str) -> None:
        """Add a definition from a definition line."""
        self.defs.append(def_line)

    def add_form(self, form: str) -> None:
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

    def struct(self) -> dict:
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


class Form(WikiBase):
    """Word form line parsing."""

    form_regex = re.compile(r"^'''(.+?)''' ?(.+)? *$")
    template_regex = re.compile(r"(\{\{[^\}]+?\}\})")

    def __init__(self, title: str, form_line: str) -> None:
        super().__init__(title)
        self.form = None
        self.prons = []
        self.attributes = []

        self.parse_form_line(form_line)

    def parse_form_line(self, line: str) -> None:
        """Parse a form line in the form '''(WORD)''' (PROPERTIES in templates)"""
        templates = self.get_templates(line)

        # Get pronunciations
        if "pron" in templates:
            prons = templates["pron"]

            for pron in prons:
                if "1" in pron:
                    pron_str = pron["1"]
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

    def get_templates(self, string: str) -> Dict[str, str]:
        """Retrieve all templates from a wiki string."""
        templates = {}

        if string is None:
            return templates

        temps = self.template_regex.findall(string)

        for temp_str in temps:
            parts = self.parse_template(temp_str)
            title = parts.get("0", "")
            if title in templates:
                templates[title].append(parts)
            else:
                templates[title] = [parts]

        return templates
