# ᕦ(ツ)ᕤ
# parser.py
# author: asnaroo
# experiment: replacement for util.py

import os
import re
from typing import List
import copy
from threading import Thread
import subprocess
import datetime

#----------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------
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
        log(f"  {file} : {humanReadableDate}")
    return filesFound

#----------------------------------------------------------------------------------------
# shell / config stuff for installing things

# runs a shell command, optionally processes output+errors line by line, returns collected output
def runProcess(cmd: List[str], processFn=(lambda x: x)) -> str:
    collected_output = ""
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Helper function to process and log output
    def process_output(stream, append_to):
        nonlocal collected_output
        while True:
            line = stream.readline()
            if line:
                processed_line = processFn(line).strip()
                log(processed_line)
                append_to.append(processed_line + '\n')
            else:
                break

    # Using lists to collect output as strings are immutable
    stdout_output = []
    stderr_output = []

    # Start threads to handle stdout and stderr
    stdout_thread = Thread(target=process_output, args=(process.stdout, stdout_output))
    stderr_thread = Thread(target=process_output, args=(process.stderr, stderr_output))

    stdout_thread.start()
    stderr_thread.start()
    stdout_thread.join()
    stderr_thread.join()

    # Collect final outputs
    collected_output = ''.join(stdout_output) + ''.join(stderr_output)
    return collected_output

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

#----------------------------------------------------------------------------------------
# SourceFile is a filename

class SourceFile:
    def __init__(self, filename: str):
        self.filename = filename
        self.text = readTextFile(filename)

#----------------------------------------------------------------------------------------
# SourceLocation is a SourceFile, line number, and column number (default 0)

class SourceLocation:
    def __init__(self, file: SourceFile, line: int, col: int = 0):
        self.file = file
        self.line = line
        self.col = col

    def __str__(self):
        return f"{self.file.filename}:{self.line}:{self.col}"
    
    def __repr__(self):
        return self.__str__()

#----------------------------------------------------------------------------------------
# SourceMap maps (iChar) => SourceLocation

class SourceMap:
    def __init__(self):
        self.map = []
    
    def add(self, iChar: int, loc: SourceLocation):
        self.map.append((iChar, loc))

    def get(self, iChar: int) -> SourceLocation:
        for i in range(len(self.map)):
            if iChar < self.map[i][0]:
                nChars = (iChar - self.map[i-1][0]) + 1
                location = self.map[i-1][1]
                return SourceLocation(location.file, location.line, location.col + nChars)
        return self.map[-1][1]

#----------------------------------------------------------------------------------------
# Code is the ... code!

class Code:
    def __init__(self):
        self.file : SourceFile = None
        self.text = ""
        self.map = SourceMap()

    def location(self, iChar: int) -> SourceLocation:
        return self.map.get(iChar)
    
    def extract(self, file: SourceFile):
        lines = file.text.split("\n")
        inCodeBlock = False
        self.sourceMap = []
        for i, line in enumerate(lines):
            if not inCodeBlock:
                if line.startswith("    "):
                    codeLine = line.rstrip()
                    self.pushLine(codeLine, SourceLocation(file, i+1))
                else:
                    if line.startswith("```"):
                        inCodeBlock = True
            else:
                if line.startswith("```"):
                    inCodeBlock = False
                else:
                    codeLine = line.rstrip()
                    self.pushLine(codeLine, SourceLocation(file, i+1))

    def pushLine(self, line: str, loc: SourceLocation =None):
        if loc:
            self.map.add(len(self.text), loc)
        self.text += line + "\n"

    def __str__(self):
        out = ""
        lines = self.text.split("\n")
        if lines[-1] == "": lines = lines[:-1]
        iChar = 0
        for line in lines:
            loc = self.location(iChar)
            out += (f"[{loc.line:3}] {line}") + "\n"
            iChar += len(line) + 1
        return out

    def __repr__(self):
        return self.__str__()

#----------------------------------------------------------------------------------------
# Reader is Code, plus a read pointer and an end index

