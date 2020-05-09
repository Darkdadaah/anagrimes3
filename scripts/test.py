#!/usr/bin/python

import os
from wikt.article import Article

test_file = os.path.join(os.path.dirname(__file__), "../data/coin.txt")
title = "coin"
with open(test_file, "r") as f:
    text = f.read()

a = Article(title, text)
print(a.title)
#print(a.text)
