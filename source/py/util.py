# ᕦ(ツ)ᕤ
# util.py
# author: asnaroo
# this is a low-level module imported by fnf.py and languages/*.py
# it contains generally useful functions for files, logging, parsing, errors

import os
import re
import json
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

def log_c(*args):
    if log_enabled:
        print(*args, end="")

def clear_console():
    os.system('clear')  # For Linux/macOS

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

#---------------------------------------------------------------------------------
# SourceFile holds filename, sourcemap, does extraction/initial processing

class SourceFile:
    def __init__(self):
        self.mdFile = ""                # filename of markdown file
        self.text = ""                  # original file text
        self.code = ""                  # extracted code        
        self.sourceMap = []             # list of pairs (charIndex, lineIndexInOrig)
        
    # load markdown file, figure out language, extract code
    def loadMarkdown(self, mdFile: str):
        self.mdFile = mdFile
        self.text = readTextFile(self.mdFile)
        ext = self.mdFile.split(".")[2]      # => "ts"
        log("ext:", ext)
        self.extractCode()

    # extract code from markdown text, set up sourcemap
    def extractCode(self):
        self.code = ""
        lines = self.text.split("\n")
        inCodeBlock = False
        self.sourceMap = []
        for i, line in enumerate(lines):
            if not inCodeBlock:
                if line.startswith("    "):
                    codeLine = line[4:].rstrip()
                    self.pushLine(codeLine, i+1)
                else:
                    if line.startswith("```"):
                        inCodeBlock = True
            else:
                if line.startswith("```"):
                    inCodeBlock = False
                else:
                    codeLine = line.rstrip()
                    self.pushLine(codeLine, i+1)

    # pushes a code line and source code line-index
    def pushLine(self, codeLine: str, iLineSource: int =0):
        self.sourceMap.append((len(self.code), iLineSource))
        self.code += codeLine + "\n"

    # maps character-index in source code to line/character in markdown file
    def sourceLine(self, iChar: int) -> Tuple[int, int]:
        for i in range(0, len(self.sourceMap)): # TODO: binary search
            if self.sourceMap[i][0] <= iChar and (i==len(self.sourceMap)-1 or self.sourceMap[i+1][0] > iChar):
                iLine = self.sourceMap[i][1]
                iCharOut = (iChar - self.sourceMap[i][0]) + 1
                return iLine, iCharOut
        return -1, -1
    
    # show source file with source line numbers
    def show(self):
        lines = self.code.split("\n")
        iChar = 0
        for line in lines:
            (iLine, iCharOut) = self.sourceLine(iChar)
            log(f'{iLine:4d}: {line}')
            iChar += len(line) + 1

#---------------------------------------------------------------------------------
# Source is a read-range (start--end) within a SourceFile

class Source:
    def __init__(self, sourceFile: SourceFile, start=0, end=-1):
        self.file = sourceFile              # source file object
        self.set(start, end)                # range within it

    def set(self, start: int, end: int =-1):
        self.start = start
        self.end = end if end != -1 else len(self.file.code)

    def __str__(self):
        return self.file.code[self.start:self.end]
    
    def __repr__(self):
        return self.__str__()
    
    def line(self):
        return self.file.sourceLine(self.start)[0]
    
    def show(self, nChars: int = 16):
        out = self.file.code[self.start:self.start+nChars]
        out = out.replace("\n", "↩︎")
        return f"'{out}…'"

#---------------------------------------------------------------------------------
# Error holds a message and a source location

class Error:
    def __init__(self, message: str, source: Source):
        self.message = message
        self.source = Source(source.file)
        self.source.start = source.start

    def __str__(self):
        (iLine, iChar) = self.source.file.sourceLine(self.source.start)
        return f"Error: {self.message} at {self.source.file.mdFile}:{iLine}:{iChar}\n       {self.source.show(32)}"

def err(obj)->bool:
    return obj==None or isinstance(obj, Error)

#---------------------------------------------------------------------------------
# Parser functions: combine them to parse anything

def isWhitespace(c: str):
    return c in " \t\n\r"

# skipWhitespace returns the index of the next non-whitespace character
def skipWhitespace(source: Source):
    while source.start < source.end and isWhitespace(source.file.code[source.start]):
        source.start += 1
    
# keyword(value) checks if the source starts with the value, and if so, returns the value
def keyword(value: str):
    def parse_keyword(source: Source, value: str):
        skipWhitespace(source)
        if value=="}" and source.start == source.end:  # tolerate unclosed } at end of file
            return {}
        log_c(f"keyword('{value}'): {source.show()}")
        pos = source.start
        if source.file.code.startswith(value, source.start):
            source.start += len(value)
            log(f" => matched")
            return {}
        log(f" => None")
        return Error(f"expected '{value}'", source)
    return lambda source: parse_keyword(source, value)

# word() returns a function that takes source, and returns the first alphanumeric word
def word():
    def parse_word(source: Source):
        skipWhitespace(source)
        log_c(r"word():", source.show())
        pos = source.start
        i = source.start
        while i < source.end and (source.file.code[i].isalnum() or source.file.code[i]=="_"):
            i += 1
        if i > source.start:
            word = source.file.code[source.start:i]
            if word in ["const", "var", "struct", "extend", "feature", "extends", 
                        "on", "after", "before", "replace"]:
                log(" => None {keyword}")
                return None
            source.start = i
            log(f" => '{word}'")
            return Source(source.file, pos, i)
        return Error("expected word", source)
    return lambda source: parse_word(source)

