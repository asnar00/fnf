# ᕦ(ツ)ᕤ
# fnf.py
# author: asnaroo
# processes .fnf.*.md files => .* files
# initially supporting ts, py, cpp
# to auto-rerun this when this file or source mds change, use
# (find source/fnf source/py -type f | entr -r python3 source/py/fnf.py)

#---------------------------------------------------------------------------------
# import mechanics

import sys
from pathlib import Path

# Add the py directory to the Python path
py_root = Path(__file__).resolve().parent
sys.path.append(str(py_root))

#---------------------------------------------------------------------------------
# batteries

import os
import re
import json
from typing import List
from typing import Tuple

#---------------------------------------------------------------------------------
# local imports

from util import *
from languages import Language, Typescript
from backends import Backend, Deno

#---------------------------------------------------------------------------------

def testSourceFile():
    log_enable()
    log("testExtractSource")
    sourceFile = SourceFile("source/fnf/Hello.fnf.ts.md")
    sourceFile.show()

#---------------------------------------------------------------------------------

def testError():
    log_enable()
    log("testError")
    sourceFile = SourceFile("source/fnf/Hello.fnf.ts.md")
    sourceFile.show()
    source = Source(sourceFile)
    source.set(50)
    error = Error("test error", source)
    log(error)

#---------------------------------------------------------------------------------

def testParser():
    sourceFile = SourceFile("source/fnf/Hello.fnf.ts.md")
    log_enable()
    log("testParser")
    log("source: ------------------------------------")
    sourceFile.show()
    log("---------------------------------------------")
    log_disable()
    result = sourceFile.parse()
    log_enable()
    log("result:", result)

#---------------------------------------------------------------------------------
# code generation

def generateCode(contextName: str, features: List[dict], language: Language, backend: Backend) -> SourceFile:
    out = SourceFile()
    vars = {}   # map name => dict
    structs = {}  # map name => dict
    functions = {}  # map name => List[dict]

    # first put everything together
    for feature in features:
        for component in feature["components"]:
            component["_feature"] = feature["name"]
            if component["_type"] == "test":
                continue
            name = component["name"]
            if component["_type"] == "local":
                vars[name] = component
            elif component["_type"] == "struct":
                if not name in structs:
                    structs[name] = component
                else:
                    structs[name].properties.extend(component.properties)
            elif component["_type"] == "function":
                if not name in functions:
                    functions[name] = [component]
                else:
                    functions[name].append(component)

    # fnf preamble
    out.pushLine("// ᕦ(ツ)ᕤ")
    out.pushLine("// generated by fnf.py")
    out.pushLine("// ----------------------------------------------------------------")

    # then output the backend preamble
    lines = backend.preamble().split("\n")
    for line in lines:
        out.pushLine(line)
    out.pushLine("")
    out.pushLine("// ----------------------------------------------------------------")
    out.pushLine("")
    # then output a namespace for the context
    language.output_openContext(out, contextName)

    log("structs:")
    for name, struct in structs.items():
        print(f"  {name}: {struct}")
        language.output_struct(out, struct)

    log("\nvars:")
    for name, var in vars.items():
        print(f"  {name}: {var}")
        language.output_variable(out, var)

    log("\nfunctions:")
    for name, fnList in functions.items():
        print(f"  {name}: {fnList}\n")
        language.output_function(out, name, fnList)

    language.output_tests(out, features)

    language.output_closeContext(out)

    out.pushLine("")
    out.pushLine("// ----------------------------------------------------------------")

    # finally output the backend postamble
    lines = backend.postamble(contextName).split("\n")
    for line in lines:
        out.pushLine(line)
    return out

def testCodeGeneration():
    sourceFile = SourceFile()
    sourceFile.loadMarkdown("source/fnf/Hello.fnf.ts.md")
    language = Typescript()
    backend = Deno()
    log_enable()
    log("testCodeGeneration")
    log("source: ------------------------------------")
    sourceFile.show()
    log("---------------------------------------------")
    log_disable()
    source = Source(sourceFile)
    parser = Typescript().feature()
    result = parser(source)
    result["_mdFile"] = sourceFile.mdFile
    log_enable()
    log("result:", result)
    if err(result):
        return
    log("---------------------------------------------")
    outFile = generateCode("mycontext", [result], language, backend)
    log("---------------------------------------------")
    log("generated code:")
    outFile.show()
    writeTextFile("build/deno/test/main.ts", outFile.code)

#---------------------------------------------------------------------------------

def testBackend():
    log_enable()
    log("testBackend")
    backend = Deno()
    #backend.ensure_latest_version()
    #backend.setup("build/deno/test")
    log("running main.ts")
    output = backend.run("build/deno/test/main.ts")
    log("---------------------------------------------")
    log(output)
    log("---------------------------------------------")
    pass

#---------------------------------------------------------------------------------
def test():
    #testError()
    #testSourceFile()
    #testParser()
    testCodeGeneration()
    #testBackend()

if __name__ == "__main__":
    clear_console()
    log_enable()
    log("----------------------------------------------")
    log("ᕦ(ツ)ᕤ fnf.py")
    log_disable()
    result = test()
    log_enable()
    log("done.")