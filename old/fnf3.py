# ᕦ(ツ)ᕤ
# fnf.py
# author: asnaroo
# processes .fnf.*.md files => .* files
# initially supporting ts, py, cpp

import os
import re
from typing import List
from typing import Tuple

#---------------------------------------------------------------------------------
# switch-on-and-offable logging

global log_enabled
log_enabled: bool = False

def log_enable():
    global log_enabled
    log_enabled = True

def log_disable():
    global log_enabled
    log_enabled = False

def log(*args):
    if log_enabled:
        print(*args)

#---------------------------------------------------------------------------------
# human-readable regexps

# represents a regular expression term
class RegTerm:
    def __init__(self, desc: str):
        iBracket = desc.find("(")
        if iBracket >= 0 and not (desc[iBracket-1] == "'" and desc[iBracket+1] == "'"):
            jBracket = desc.find(")")
            orList = desc[iBracket+1:jBracket].split(" or ")
            desc = desc[:iBracket] + desc[jBracket+1:]
        else:
            orList = []
        optional = False
        if desc.startswith("optional "):
            optional = True
            desc = desc[9:]
        wordList = desc.split(" ")
        self.orList = orList
        self.optional = optional
        self.wordList = wordList

# take a human-readable list of strings and convert it to a regex
def regMatch(descriptor: List[str], text: str) -> List[dict]:
    log_enable()
    log("regMatch", descriptor)
    regTerms = [RegTerm(desc) for desc in descriptor]
    fullRegex = ""
    members = []
    wordPattern = r'\b[a-zA-Z]\w*'
    numberPattern = r'\b\d+(?:\.\d+)?'
    stringPattern = r'"[^"]*"|\'[^\']*\''
    combinedPattern = fr'({numberPattern}|{wordPattern}|{stringPattern})'
    endPattern = r'[^;\r]+'  # match anything except semicolon, or newline
    endBracketPattern = r'[^\)]*'  # match anything except closing bracket
    patterns = { "word": wordPattern, "number": numberPattern, "string": stringPattern, "any": combinedPattern, "toEnd": endPattern, "toEndBracket": endBracketPattern }
    for parsedTerm in regTerms:
        regex = ""
        for i, word in enumerate(parsedTerm.wordList):
            if word.startswith("'") and word.endswith("'"):
                log("word:", word)
                word = word[1:-1]
                log("literal", word)
                escaped = re.escape(word)
                log("escaped", escaped)
                regex += escaped                        # match specific word, discard
            else:
                members.append(word)                           # word is name of class member to write
                if i == len(parsedTerm.wordList)-1:
                    if len(parsedTerm.orList) > 1:  # it's an "or" list
                        regex += "(" + r'|'.join(re.escape(s[1:-1])+r'\s+' for s in parsedTerm.orList) + ")"   # match option-list, capture
                    elif len(parsedTerm.orList) ==1: # it's specifying which regex to use!
                        log("using pattern", parsedTerm.orList[0], "for", word)
                        regex += r'(' + patterns[parsedTerm.orList[0]] + r')' # match specific pattern, capture
                    else: # use the most general pattern
                        regex += combinedPattern
            if i < len(parsedTerm.wordList) - 1:
                regex += r'\s+'                                     # match whitespace
        if parsedTerm.optional:
            if regex.startswith("(") and regex.endswith(")"):
                regex = regex + r'?'                          # make the whole term optional
            else:
                regex = r'(?:' + regex + r')?'                # make the whole term optional, but without capturing extra stuff
        log("    =>", regex)
        fullRegex += regex
        fullRegex += r'\s*'                                 # match whitespace
    log("fullRegex:", fullRegex)
    log("members:", members)
    pattern = re.compile(fullRegex)
    matches = pattern.finditer(text)
    results = []
    for match in matches:
        result = {}
        # get start and end character indices
        result["_start"] = match.start(0)
        result["_end"] = match.end(0)
        for i, member in enumerate(members):
            result[member] = match.group(i+1)
        results.append(result)
    log_enable()
    return results

def regPrintSingle(parsedTerm: RegTerm, data: dict) -> str:
    termString = ""
    for i, word in enumerate(parsedTerm.wordList):
        if word.startswith("'") and word.endswith("'"):
            word = word[1:-1]
            termString += word
        else:
            if word in data and data[word] != None:
                termString += data[word]
            else:
                return ""
        if i < len(parsedTerm.wordList) - 1:
            termString += " "
    return termString

def regPrint(descriptor: List[str], data: dict) -> str:
    regTerms = [RegTerm(desc) for desc in descriptor]
    fullString = ""
    for parsedTerm in regTerms:
        termString = regPrintSingle(parsedTerm, data)
        if termString != "":
            fullString += termString + " "
    return fullString

