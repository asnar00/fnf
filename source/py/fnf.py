# ᕦ(ツ)ᕤ
# fnf.py
# we're going to do everything in one place

import os
from typing import List, Tuple
from threading import Thread
import subprocess
import datetime
import inspect

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
        log("\npassed:", sourcePos, "\n")
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

class SourceLocation:
    def __init__(self, path: str, line: int, column: int):
        self.path = path
        self.line = line
        self.column = column

class SourceMap:
    def __init__(self):
        self.map : List[Tuple[int, SourceLocation]] = []       # list of (int, SourceLocation) tuples

#---------------------------------------------------------------------------------
# Lex is a lexeme: a source file, plus a position and range

class Lex:
    def __init__(self, type: str, source: SourceFile, iStart: int, iEnd: int):
        self.type = type
        self.source = source
        self.iStart = iStart
        self.iEnd = iEnd

    def __str__(self):
        if self.type == 'indent': return "{indent}"
        elif self.type == 'undent': return "{undent}"
        return self.source.text[self.iStart:self.iEnd]
    
    def __repr__(self):
        return self.__str__()

# lexer takes source and turns it into a list of lexemes
# handles C-style ("{") or python-style (":") indentation
def lexer(source: SourceFile, indentChar='{') -> List[Lex]:
    i = 0
    safeCount = 10000
    out : List[Lex] = []
    inQuotes : bool = False
    whichQuote : str = ""
    iQuoteStart : int = 0
    punctuation = '[]():;,.'
    operators = '!@$%^&*-+=/?<>~'
    indentLevel = 0
    while i < len(source.text) and safeCount > 0:
        safeCount -= 1
        c = source.text[i]
        cp = source.text[i-1] if i > 0 else ""
        cn = source.text[i+1] if i < len(source.text) - 1 else ""
        if inQuotes:
            if c == whichQuote:
                if i > 0 and cp != '\\': 
                    out.append(Lex('quote', source, iQuoteStart, i+1))
                    inQuotes = False
        else:
            if c in '`\"\'':  # start of quotes
                inQuotes = True
                whichQuote = c
                iQuoteStart = i
            else:
                if c in punctuation: out.append(Lex('punct', source, i, i+1))
                elif c in operators: 
                    j = (i+2) if cn in operators else (i+1)
                    out.append(Lex('op', source, i, j))
                    i = j-1
                elif c.isalpha() or c == '_':
                    j = i+1
                    while j < len(source.text) and (source.text[j].isalnum() or source.text[j] == '_'):
                        j += 1
                    out.append(Lex('id', source, i, j))
                    i = j-1
                elif c.isdigit():
                    j = i+1
                    while j < len(source.text) and source.text[j].isdigit():
                        j += 1
                    out.append(Lex('num', source, i, j))
                    i = j-1
                else:
                    if indentChar == '{':
                        if c in ' \t\n\r': pass       # skip whitespace
                        elif c == '{': out.append(Lex('indent', source, i, i+1))
                        elif c == '}': out.append(Lex('undent', source, i, i+1))
                    else:
                        pass
        i = i + 1
    return out


test_code = """
feature Hello extends Feature {
    on hello(name: string) { 
        console.log(`Hello, ${name}!`);
    }
    replace main() {
        hello("world");
    }
}
"""

def test_lexer(source: SourceFile):
    log("test_lexer ----------------------------------------------------------")
    lexemes = lexer(source)
    out = """
        [feature, Hello, extends, Feature, {indent}, on, hello, (, name, :, string, ), {indent}, console, ., log, (, `Hello, ${name}!`, ), ;, {undent}, replace, main, (, ), {indent}, hello, (, "world", ), ;, {undent}, {undent}]
    """
    log_assert(out, lexemes)
    return lexemes

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
        if lex and str(lex) == word:
            reader.advance()
            return {}
        return Error(f"Expected '{word}'", reader)
    def print_keyword(writer: Writer, ast, word: str):
        writer.write(Lex('id', SourceFile(None, word), 0, len(word)))
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_keyword(x, word)
        else: return print_keyword(x, ast, word)
    return handler

