# ᕦ(ツ)ᕤ
# fnf.py
# we're going to do everything in one place

import os
from typing import List, Tuple
from threading import Thread
import subprocess
import datetime
import inspect
import os
import sys
import json
import subprocess
import re
import requests
import shutil
import traceback

#--------------------------------------------------------------------------------------------------
# logging

global log_enabled
log_enabled: bool = False

def log_enable():
    global log_enabled
    log_enabled = True

def log_disable():
    global log_enabled
    log_enabled = False

def log(*args):
    global log_enabled
    if log_enabled:
        print(*args)

def log_assert(check_against, *args):
    # print the file/line of the caller fn
    frame = inspect.currentframe()
    frame = inspect.getouterframes(frame)[1]
    sourcePos = f"{"/".join(frame.filename.split("/")[-3:])}:{frame.lineno} "
    # print the args to a string
    s = " ".join([str(arg) for arg in args])
    if s == check_against.strip():
        print("passed:", sourcePos)
        log(s)
    else:
        print("\nFAILED!", sourcePos, "\n")
        print(s)

def log_c(*args):
    if log_enabled:
        print(*args, end="")

def clear_console():
    os.system('clear')  # For Linux/macOS

#--------------------------------------------------------------------------------------------------------------------------
# file system low-level

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

def scanFolder(folder, ext: str) -> List[str]:
    cwd = currentWorkingDirectory()
    filesFound = []
    for root, dirs, files in os.walk(folder):
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

#---------------------------------------------------------------------------------
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

#---------------------------------------------------------------------------------
# files and stuff

class SourceFile:
    def __init__(self, path: str, text: str=""):
        self.path = path
        self.text = readTextFile(path) if path else text.strip()

    def numberedText(self):
        lines = self.text.split('\n')
        out = ""
        for i in range(0, len(lines)):
            out += f"{i+1:3} {lines[i]}\n"
        return out

class SourceLocation:
    def __init__(self, path: str, line: int, column: int):
        self.path = path
        self.line = line
        self.column = column

class SourceRange:
    def __init__(self, source: SourceFile, iStart: int =0, iEnd: int=None):
        self.source = source
        self.iStart = iStart
        self.iEnd = iEnd if iEnd else len(source.text)

    def __str__(self):
        return "\n" + self.source.text[self.iStart:self.iEnd] + "\n"
    
    def __repr__(self):
        return self.__str__()

#---------------------------------------------------------------------------------
# Lex is a lexeme: a source file, plus a position and range

class Lex:
    def __init__(self, source: SourceFile, iStart: int, iEnd: int, val: str=None):
        self.source = source
        self.iStart = iStart
        self.iEnd = iEnd
        self.val = val if val else source.text[iStart:iEnd]

    def __str__(self):
        return self.val
    
    def __repr__(self):
        return self.__str__()
    
    def is_id(self):
        return self.val[0].isalpha() or self.val[0] == '_'