def testRegex():
    var = ["optional modifier('var' or 'const')", 
           "name(word)",
           "optional ':' type(word)",
           "optional '=' value(any)"]
    text = "var x: int = 5"
    match = regMatch(var, text)
    print(match)
    print(regPrint(var, match[0]))
    text = "const y: string"
    match = regMatch(var, text)
    print(match)
    print(regPrint(var, match[0]))

#---------------------------------------------------------------------------------
# file operations

def readTextFile(path: str) -> str:
    with open(path, "r") as file:
        return file.read()
    
def writeTextFile(path: str, text: str):
    # ensure directories exist:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        file.write(text)

#---------------------------------------------------------------------------------
# extracts code, with each line starting with a source line number

def annotatedLine(text: str, lineNumber: str)->str:
    return f"{lineNumber:4d}_ {text}"

def extractCode(text) -> str:
    log("extractCode")
    out = ""
    lines = text.split("\n")
    inCodeBlock = False
    for i, line in enumerate(lines):
        if not inCodeBlock:
            if line.startswith("    "):
                codeLine = line[4:].rstrip()
                out += annotatedLine(codeLine, i+1) + "\n"
            else:
                if line.startswith("```"):
                    inCodeBlock = True
        else:
            if line.startswith("```"):
                inCodeBlock = False
            else:
                codeLine = line.rstrip()
                out += annotatedLine(codeLine, i+1) + "\n"
    log(out)
    return out

def testExtractCode():
    text = readTextFile("source/fnf/Hello.fnf.ts.md")
    code = extractCode(text)
    print(code)

#---------------------------------------------------------------------------------
# multi-language support: minimal, human-readable language syntax definitions
# support typescript, python(soon), cpp(soon)

class Language:
    def __init__(self, name: str, extension: str):
        self.name = name
        self.extension = extension

    def comment_format(self): pass
    def indent_format(self): pass
    def feature_format(self): pass
    def variable_format(self): pass
    def struct_format(self): pass
    def function_format(self): pass
    
class Typescript(Language):
    def __init__(self):
        super().__init__("typescript", "ts")

    def comment_format(self):
        return "//"
    
    def indent_format(self):
        return "{"
    
    def feature_format(self):
        return ["'feature'", "name(word)", "optional 'extends' parent(word)"]

    def variable_format(self):
        return ["optional modifier('var' or 'const')",
                "name(word)",
                "optional ':' type(word)",
                "optional '=' value(toEnd)"]
    
    def struct_format(self):
        return ["modifier('struct' or 'extend')", "name(word)"]
    
    def function_format(self):
        return ["modifier('def' or 'replace' or 'on' or 'before' or 'after')", 
                "name(word)", 
                "'('", "params(toEndBracket)", "')'", 
                "optional ':' type(word)"]

#---------------------------------------------------------------------------------

def testTypescriptFormats():
    lang = Typescript()
    feature = "feature Hello extends Feature {"
    log_enable()
    log("FEATURE:", feature)
    match = regMatch(lang.feature_format(), feature)
    log("matched:", match)
    log("formatted:", regPrint(lang.feature_format(), match[0]))
    variable = "var my_colour : Colour = new Colour(1, 2, 3);"
    log("VARIABLE:", variable)
    match = regMatch(lang.variable_format(), variable)
    log("matched:", match)
    log("formatted:", regPrint(lang.variable_format(), match[0]))
    struct = "struct Point {"
    log("STRUCT:", struct)
    match = regMatch(lang.struct_format(), struct)
    log("matched:", match)
    log("formatted:", regPrint(lang.struct_format(), match[0]))
    function = "def add(x: number, y: number): number {"
    log("FUNCTION:", function)
    match = regMatch(lang.function_format(), function)
    log("matched:", match)
    log("formatted:", regPrint(lang.function_format(), match[0]))
            
#---------------------------------------------------------------------------------
# so next: read in a feature, extract blocks for vars/structs/functions/tests, parse.

# given code and position of first "{" find the position of the matching "}"
def findNextBlock(code: str, pos: int, bracket: str):
    log("findEndOfBlock", pos, bracket)
    open = "[({"  # open brackets
    closed = "])}" # closed brackets
    index = open.find(bracket)
    if index < 0: return -1, -1
    close = closed[index]
    i = code.find(bracket, pos)
    if i < 0: return [-1, -1]
    depth = 1
    for j in range(i+1, len(code)):
        if code[j] == bracket:
            depth += 1
        elif code[j] == close:
            depth -= 1
        if depth == 0:
            return i, (j+1)
    return i, len(code)

def testFindEndOfBlock():
    log_enable()
    lang = Typescript()
    md = readTextFile("source/fnf/Hello.fnf.ts.md")
    code = extractCode(md)
    log(code)
    i, j = findNextBlock(code, 0, "{")
    log(code[i:j])

def startOfLine(code: str, pos: int) -> int:
    while pos > 0 and code[pos] != "\n":
        pos -= 1
    return pos if pos==0 else pos+1

