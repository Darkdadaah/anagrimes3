#!/usr/bin/python

import os
from wikt.parser import Parser

test_file = os.path.join(os.path.dirname(__file__), "../data/coin.txt")
title = "coin"
with open(test_file, "r") as f:
    text = f.read()

p = Parser(title, text)
print(p.title)
print(p.text)
