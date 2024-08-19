# ᕦ(ツ)ᕤ
# util.py
# author: asnaroo
# this is a low-level module imported by fnf.py and languages/*.py
# it contains generally useful functions for files, logging, parsing, errors

import os
import re
import json
import subprocess
from typing import List
from typing import Tuple
import datetime

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

def currentWorkingDirectory() -> str:
    return os.getcwd()

def getCreationTimestamp(file_path):
    try:
        stat = os.stat(file_path)
        return stat.st_birthtime
    except AttributeError:
        # This may not be available on all systems
        return None

def scanFolder(self, ext: str) -> List[str]:
    cwd = currentWorkingDirectory()
    # scan the directory for .fnf.md files
    filesFound = []
    for root, dirs, files in os.walk(cwd):
        for file in files:
            if file.endswith(ext):
                filesFound.append(os.path.join(root, file))
    # sort files into ascending order of creation-date
    filesFound.sort(key=lambda x: getCreationTimestamp(x))
    filesFound= [file.replace(cwd+"/", "") for file in filesFound]
    log("filesFound:")
    for file in filesFound:
        dateAsString = os.path.getctime(file)
        humanReadableDate = datetime.datetime.fromtimestamp(dateAsString).isoformat()
        log(f"  {file} : creation date {humanReadableDate}")
    return filesFound

#---------------------------------------------------------------------------------
# shell / config stuff for installing things

# returns the correct shell config file path depending on the shell in use
def get_shell_config_file():
    shell = os.environ.get('SHELL', '')
    home = os.path.expanduser('~')
    if 'zsh' in shell:
        return os.path.join(home, '.zshrc')
    elif 'bash' in shell:
        return os.path.join(home, '.bash_profile')
    else:
        return os.path.join(home, '.profile')

# ensures that new_path is added to the PATH variable
def update_PATH(new_path):
    shell_config = get_shell_config_file()
    path_entry = f'export PATH="{new_path}:$PATH"'
    
    # Check if path already exists in the file
    with open(shell_config, "r") as f:
        content = f.read()
        if new_path in content:
            log(f"PATH entry for {new_path} already exists in {shell_config}")
            return

    # If not, append it to the file
    with open(shell_config, "a") as f:
        f.write(f'\n{path_entry}\n')
    
    log(f"Updated {shell_config} with new PATH entry: {new_path}")

    # Source the shell configuration file
    source_command = f"source {shell_config}"
    subprocess.run(source_command, shell=True, executable="/bin/bash")
    
    # Update current environment
    os.environ["PATH"] = f"{new_path}:{os.environ['PATH']}"

#---------------------------------------------------------------------------------
# SourcePath just contains a filename: to avoid massive string copying nonsense

class SourcePath:
    def __init__(self, filename: str):
        self.filename = filename

    def __str__(self):
        return self.filename

    def __repr__(self):
        return self.__str__()
    
#---------------------------------------------------------------------------------
# SourceLocation is a triple (filename, lineIndex, charInLine)

class SourceLocation:
    def __init__(self, path: SourcePath, lineIndex: int, charInLine: int=0):
        self.path = path
        self.lineIndex = lineIndex
        self.charInLine = charInLine

    def __str__(self):
        out = f"{self.path}:{self.lineIndex}"
        if self.charInLine > 1:
            out += f":{self.charInLine}"
        return out
    
    def __repr__(self):
        return self.__str__()

#---------------------------------------------------------------------------------
# SourceFile holds filename, sourcemap, does extraction/initial processing

class SourceFile:
    def __init__(self, path=None):
        self.text = ""                  # original file text
        self.code = ""                  # extracted code    
        self.filenames = []             # list of filenames for source map    
        self.sourceMap = []             # list of (charIndex, SourceMap) pairs
        if path:
            self.loadMarkdown(path)
        
    # load markdown file, figure out language, extract code
    def loadMarkdown(self, mdFile: str):
        self.text = readTextFile(mdFile)
        self.extractCode(mdFile)

    # extract code from markdown text, set up source-map
    def extractCode(self, mdFile: str):
        path = SourcePath(mdFile)
        self.code = ""
        lines = self.text.split("\n")
        inCodeBlock = False
        self.sourceMap = []
        for i, line in enumerate(lines):
            if not inCodeBlock:
                if line.startswith("    "):
                    codeLine = line[4:].rstrip()
                    self.pushLine(codeLine, SourceLocation(path, i+1))
                else:
                    if line.startswith("```"):
                        inCodeBlock = True
            else:
                if line.startswith("```"):
                    inCodeBlock = False
                else:
                    codeLine = line.rstrip()
                    self.pushLine(codeLine, SourceLocation(path, i+1))

    # pushes a code line and source code line-index
    def pushLine(self, codeLine: str, location: SourceLocation = None):
        self.sourceMap.append((len(self.code), location))
        self.code += codeLine + "\n"

    # pushes all lines of (source) to end of lines, merges sourcemaps
    def appendSource(self, source: 'SourceFile'):
        length = len(self.code)
        self.code += source.code
        for i in range(0, len(source.sourceMap)):
            self.sourceMap.append((source.sourceMap[i][0]+length, source.sourceMap[i][1]))

    # maps character-index in source code to location in original file
    def sourceLocation(self, iChar: int) -> SourceLocation:
        for i in range(0, len(self.sourceMap)): # TODO: binary search
            if self.sourceMap[i][0] <= iChar and (i==len(self.sourceMap)-1 or self.sourceMap[i+1][0] > iChar):
                loc = self.sourceMap[i][1]
                if loc == None: return None
                iCharOut = (iChar - self.sourceMap[i][0])+1
                return SourceLocation(loc.path, loc.lineIndex, iCharOut)
        return None
    
    # returns an array of character-indices for the start of each line
    def lineStarts(self) -> List[int]:
        starts = [0]
        for i, c in enumerate(self.code):
            if c == "\n":
                starts.append(i+1)
        return starts
    
    # show source file with source line numbers
    def show(self):
        lines = self.code.split("\n")
        if lines[-1] == "": lines.pop()
        # first get the max length of the source locations:
        maxLocLen = 0
        iChar = 0
        for line in lines:
            location = self.sourceLocation(iChar)
            if location != None: maxLocLen = max(maxLocLen, len(str(location)))
            iChar += len(line) + 3
        # now print the lines with locations, padded
        iChar = 0
        for i, line in enumerate(lines):
            location = self.sourceLocation(iChar)
            locStr = f'[{location}]' if location != None else ""
            locStr = locStr + " " * (maxLocLen - len(locStr))
            log(f"{locStr} {line}")
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
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.file.code[self.start:self.start + len(other)] == other

    def __hash__(self):
        return hash((self.name, self.offset))
    
    def sourceLocation(self):
        return self.file.sourceLocation(self.start)
    
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
        loc = self.source.file.sourceLocation(self.source.start)
        return f"Error: {self.message} at {loc}\n       {self.source.show(32)}"

    def __repr__(self):
        return self.__str__()
    
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
