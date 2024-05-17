"""Main Wiktionnaire articles representation."""

import logging
import re
from re import Match
from typing import Any, Dict, List, Tuple
from wikt.data import word_types, word_attributes


class Template:
    """Template representation."""

    def __init__(
        self, title: str, params_list: None | List[str] = None, params_dict: None | Dict[str, str] = None
    ) -> None:
        self.title = title

        self.list_params = []
        if params_list:
            self.list_params = params_list

        self.dict_params = {}
        if params_dict:
            self.dict_params = params_dict


class TemplateFactory:
    """Generate template/templates from a wiki string."""

    template_inside_regex = re.compile(r"^ *\{\{ *([^\}]+) *\}\} *$")
    template_parts_regex = re.compile(r"^ *(.+?) *= *(.*?) *$")

    @classmethod
    def parse_template(cls, template_str: str) -> Template:
        """Parse a template string."""
        title = ""
        params_dict = {}
        params_list = []

        if templ_match := cls.template_inside_regex.search(template_str):
            templ_content = templ_match.group(1)
            templ_parts = templ_content.split("|")

            for part in templ_parts:
                if part_match := cls.template_parts_regex.search(part):
                    pkey = part_match.group(1)
                    pval = part_match.group(2)
                    if pval:
                        params_dict[pkey] = pval
                else:
                    pval = part.strip()
                    if not pval:
                        continue
                    if not title:
                        title = pval
                        continue
                    params_list.append(pval)

        template = Template(title, params_list=params_list, params_dict=params_dict)

        return template


class WikiBase:
    """A base Wiki object with an article title."""

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
        super().__init__(title)
        self.form = None
        self.prons: List[str] = []
        self.attributes: List[str] = []

        self.parse_form_line(form_line)

    def parse_form_line(self, line: str) -> None:
        """Parse a form line in the form '''(WORD)''' (PROPERTIES in templates)"""
        templates: Dict[str, List[Template]] = self.get_templates(line)

        # Get pronunciations
        if "pron" in templates:
            prons = templates["pron"]

            for pron in prons:
                if pron.list_params:
                    pron_str = pron.list_params[0]
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

    def get_templates(self, string: str) -> Dict[str, List[Template]]:
        """Retrieve all templates from a wiki string."""
        templates: Dict[str, List[Template]] = {}

        if string is None:
            return templates

        template_strings = self.template_regex.findall(string)

        for temp_str in template_strings:
            template = TemplateFactory.parse_template(temp_str)
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
        super().__init__(title)
        self.lang = lang
        self.type = wtype
        self.form: Form = Form(title, "")
        self.defs: List[str] = []
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

    def struct(self) -> Dict[str, Any]:
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


class WikiArticle(WikiBase):
    """General Wiki page split in wiki sections."""

    section_regex = re.compile(r"^(=+) *(.+?) *(=+)$")
    empty_regex = re.compile(r"^ *$")

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
        super().__init__(title)
        self.words: List[Word] = self.parse(title, text)

    def __str__(self):
        lines = [f"TITLE = {self.title}", f"WORDS = {len(self.words)}"]
        return "\n".join(lines)

    def parse(self, title: str, text: str) -> List[Word]:
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
                    section = TemplateFactory.parse_template(sec_title)

                    if not section:
                        self.log("Section 2 is not a template", line)
                        continue

                    if section.title == "langue":
                        pars = section.list_params
                        if pars:
                            lang = pars[0]
                        else:
                            lang = ""
                            self.log("Langue section has no lang parameter", line)
                    elif section.title == "caractère":
                        lang = ""
                        self.debug("Skip Caractere section", line)
                    else:
                        lang = ""
                        self.log("Unrecognized level 2 section template", line)
                elif lang and level == 3:
                    section = TemplateFactory.parse_template(sec_title)

                    if not section:
                        self.log("Section 3 is not a template", line)
                        continue

                    templ_name = section.title

                    # Section template
                    if templ_name == "S":
                        pars = section.list_params
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
                                number = int(section.dict_params.get("num", 1))

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

        if len(words) == 0 and not re.match("#REDIRECT", text, re.IGNORECASE):
            self.log("No word parsed")
        return words

    def _template_def(self, match: Match) -> str:
        template_str = match.group(1)
        template = TemplateFactory.parse_template(template_str)
        title = template.title
        par = ""
        if len(template.list_params) > 0:
            par = template.list_params[0]

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
