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
log_enabled: bool = True

def log_enable():
    global log_enabled
    log_enabled = True

def log_disable():
    global log_enabled
    log_enabled = False

def log(*args):
    if log_enabled:
        print(*args)

#--------------------------------------------------------------------------------------------------------------------------
# regular expressions to detect terms in the language definitions

def literalRegex(): return r"('[^']*')"
def wordRegex(): return r'(\w+)'
def bracketRegex(): return r'(\([^)]*\))'
def propertyRegex(): return wordRegex() + bracketRegex() + '?'
def itemRegex(): return literalRegex() + "|" + propertyRegex()

def reMatch(regex: str, text: str) -> List[str]:
    pattern = re.compile(regex)
    match = pattern.search(text)
    if match==None: return []
    return [match.group(i) for i in range(1, len(match.groups())+1)]

def testLiteralRegex():
    log("testLiteralRegex", reMatch(literalRegex(), "'hello'"))

def testWordRegex():
    log("testWordRegex", reMatch(wordRegex(), "hello"))

def testBracketRegex():
    log("testBracketRegex", reMatch(bracketRegex(), "(hello)"))

def testPropertyRegex():
    log("testPropertyRegex", reMatch(propertyRegex(), "hello(world)"))

def testItemRegex():
    log("testItemRegex", reMatch(itemRegex(), "'hello'"))
    log("testItemRegex", reMatch(itemRegex(), "hello"))
    log("testItemRegex", reMatch(itemRegex(), "hello(world)"))

def testRegex():
    testLiteralRegex()
    testWordRegex()
    testBracketRegex()
    testPropertyRegex()
    testItemRegex()

#--------------------------------------------------------------------------------------------------------------------------
# rules and terms

# the smallest atom: it's either a literal, or a named property
class TermItem:
    def __init__(self, literal: str, name: str, brackets: str):
        self.literal = literal[1:-1] if literal else None
        self.name = name
        self.brackets = brackets[1:-1] if brackets else None
        self.options = []
        if self.brackets:
            if " or " in self.brackets:
                self.options = [option[1:-1] for option in self.brackets.split(" or ")]

    def __str__(self):
        out = ""
        if self.literal!=None: out += "'" + self.literal + "'"
        if self.name!=None: out += self.name
        if self.brackets!=None: out += "(" + self.brackets + ")"
        return out

# a term is an optional sequence of one or more items
class Term:
    def __init__(self, text: str):
        pattern = re.compile(itemRegex())
        matches = pattern.finditer(text)
        self.items = []
        self.optional = False
        for match in matches:
            literal = match.group(1)
            name = match.group(2)
            brackets = match.group(3)
            if name=="optional":
                self.optional = True
            else:
                self.items.append(TermItem(literal, name, brackets))
    def __str__(self):
        out = "Term(" if not self.optional else "Optional("
        out += ", ".join([str(item) for item in self.items])
        out += ")"
        return out

# and a rule is a list of terms
class Rule:
    def __init__(self, name: str, parts: List[str]):
        self.name = name
        self.terms = [Term(part) for part in parts]

    def __str__(self):
        out = "Rule("
        out += ", ".join([str(term) for term in self.terms])
        out += ")"
        return out
    
#--------------------------------------------------------------------------------------------------------------------------
# parsing typescript/python/cpp using language-specific grammars in a human-readable format

class Language:
    def __init__(self, name: str, extension: str): 
        self.name = name
        self.extension = extension
    def rules(self): return {}
    @staticmethod
    def fromExtension(extension: str):
        for subclass in Language.__subclasses__():
            if subclass().extension == extension:
                return subclass()
        return None
    
class Typescript(Language):
    def __init__(self): super().__init__("typescript", "ts")
    def rules(self): 
        return {
            "feature": Rule("feature", ["'feature'", "name(word)", "optional 'extends' parent(word)", "body(block{})"]),
            "variable": Rule("variable", ["modifier('var' or 'const')", "name(word)", "optional ':' type(word)", "optional '=' value(toEnd)"]),
            "struct": Rule("struct", ["modifier('struct' or 'extend')", "name(word)", "body(block{})"]),
            "function": Rule("function", ["modifier('def' or 'replace' or 'on' or 'before' or 'after')", "name(word)", "params(bracketList)", "optional ':' type(word)", "body(block{})"])
        }
    
class Python(Language):
    def __init__(self): super().__init__("python", "py")
    def rules(self):
        return {
            "feature" : ["'feature'", "name(word)", "optional '(' parent(word) ')'", "body(block)"],
            "variable" : ["name(word)", "optional ':' type(word)", "optional '=' value(toEnd)"],
            "struct" : ["modifier('struct' or 'extend')", "name(word)", "body(block)"],
            "function": ["modifier('def' or 'replace' or 'on' or 'before' or 'after')", "name(word)", "params(bracketList)", "optional '->' type(word)", "body(blockIndent)"]
        }

