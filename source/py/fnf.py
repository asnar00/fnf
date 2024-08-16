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

def generateCode(contextName: str, features: List[dict], language: Language) -> SourceFile:
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
                
    # then output a namespace for the context
    language.output_openContext(out, "Context_" + contextName)

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
    log("---------------------------------------------")
    log("generated code:")
    out.show()

def testCodeGeneration():
    sourceFile = SourceFile()
    sourceFile.loadMarkdown("source/fnf/Hello.fnf.ts.md")
    language = Typescript()
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
    testSource = Source(sourceFile, 0, 7)
    outFile = generateCode("mycontext", [result], language)

#---------------------------------------------------------------------------------

def testBackendSetup():
    log_enable()
    log("testBackendSetup")
    backend = Deno()
    backend.setup("build/deno/test")
    pass

#---------------------------------------------------------------------------------
def test():
    #testError()
    #testSourceFile()
    #testParser()
    #testCodeGeneration()
    testBackendSetup()

if __name__ == "__main__":
    clear_console()
    log_enable()
    log("----------------------------------------------")
    log("ᕦ(ツ)ᕤ fnf.py")
    log_disable()
    result = test()
    log_enable()
    log("done.")