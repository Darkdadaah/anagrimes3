#!/usr/bin/env python
"""Get controlled vocabulary from Wiktionary."""

import argparse
import json
import logging
from pathlib import Path
import re
from typing import Any

import requests
from lupa.lua54 import LuaRuntime, lua_type
lua = LuaRuntime(unpack_returned_tuples=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s\t%(message)s')


URL = "https://fr.wiktionary.org/w/index.php?title=Module:section_article/data&action=raw"


def get_raw_data(url: str, user_agent: str, cache_file: Path) -> list[str]:
    """Get raw data from Wiktionary."""
    logger.info("Starting to get raw data.")
    if cache_file.exists():
        logger.info("File exists, reading from it.")
        with cache_file.open("r", encoding="utf-8") as f:
            return f.read()
    else:
        logger.info("Cache file not found, downloading Lua code.")
        headers = {
            "User-Agent": user_agent,
        }
        response = requests.get(url, headers=headers)
        lua_code = response.text
        with cache_file.open("w", encoding="utf-8") as f:
            f.write(lua_code)
        return lua_code


def convert_lua_python_data(lua_code: list[str]) -> list[str]:
    """Convert Lua data to Python data."""
    logger.info("Converting Lua data to Python data.")
    python_code = []
    for line in lua_code:
        if re.match(r"^\s*--", line):
            continue
        if re.match(r"^\s*$", line):
            continue

        # Define variables, symbol "local"
        local = re.match(r"^local (.+) = {", line)
        if local:
            local_name = local.group(1)
            line = local_name + r" = {"

        # Define dict, dict keys in []
        dict_m = re.match(r'^(\s+)\["(.+?)"\] = {', line)
        if dict_m:
            line = dict_m.group(1) + '"{}"' r" = {"
        python_code.append(line)
    return python_code


def unluafy(code: Any) -> Any:
    """Take a Lua code string and eval it to get the local variable it produces."""
    if lua_type(code) == "table":
        code = dict(code)
        for k, v in code.items():
            code[k] = unluafy(v)
        return code
    return code


def process_sections(out_dir: Path, cache_dir: Path, user_agent: str) -> None:
    """Process sections from the Lua code."""
    logger.info("Starting to process sections.")
    cache_file = cache_dir / "./file_sections.lua"
    raw_lua = get_raw_data(URL, user_agent, cache_file)

    # Make lua return a function that returns the data.
    lua_code = "function(L)\n" + raw_lua + "\nend"
    new_data = lua.eval(lua_code)()
    new_data = unluafy(new_data)

    out_file = out_dir / "sections.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    logger.info(f"Data dumped to {out_file}")


def main() -> None:
    """Main entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out_dir", type=Path, required=True, help="Output directory for the sections.json file")
    parser.add_argument("--cache_dir", type=Path, required=True, help="Cache directory for the Lua code downloaded from Wiktionary")
    parser.add_argument("--user_agent", type=str, required=True, help="User agent to download from Wiktionary")
    args = parser.parse_args()
    process_sections(args.out_dir, args.cache_dir, args.user_agent)


if __name__ == "__main__":
    main()