# lexer takes source range and turns it into a list of lexemes
# handles C-style ("{") or python-style (":") indentation
def lexer(ranges: SourceRange, indentChar='{') -> List[Lex]:
    safeCount = 10000
    out : List[Lex] = []
    inQuotes : bool = False
    whichQuote : str = ""
    iQuoteStart : int = 0
    punctuation = '[]():;,.'
    operators = '!@$%^&*-+=/?<>~'
    indentLevel = 0
    startOfLine = True
    lineIndentLevel = 0
    for range in ranges:
        i = range.iStart
        while i < range.iEnd and safeCount > 0:
            safeCount -= 1
            c = range.source.text[i]
            cp = range.source.text[i-1] if i > 0 else ""
            cn = range.source.text[i+1] if i < range.iEnd - 1 else ""
            if inQuotes:
                if c == whichQuote:
                    if i > 0 and cp != '\\': 
                        out.append(Lex(range.source, iQuoteStart, i+1))
                        inQuotes = False
            else:
                if c in '`\"\'':  # start of quotes
                    inQuotes = True
                    whichQuote = c
                    iQuoteStart = i
                else:
                    if c != ' ': startOfLine = False
                    if c in punctuation: out.append(Lex(range.source, i, i+1))
                    elif c in operators: 
                        j = (i+2) if cn in operators else (i+1)
                        out.append(Lex(range.source, i, j))
                        i = j-1
                    elif c.isalpha() or c == '_':
                        j = i+1
                        while j < range.iEnd and (range.source.text[j].isalnum() or range.source.text[j] == '_'):
                            j += 1
                        out.append(Lex(range.source, i, j))
                        i = j-1
                    elif c.isdigit():
                        j = i+1
                        while j < range.iEnd and range.source.text[j].isdigit():
                            j += 1
                        out.append(Lex(range.source, i, j))
                        i = j-1
                    else:
                        if indentChar == '{':
                            if c in ' \t\n\r': pass       # skip whitespace
                            elif c == '{': out.append(Lex(range.source, i, i+1, '{indent}'))
                            elif c == '}': out.append(Lex(range.source, i, i+1, '{undent}'))
                        elif indentChar == ":":
                            if c != ' ': 
                                startOfLine = False
                            if c == '\n':
                                startOfLine = True
                                i = i + 1
                            if startOfLine:
                                j = i
                                while j < range.iEnd and range.source.text[j] == ' ':
                                    j += 1
                                startOfLine = False
                                indentLevel = (j - i) // 4
                                if lineIndentLevel != -1:
                                    if len(out) > 0 and str(out[-1]) == ":": 
                                        out.pop()
                                    if indentLevel > lineIndentLevel:
                                        out.append(Lex(range.source, i, j, '{indent}'))
                                    elif indentLevel < lineIndentLevel:
                                        out.append(Lex(range.source, i, j, '{undent}'))
                                    elif indentLevel == lineIndentLevel:
                                        out.append(Lex(range.source, i, j, '{newline}'))
                                lineIndentLevel = indentLevel
                                startOfLine = False
                                i = j - 1    
            i = i + 1
    return out

#---------------------------------------------------------------------------------
# parse/print helpers

# Reader reads forward in a lexeme-list
class Reader:
    def __init__(self, lexemes: List[Lex]):
        self.lexemes = lexemes
        self.i = 0

    def peek(self) -> Lex:
        return self.lexemes[self.i] if self.i < len(self.lexemes) else None
    
    def advance(self):
        self.i += 1

    def location(self, iLex: int=None) -> str:
        if iLex is None: iLex = self.i
        if iLex >= len(self.lexemes): return "EOF"
        lex = self.lexemes[iLex]
        path = lex.source.path if lex.source and lex.source.path else ""
        line = 1
        iCr = 0
        if lex.source:
            for i in range(0, lex.iStart):
                if lex.source.text[i] == '\n': 
                    iCr = i
                    line += 1
        return f"{path}:{line}:{lex.iStart - iCr}"

# Writer writes into a List[Lex]
class Writer:
    def __init__(self):
        self.lexemes = []

    def write(self, lex: Lex):
        self.lexemes.append(lex)

def is_reader(obj):
    return isinstance(obj, Reader)

# Error just holds a message and a point in the source file
class Error:
    def __init__(self, message: str, reader: Reader):
        self.message = message
        self.reader = reader
        self.iLex = reader.i
        log(self)

    def __str__(self):
        loc = self.reader.location(self.iLex)
        val = self.reader.lexemes[self.iLex] if self.iLex < len(self.reader.lexemes) else "eof"
        return f"Error: {self.message} at {loc} ('{val}')"

# quick fn to determine if an object is an error
def err(obj) -> bool:
    is_err = isinstance(obj, Error)
    #if is_err: log(obj)
    return is_err

#---------------------------------------------------------------------------------
# parse and print using human-readable parser structures

# keyword: match if this precise word appears next
def keyword(word: str):
    def parse_keyword(reader: Reader, word: str):
        lex = reader.peek()
        if lex == None and word in ['{newline}', '{undent}']: return {} # special case for premature eof
        if lex and str(lex) == word:
            reader.advance()
            return {}
        return Error(f"Expected '{word}'", reader)
    def print_keyword(writer: Writer, ast, word: str):
        writer.write(Lex(SourceFile(None, word), 0, len(word)))
        return True
    def despatch_keyword(x, ast=None):
        if is_reader(x): return parse_keyword(x, word)
        else: return print_keyword(x, ast, word)
    return despatch_keyword

# identifier: match and return if the next lex is alphanum (including '_')
def id():
    def parse_id(reader: Reader):
        lex = reader.peek()
        if lex and lex.is_id():
            reader.advance()
            return [lex]
        return Error("Expected an identifier", reader)
    def print_id(writer: Writer, ast):
        writer.write(ast[0])
        return True
    def despatch_id(x, ast=None):
        if is_reader(x): return parse_id(x)
        else: return print_id(x, ast)
    return despatch_id