class Reader:
    def __init__(self, code: Code, iChar: int = 0, iEnd: int = -1):
        self.code = code
        self.iChar = iChar
        self.iEnd = iEnd if iEnd >= 0 else len(code.text)
        self.nChars = 0
    
    def location(self) -> SourceLocation:
        return self.code.location(self.iChar)
    
    def skipWhitespace(self):
        while self.iChar < self.iEnd and self.code.text[self.iChar] in ' \t\n\r':
            self.iChar += 1

    def advance(self):
        self.iChar += self.nChars
        self.nChars = 0

    def copyAndAdvance(self, iChar: int=None) -> 'Reader':
        iChar = iChar if iChar else self.iChar
        result = Reader(self.code, iChar, iChar + self.nChars)
        self.advance()
        return result

    def restore(self, iChar: int):
        self.iChar = iChar
        self.nChars = 0
    
    def match(self, regexp: str, iChar: int=None) -> bool: # returns True if regexp matches at iChar
        iChar = self.iChar if iChar == None else iChar
        pattern = re.compile(regexp)
        match = pattern.match(self.code.text, iChar, self.iEnd)
        self.nChars = (match.end() - match.start()) if match else 0
        return (self.nChars > 0)
    
    def char(self, iChar: int) -> str:
        return self.code.text[iChar]
    
    def __str__(self):
        return self.code.text[self.iChar:self.iEnd]
    
    def __repr__(self):
        return self.__str__()

#----------------------------------------------------------------------------------------
# Writer is Code, plus a write pointer

class Writer:
    def __init__(self, code: Code):
        self.code = code
        self.indentLevel = 0
        self.toWrite = ""
        self.location = None

    def write(self, *args):
        for arg in args:
            if isinstance(arg, str):
                self.toWrite += arg
            elif isinstance(arg, Reader):
                self.location = arg.location()
                self.toWrite += arg.code.text[arg.iChar:arg.iEnd]

    def indent(self):
        self.indentLevel += 1

    def undent(self):
        self.indentLevel -= 1
    
    def nextLine(self):
        self.code.pushLine((' '*(self.indentLevel*4)) + self.toWrite.strip(), self.location)
        self.toWrite = ""
        self.location = None

    def copy(self)-> 'Writer':
        newCode = copy.copy(self.code)
        newWriter = copy.copy(self)
        newWriter.code = newCode
        return newWriter
    
    def restore(self, writer: 'Writer'):
        self.code.text = writer.code.text
        self.code.map = writer.code.map
        self.indentLevel = writer.indentLevel
        self.toWrite = writer.toWrite
        self.location = writer.location

#----------------------------------------------------------------------------------------
# Error is a message and a SourceLocation

class Error:
    def __init__(self, message: str, reader: Reader):
        self.message = message
        self.location = reader.location()

    def __str__(self):
        return f"Error: {self.message} at {self.location}"
    
    def __repr__(self):
        return self.__str__()

def err(value):
    return isinstance(value, Error)

#----------------------------------------------------------------------------------------
# Executor is either a Parser or a Printer, or anything else we might think of

class Executor:
    def __init__(self):
        pass

#----------------------------------------------------------------------------------------
# Parser does parsing

class Parser(Executor):
    def __init__(self):
        pass

    def label(self, reader, ast, name: str, parserFn):
        ast = { "_type" : name }
        subAst = parserFn(self, reader, None)
        if err(subAst):
            return subAst
        ast.update(subAst)
        return ast

    def keyword(self, reader: Reader, ast, value: str) -> dict:
        reader.skipWhitespace()
        regex = re.escape(value)
        if reader.match(regex):
            reader.advance()
            return {}
        return Error(f"Expected keyword '{value}'", reader)

    def identifier(self, reader, ast) -> Reader:
        reader.skipWhitespace()
        if reader.match(r"[a-zA-Z_][a-zA-Z0-9_]*"):
            return reader.copyAndAdvance()
        return Error(f"Expected identifier", reader)

    def set(self, reader, ast, name: str, valueFn):
        ast = valueFn(self, reader, None)
        return { name : ast }

    def sequence(self, reader, ast, *parserFns):
        ast = {}
        for parserFn in parserFns:
            subAst = parserFn(self, reader, None)
            if err(subAst):
                return subAst
            ast.update(subAst)
        return ast
    
    def optional(self, reader, ast, parserFn):
        subAst = parserFn(self, reader, None)
        if err(subAst):
            return {}
        return subAst
    
    def indent(self, reader, ast):
        reader.skipWhitespace()
        return {}
    
    def undent(self, reader, ast):
        reader.skipWhitespace()
        return {}
    
    def list(self, reader : Reader, ast, parserFn):
        results = []
        safeCount = 1000
        while safeCount > 0:
            safeCount -= 1
            pos = reader.iChar
            result = parserFn(self, reader, None)
            if err(result):
                reader.restore(pos)
                break
            results.append(result)
            if safeCount==0:
                print("list: safeCount exceeded!")
                return results
        return results
    
    def anyof(self, reader, ast, *parserFns):
        reader.skipWhitespace()
        iChar = reader.iChar
        for parserFn in parserFns:
            reader.restore(iChar)
            subAst = parserFn(self, reader, None)
            if not err(subAst):
                return subAst
        return Error("Expected one of the alternatives", reader)
    
    def enum(self, reader, ast, *values):
        reader.skipWhitespace()
        iChar = reader.iChar
        for value in values:
            if reader.match(re.escape(value)):
                return reader.copyAndAdvance()
            else:
                reader.restore(reader.iChar)
        return Error(f"Expected one of {values}", reader)
    
    def toNextOuter(self, reader: Reader, ast, find: List[str], startDepth: int):
        reader.skipWhitespace()
        depth = startDepth
        inQuote = False
        iChar = reader.iChar
        i = reader.iChar
        while i < reader.iEnd:
            c = reader.char(i)
            if not inQuote:
                if depth == 0 and reader.match(re.escape(find), i):
                    return reader.copyAndAdvance(i)
                elif c in "{([":
                    depth += 1
                elif c in "})]":
                    depth -= 1
                elif c == '"':
                    inQuote = True
            else:
                if c == '"' and reader.char(i-1) != "\\":
                    inQuote = False
            i += 1
        return reader


