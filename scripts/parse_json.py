#!/usr/bin/python

import os
import re
import json
from wikt.article import Article
from lxml import etree as ET
import argparse

parser = argparse.ArgumentParser(description="Parse a Wiktionnaire xml dump into a json array")
parser.add_argument('input', type=str, help='xml dump path')
parser.add_argument('output', type=str, help='json output path')
args = parser.parse_args()

xml_file = args.input
out_file = args.output

# Print to json file
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
            
            for ancestor in elem.xpath('ancestor-or-self::*'):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]
    del context
    outf.write("]\n")

