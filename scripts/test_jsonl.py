#!/usr/bin/python

import os
import json
from wikt.article import Article


test_file = os.path.join(os.path.dirname(__file__), "../data/coin.txt")
title = "coin"
with open(test_file, "r") as f:
    text = f.read()

a = Article(title, text)

# Print to json file
out_file = os.path.join(os.path.dirname(__file__), "../data/coin.jsonl")
print(out_file)

with open(out_file, "w") as outf:
    for word in a.words:
        outf.write(json.dumps(word.struct(), ensure_ascii=False) + "\n")
