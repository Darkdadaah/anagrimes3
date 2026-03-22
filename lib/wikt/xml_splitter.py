"""Parse a Wiktionnaire xml dump into a jsonl format."""

from io import FileIO
import logging
from pathlib import Path
from typing import Generator

import argparse
from lxml import etree

from .xml import get_pages


DEFAULT_BATCH = 10_000
MAX_BATCH_FILES = 100_000


def batch_file_writer(xml_file: Path, output_dir: Path, file_name: str) -> Generator[FileIO, None, None]:
    """Yield file objects for writing batches of data.

    Adds the mediawiki header and footer to each file.
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    if not output_dir.is_dir():
        raise FileNotFoundError(f"Output directory {output_dir} does not exist")

    # Get mediawiki header
    with open(xml_file) as inxml:
        line1 = inxml.readline()
        if not line1.startswith("<mediawiki"):
            raise ValueError("XML is not a Mediawiki dump")
        xml_head = bytes(line1, "utf-8")
    xml_foot = b"</mediawiki>"

    # Yield every file we can
    num_file = 0
    while num_file < MAX_BATCH_FILES:
        num_file += 1
        out_file = output_dir / f"{file_name}_{num_file:06d}.xml"
        with out_file.open("wb") as outf:
            outf.write(xml_head)
            yield outf
            outf.write(xml_foot)


def split_xml(xml_file: Path, output_dir: Path, file_name: str, batch_size: int = DEFAULT_BATCH) -> None:
    """Split a Mediawiki xml dump into smaller files."""

    num_articles = 0
    files_gen = batch_file_writer(xml_file, output_dir, file_name)
    for elem in get_pages(xml_file):
        # Get a new file for a new batch
        if num_articles % batch_size == 0:
            outf = next(files_gen)
            logging.info(f"{num_articles} articles to {outf.name}")
        outf.write(etree.tostring(elem))
        num_articles += 1

    logging.info(f"{num_articles} pages parsed")


def main():
    """main entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, help="xml dump path")
    parser.add_argument("output_dir", type=Path, help="output directory for the files generated")
    parser.add_argument("file_name", type=str, help="name of the files generated")
    parser.add_argument(
        "batch",
        type=int,
        help=f"number of articles per batch file (default: {DEFAULT_BATCH})",
        default=DEFAULT_BATCH,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    split_xml(Path(args.input), Path(args.output_dir), args.file_name, args.batch)


if __name__ == "__main__":
    main()
