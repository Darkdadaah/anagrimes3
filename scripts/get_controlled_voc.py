#!/usr/bin/env python
"""Get controlled vocabulary from Wiktionary."""

import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s\t%(message)s')


sec_file = Path("./file_sections.txt")
url = "https://fr.wiktionary.org/w/index.php?title=Module:section_article/data&action=raw"
user_agent = "AnagrimesBot/3.0 (https://github.com/Darkdadaah/anagrimes3)"


def get_raw_data() -> list[str]:
    """Get raw data from Wiktionary."""
    logger.info("Starting to get raw data.")
    if sec_file.exists():
        logger.info("File exists, reading from it.")
        with sec_file.open("r") as f:
            return f.read().splitlines()
    else:
        logger.info("Cache file not found, downloading Lua code.")
        headers = {
            "User-Agent": user_agent,
        }
        response = requests.get(url, headers=headers)
        lua_code = response.text
        with sec_file.open("w") as f:
            f.write(lua_code)
        return lua_code.splitlines()


def process_sections():
    """Process sections from the Lua code."""
    logger.info("Starting to process sections.")
    raw_lua = get_raw_data()
    print(raw_lua[0:10])


if __name__ == "__main__":
    process_sections()
