ᕦ(ツ)ᕤ
# fnf

`fnf` stands for "feature normal form" : an experimental way of representing code written in any (or many) languages.

`fnf` is :

- *feature-modular* : code is organised as a tree of feature clauses, each of which adds detail to its parent. Feature clauses define and extend variables, types, and functions.

- *literate* : code is expressed as a human-readable markdown file (`.fnf.**.md`) with code snippets appearing within blocks of text, similar to a blog post.

- *contextual* : a feature source file contains contextual information such as specification, explanation, documentation, pseudocode, and tests, as well as the code; all next to each other, rather in separate artefacts.

Because fnf combines precision with context, fnf code should be easier to understand, particularly by laypeople and beginners. Not uncoincidentally, it should also be easier for LLMs to understand, potentially enabling a large range of LLM-based code transformations. These are discussed at the end of this readme.

## fnf.py

`fnf.py` is a python script that chews up a folder containing features (expressed as `.fnf.**.md` files) and spits out monolithic code in the target language(s) and platform(s). It then builds the code, runs tests, scrapes up the console output and remaps the source file/line pairs to the original .md files.

I'm choosing python as the implementation language for fnf because it's got the lowest setup friction.

The target languages/backends for the first round will be typescript/deno, followed by python/flask, and then cpp. The architecture is modular, so you can add your own languages and backends as you wish by adding files to the `source/py/languages` and `source/py/backends` folders. 

## fnf syntax

An fnf file is identified by the extension `.fnf.<lang>.md`, where `lang` is the language we're writing the code in. For instance, `Hello.fnf.ts.md` is feature-normal form typescript, with a .md extension so you can edit it in a markdown editor.

The demonstration file [Hello.fnf.ts.md](source/fnf/Hello.fnf.ts.md) contains a good rundown of the syntax.

## LLM-based code transformation

Here is a short list of tasks that we expect to be enabled by fnf code combined with LLMs and agents:

    - generation of fnf code from patch sequences / pull requests
    - generation of tests, documentation and other contextual information from code
    - generation of code from contextual information
    - translation of code between languages (including pseudocode)
    - translation of contextual information between languages
    - mangement of polyglot projects - write in whatever you like, deploy anywhere/how
    - translation of projects between different platforms and SDKs

