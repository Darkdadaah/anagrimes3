#!/usr/bin/python

import re, sys
from wikt.data import word_types, word_attributes


class WikiBase(object):

    section_regex = re.compile("^(=+) *(.+?) *(=+)$")
    template_inside_regex = re.compile("^ *\{\{ *([^\}]+) *\}\} *$")
    template_parts_regex = re.compile("^ *(.+?) *= *(.*?) *$")
    empty_regex = re.compile("^ *$")

    def log(self, name, detail=""):
        print("LOG\t[[%s]]\t%s\t%s" % (self.title, name, detail), file=sys.stderr)

    def debug(self, name, details=""):
        pass
        # self.log(name, details)

    def parse_section(self, section_str):
        # Extract the level and content of the section title
        if sec_match := self.section_regex.search(section_str.strip()):
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
        else:
            self.log("Can't parse section", section_str)
            return (0, "")

    def parse_template(self, template_str):
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

    def __init__(self, title, text):
        self.title = title
        self.words = self.parse(title, text)

    def parse(self, title, text):
        words = []

        # Parse language sections
        lang = ""
        cur_word = None
        if text == None:
            return words
        for line in text.split("\n"):
            # Get title elements
            if line.startswith("=="):
                (level, sec_title) = self.parse_section(line)

                if level == None or self.empty_regex.search(sec_title):
                    self.debug("Skip section", line)
                    continue

                # Language section
                if level == 2:
                    section = self.parse_template(sec_title)

                    if section == {}:
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

                    if section == {}:
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
                                if "2" in section:
                                    wlang = section["2"]

                                # Get controlled type name
                                if sname in word_types:
                                    wtype = word_types[sname]
                                    add_word = True

                                # Check if this is considered a word section
                                if add_word and wlang == None:
                                    wlang = lang
                                    self.log("Word has no lang", lang)

                                # Create a word
                                if add_word:
                                    if cur_word:
                                        words.append(cur_word)
                                        cur_word = None

                                    # Number
                                    number = 1
                                    if "num" in section:
                                        number = section["num"]

                                    # Check if flexion
                                    is_flexion = False
                                    if "3" in section:
                                        if section["3"] == "flexion":
                                            is_flexion = True
                                        else:
                                            self.log(
                                                "Parameter 3 should be flexion", line
                                            )

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
                                            "%s vs %s" % (lang, wlang),
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

    def _template_def(self, match):
        template_str = match.group(1)
        parts = self.parse_template(template_str)

        title = None
        par = None
        if "0" in parts:
            title = parts["0"]
        if "1" in parts:
            par = parts["1"]

        temp_str = ""
        if title in self.temp_def_keep_with_par and par != None:
            temp_str = title + " " + par

        elif title in self.temp_def_keep_only_par and par != None:
            temp_str = par
        else:
            temp_str = title

        if title not in self.temp_def_no_capitalize:
            temp_str = temp_str.capitalize()

        if title not in self.temp_def_no_parentheses:
            temp_str = "(" + temp_str + ")"

        return temp_str

    def clean_def(self, line):
        # Remove wiki links
        line = re.sub("\[\[([^\|\]]+?\|)?([^\|\]]+?)\]\]", r"\2", line)

        # Remove templates links with 1 parameter
        line = re.sub("(\{\{.+?\}\})", self._template_def, line)

        # Remove italic and bold
        line = re.sub("'''(.+)'''", r"\1", line)
        line = re.sub("''(.+)''", r"\1", line)

        return line

    def __str__(self):
        lines = ["TITLE = %s" % self.title, "WORDS = %d" % len(self.words)]
        return "\n".join(lines)


class Word(WikiBase):

    def __init__(
        self, title, lang, wtype, is_flexion=False, is_locution=False, number=None
    ):
        self.title = title
        self.lang = lang
        self.type = wtype
        self.form = None
        self.defs = []
        self.is_flexion = is_flexion
        self.is_locution = is_locution
        self.number = number

    def add_def(self, def_line):
        self.defs.append(def_line)

    def add_form(self, form):
        self.form = form

    def __str__(self):
        lines = [
            "TITLE = %s" % self.title,
            "LANG  = %s" % self.lang,
            "TYPE  = %s" % self.type,
            "PRONS = %s" % self.form.prons,
            "DEFS  = %d" % len(self.defs),
        ]
        return "\n\t".join(lines)

    def struct(self):
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

    form_regex = re.compile("^'''(.+?)''' ?(.+)? *$")
    template_regex = re.compile("(\{\{[^\}]+?\}\})")

    def __init__(self, title, form_line):
        self.title = title
        self.form = None
        self.prons = []
        self.attributes = []

        self.parse_form_line(form_line)

    def parse_form_line(self, line):
        # Form line is like this: '''(WORD)''' (PROPERTIES in templates)
        templates = self.get_templates(line)

        # Get pronunciations
        if "pron" in templates:
            prons = templates["pron"]

            for pron in prons:
                if "1" in pron:
                    pron_str = pron["1"]
                    self.add_pron(pron_str)

        # Get other attributes
        for attr in word_attributes:
            if attr in templates:
                self.add_attribute(word_attributes[attr])

    def add_pron(self, pron_str):
        self.prons.append(pron_str)

    def add_attribute(self, attr):
        if attr not in self.attributes:
            self.attributes.append(attr)
        else:
            self.log("Attribute written twice", attr)

    def get_templates(self, string):
        templates = {}

        if string == None:
            return templates

        temps = self.template_regex.findall(string)

        for temp_str in temps:
            parts = self.parse_template(temp_str)
            title = parts["0"]
            if title in templates:
                templates[title].append(parts)
            else:
                templates[title] = [parts]

        return templates
