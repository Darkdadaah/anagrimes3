"""French Wiktionary parser."""

from __future__ import annotations
# import logging
import re
from re import Match

from wikt.data.en import word_types, word_attributes
from wikt.wiki import Template
from wikt.wiktionary import WiktArticle, WiktForm, WiktWord

__all__ = ['Article']

class Form(WiktForm):
    """Word form line parsing."""

    def __init__(self, title: str, form_line: str) -> None:
        super().__init__(f"{title}-form_line")
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


class Article(WiktArticle):
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
        self.words: list[WiktWord] = self.parse_words()

    def parse_words(self) -> list[WiktWord]:
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

                                cur_word = WiktWord(
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