def findFeature(code: str, lang: Language):
    log("findFeature")
    matches = regMatch(lang.feature_format(), code)
    if len(matches) == 1:
        i = startOfLine(code, matches[0]["_start"])
        j = matches[0]["_end"]
        sig = code[i:j]
        bodyStart, bodyEnd = findNextBlock(code, matches[0]["_end"], "{")
        matches[0]["_lineStart"] = i
        matches[0]["_end"] = bodyEnd
        return { "match": matches[0], "signature": sig, "body": code[bodyStart:bodyEnd] }
    log("matches:", matches)
    return None

def findVariables(code: str, lang: Language):
    log("findVariables")
    variables = []
    matches = regMatch(lang.variable_format(), code)
    for match in matches:
        i = startOfLine(code, match["_start"])
        j = match["_end"]
        match["_lineStart"] = i
        sig = code[i:j]
        variables.append({ "match": match, "signature": sig })
    return variables

def findStructs(code: str, lang: Language):
    log("findStructs")
    structs = []
    matches = regMatch(lang.struct_format(), code)
    for match in matches:
        i = startOfLine(code, match["_start"])
        j = match["_end"]
        sig = code[i:j]
        bodyStart, bodyEnd = findNextBlock(code, match["_end"], "{")
        match["_lineStart"] = i
        match["_end"] = bodyEnd
        structs.append({ "match": match, "signature": sig, "body": code[bodyStart:bodyEnd] })
    for struct in structs:
        body = (struct["body"])
        variables = findVariables(body, lang)
        struct["variables"] = variables
    return structs

def findFunctions(code: str, lang: Language):
    log("findFunctions")
    functions = []
    matches = regMatch(lang.function_format(), code)
    for match in matches:
        i = startOfLine(code, match["_start"])
        j = match["_end"]
        sig = code[i:j]
        bodyStart, bodyEnd = findNextBlock(code, match["_end"], "{")
        match["_lineStart"] = i
        match["_end"] = bodyEnd
        functions.append({ "match": match, "signature": sig, "body": code[bodyStart:bodyEnd] })
    for function in functions:
        sig = function["signature"]
        i, j = findNextBlock(sig, 0, "(")
        paramsCode = sig[i:j]
        params = findVariables(paramsCode, lang)
        function["params"] = params
    return functions

def testFindFeature():
    log_enable()
    lang = Typescript()
    md = readTextFile("source/fnf/Hello.fnf.ts.md")
    code = extractCode(md)
    result = findFeature(code, lang)
    featureBody = result["body"]
    structs = findStructs(featureBody, lang)
    functions = findFunctions(featureBody, lang)
    removeExtents = []
    log("structs:")
    for struct in structs:
        lineStart = struct["match"]["_lineStart"]
        end = struct["match"]["_end"]
        removeExtents.append((lineStart, end))
        log(struct["match"]["name"])
        for variable in struct["variables"]:
            log("  ", variable["match"]["name"])
        log(featureBody[struct["match"]["_lineStart"]:struct["match"]["_end"]])
        log("-----")
    log("functions:")
    for function in functions:
        lineStart = function["match"]["_lineStart"]
        end = function["match"]["_end"]
        removeExtents.append((lineStart, end))
        log(function["match"]["name"])
        for variable in function["params"]:
            log("  ", variable["match"]["name"], variable["match"]["type"])
        log(" => ", function["match"]["type"])
        log(featureBody[function["match"]["_lineStart"]:function["match"]["_end"]])
        log("-----")
    log("remaining code:")
    # sort removeExtents by start, descending
    removeExtents.sort(key=lambda x: x[0], reverse=True)
    for extent in removeExtents:
        featureBody = featureBody[:extent[0]] + featureBody[extent[1]:]
    # remove empty lines
    featureBody = re.sub(r'\n\s*\n', '\n', featureBody)
    log(featureBody)
    # now get test lines
    lines = featureBody.split("\n")
    remaining = ""
    testCode = ""
    for line in lines:
        if "==>" in line:
            testCode += line + "\n"
        else:
            remaining += line + "\n"
    log("tests:")
    log(testCode)
    log("remaining:", remaining)
    variables = findVariables(remaining, lang)
    log("variables:")
    for variable in variables:
        log(variable["match"])
    match = regMatch(lang.variable_format(), remaining)
    log("match:")
    log(match)

def testWtf():
    lang = Typescript()
    p1 = "{ var my_colour : Colour = new Colour(1, 2, 3);"
    match = regMatch(lang.variable_format(), p1)
    print(match)



#---------------------------------------------------------------------------------

def test():
    #testRegex()
    #testExtractCode()
    #testTypescriptFormats()
    #testFindEndOfBlock()
    #testFindFeature()
    testWtf()

#---------------------------------------------------------------------------------

def main():
    print("ᕦ(ツ)ᕤ")
    print("fnf.py")
    test()

#---------------------------------------------------------------------------------
if __name__ == "__main__":
    main()