# identifier: match and return if the next lex is alphanum (including '_')
def id():
    def parse_id(reader: Reader):
        lex = reader.peek()
        if lex and lex.type == 'id':
            reader.advance()
            return [lex]
        return Error("Expected an identifier", reader)
    def print_id(writer: Writer, ast):
        writer.write(ast[0])
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_id(x)
        else: return print_id(x, ast)
    return handler

# set: set key in AST to the result of fn
def set(name: str, fn):
    def parse_set(reader: Reader, name: str, parse_fn):
        ast = parse_fn(reader)
        if err(ast): return ast
        return { name : ast }
    def print_set(writer: Writer, ast, name: str, print_fn):
        if not (name in ast): return False
        return print_fn(writer, ast[name])
    def handler(x, ast=None):
        if is_reader(x): return parse_set(x, name, fn)
        else: return print_set(x, ast, name, fn)
    return handler

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
    def handler(x, ast=None):
        if is_reader(x): return parse_sequence(x, *parse_fns)
        else: return print_sequence(x, ast, *parse_fns)
    return handler

# label: set "_type" property of the AST to (type)
def label(type: str, fn):
    def parse_label(reader: Reader, type: str, parse_fn):
        ast = { '_type' : type }
        sub_ast = parse_fn(reader)
        if err(sub_ast): return sub_ast
        ast.update(sub_ast)
        return ast
    def print_label(writer: Writer, ast, type: str, print_fn):
        if not ('_type' in ast or ast['_type'] != type): return False
        return print_fn(writer, ast)
    def handler(x, ast=None):
        if is_reader(x): return parse_label(x, type, fn)
        else: return print_label(x, ast, type, fn)
    return handler

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
    def handler(x, ast=None):
        if is_reader(x): return parse_optional(x, fn)
        else: return print_optional(x, ast, fn)
    return handler

# indent: match if the next lex is an indent
def indent():
    def parse_indent(reader: Reader):
        lex = reader.peek()
        if lex and lex.type == 'indent':
            reader.advance()
            return {}
        return Error("Expected an indent", reader)
    def print_indent(writer: Writer, ast):
        writer.write(Lex('indent', SourceFile(None, "{"), 0, 1))
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_indent(x)
        else: return print_indent(x, ast)
    return handler

# undent: match if the next lex is an undent
def undent():
    def parse_undent(reader: Reader):
        lex = reader.peek()
        if lex and lex.type == 'undent':
            reader.advance()
            return {}
        return Error("Expected an undent", reader)
    def print_undent(writer: Writer, ast):
        writer.write(Lex('undent', SourceFile(None, "}"), 0, 1))
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_undent(x)
        else: return print_undent(x, ast)
    return handler

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
    def handler(x, ast=None):
        if is_reader(x): return parse_list(x, fn)
        else: return print_list(x, ast, fn)
    return handler

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
            iLex = writer.i
            if print_fn(writer, ast): return True
            writer.i = iLex
        return False
    def handler(x, ast=None):
        if is_reader(x): return parse_anyof(x, *fns)
        else: return print_anyof(x, ast, *fns)
    return handler

# match any of the given words (like keyword), return it
def enum(*words):
    def parse_enum(reader: Reader, *words):
        lex = reader.peek()
        if lex and lex.type == 'id' and str(lex) in words:
            reader.advance()
            return [lex]
        return Error(f"Expected one of {words}", reader)
    def print_enum(writer: Writer, ast, *words):
        writer.write(ast[0])
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_enum(x, *words)
        else: return print_enum(x, ast, *words)
    return handler

