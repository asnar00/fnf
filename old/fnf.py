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

# read markdown file, extract code, parse it
def parseFeature(sourceFile: SourceFile, language: Language) -> dict | Error:
    parser = language.feature()
    source = Source(sourceFile)
    result = parser(source)
    return result
    


# given a list of parsed features, return source code for the chosen language/backend
def generateCode(contextName: str, features: List[dict], language: Language, backend: Backend) -> SourceFile:
    out = SourceFile()

    vars = {}  # map name => dict
    structs = {}  # map name => dict
    functions = {}  # map name => List[dict]

    # first put everything together
    for feature in features:
        if err(feature):
            print(feature)
            exit(0)
        for component in feature["components"]:
            component["_feature"] = feature["name"]
            if component["_type"] == "test":
                continue
            name = str(component["name"])
            if component["_type"] == "local":
                vars[name] = component
            elif component["_type"] == "struct":
                if name not in structs:
                    structs[name] = component
                else:
                    structs[name]["properties"].extend(component["properties"])
            elif component["_type"] == "function":
                if name in functions:
                    functions[name].append(component)
                else:
                    functions[name] = [component]

    # deal with async functions
    log_enable()
    asyncFns = findAsyncFunctions(language, functions)
    log_disable()

    # fnf preamble
    out.pushLine("// ᕦ(ツ)ᕤ")
    out.pushLine("// generated by fnf.py")
    out.pushLine("")
    out.pushLine("// ----------------------------------------------------------------")
    out.pushLine("// logging functions")

    # then output the backend preamble
    lines = backend.preamble().split("\n")
    for line in lines:
        out.pushLine(line)
    out.pushLine("")
    out.pushLine("// ----------------------------------------------------------------")
    out.pushLine("// context")
    out.pushLine("")

    # then output a namespace for the context
    language.output_openContext(out, contextName)

    log_disable()
    log("structs:")
    for name, struct in structs.items():
        log(f"  {name}: {struct}")
        language.output_struct(out, struct)

    log("\nvars:")
    for name, var in vars.items():
        log(f"  {name}: {var}")
        language.output_variable(out, var)

    log("\nfunctions:")
    for name, functionList in functions.items():
        log(f"  {name}: {functionList}")
        language.output_function(out, name, functionList, asyncFns)

    language.output_tests(out, features, asyncFns)

    language.output_closeContext(out)

    out.pushLine("")
    out.pushLine("// ----------------------------------------------------------------")
    out.pushLine("// entry point")

    # finally output the backend postamble
    lines = backend.postamble(contextName).split("\n")
    for line in lines:
        out.pushLine(line)
    return out

# return dictionary mapping function names => async/non-async; mark sub-functions async if they call async functions
def findAsyncFunctions(language: Language, functions: dict) -> dict:
    log("findAsyncFunctions ----------------------------")
    asyncFunctions = {}
    # 1 - find all leaf async functions
    for name, functionList in functions.items():
        for function in functionList:
            if language.is_function_async(function):
                asyncFunctions[name] = True
                function["_async"] = True
                log(f"async: {name}_{function["_feature"]}")
                break
    log("-----------")
    # 2 - a function is async if it contains an "on" subfunction in >=2nd position
    for name, functionList in functions.items():
        for i in range(1, len(functionList)):
            if functionList[i]["modifier"] == "on":
                asyncFunctions[name] = True
                functionList[i]["_async"] = True
                log(f"async: {name}_{functionList[i]["_feature"]}")
                break
    # 3 - a function is async if it calls an async function
    done = False
    safeCount = 10000
    while (not done):
        foundAsyncFunction = False
        safeCount -= 1
        if safeCount <= 0:
            log("handleAsyncFunctions: too many iterations")
            break
        for name, functionList in functions.items():
            if name in asyncFunctions:
                continue
            for fn in functionList:
                body = str(fn["body"])
                # match any alphanumeric word followed by an open paren
                matches = re.findall(r'\b\w+\(', body)
                for match in matches:
                    callee = match[:-1]
                    if callee in asyncFunctions:
                        asyncFunctions[name] = True
                        fn["_async"] = True
                        foundAsyncFunction = True
                        log(f"async caller: {name}_{fn["_feature"]} calls {callee}")
                        break
        if not foundAsyncFunction:
            done = True
    log("async functions:")
    for name in asyncFunctions:
        log(f"  {name}")
    log("---------------------------------------------")
    return asyncFunctions

def testCodeGeneration():
    sourceFile = SourceFile("source/fnf/Hello.fnf.ts.md")
    language = Typescript()
    backend = Deno()
    feature = parseFeature(sourceFile, language)
    log_enable()
    log("result:", feature)
    if err(feature):
        return
    log("---------------------------------------------")
    outFile = generateCode("mycontext", [feature], language, backend)
    log("---------------------------------------------")
    log("generated code:")
    outFile.show()
    writeTextFile("build/deno/test/main.ts", outFile.code)

#---------------------------------------------------------------------------------

def remove_ansi_sequences(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def processLog(output: str, outFile: SourceFile) -> str:
    output = remove_ansi_sequences(output)
    starts = outFile.lineStarts()
    def map_function(file, line, char):
        iChar = starts[int(line)-1]
        location = outFile.sourceLocation(iChar)
        if location == None:
            return f"file://{file}:{line}:{char}"
        return str(location)
    def replace_callback(match):
        file, line, char = match.groups()
        return map_function(file, line, char)
    # Assuming 'content' contains your file contents
    pattern = r'file://([^:]+):(\d+):(\d+)'
    new_output = re.sub(pattern, replace_callback, output)
    return new_output

def testBackend():
    sourceFile = SourceFile("source/fnf/Hello.fnf.ts.md")
    language = Typescript()
    backend = Deno()
    feature = parseFeature(sourceFile, language)
    if err(feature): 
        log_enable()
        log(feature)
        return
    outFile = generateCode("mycontext", [feature], language, backend)
    writeTextFile("build/deno/test/main.ts", outFile.code)
    backend = Deno()
    #backend.ensure_latest_version()
    #backend.setup("build/deno/test")
    log_enable()
    log("testBackend")
    log("running main.ts")
    processFn = lambda line: processLog(line, outFile)
    output = backend.run(processFn, "build/deno/test/main.ts", ["-test"])
    log("output after processing: ----------------------")
    log(output)
    log("-----------------------------------------------")
    
def testBuildContext():
    log_enable()
    log("testBuildContext")
    language = Typescript()
    backend = Deno()
    ext = ".fnf.ts.md"
    files = scanFolder("source/fnf", ext)
    sourceFiles = [SourceFile(file) for file in files]
    log_disable()
    features = [parseFeature(s, language) for s in sourceFiles]
    log("features:")
    for feature in features:
        log("-------------------")
        log(feature)
    log_enable()
    log("------------------------------------------------------")
    
    outFile = generateCode("mycontext", features, language, backend)
    outFile.show()
    log("------------------------------------------------------")
    writeTextFile("build/deno/test/main.ts", outFile.code)
    log_enable()
    processFn = lambda line: processLog(line, outFile)
    output = backend.run(processFn, "build/deno/test/main.ts", ["-test"])
    


#---------------------------------------------------------------------------------
def test():
    #testError()
    #testSourceFile()
    #testParser()
    #testCodeGeneration()
    #testBackend()
    testBuildContext()
    #testFns()

if __name__ == "__main__":
    clear_console()
    log_enable()
    log("----------------------------------------------")
    log("ᕦ(ツ)ᕤ fnf.py")
    log_disable()
    result = test()
    log_enable()
    log("done.")