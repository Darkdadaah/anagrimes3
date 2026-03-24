"""Template from a wiki."""

from __future__ import annotations
from dataclasses import dataclass, field
import re


MAX_UNAMED = 50


class TemplateError(Exception):
    """Raised when parsing a template fails."""


@dataclass
class Template:
    """Generic Wiki Template representation.

    Attributes:
        title: Template name.
        unnamed: An ordered list of unnamed parameters.
        named: A dictionary of named parameters.
    """

    title: str
    unnamed: list[str] = field(default_factory=list)
    named: dict[str, str] = field(default_factory=dict)

    _template_inside_regex = re.compile(r"^ *\{\{ *([^\}]+) *\}\} *$")
    _template_parts_regex = re.compile(r"^ *(.+?) *= *(.*?) *$")

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
        unnamed = unnamed[0 : last_index + 1]
        if len(unnamed) == 1 and unnamed[0] == "":
            unnamed = []

        return Template(title, unnamed, named)

    @classmethod
    def list_templates(cls, line_str: str) -> list[Template]:
        """Returns a list of templates in a line.
        This assumes there are no nested templates.
        """
        line_str = line_str.strip()
        templates = []
        for temp_str in line_str.split(r"}}"):
            if not temp_str.endswith(r"}}"):
                temp_str = temp_str + "}}"
            temp = Template.from_string(temp_str)
            if temp.title:
                templates.append(temp)

        return templates
