#!/usr/bin/python

import re

class Article:
    
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
            if line.startswith("==="):
                if word_match := re.search("\{\{S\|([^\|\}]+)\|([^\|\}]+)\}\}", line):
                    wtype = word_match.group(1)
                    wlang = word_match.group(2)
                    self.debug("Word = " + wtype)

                    if cur_word:
                        words.append(cur_word)
                        cur_word = None

                    cur_word = Word(title, lang, wtype)

                    if wlang != lang:
                        self.log("Langue different in word section: %s vs %s " % (lang, wlang))

            elif line.startswith("=="):
                if lang_match := re.search("\{\{langue\|(.+)\}\}", line):
                    lang = lang_match.group(1)
                    self.debug("Langue = " + lang)
                elif lang_match := re.search("\{\{caractère\}\}", line):
                    pass
                else:
                    self.log("Parsing error: template:langue <%s>" % line)

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

    def _template_sub(self, match):
     return '(' + match.group(1).capitalize() + ')'

    def clean_def(self, line):
        line = re.sub("\[\[([^\|\]]+?\|)?([^\|\]]+?)\]\]", r"\2", line)
        line = re.sub("\{\{([^\|\}]+?)\|(.+?)\}\}", self._template_sub, line)
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

class Word:

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