# set(varname, parserFn) just calls parserFn, and sets the result to varname
def set(varname: str, parserFn):
    def parse_set(varname: str, parserFn, source: Source):
        log_c(f"set({varname}): {source.show()}")
        result = parserFn(source)
        if err(result):
            log(f" => err")
            return result
        log(f" => {result}")
        return { varname: result }
    return lambda source: parse_set(varname, parserFn, source)

# parse_sequence(source) calls each parserFn in sequence, accumulating results in a dictionary
def sequence(*parserFns: List):
    def parse_sequence(source: Source, *parserFns):
        result = {}
        pos = source.start
        for parserFn in parserFns:
            singleResult = parserFn(source)
            if err(singleResult):
                source.start = pos
                return singleResult
            else:
                if isinstance(singleResult, dict):
                    result.update(singleResult)
        return result
    return lambda source: parse_sequence(source, *parserFns)

# optional(parserFn) calls parserFn, returns {} even if no match
def optional(parserFn):
    def parse_optional(source: Source, parserFn):
        skipWhitespace(source)
        result = parserFn(source)
        if err(result):
            if result.source.start == source.start:
                return {}
        return result
    return lambda source: parse_optional(source, parserFn)

# and anyof(parserFns) returns a function that calls parse_anyof with the parserFns
def anyof(*parserFns):
    def parse_anyof(source: Source, *parserFns):
        pos = source.start
        for parserFn in parserFns:
            result = parserFn(source)
            if not err(result):
                return result
            else:
                source.start = pos
        return Error("anyof failed", source)
    return lambda source: parse_anyof(source, *parserFns)

# enum is a special case of anyof that takes a list of strings and matches keywords
def enum(*values):
    def parse_enum(source: Source, *values):
        log_c(f"enum({values}): {source.show()}")
        skipWhitespace(source)
        for value in values:
            pos = source.start
            if source.file.code.startswith(value, source.start):
                source.start += len(value)
                log(f" => '{value}'")
                return Source(source.file, pos, source.start)
            else:
                source.start = pos
        log(" => None")
        return Error(f"expected one of {values}", source)
    return lambda source: parse_enum(source, *values) 

# and list(parserFn) returns a function that calls parse_list with the parserFn
def list(parserFn):
    def parse_list(source: Source, parserFn):
        log(f'parse_list on "{source.file.code[source.start:source.start+16]}..."')
        results = []
        count = 10
        while count > 0:
            log(f'  applying parserFn to "{source.file.code[source.start:source.start+16]}..."')
            count -= 1
            pos = source.start
            result = parserFn(source)
            log("    result:", result)
            if err(result):
                source.start = pos
                break
            results.append(result)
            if count==0:
                print("list: count exceeded!")
                return results
        return results
    return lambda source: parse_list(source, parserFn)

# debug(source) turns on logging before calling whatever
def debug(parserFn):
    def debugFn(source: Source):
        log_enable()
        result = parserFn(source)
        log("returning:", result)
        log(f'after: "{source.file.code[source.start:source.end]}"')
        log_disable()
        return result
    return lambda source: debugFn(source)

global level
level = 0

# label(type) just adds { "_type": type } to the result
def label(type: str, parserFn):
    def parse_label(type: str, parserFn, source: Source):
        skipWhitespace(source)
        global level
        toShow = f"{'  ' * level}label({type}): {source.show()}"
        #log_enable()
        log(toShow)
        #log_disable()
        out = { "_type": type }
        level += 1
        result = parserFn(source)
        level -= 1
        if err(result):
            return result
        out.update(result)
        return out
    return lambda source: parse_label(type, parserFn, source)

# toUndent() scans forward to outermost undent assuming we're in one already
def toUndent():
    def parse_toUndent(source: Source):
        depth = 1
        inQuote = False
        skipWhitespace(source)
        pos = source.start
        i = source.start
        while i < source.end:
            if not inQuote:
                if source.file.code[i] == '"':
                    inQuote = True
                elif source.file.code[i] == "{":
                    depth += 1
                elif source.file.code[i] == "}":
                    depth -= 1
                    if depth == 0:
                        match = source.file.code[source.start:i]
                        source.start = i
                        return Source(source.file, pos, i)
            else:
                if source.file.code[i] == '"' and source.file.code[i-1] != "\\":
                    inQuote = False
            i += 1
        return Source(source.file, pos, source.end)
    return lambda source: parse_toUndent(source)

# toEnd() scans forward to next occurrence of any of [strs] outside of any braces/brackets/quotes;
# only matches if len(match) > 0
def toEnd(findChars: str = ",;\n)"):
    def parse_toEnd(source: Source):
        depth = 0
        inQuote = False
        pos = source.start
        log_c(f"toEnd(): {source.show()}")
        i = source.start
        while i < source.end:
            if not inQuote:
                if depth == 0 and source.file.code[i] in findChars:
                    match = source.file.code[source.start:i]
                    if len(match.strip()) == 0:
                        source.start = pos
                        return Error("empty toEnd() match", source)
                    source.start = i
                    log(f" => '{match.replace("\n", "↩︎")}'")
                    return Source(source.file, pos, i)
                elif source.file.code[i] in "{([":
                    depth += 1
                elif source.file.code[i] in "})]":
                    depth -= 1
                elif source.file.code[i] == '"':
                    inQuote = True
            else:
                if source.file.code[i] == '"' and source.file.code[i-1] != "\\":
                    inQuote = False
            i += 1
        if source.start == source.end:
            source.start = pos
            return Error("empty toEnd() match at eof", source)
        return Source(source.file, pos, source.end)
    return lambda source: parse_toEnd(source)