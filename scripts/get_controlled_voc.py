#!/usr/bin/env python
"""Get controlled vocabulary from Wiktionary."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import requests
from lupa.lua54 import LuaRuntime, lua_type

lua = LuaRuntime(unpack_returned_tuples=True)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(message)s")


URL = "https://fr.wiktionary.org/w/index.php?title=Module:section_article/data&action=raw"


def get_raw_data(url: str, user_agent: str, cache_file: Path | None) -> list[str]:
    """Get raw data from a given page."""

    if cache_file and cache_file.exists():
        logger.info(f"Get data cached in {cache_file}")
        with cache_file.open("r", encoding="utf-8") as f:
            return f.read()

    logger.info(f"Downloading raw code from {url}")
    headers = {
        "User-Agent": user_agent,
    }
    response = requests.get(url, headers=headers)

    # Write it out to cache
    if cache_file:
        raw_code = response.text
        logging.info(f"Cache data in {cache_file}")
        with cache_file.open("w", encoding="utf-8") as f:
            f.write(raw_code)
    return raw_code


def unluafy(code: Any) -> Any:
    """Take a Lua code and change into pure Python (table = dict or list)."""
    if lua_type(code) == "table":
        code = dict(code)
        for k, v in code.items():
            code[k] = unluafy(v)
        return code
    return code


def process_data(out_dir: Path, cache_dir: Path, user_agent: str, url: str, name: str) -> None:
    """Process sections from the Lua code."""
    raw_lua = get_raw_data(url, user_agent, cache_dir / f"{name}.lua")

    # Make lua return a function that returns the data.
    lua_code = "function(L)\n" + raw_lua + "\nend"
    new_data = lua.eval(lua_code)()
    new_data = unluafy(new_data)

    out_file = out_dir / f"{name}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    logger.info(f"Data for '{name}' dumped in {out_file}")


def main() -> None:
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out_dir", type=Path, required=True, help="Output directory for the json files")
    parser.add_argument(
        "--cache_dir", type=Path, help="Cache directory for the Lua code downloaded from Wiktionary"
    )
    parser.add_argument(
        "--user_agent", type=str, required=True, help="User agent to download from Wiktionary"
    )
    args = parser.parse_args()

    urls = [
        ("sections", "https://fr.wiktionary.org/w/index.php?title=Module:section_article/data&action=raw")
    ]

    for name, url in urls:
        logging.info(f"Process data for '{name}'")
        process_data(args.out_dir, args.cache_dir, args.user_agent, url, name)


if __name__ == "__main__":
    main()