#----------------------------------------------------------------------------------------
# Printer does printing

class Printer(Executor):
    def __init__(self): pass

    def label(self, writer, ast: dict, name: str, printerFn):
        if not "_type" in ast or ast["_type"] != name:
            return False
        return printerFn(self, writer, ast)

    def keyword(self, writer, ast: dict, value: str):
        writer.write(" " + value)
        return True

    def identifier(self, writer, ast):
        if isinstance(ast, Reader):
            writer.write(" ")
            writer.write(ast)
            return True
        else:
            return False
        
    def set(self, writer, ast: dict, name: str, printerFn):
        if not name in ast:
            return False
        return printerFn(self, writer, ast[name])

    def sequence(self, writer, ast: dict, *printerFns: List):
        for printerFn in printerFns:
            success = printerFn(self, writer, ast)
            if not success: 
                return False
        return True
    
    def optional(self, writer, ast: dict, printerFn):
        stored = writer.copy()
        success = printerFn(self, writer, ast)
        if not success:
            writer.restore(stored)
        return True
    
    def indent(self, writer, ast):
        writer.newLine()
        writer.indent()
        return True
    
    def undent(self, writer, ast):
        writer.newLine()
        writer.undent()
        return True
    
    def list(self, writer, ast, printerFn):
        if not isinstance(ast, list):
            return False
        for item in ast:
            printerFn(self, writer, item)
            writer.newLine()
        return True
    
    def anyof(self, writer, ast, *printerFns):
        stored = writer.copy()
        for printerFn in printerFns:
            if printerFn(self, writer, ast):
                return True
            writer.restore(stored)
        return False
    
    def enum(self, writer, ast, *values):
        if not isinstance(ast, Reader):
            return False
        writer.write(ast)
        return True
        

#----------------------------------------------------------------------------------------
# naked parsing functions

def label(value: str, fn):
    return lambda executor, reader, ast : executor.label(reader, ast, value, fn)

def keyword(value: str):
    return lambda executor, readerOrWriter, ast : executor.keyword(readerOrWriter, ast, value)

def identifier():
    return lambda executor, reader, ast : executor.identifier(reader, ast)

def set(key: str, fn):
    return lambda executor, readerOrWriter, ast : executor.set(readerOrWriter, ast, key, fn)

def sequence(*fns: List):
    return lambda executor, readerOrWriter, ast : executor.sequence(readerOrWriter, ast, *fns)

def optional(fn):
    return lambda executor, readerOrWriter, ast : executor.optional(readerOrWriter, ast, fn)

def indent():
    return lambda executor, readerOrWriter, ast : executor.indent(readerOrWriter, ast)

def undent():
    return lambda executor, readerOrWriter, ast : executor.undent(readerOrWriter, ast)

def list(fn):
    return lambda executor, readerOrWriter, ast : executor.list(readerOrWriter, ast, fn)

def anyof(*fns):
    return lambda executor, reader, ast : executor.anyof(reader, ast, *fns)

def enum(*values):
    return lambda executor, reader, ast : executor.enum(reader, ast, *values)

def toNextOuter(find: List[str], startDepth: int):
    return lambda executor, reader, ast : executor.toNextOuter(reader, ast, find, startDepth)
#----------------------------------------------------------------------------------------
