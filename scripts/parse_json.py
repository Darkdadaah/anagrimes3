#!/usr/bin/python

import os
import re
import json
from wikt.article import Article
from lxml import etree as ET
import argparse

parser = argparse.ArgumentParser(
    description="Parse a Wiktionnaire xml dump into a json array"
)
parser.add_argument("input", type=str, help="xml dump path")
parser.add_argument("output", type=str, help="json output path")
args = parser.parse_args()

xml_file = args.input
out_file = args.output

xml_ns = "{http://www.mediawiki.org/xml/export-0.10/}"
ns = 0

# Print to json file
with open(out_file, "w") as outf:
    num = 0
    skipped = 0
    noword = 0

    outf.write("[\n")
    context = ET.iterparse(xml_file, events=("start", "end"))
    for event, elem in context:
        _, _, tag = elem.tag.rpartition("}")

        if tag == "page" and event == "end":
            page_ns = int(elem.find(xml_ns + "ns").text)
            if page_ns != ns:
                skipped += 1
                continue
            title = elem.find(xml_ns + "title").text
            revision = elem.findall(xml_ns + "revision")[-1]
            text = revision.find(xml_ns + "text").text
            elem.clear()

            num += 1
            if num % 1000 == 0:
                print("%d articles" % num)
            article = Article(title, text)

            for word in article.words:
                if num > 1:
                    outf.write(",\n")
                outf.write(
                    json.dumps(word.struct(), ensure_ascii=False, indent=4) + "\n"
                )

            for ancestor in elem.xpath("ancestor-or-self::*"):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]

    print("%d pages parsed" % num)
    print("%d pages skipped" % skipped)
    print("%d pages without words" % noword)

    del context
    outf.write("]\n")
