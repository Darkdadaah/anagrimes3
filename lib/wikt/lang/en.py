"""English Wiktionary parser."""

from __future__ import annotations
# import logging
import re
from re import Match

from wikt.data.en import word_types, word_attributes
from wikt.wiki import Template, WikiParserError
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

        headword_lang = ""
        headword_type = ""

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
                    self.debug(f"Got language section {lang}")

            # Don't bother parsing without lang section
            if not lang:
                continue

            # In en.wiktionary headword lines are the best way to find word sections
            # See https://en.wiktionary.org/wiki/Wiktionary:Entry_layout#Headword_line
            # Two cases, both on one line (may be followed by other templates):
            # 1) General template {{head|lang|part of speech}}
            # 2) Language specific templates {{lang-part_of_speech}}
            # Both may have additional parameters like genre
            # 2 is harder to parse given that we have to guess with the context and the format

            # {{head|lang|part of speech}}
            if line.startswith("{{head|"):
                head = Template.list_templates(line)[0]
                if not head.title == "head":
                    raise WikiParserError(f"Should be a headword line in {head}: {line}")
                try:
                    headword_lang = head.unnamed[0]
                    headword_type = head.unnamed[1]
                except IndexError as e:
                    raise WikiParserError(f"Invalid headword template: {line}") from e

            # {{lang-part_of_speech}} (assumed)
            if not headword_lang and not headword_type and line.startswith("{{"):
                if re.search(r"^\{\{.{2,3}-([^\|\}]+)[\|\}]", line):
                    head = Template.list_templates(line)[0]
                    self.debug(f"Check matching {head}")

                    # Lang-type template
                    m = re.search(r"^(.{2,3})-([^-]+?)$", head.title)
                    if m:
                        wlang = m.group(1)
                        part2 = m.group(2)
                        if part2 == "head":
                            headword_lang = wlang
                            headword_type = head.unnamed[0]
                        elif part2 in word_types:
                            headword_lang = wlang
                            headword_type = part2
                        # By this point we can't know if this is a POS

            # Whatever method we used, we found a headword line!
            if headword_lang and headword_type:
                wtype = headword_type
                wlang = headword_lang

                # Only do this once
                headword_type = ""
                headword_lang = ""

                # TODO: Check if "form" before checking the type
                is_flexion = False
                m = re.search(r"^(.+) form$", wtype)
                if m:
                    wtype = m.group(1)
                    is_flexion = True

                if wtype not in word_types:
                    if wtype.endswith("f"):
                        wtype = wtype[:-1]
                        if wtype in word_types:
                            self.debug(f"Found 'wordf' form: {wtype} in {head}")
                            is_flexion = True
                        else:
                            self.log(f"Unknown word type: {wtype}")
                    else:
                        self.log(f"Unknown word type: {wtype}")

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
                    is_flexion=is_flexion,
                    number=number,
                )
                form = Form(self.title, line)
                cur_word.add_form(form)

                # Last try to get the Word type
                if not wtype:
                    wtype = section_title.strip().lower()
                    self.debug(f"Using section title for Word type: {wtype}")


            elif line.startswith("#") and cur_word:
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