# set: set key in AST to the result of fn
def set(name: str, fn):
    def parse_set(reader: Reader, name: str, parse_fn):
        ast = parse_fn(reader)
        if err(ast): return ast
        log("set(", name, "):", ast)
        return { name : ast }
    def print_set(writer: Writer, ast, name: str, print_fn):
        if not (name in ast): return False
        return print_fn(writer, ast[name])
    def despatch_set(x, ast=None):
        if is_reader(x): return parse_set(x, name, fn)
        else: return print_set(x, ast, name, fn)
    return despatch_set

# sequence: match a sequence of parsers
def sequence(*parse_fns):
    def parse_sequence(reader: Reader, *parse_fns):
        ast = {}
        for parse_fn in parse_fns:
            result = parse_fn(reader)
            if err(result): return result
            ast.update(result)
        return ast
    def print_sequence(writer: Writer, ast, *print_fns):
        for print_fn in print_fns:
            if not print_fn(writer, ast): return False
        return True
    def despatch_sequence(x, ast=None):
        if is_reader(x): return parse_sequence(x, *parse_fns)
        else: return print_sequence(x, ast, *parse_fns)
    return despatch_sequence

# label: set "_type" property of the AST to (type)
def label(type: str, fn):
    def parse_label(reader: Reader, type: str, parse_fn):
        ast = { '_type' : type }
        sub_ast = parse_fn(reader)
        if err(sub_ast): return sub_ast
        log("label(", type, "): ", sub_ast)
        ast.update(sub_ast)
        return ast
    def print_label(writer: Writer, ast, type: str, print_fn):
        if not ('_type' in ast or ast['_type'] != type): return False
        return print_fn(writer, ast)
    def despatch_label(x, ast=None):
        if is_reader(x): return parse_label(x, type, fn)
        else: return print_label(x, ast, type, fn)
    return despatch_label

# optional: match if the parser matches, or skip if it doesn't
def optional(fn):
    def parse_optional(reader: Reader, parse_fn):
        iLex = reader.i
        ast = parse_fn(reader)
        if err(ast):
            if ast.iLex == iLex: return {}
            return ast
        return ast
    def print_optional(writer: Writer, ast, print_fn):
        length = len(writer.lexemes)
        success = print_fn(writer, ast)
        if not success:
            writer.lexemes = writer.lexemes[:length]
        return True
    def despatch_optional(x, ast=None):
        if is_reader(x): return parse_optional(x, fn)
        else: return print_optional(x, ast, fn)
    return despatch_optional

# match zero or more occurrences of (fn)
def list(fn):
    def parse_list(reader: Reader, parse_fn):
        ast = []
        while True:
            sub_ast = parse_fn(reader)
            if err(sub_ast): break
            ast.append(sub_ast)
        return ast
    def print_list(writer: Writer, ast, print_fn):
        for sub_ast in ast:
            if not print_fn(writer, sub_ast): return False
        return True
    def despatch_list(x, ast=None):
        if is_reader(x): return parse_list(x, fn)
        else: return print_list(x, ast, fn)
    return despatch_list

# match zero or more occurrences of (fn) separated by (sep) [internally only]
def list_separated(fn, sep: str):
    def parse_list_separated(reader: Reader, parse_fn, sep):
        ast = []
        while True:
            sub_ast = parse_fn(reader)
            if err(sub_ast): break
            ast.append(sub_ast)
            next = reader.peek()
            if not next or str(next) != sep: 
                break
            else:
                reader.advance()
        return ast
    def print_list_separated(writer: Writer, ast, print_fn, sep: str):
        for sub_ast in ast:
            if not print_fn(writer, sub_ast): return False
            writer.write(Lex(SourceFile(None, sep), 0, len(sep)))
        return True
    def despatch_list_separated(x, ast=None):
        if is_reader(x): return parse_list_separated(x, fn, sep)
        else: return print_list_separated(x, ast, fn, sep)
    return despatch_list_separated

