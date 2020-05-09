#!/usr/bin/python

import os
import json
from wikt.article import Article


test_file = os.path.join(os.path.dirname(__file__), "../data/coin.txt")
title = "coin"
with open(test_file, "r") as f:
    text = f.read()

a = Article(title, text)
print(a.title)

print(a)
for word in a.words:
    print(word)

# Print to json file
out_file = os.path.join(os.path.dirname(__file__), "../data/coin.json")

struct = [w.struct() for w in a.words]
with open(out_file, "w") as outf:
     outf.write(json.dumps(struct, indent=4, ensure_ascii=False))
