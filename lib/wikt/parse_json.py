"""Parse a Wiktionnaire xml dump into a jsonl format."""

import json
import importlib
import logging

import argparse
from lxml import etree

wikt_languages = set(("fr","en"))

def main():
    """main entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, help="xml dump path")
    parser.add_argument("output", type=str, help="json output path")
    parser.add_argument("lang", type=str, help="Wiktionary language code", default="fr")
    parser.add_argument(
        "-v",
        "--verbose",
        help="Be verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Print lots of debugging statements",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    xml_file = args.input
    out_file = args.output
    lang = args.lang

    if lang in wikt_languages:
        wiktionary = importlib.import_module(f"wikt.lang.{lang}")
    else:
        raise RuntimeError(f"Language code {lang} is not supported")

    xml_ns = "{http://www.mediawiki.org/xml/export-0.11/}"
    ns = 0

    # Print to json file
    with open(out_file, "w") as outf:
        num = 0
        skipped = 0
        noword = 0

        context = etree.iterparse(xml_file, events=("start", "end"))
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
                    print(f"{num} articles")
                article = wiktionary.Article(title, text)

                for word in article.words:
                    outf.write(json.dumps(word.struct(), ensure_ascii=False) + "\n")

                for ancestor in elem.xpath("ancestor-or-self::*"):
                    while ancestor.getprevious() is not None:
                        del ancestor.getparent()[0]

        print(f"{num} pages parsed")
        print(f"{skipped} pages skipped")
        print(f"{noword} pages without words")

        del context


if __name__ == "__main__":
    main()