# match any of the given fns
def anyof(*fns):
    def parse_anyof(reader: Reader, *parse_fns):
        for parse_fn in parse_fns:
            iLex = reader.i
            ast = parse_fn(reader)
            if not err(ast): return ast
            reader.i = iLex
        return Error("Expected one of the options", reader)
    def print_anyof(writer: Writer, ast, *print_fns):
        for print_fn in print_fns:
            iLex = len(writer.lexemes)
            if print_fn(writer, ast): return True
            writer.lexemes = writer.lexemes[:iLex]
        return False
    def despatch_anyof(x, ast=None):
        if is_reader(x): return parse_anyof(x, *fns)
        else: return print_anyof(x, ast, *fns)
    return despatch_anyof

# match any of the given words (like keyword), return it
def enum(*words):
    def parse_enum(reader: Reader, *words):
        lex = reader.peek()
        if lex and str(lex) in words:
            reader.advance()
            return [lex]
        return Error(f"Expected one of {words}", reader)
    def print_enum(writer: Writer, ast, *words):
        writer.write(ast[0])
        return True
    def despatch_enum(x, ast=None):
        if is_reader(x): return parse_enum(x, *words)
        else: return print_enum(x, ast, *words)
    return despatch_enum

# match up one of (words), but only if not inside braces/brackets/parens
def upto(words : List[str]):
    def parse_upto(reader: Reader, words):
        depth = 0
        out = []
        while True:
            lex = reader.peek()
            if not lex: return out
            if depth ==0 and str(lex) in words: 
                return out
            out.append(lex)
            if str(lex) in ["(", "[", "{indent}"]: depth += 1
            elif str(lex) in [")", "]", "{undent}"]: depth -= 1
            reader.advance()
    def print_upto(writer: Writer, ast, words):
        for lex in ast:
            writer.write(lex)
        return True
    def despatch_upto(x, ast=None):
        if is_reader(x): return parse_upto(x, words)
        else: return print_upto(x, ast, words)
    return despatch_upto

# debug: turns on logging for the sub-parser
def debug(fn):
    def parse_debug(reader: Reader, parse_fn):
        log_enable()
        result = parse_fn(reader)
        log_disable()
        return result
    def print_debug(writer: Writer, ast, print_fn):
        log_enable()
        result = print_fn(writer, ast)
        log_disable()
        return result
    def despatch_debug(x, ast=None):
        if is_reader(x): return parse_debug(x, fn)
        else: return print_debug(x, ast, fn)
    return despatch_debug

def indent(): return keyword('{indent}')
def undent(): return keyword('{undent}')
def newline(): return keyword('{newline}')

#---------------------------------------------------------------------------------
# Language base class and common parser structures

class Language:
    def ext(self): pass
    def indentChar(self): pass
    @staticmethod
    def find(ext: str):
        for subclass in Language.__subclasses__():
            if subclass().ext() == ext:
                return subclass()
        return None

def feature(lang : Language):
    return label("feature", 
        sequence(
            keyword('feature'), set('name', id()),
            optional(sequence(keyword('extends'), set('parent', id()))),
            indent(),
            set("components", list(component(lang))),
            undent()))

def component(lang : Language):
    return anyof(function(lang), struct(lang), variable(lang))

def function(lang : Language):
    return label("function",
            sequence(
                set('modifier', enum('on', 'replace', 'after', 'before')),
                lang.function_signature(),
                indent(),
                set("body", upto(['{undent}'])),
                undent()))

def struct(lang : Language):
    return label("struct",
            sequence(
                set('modifier', enum('struct', 'extend')),
                set('name', id()),
                indent(),
                set("properties", list_separated(lang.parameter(), lang.decl_separator())),
                undent()))

def variable(lang : Language):
    return label("variable",
            sequence(
                keyword("local"),
                lang.parameter(),
                keyword(lang.decl_separator())))

#---------------------------------------------------------------------------------
# test code, lexemes, ast and printed output for typescript

# parsers for typescript-specific things
class Typescript(Language):
    def ext(self): return "ts"
    def indentChar(self): return "{"
    def decl_separator(self): return ";"
    def function_signature(self):
        return sequence(
            set('name', id()),
            keyword("("),
            set("parameters", list(self.parameter())),
            keyword(")"),
            optional(sequence(keyword(":"), set("returnType", upto(['{indent}']))))
        )
    def parameter(self):
        return sequence(
            set('name', id()),
            optional(sequence(keyword(':'), set('type', id()))),
            optional(sequence(keyword('='), set('default', upto([',',')',';']))))
        )

