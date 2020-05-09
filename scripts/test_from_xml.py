#!/usr/bin/python

import os
import json
from wikt.article import Article
import xml.etree.ElementTree as ET
import re


xml_file = os.path.join(os.path.dirname(__file__), "../data/frwikt.xml")

# Print to json file
out_file = os.path.join(os.path.dirname(__file__), "../data/frwikt.jsonl")

with open(out_file, "w") as outf:
    title = None
    namespaced = re.compile(".+:.+")
    for event, elem in ET.iterparse(xml_file, events=("start","end")):
        _, _, tag = elem.tag.rpartition('}')
        if tag == "title" and event == "end":
            if namespaced.match(elem.text):
                continue
            title = elem.text
            elem.clear()
        elif title != None and tag == "text" and event == "end":
            article = Article(title, elem.text)
            for word in article.words:
                outf.write(json.dumps(word.struct(), ensure_ascii=False) + "\n")
            title = None
            elem.clear()

