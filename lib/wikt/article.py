#!/usr/bin/python

import re

class WikiBase(object):

    def parse_section(self, section_str):
        # Extract the level and content of the section title
        if sec_match := re.search("^(=+) *(.+?) *(=+)$", section_str.strip()):
            sec_start = sec_match.group(1)
            sec_title = sec_match.group(2)
            sec_end = sec_match.group(3)
            
            # Get level
            sec_level = 0
            for nlevel in range(2,6):
                sec_signs = '=' * nlevel
                if sec_start == sec_signs:
                    sec_level = nlevel
                    if sec_end != sec_signs:
                        self.log("Section level start and end differ: %s ... %s" % (sec_start, sec_end))

            return (sec_level, sec_title)
        else:
            self.log("Can't parse section: <%s>" % section_str)
            return(0, "")

    def parse_template(self, template_str):
        template = {}
        
        if templ_match := re.search("^ *\{\{ *(.+) *\}\} *$", template_str):
            templ_content = templ_match.group(1)
            templ_parts = templ_content.split("|")

            part_i = 0
            for part in templ_parts:
                if part_match := re.search("^ *(.+?) *= *(.+?) *$", part):
                    pkey = part_match.group(1)
                    pval = part_match.group(2)
                    template[pkey] = pval
                else:
                    template[str(part_i)] = part.strip()
                    part_i += 1

        return template

class Article(WikiBase):
    
    def __init__(self, title, text):
        self.title = title
        self.words = self.parse(title, text)

    def parse(self, title, text):
        words = []

        # Parse language sections
        lang = ""
        cur_word = None
        if text == None: return words
        for line in text.split("\n"):
            # Get title elements
            if line.startswith("=="):
                (level, sec_title) = self.parse_section(line)
                
                if level == None or re.search("^ *$", sec_title):
                    self.log("Skip section: %s" % line)
                    continue

                # Language section
                if level == 2:
                    section = self.parse_template(sec_title)

                    if section == {}:
                        self.log("Section 3 is not a template: %s" % line)
                        continue

                    if section and "0" in section:
                        templ_name = section["0"]

                        if templ_name == "langue":
                            if "1" in section:
                                lang = section["1"]
                            else:
                                lang = None
                                self.log("Langue section has no lang parameter:" % line)
                        elif templ_name == "caractère":
                            lang = None
                            self.debug("Skip Caractere section: %s" % line)
                        else:
                            lang = None
                            self.log("Unrecognized level 2 section template: %s" % line)
                    else:
                        lang = None
                        self.log("Unrecognized level 2 section: %s" % line)
                elif level == 3:
                    section = self.parse_template(sec_title)
                    
                    if section == {}:
                        self.log("Section 3 is not a template: %s" % line)
                        continue

                    if section and "0" in section:
                        templ_name = section["0"]

                        # Section template
                        if templ_name == "S":
                            if "1" in section:
                                wtype = section["1"]

                                # Check lang
                                if "2" in section:
                                    wlang = section["2"]

                                    # Create a word
                                    if cur_word:
                                        words.append(cur_word)
                                        cur_word = None
                                    cur_word = Word(title, lang, wtype)
                                    
                                    # TODO: check that is a word type
                                    if wlang != lang:
                                        self.log("Langue section parameter is different from word section section: %s vs %s" % (lang, wlang))
                                #else:
                                #    self.log("Missing lang parameter in word section title: %s" % line)
                            else:
                                self.log("Level 3 section has no type parameter:" % line)
                        else:
                            self.log("Unrecognized level 3 template: %s" % line)
                    else:
                        self.log("Unrecognized level 3 section: %s" % line)

            elif line.startswith("'''"):
                form_line = line
                self.debug("Got form line")

            elif line.startswith("#"):
                if def_match := re.search("^#+([^#*:] *.+)$", line):
                    def_line = def_match.group(1)
                    def_line = self.clean_def(def_line)
                    if (cur_word):
                        cur_word.add_def(def_line.strip())
                    else:
                        pass
#                        self.log("Trying to get def outside a word section: " + line)

        return words

    def _template_sub_1pars(self, match):
     return '(' + match.group(1).capitalize() + ' ' + match.group(2) + ')'

    def _template_sub_0pars(self, match):
     return '(' + match.group(1).capitalize() + ')'

    def clean_def(self, line):
        # Remove wiki links
        line = re.sub("\[\[([^\|\]]+?\|)?([^\|\]]+?)\]\]", r"\2", line)

        # Remove templates links with 1 parameter
        line = re.sub("\{\{([^\|\}]+?)\|(.+?)\}\}", self._template_sub_1pars, line)
        # Remove templates links with no parameters
        line = re.sub("\{\{([^\|\}]+?)\}\}", self._template_sub_0pars, line)
        
        # Remove italic and bold
        line = re.sub("'''(.+)'''", r"\1", line)
        line = re.sub("''(.+)''", r"\1", line)

        return line

    def __str__(self):
        lines = [
                "TITLE = %s" % self.title,
                "WORDS = %d" % len(self.words)
                ]
        return "\n".join(lines)


    def log(self, text):
        #pass
        print("LOG [[%s]] : %s" % (self.title, text))

    def debug(self, text):
        pass
        #print("LOG: " + text)

class Word(WikiBase):

    def __init__(self, title, lang, wtype):
        self.title = title
        self.lang = lang
        self.type = wtype
        self.form = None
        self.defs = []

    def add_def(self, def_line):
        self.defs.append(def_line)

    def __str__(self):
        lines = [
                "TITLE = %s" % self.title,
                "LANG  = %s" % self.lang,
                "TYPE  = %s" % self.type,
                "DEFS  = %d" % len(self.defs)
                ]
        return "\n\t".join(lines)

    def struct(self):
        struct = {
            "title" : self.title,
            "lang" : self.lang,
            "type" : self.type,
            "defs" : self.defs,
        }
        return struct