# test code and expected outputs
test_code_ts = """
feature Hello extends Feature {
    on hello(name: string) : number { 
        console.log(`Hello, ${name}!`);
        return 0;
    }
    replace main() : number {
        return hello("world");
    }
    struct Colour {
        red: number = 0;
        green: number = 0;
        blue: number = 0;
    }
    local colour: Colour = new Colour(1, 1, 1);
}
"""

lexemes_ts = """
[feature, Hello, extends, Feature, {indent}, on, hello, (, name, :, string, ), :, number, {indent}, console, ., log, (, `Hello, ${name}!`, ), ;, return, 0, ;, {undent}, replace, main, (, ), :, number, {indent}, return, hello, (, "world", ), ;, {undent}, struct, Colour, {indent}, red, :, number, =, 0, ;, green, :, number, =, 0, ;, blue, :, number, =, 0, ;, {undent}, local, colour, :, Colour, =, new, Colour, (, 1, ,, 1, ,, 1, ), ;, {undent}]
"""

ast_ts = """
{'_type': 'feature', 'name': [Hello], 'parent': [Feature], 'components': [{'_type': 'function', 'modifier': [on], 'name': [hello], 'parameters': [{'name': [name], 'type': [string]}], 'returnType': [number], 'body': [console, ., log, (, `Hello, ${name}!`, ), ;, return, 0, ;]}, {'_type': 'function', 'modifier': [replace], 'name': [main], 'parameters': [], 'returnType': [number], 'body': [return, hello, (, "world", ), ;]}, {'_type': 'struct', 'modifier': [struct], 'name': [Colour], 'properties': [{'name': [red], 'type': [number], 'default': [0]}, {'name': [green], 'type': [number], 'default': [0]}, {'name': [blue], 'type': [number], 'default': [0]}]}, {'_type': 'variable', 'name': [colour], 'type': [Colour], 'default': [new, Colour, (, 1, ,, 1, ,, 1, )]}]}
"""

print_ts = """
[feature, Hello, extends, Feature, {indent}, on, hello, (, name, :, string, ), :, number, {indent}, console, ., log, (, `Hello, ${name}!`, ), ;, return, 0, ;, {undent}, replace, main, (, ), :, number, {indent}, return, hello, (, "world", ), ;, {undent}, struct, Colour, {indent}, red, :, number, =, 0, ;, green, :, number, =, 0, ;, blue, :, number, =, 0, ;, {undent}, local, colour, :, Colour, =, new, Colour, (, 1, ,, 1, ,, 1, ), ;, {undent}]
"""

#---------------------------------------------------------------------------------
# language definition, test code and expected outputs for python

class Python(Language):
    def ext(self): return "py"
    def indentChar(self): return ":"
    def decl_separator(self): return "{newline}"
    def function_signature(self):
        return sequence(
            set('name', id()),
            keyword("("),
            set("parameters", list(self.parameter())),
            keyword(")"),
            optional(sequence(keyword("->"), set("returnType", id())))
        )
    def parameter(self):
        return sequence(
            set('name', id()),
            optional(sequence(keyword(':'), set('type', id()))),
            optional(sequence(keyword('='), set('default', upto(["{newline}", "{undent}"]))))
        )