# match up one of (words), but only if not inside braces/brackets/parens
def upto(words: List[str]):
    def parse_upto(reader: Reader, words):
        depth = 0
        out = []
        while True:
            lex = reader.peek()
            if not lex: break
            if depth ==0 and str(lex) in words: 
                return out
            out.append(lex)
            if str(lex) in "([" or lex.type == 'indent': depth += 1
            elif str(lex) in ")]" or lex.type == 'undent': depth -= 1
            reader.advance()
    def print_upto(writer: Writer, ast, words):
        for lex in ast:
            writer.write(lex)
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_upto(x, words)
        else: return print_upto(x, ast, words)
    return handler

# match everything up to a certain type, but only if not inside braces/brackets/parens
def uptoType(type: str):
    def parse_uptoType(reader: Reader, type):
        depth = 0
        out = []
        while True:
            lex = reader.peek()
            if not lex: break
            if depth ==0 and lex.type == type:
                return out
            out.append(lex)
            if str(lex) in "([" or lex.type == 'indent': depth += 1
            elif str(lex) in ")]" or lex.type == 'undent': depth -= 1
            reader.advance()
    def print_uptoType(writer: Writer, ast, words):
        for lex in ast:
            writer.write(lex)
        return True
    def handler(x, ast=None):
        if is_reader(x): return parse_uptoType(x, type)
        else: return print_uptoType(x, ast, type)
    return handler

#---------------------------------------------------------------------------------
# Languages

class Language:
    pass

class Typescript(Language):
    def feature(self):
        return label("feature", 
            sequence(
                keyword('feature'), set('name', id()),
                optional(sequence(keyword('extends'), set('parent', id()))),
                indent(),
                set("components", list(self.function())),
                undent()
            ))
    def function(self):
        return label("function",
            sequence(
                set('modifier', enum('on', 'replace', 'after', 'before')),
                set('name', id()),
                keyword("("),
                set("parameters", list(self.parameter())),
                keyword(")"),
                optional(sequence(keyword(":"), set("returnType", uptoType("indent")))),
                indent(),
                set("body", uptoType("undent")),
                undent()
            ))
    def parameter(self):
        return sequence(
                set('name', id()),
                optional(sequence(keyword(':'), set('type', id()))),
                optional(sequence(keyword('='), set('default', upto([',',')',';']))))
                )
    def struct(self):
        return label("struct",
            sequence(
                enum('struct', 'extend'), set('name', id()),
                keyword("{"),
                set("properties", list(sequence(self.parameter(), keyword(";")))),
                keyword("}")
            ))
    def variable(self):
        return label("variable",
            sequence(
                keyword('local'),
                self.parameter()
            ))


def test_parser(lexemes: List[Lex]):
    log("\ntest_parser ---------------------------------------------------------")
    reader = Reader(lexemes)
    parser = Typescript().feature()
    test_ast = """
        {'_type': 'feature', 'name': [Hello], 'parent': [Feature], 'components': [{'_type': 'function', 'modifier': [on], 'name': [hello], 'parameters': [{'name': [name], 'type': [string]}], 'body': [console, ., log, (, `Hello, ${name}!`, ), ;]}, {'_type': 'function', 'modifier': [replace], 'name': [main], 'parameters': [], 'body': [hello, (, "world", ), ;]}]}
        """
    ast = parser(reader)
    log_assert(test_ast, ast)
    if err(ast): return
    test_ls = """
        [feature, Hello, extends, Feature]
    """
    writer = Writer()
    success = parser(writer, ast)
    print("")
    test_printer = """
        [feature, Hello, extends, Feature, {indent}, on, hello, (, name, :, string, ), {indent}, console, ., log, (, `Hello, ${name}!`, ), ;, {undent}, replace, main, (, ), {indent}, hello, (, "world", ), ;, {undent}, {undent}]
    """
    log_assert(test_printer, writer.lexemes)

#---------------------------------------------------------------------------------
# test!

def test():
    log_enable()
    source = SourceFile(None, test_code)
    log(source.text)
    lexemes = test_lexer(source)
    ast = test_parser(lexemes)

#---------------------------------------------------------------------------------
if __name__ == "__main__":
    clear_console()
    print("-----------------------------------------------------------")
    print("ᕦ(ツ)ᕤ fnf.py")
    test()
    print("done.")