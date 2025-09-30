"""Parse a Wiktionnaire xml dump into a jsonl format."""

import argparse
from lxml import etree


def main():
    """main entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, help="xml dump path")
    parser.add_argument("output", type=str, help="json output basename")
    parser.add_argument("batch", type=int, help="number of articles per batch file", default=10000)
    args = parser.parse_args()
    # logging.basicConfig(level=args.loglevel)

    xml_file = args.input
    output = args.output
    batch_size = args.batch

    xml_ns = "{http://www.mediawiki.org/xml/export-0.11/}"
    ns = 0

    # Get mediawiki header
    with open(xml_file) as inxml:
        line1 = inxml.readline()
        if not line1.startswith("<mediawiki"):
            raise Exception("XML doesn't appears to be a Mediawiki dump.")
        xml_head = bytes(line1, "utf-8")
    xml_foot = b"</mediawiki>"

    # Print to json file
    num_file = 0
    out_file = f"{output}_{num_file}.xml"
    outf = open(out_file, "wb")
    outf.write(xml_head)

    num = 0
    skipped = 0
    context = etree.iterparse(xml_file, events=("start", "end"))
    for event, elem in context:
        _, _, tag = elem.tag.rpartition("}")

        if tag == "page" and event == "end":
            page_ns = int(elem.find(xml_ns + "ns").text)
            if page_ns != ns:
                skipped += 1
                continue

            num += 1
            if num % batch_size == 0:
                print(f"{num} articles to {out_file}")
                outf.write(xml_foot)
                outf.close()
                num_file += 1
                out_file = f"{output}_{num_file}.xml"
                outf = open(out_file, "wb")
                outf.write(xml_head)
            outf.write(etree.tostring(elem))
            elem.clear()

            for ancestor in elem.xpath("ancestor-or-self::*"):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]

    del context
    outf.write(xml_foot)
    outf.close()
    print(f"{num} pages parsed")
    print(f"{num} pages skipped")


if __name__ == "__main__":
    main()