class Cpp(Language):
    def __init__(self): super().__init__("cpp", "cpp")
    def rules(self):
        return {
            "feature" : ["'feature'", "name(word)", "optional ':' parent(word)", "body(block{})"],
            "variable" : ["optional modifier('const')", "type(word)" "name(word)", "optional '=' value(toEnd)"],
            "struct" : ["modifier('struct' or 'extend')", "name(word)", "body(block{})"],
            "function" : ["modifier('def' or 'replace' or 'on' or 'before' or 'after')", "type(word)" "name(word)", "params(bracketed)", "body(block{})"]
        }


def testRules():
    log("testRules")
    ts = Typescript()
    rule = Rule("feature", ts.rules()["feature"])
    log(rule)

#--------------------------------------------------------------------------------------------------------------------------
# files

def readTextFile(path: str) -> str:
    with open(path, "r") as file:
        return file.read()
    
def writeTextFile(path: str, text: str):
    # ensure directories exist:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        file.write(text)

#--------------------------------------------------------------------------------------------------------------------------
# extract code from .fnf.*.md files, outputs code with line numbers at the start

# pull out the code lines, also return a "dest->source" line number mapping
def extractCode(text) -> Tuple[str, List[int]]:
    out = ""
    lines = text.split("\n")
    inCodeBlock = False
    sourceMap = []
    for i, line in enumerate(lines):
        if not inCodeBlock:
            if line.startswith("    "):
                codeLine = line[4:].rstrip()
                out += codeLine + "\n"
                sourceMap.append(i+1)
            else:
                if line.startswith("```"):
                    inCodeBlock = True
        else:
            if line.startswith("```"):
                inCodeBlock = False
            else:
                codeLine = line.rstrip()
                out += codeLine + "\n"
                sourceMap.append(i+1)
    return (out, sourceMap)

def testExtractCode():
    log("testExtractCode")
    text = readTextFile("source/fnf/Hello.fnf.ts.md")
    code, sourceMap = extractCode(text)
    log(code)
    log(sourceMap)

#--------------------------------------------------------------------------------------------------------------------------
# match rules against code

def isWhitespace(c: str) -> bool:
    return c==" " or c=="\n"

def nextNonWhitespace(text: str, iChar: int) -> int:
    while iChar < len(text) and isWhitespace(text[iChar]):
        iChar += 1
    return iChar

# return (matched, iBlockStart, iBlockEnd, iCharNext)
def matchBlockWithBraces(braces: str, text: str, iChar: int) -> Tuple[bool, int, int, int]:
    log("matchBlockWithBraces")
    i = iChar
    braceCount = 0
    start = iChar
    while i < len(text):
        if text[i]== braces[0]:
            braceCount += 1
            if braceCount==1:
                start = i+1
        elif text[i]== braces[1]:
            braceCount -= 1
            if braceCount==0:
                return (True, nextNonWhitespace(text, start), i-1, i+1)
        i += 1
    if braceCount == 1:
        return (True, nextNonWhitespace(text, start), len(text), len(text))
    return (False, iChar, iChar, iChar)

# return matched, iStart, iEnd, iCharNext
def matchToEnd(text: str, iChar: int) -> Tuple[bool, int, int, int]:
    iChar = nextNonWhitespace(text, iChar)
    i = iChar
    while i < len(text) and text[i] != '\n':
        i += 1
    return (True, iChar, i, i+1)

# return matched, remaining, values
def matchItem(item: TermItem, text: str, iChar: int) -> Tuple[bool, int, dict]:
    regexps = { "word": wordRegex() }
    if item.literal:
        if text[iChar:].startswith(item.literal):
            iReturn = nextNonWhitespace(text, iChar + len(item.literal))
            return (True, iReturn, {})
    elif item.name:
        if len(item.options)>0:
            log("trying options:", item.options)
            for option in item.options:
                if text[iChar:].startswith(option):
                    iReturn = nextNonWhitespace(text, iChar + len(option))
                    return (True, iReturn, {item.name: option})
            return (False, iChar, {})
        else:
            matchType = item.brackets
            if matchType in regexps:
                match = reMatch(regexps[matchType], text[iChar:])
                if len(match)>0:
                    iReturn = nextNonWhitespace(text, iChar + len(match[0]))
                    return (True, iReturn, {item.name: match[0]})
            else:
                if matchType == "bracketList": matchType = "block()" # really should just be able to put block() in grammar
                if matchType.startswith("block"):
                    braces = matchType[5:]
                    (matched, iStart, iEnd, iCharNext) = matchBlockWithBraces(braces, text, iChar)
                    if matched:
                        iStart = nextNonWhitespace(text, iStart)
                        iCharNext = nextNonWhitespace(text, iCharNext)
                        return (True, iCharNext, {item.name: (iStart, iEnd)})
                    else:
                        return (False, iChar, {})
                if matchType == "toEnd":
                    (matched, iStart, iEnd, iCharNext) = matchToEnd(text, iChar)
                    if matched:
                        return (True, iCharNext, {item.name: (iStart, iEnd)})
                    else:
                        return (False, iChar, {})
                log("unknown matchType:", matchType)
    return (False, iChar, {})

