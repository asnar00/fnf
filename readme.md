ᕦ(ツ)ᕤ
# fnf

`fnf` stands for "feature normal form" : an experimental way of representing code written in any (or many) languages.

`fnf` is :

- *feature-modular* : code is organised as a tree of feature clauses, each of which adds detail to its parent. Feature clauses define and extend variables, types, and functions.

- *literate* : code is expressed as a human-readable markdown file (.fnf.md) with code snippets appearing within blocks of text.

- *contextual* : a feature source file contains contextual information such as specification, explanation, documentation, and tests, as well as the code; all next to each other, rather in separate artefacts.

## fnf.py

`fnf.py` is a python script that chews up a folder containing features (expressed as .fnf.**.md files) and spits out monolithic code in the target language(s).

I'm choosing python as the implementation language for fnf because it's got the lowest setup friction.

The target languages for the first round will be typescript/deno (treated as separate targets), python, and c++. This ensures we end up with the flexibility to generate other languages as well.

## fnf syntax

An fnf file is identified by the extension `.fnf.<lang>.md`, where `lang` is the language we're writing the code in. For instance, `Hello.fnf.ts.md` is feature-normal form typescript, with a .md extension so you can edit it in a markdown editor.

The demonstration file `Hello.fnf.ts.md` contains a good rundown of the syntax.



