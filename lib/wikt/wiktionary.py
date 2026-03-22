"""Generic Wiktionary objects, independent of language."""

from __future__ import annotations

# import logging
import re
from typing import Any

from wikt.wiki import Template, WikiBase, WikiArticle

__all__ = ["WiktForm", "WiktArticle", "WiktWord"]


class WiktForm(WikiBase):
    """Word form line parsing."""

    template_regex = re.compile(r"(\{\{[^\}]+?\}\})")

    def __init__(self, title: str) -> None:
        super().__init__(f"{title}-form_line")
        self.form = None
        self.prons: list[str] = []
        self.attributes: list[str] = []

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


class WiktWord(WikiBase):
    """A Wiktionary word representation."""

    def __init__(
        self,
        title: str,
        lang: str,
        wtype: str,
        is_flexion: bool = False,
        is_locution: bool = False,
        is_mutation: bool = False,
        number: int = 0,
    ) -> None:
        super().__init__(f"{title}#{lang}-{wtype}-{number}")
        self.lang = lang
        self.type = wtype
        self.form: WiktForm = WiktForm(title)
        self.defs: list[str] = []
        self.is_flexion = is_flexion
        self.is_locution = is_locution
        self.is_mutation = is_mutation
        self.number = number

    def add_def(self, def_line: str) -> None:
        """Add a definition from a definition line."""
        self.defs.append(def_line)

    def add_form(self, form: WiktForm) -> None:
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
            "is_mutation": self.is_mutation,
            "number": self.number,
        }

        # Add form properties
        if self.form:
            if self.form.prons:
                struct["prons"] = self.form.prons
            if self.form.attributes:
                struct["attributes"] = self.form.attributes
        return struct


class WiktArticle(WikiArticle):
    """A Wiktionnaire article."""

    def __init__(self, title: str, text: str) -> None:
        super().__init__(title, text)
        self.words: list[WiktWord] = []

    def __str__(self):
        lines = [f"TITLE = {self.title}", f"WORDS = {len(self.words)}"]
        return "\n".join(lines)
