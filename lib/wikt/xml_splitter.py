"""Parse a Wiktionnaire xml dump into a jsonl format."""

import logging
from pathlib import Path

import argparse
from lxml import etree

DEFAULT_BATCH = 10000


def main():
    """main entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, help="xml dump path")
    parser.add_argument("output", type=str, help="json output basename")
    parser.add_argument("batch", type=int, help="number of articles per batch file", default=DEFAULT_BATCH)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    split_xml(Path(args.input), Path(args.output),args.batch)

def split_xml(xml_file: Path, output: Path, batch_size: int = DEFAULT_BATCH) -> None:
    """Split a Mediawiki xml dump into smaller files.
    """
    # Define Namespace to keep: only main articles
    xml_ns = "{http://www.mediawiki.org/xml/export-0.11/}"
    ns = 0

    # Get mediawiki header
    with open(xml_file) as inxml:
        line1 = inxml.readline()
        if not line1.startswith("<mediawiki"):
            raise ValueError("XML is not a Mediawiki dump")
        xml_head = bytes(line1, "utf-8")
    xml_foot = b"</mediawiki>"

    # Prep first batch file
    num_file = 0
    out_file = f"{output}_{num_file}.xml"
    outf = open(out_file, "wb") # pylint: disable=consider-using-with
    outf.write(xml_head)

    # Keep some stats
    num_articles = 0
    num_skipped = 0

    # Parse XML
    context = etree.iterparse(xml_file, events=("start", "end"))
    for event, elem in context:
        _, _, tag = elem.tag.rpartition("}")

        if tag == "page" and event == "end":
            page_ns = int(elem.find(f"{xml_ns}ns").text)
            if page_ns != ns:
                num_skipped += 1
                continue

            num_articles += 1
            if num_articles % batch_size == 0:
                # Close current file
                logging.info(f"{num_articles} articles to {out_file}")
                outf.write(xml_foot)
                outf.close()

                # Prep next file
                num_file += 1
                out_file = f"{output}_{num_file}.xml"
                outf = open(out_file, "wb") # pylint: disable=consider-using-with
                outf.write(xml_head)
            outf.write(etree.tostring(elem))
            elem.clear()

            # Clean up
            for ancestor in elem.xpath("ancestor-or-self::*"):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]
    outf.write(xml_foot)
    outf.close()
    del context

    logging.info(f"{num_articles} pages parsed")
    logging.info(f"{num_articles} pages skipped")


if __name__ == "__main__":
    main()
