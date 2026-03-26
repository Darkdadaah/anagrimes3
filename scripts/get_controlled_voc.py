#!/usr/bin/env python
"""Get controlled vocabulary from Wiktionary."""

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
USER_AGENT = "AnagrimesBot/3.0 (https://github.com/Darkdadaah/anagrimes3)"


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


def process_sections(out_dir: Path, cache_dir: Path) -> None:
    """Process sections from the Lua code."""
    logger.info("Starting to process sections.")
    cache_file = cache_dir / "./file_sections.lua"
    raw_lua = get_raw_data(URL, USER_AGENT, cache_file)

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
    out_dir = Path("output/")
    cache_dir = Path("cache/")
    process_sections(out_dir, cache_dir)


if __name__ == "__main__":
    main()
