"""Tools to parse a Mediawiki XML dump into individual page elements."""

from pathlib import Path
from typing import Generator

from lxml import etree


# Only return pages from the Main namespace by default
_ALLOWED_NS = (0,)
_XML_NS = "{http://www.mediawiki.org/xml/export-0.11/}ns"
def get_pages(xml_file: Path, allowed_ns: tuple[int] = _ALLOWED_NS) -> Generator[etree.Element, None, None]:
    """Generator for mediawiki XML pages from an XML dump.

    This function parses a Mediawiki XML dump and yields individual page elements
    that belong to the specified namespaces. By default, it only returns pages from
    the Main namespace (namespace ID 0).

    Parameters:
        xml_file (Path): The path to the Mediawiki XML dump file.
        allowed_ns (tuple[int]): A tuple of namespace IDs to include in the output.

    Yields:
        etree.Element: An XML element representing a Mediawiki page.
    """

    # Parse XML
    context = etree.iterparse(xml_file, events=("start", "end"))
    for event, elem in context:
        _, _, tag = elem.tag.rpartition("}")

        if tag == "page" and event == "end":
            page_ns = int(elem.find(_XML_NS).text)
            if page_ns not in allowed_ns:
                continue
            yield elem

            # Clean up memory
            for ancestor in elem.xpath("ancestor-or-self::*"):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]
            elem.clear()
    del context
