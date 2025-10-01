"""English Wiktionary parser."""

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

    def parse_form_line(self, _: str) -> None:
        """Parse a form line in the form {{head|lang|form name|+}}"""
        # TODO: get word attributes
        assert word_attributes


class Article(WiktArticle):
    """A Wiktionary article."""

    def_regex = re.compile("^#+([^#*:] *.+)$")

    temp_def_keep_only_par = ["lb"]
    temp_def_keep_with_par = [""]
    temp_def_no_parentheses = temp_def_keep_with_par
    temp_def_no_capitalize = [""]

    def __init__(self, title: str, text: str) -> None:
        super().__init__(title, text)
        self.words: list[WiktWord] = self.parse_words()

    def parse_words(self) -> list[WiktWord]:
        """Parse a Wiktionary article into words."""
        words = []

        # Parse language sections
        lang = ""
        cur_word = None
        section_title = ""
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
                    lang = section_title.strip()

            # {{head|}} Is the true sign that this is a word section
            elif line.startswith("{{head|") and lang:
                head = Template.from_string(line)

                wlang = ""
                wtype = ""
                if head.title == "head":
                    try:
                        wlang = head.unnamed[0]
                        wtype = head.unnamed[1]
                    except IndexError as e:
                        raise RuntimeError(f"Format error: {line} -> {head}") from e

                wtype = wtype.replace(" form", "").strip().lower()
                try:
                    wtype = word_types[wtype]
                except KeyError:
                    self.log(f"Section 3 of {self.title} is not a known word type: '{wtype}'", line)
                self.debug(f"Found Word section: {wlang}-{wtype}")

                # Store any previous word we were scanning for
                if cur_word:
                    words.append(cur_word)
                    cur_word = None

                # Number
                # TODO: add a number if several same types are found
                number = 1

                # Check if locution
                is_locution = False
                if " " in self.title:
                    is_locution = True

                cur_word = WiktWord(
                    self.title,
                    wlang,
                    wtype,
                    is_locution=is_locution,
                    number=number,
                )
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
