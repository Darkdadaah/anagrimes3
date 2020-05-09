#!/usr/bin/python

import os
import json
from wikt.article import Article
#import xml.etree.ElementTree as ET
from lxml import etree as ET
import re


xml_file = os.path.join(os.path.dirname(__file__), "../data/frwikt.xml")

# Print to json file
out_file = os.path.join(os.path.dirname(__file__), "../data/frwikt.json")

with open(out_file, "w") as outf:
    title = None
    num = 0
    namespaced = re.compile(".+:.+")
    outf.write("[\n")
    context = ET.iterparse(xml_file, events=("start","end"))
    for event, elem in context:
        _, _, tag = elem.tag.rpartition('}')
        if tag == "title" and event == "end":
            if namespaced.match(elem.text):
                continue
            title = elem.text
            elem.clear()
        elif title != None and tag == "text" and event == "end":
            num += 1
            if num % 100000 == 0:
                print("%d articles" % num)
            article = Article(title, elem.text)
            for word in article.words:
                if num > 1:
                    outf.write(",\n")
                outf.write(json.dumps(word.struct(), ensure_ascii=False, indent=4) + "\n")
            title = None
            
            # Cleanup, from https://www.ibm.com/developerworks/xml/library/x-hiperfparse/
#            elem.clear()
#            while elem.getprevious() is not None:
#                del elem.getparent()[0]


            for ancestor in elem.xpath('ancestor-or-self::*'):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]
    del context
    outf.write("]\n")