test_code_py = """
feature Hello extends Feature:
    on hello(name: string) -> int:
        print(f"Hello, {name}!")
        return 0
    replace main() -> int:
        return hello("world")
    struct Colour:
        red: int = 0
        green: int = 0
        blue: int = 0
    local colour: Colour = Colour(1, 1, 1)
"""
lexemes_py = """
[feature, Hello, extends, Feature, {indent}, on, hello, (, name, :, string, ), ->, int, {indent}, print, (, f, "Hello, {name}!", ), {newline}, return, 0, {undent}, replace, main, (, ), ->, int, {indent}, return, hello, (, "world", ), {undent}, struct, Colour, {indent}, red, :, int, =, 0, {newline}, green, :, int, =, 0, {newline}, blue, :, int, =, 0, {undent}, local, colour, :, Colour, =, Colour, (, 1, ,, 1, ,, 1, )]
"""
ast_py = """
{'_type': 'feature', 'name': [Hello], 'parent': [Feature], 'components': [{'_type': 'function', 'modifier': [on], 'name': [hello], 'parameters': [{'name': [name], 'type': [string]}], 'returnType': [int], 'body': [print, (, f, "Hello, {name}!", ), {newline}, return, 0]}, {'_type': 'function', 'modifier': [replace], 'name': [main], 'parameters': [], 'returnType': [int], 'body': [return, hello, (, "world", )]}, {'_type': 'struct', 'modifier': [struct], 'name': [Colour], 'properties': [{'name': [red], 'type': [int], 'default': [0]}, {'name': [green], 'type': [int], 'default': [0]}, {'name': [blue], 'type': [int], 'default': [0]}]}, {'_type': 'variable', 'name': [colour], 'type': [Colour], 'default': [Colour, (, 1, ,, 1, ,, 1, )]}]}
"""
print_py = """
[feature, Hello, extends, Feature, {indent}, on, hello, (, name, :, string, ), ->, int, {indent}, print, (, f, "Hello, {name}!", ), {newline}, return, 0, {undent}, replace, main, (, ), ->, int, {indent}, return, hello, (, "world", ), {undent}, struct, Colour, {indent}, red, :, int, =, 0, {newline}, green, :, int, =, 0, {newline}, blue, :, int, =, 0, {newline}, {undent}, local, colour, :, Colour, =, Colour, (, 1, ,, 1, ,, 1, ), {newline}, {undent}]
"""
#---------------------------------------------------------------------------------
# test code and expected outputs for C

class C(Language):
    def ext(self): return "c"
    def indentChar(self): return "{"
    def decl_separator(self): return ";"
    def function_signature(self):
        return sequence(
            set('returnType', id()),
            set('name', id()),
            keyword("("),
            set("parameters", list(self.parameter())),
            keyword(")")
        )
    def parameter(self):
        return sequence(
            set('type', id()),
            set('name', id()),
            optional(sequence(keyword('='), set('default', upto([',',')',';']))))
        )
    
test_code_c = """
feature Hello extends Feature {
    on int hello(string name) { 
        printf("Hello, %s!", name);
        return 0;
    }
    replace int main() {
        return hello("world");
    }
    struct Colour {
        int red = 0;
        int green = 0;
        int blue = 0;
    }
    local Colour colour = Colour(1, 1, 1);
}
"""

lexemes_c = """
[feature, Hello, extends, Feature, {indent}, on, int, hello, (, string, name, ), {indent}, printf, (, "Hello, %s!", ,, name, ), ;, return, 0, ;, {undent}, replace, int, main, (, ), {indent}, return, hello, (, "world", ), ;, {undent}, struct, Colour, {indent}, int, red, =, 0, ;, int, green, =, 0, ;, int, blue, =, 0, ;, {undent}, local, Colour, colour, =, Colour, (, 1, ,, 1, ,, 1, ), ;, {undent}]
"""

ast_c = """
{'_type': 'feature', 'name': [Hello], 'parent': [Feature], 'components': [{'_type': 'function', 'modifier': [on], 'returnType': [int], 'name': [hello], 'parameters': [{'type': [string], 'name': [name]}], 'body': [printf, (, "Hello, %s!", ,, name, ), ;, return, 0, ;]}, {'_type': 'function', 'modifier': [replace], 'returnType': [int], 'name': [main], 'parameters': [], 'body': [return, hello, (, "world", ), ;]}, {'_type': 'struct', 'modifier': [struct], 'name': [Colour], 'properties': [{'type': [int], 'name': [red], 'default': [0]}, {'type': [int], 'name': [green], 'default': [0]}, {'type': [int], 'name': [blue], 'default': [0]}]}, {'_type': 'variable', 'type': [Colour], 'name': [colour], 'default': [Colour, (, 1, ,, 1, ,, 1, )]}]}
"""

print_c = """
[feature, Hello, extends, Feature, {indent}, on, int, hello, (, string, name, ), {indent}, printf, (, "Hello, %s!", ,, name, ), ;, return, 0, ;, {undent}, replace, int, main, (, ), {indent}, return, hello, (, "world", ), ;, {undent}, struct, Colour, {indent}, int, red, =, 0, ;, int, green, =, 0, ;, int, blue, =, 0, ;, {undent}, local, Colour, colour, =, Colour, (, 1, ,, 1, ,, 1, ), ;, {undent}]
"""

#---------------------------------------------------------------------------------
# extract code from markdown file

