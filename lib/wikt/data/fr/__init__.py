"""Dicts of template names to standardize names."""

from importlib.resources import files
import json


__all__ = ["word_types", "word_attributes", "word_subsections"]

# Load word types
with open(files("wikt.data.fr") / "word_types.json", "r", encoding="utf-8") as f:
    word_types_raw = json.load(f)
word_types = {al: w["abrev"] for wname, w in word_types_raw.items() for al in [*w["alias"], wname]}

# Load word sections
with open(files("wikt.data.fr") / "sections.json", "r", encoding="utf-8") as f:
    sections_raw = json.load(f)
word_subsections = {al: wname for wname, w in sections_raw.items() for al in [*w["alias"], wname]}

# # https://fr.wiktionary.org/wiki/Module:section_article/data
# # TODO: generate this page automatically
# word_subsections = {
#     "composés",
#     "compos",
#     "anciennes orthographes",
#     "anagrammes",
#     "prononciation",
#     "dico sinogrammes",
#     "étymologie",
#     "dérivés",
#     "références",
#     "synonymes",
#     "variantes",
#     "vocabulaire",
#     "voir aussi",
#     "voir",
#     "écriture",
#     "notes",
# }

word_attributes = {
    "m": "m",
    "masculin": "m",
    "f": "f",
    "féminin": "f",
    "c": "c",
    "fplur": "fplur",
    "fsing": "fsing",
    "fm?": "fm?",
    "fm ?": "fm?",
    "genre": "genre",
    "mf": "mf",
    "masculin et féminin": "mf",
    "mf?": "mf?",
    "mf ?": "mf?",
    "mn ?": "mn?",
    "mplur": "mplur",
    "msing": "msing",
    "n": "n",
    "nplur": "nplur",
    "nsinig": "nsinig",
    "i": "i",
    "intransitif": "i",
    "t": "t",
    "transitif": "t",
}