# return matched y/n, remaining, values
def matchTermNonOptional(term: Term, text: str, iChar: int) -> Tuple[bool, int, dict]:
    iItem = 0
    outputValues = {}
    originalText = text
    while iItem < len(term.items):
        (matched, iCharNext, values) = matchItem(term.items[iItem], text, iChar)
        if not matched:
            return (False, iChar, {})
        else:
            outputValues.update(values)
            iChar = iCharNext
            iItem += 1
    return (True, iChar, outputValues)

# return matched y/n, remaining, values
def matchTerm(term: Term, text: str, iChar: int) -> Tuple[bool, int, dict]:
    log("matchTerm", term)
    (matched, iCharNext, values) = matchTermNonOptional(term, text, iChar)
    if not matched and term.optional:
        return (True, iChar, {})
    return (matched, iCharNext, values)

def matchRule(rule: Rule, text: str, iChar: int) -> Tuple[bool, int, dict]:
    log("matchRule", rule)
    iTerm = 0
    allValues = { "_rule": rule.name, "_start": iChar }
    while iTerm < len(rule.terms):
        (matched, iCharNext, values) = matchTerm(rule.terms[iTerm], text, iChar)
        if not matched:
            return (False, iChar, {})
        allValues.update(values)
        iChar = iCharNext
        iTerm += 1
    return (True, iCharNext, allValues)

def matchAnyRule(rules: List[Rule], text: str, iChar: int) -> Tuple[bool, int, dict]:
    log_disable()
    log("matchAnyRule", [rule.name for rule in rules])
    for rule in rules:
        log("trying rule:", rule.name)
        (matched, iCharNext, values) = matchRule(rule, text, iChar)
        if matched:
            log_enable()
            return (matched, iCharNext, values)
        else:
            log("no match")
    log_enable()
    return (False, iChar, {})

def matchFeatureInternals(lang: Language, text: str, iChar: int) -> List[dict]:
    rules = [lang.rules()["function"], lang.rules()["struct"], lang.rules()["variable"]]
    results = []
    while iChar < len(text):
        (matched, iChar, values) = matchAnyRule(rules, text, iChar)
        if matched:
            results.append(values)
            log("matched feature internal: ", values["_rule"])
            log(values)
            if "body" in values:
                iStart = values["body"][0]
                iEnd = values["body"][1]
                log("body:")
                log(text[iStart:iEnd])
        else:
            log("houston we have a problem")
            log("remaining:")
            log(text[iChar:])
            break
    return results

def matchFeature(lang: Language, text: str, iChar: int) -> Tuple[bool, int, dict]:
    (matched, iChar, values) = matchRule(lang.rules()["feature"], text, iChar)
    if matched:
        values["internals"] = matchFeatureInternals(lang, text[:values["body"][1]], values["body"][0])
        log("matched feature :-)")
    return (matched, iChar, values)

def testMatchFunction():
    lang = Typescript()
    text = "def hello(name: string) : number  {\n    return 42;\n }"
    (matched, iCharNext, values) = matchRule(lang, "function", text, 0)
    log(values)
    params = values["params"]
    paramText = text[params[0]:params[1]]
    log("params:", paramText)
    body = values["body"]
    bodyText = text[body[0]:body[1]].strip()
    log("body:", bodyText)

def testMatchFeature():
    log("testMatchFeature")
    path = "source/fnf/Hello.fnf.ts.md"
    ext = path.split(".")[-2]
    log(ext)
    language = Language.fromExtension(ext)
    (code, sourceMap) = extractCode(readTextFile(path))
    (matched, remaining, values) = matchFeature(language, code, 0)
    log(values)
    log("body:")
    iStart = values["body"][0]
    iEnd = values["body"][1]
    log(code[iStart:iEnd])

#--------------------------------------------------------------------------------------------------------------------------

def test():
    #testRegex()
    #testRules()
    #testExtractCode()
    #testMatchFunction()
    testMatchFeature()

if __name__ == "__main__":
    log("----------------------------------------------")
    log("ᕦ(ツ)ᕤ fnf.py")
    test()