def extractCode(source: SourceFile) -> List[SourceRange]:
    ranges = []
    inTripleQuoteBlock = False
    inTabbedBlock = False
    iChar = 0
    lines = source.text.split('\n')[:-1]
    for line in lines:
        if not (inTripleQuoteBlock or inTabbedBlock):
            if line.startswith("```"):
                inTripleQuoteBlock = True
                ranges.append(SourceRange(source, iChar + len(line) + 1))
            elif line.startswith("    "):
                inTabbedBlock = True
                ranges.append(SourceRange(source, iChar))
        elif inTripleQuoteBlock:
            if line.startswith("```"):
                inTripleQuoteBlock = False
                ranges[-1].iEnd = iChar-1
        elif inTabbedBlock:
            if not line.startswith("    "):
                inTabbedBlock = False
                ranges[-1].iEnd = iChar-1
        iChar += len(line) + 1
    return ranges

test_md = """
# Hello

This is a test markdown file containing two kinds of code snippets:

```ts
feature Hello extends Feature {
    on hello() {
        print("hello world");
    }
```

and tabbed code:

    on print(msg: string) {
        console.log(msg);
    }

And that's it! 
"""

expected_ranges = """
[
feature Hello extends Feature {
    on hello() {
        print("hello world");
    }
, 
    on print(msg: string) {
        console.log(msg);
    }
]
"""

#---------------------------------------------------------------------------------
# Feature collects source, code, lexemes, ast for a particular sourcefile

class Feature:
    def __init__(self, source: SourceFile):
        self.source = source
        self.language = self.findLanguage(source.path)

    def findLanguage(self, path: str):
        filename = os.path.basename(path)
        parts = filename.split('.')
        ext = parts[2] if len(parts) > 2 else ""
        return Language.find(ext)

    def parse(self):
        self.ranges = extractCode(self.source)
        self.lexemes = lexer(self.ranges, self.language.indentChar())
        reader = Reader(self.lexemes)
        parser = feature(self.language)
        self.ast = parser(reader)

#---------------------------------------------------------------------------------
# Context is a list of features that gets built and run

class Context:
    def __init__(self, features: List[Feature]):
        self.features = features
        self.compose()

    def compose(self):
        self.functions = {} # name -> array of subfunctions
        self.structs = {} # name -> array of sub-structs
        self.variables = {} # name -> array of variables

        for feature in self.features:
            feature.parse()

    
#---------------------------------------------------------------------------------
# test routines

def test_extract():
    print("\ntest_extract -------------------------------------------------\n")
    source = SourceFile(None, test_md)
    ranges = extractCode(source)
    log_assert(expected_ranges, ranges)

def test_parser(language: Language, test_code, expected_lexemes, expected_ast, expected_print):
    print(f"\ntest_parser ({language.__class__.__name__}) -------------------------------------------------\n")
    source = SourceFile(None, test_code)
    range = SourceRange(source)
    log(source.numberedText())
    log_disable()
    parser = feature(language)
    lexemes = lexer([range], language.indentChar())
    log_assert(expected_lexemes, lexemes)
    reader = Reader(lexemes)
    ast = parser(reader)
    log_assert(expected_ast, ast)
    if err(ast): return
    writer = Writer()
    success = parser(writer, ast)
    log_assert(expected_print, writer.lexemes)

test_folder = "source/test"
expected_files = """
['source/test/Hello.fnf.ts.md', 'source/test/Hello/Goodbye.fnf.ts.md', 'source/test/Hello/Countdown.fnf.ts.md']
"""

def test_context():
    print("\ntest_context -------------------------------------------------\n")
    markdown_files = scanFolder(test_folder, ".md")
    log_assert(expected_files, markdown_files)
    sourceFiles = [SourceFile(file) for file in markdown_files]
    features = [Feature(sourceFile) for sourceFile in sourceFiles]
    context = Context(features)
    context.compose()

#---------------------------------------------------------------------------------
# test!

def test():
    test_parser(Typescript(), test_code_ts, lexemes_ts, ast_ts, print_ts)
    test_parser(Python(), test_code_py, lexemes_py, ast_py, print_py)
    test_parser(C(), test_code_c, lexemes_c, ast_c, print_c)
    test_extract()
    test_context()

#---------------------------------------------------------------------------------
if __name__ == "__main__":
    clear_console()
    print("-----------------------------------------------------------")
    print("ᕦ(ツ)ᕤ fnf.py")
    test()
    print("done.")