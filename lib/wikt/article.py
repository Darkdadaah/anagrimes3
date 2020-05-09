#!/usr/bin/python

import re

class Article:
    
    def __init__(self, title, text):
        self.title = title
        self.words = self.parse(text)

    def parse(self, text):
        words = {}

        # Parse language sections
        lang = ""
        cur_word = None
        for line in text.split("\n"):
            if line.startswith("== {{langue|"):
                if lang_match := re.search("\{\{langue\|(.+)\}\}", line):
                    lang = lang_match.group(1)
                    self.log("Langue = " + lang)
                else:
                    self.log("Parsing error: template:langue")
            elif line.startswith("=== {{S|"):
                if word_match := re.search("\{\{S\|([^\|\}]+)\|([^\|\}]+)\}\}", line):
                    wtype = word_match.group(1)
                    wlang = word_match.group(2)
                    self.log("Word = " + wtype)

                    if wlang != lang:
                        self.log("Langue different in word section: %s vs %s " % (lang, wlang))
                #else:
                    #self.log("Skipped section: " + line)
            elif line.startswith("'''"):
                form_line = line
                self.log("Got form line")
            elif line.startswith("#"):
                def_line = "line"
                self.log("Got def")

        return words

    def log(self, text):
        print("LOG: " + text)


