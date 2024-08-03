ᕦ(ツ)ᕤ
# fnf

`fnf` stands for "feature normal form" : an experimental way of representing code written in any (or many) languages.

`fnf` is :

- *feature-modular* : code is organised as a tree of feature clauses, each of which adds detail to its parent. Feature clauses define and extend variables, types, and functions.

- *literate* : code is expressed as a human-readable markdown file (.fnf.md) with code snippets appearing within blocks of text.

- *contextual* : a feature source file contains contextual information such as specification, explanation, documentation, and tests, as well as the code.

## fnf utility

`fnf.py` is a python script that chews up a folder containing features (expressed as .fnf.md files) and spits out monolithic code in the target language.

I'm choosing python as the implementation language for fnf because it's got the lowest friction when it comes to setting it up.

However, the first target language I'm choosing is typescript (deno on the server side) because it's currently the cleanest option for web programming.