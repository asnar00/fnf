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
# parser mechanics: rules and things

# Source is a string, an index, and an end index
class Source:
    def __init__(self, text: str, start: int=0, end: int=None):
        self.text = text
        self.start = start
        self.end = end if end is not None else len(text)

    def set(self, start: int, end: int):
        self.start = start
        self.end = end

    def __str__(self):
        return self.text[self.start:self.end]

def isWhitespace(c: str):
    return c in " \t\n\r"

# skipWhitespace returns the index of the next non-whitespace character
def skipWhitespace(source: Source):
    while source.start < source.end and isWhitespace(source.text[source.start]):
        source.start += 1
    
# literal(value) checks if the source starts with the value, and if so, returns the value
def literal(value: str):
    def parse_literal(source: Source, value: str):
        log(f'parse_literal({value}) on "{source.text[source.start:source.end]})"')
        skipWhitespace(source)
        pos = source.start
        if source.text.startswith(value, source.start):
            source.start += len(value)
            return {}
        return None
    return lambda source: parse_literal(source, value)

# word() returns a function that takes source, and returns the first alphanumeric word
def word():
    def parse_word(source: Source):
        skipWhitespace(source)
        log(f'parse_word on "{source.text[source.start:source.end]}"')
        pos = source.start
        i = source.start
        while i < source.end and source.text[i].isalnum():
            i += 1
        if i > source.start:
            word = source.text[source.start:i]
            if word in ["const", "var", "struct", "extend", "feature", "extends", 
                        "on", "after", "before", "replace"]:
                return None
            source.start = i
            return { "_val": word, "_pos": pos }
        return None
    return lambda source: parse_word(source)

# set(varname, parserFn) just calls parserFn, and sets the result to varname
def set(varname: str, parserFn):
    def parse_set(varname: str, parserFn, source: Source):
        result = parserFn(source)
        if result is None:
            return None
        if isinstance(result, dict):        # comment this out for proper source-mapping
            result = result["_val"]         # but it makes it more readable for now
        return { varname: result }
    return lambda source: parse_set(varname, parserFn, source)

# parse_sequence(source) calls each parserFn in sequence, accumulating results in a dictionary
def sequence(*parserFns: List):
    def parse_sequence(source: Source, *parserFns):
        result = {}
        pos = source.start
        for parserFn in parserFns:
            singleResult = parserFn(source)
            if singleResult is None:
                source.start = pos
                return None
            else:
                if isinstance(singleResult, dict):
                    result.update(singleResult)
        return result
    return lambda source: parse_sequence(source, *parserFns)

# optional(parserFn) calls parserFn, returns {} even if no match
def optional(parserFn):
    def parse_optional(source: Source, parserFn):
        result = parserFn(source)
        if result is None:
            return {}
        return result
    return lambda source: parse_optional(source, parserFn)

# and anyof(parserFns) returns a function that calls parse_anyof with the parserFns
def anyof(*parserFns):
    def parse_anyof(source: Source, *parserFns):
        pos = source.start
        for parserFn in parserFns:
            result = parserFn(source)
            if result is not None:
                return result
            else:
                source.start = pos
        return None
    return lambda source: parse_anyof(source, *parserFns)

# enum is a special case of anyof that takes a list of strings and matches literals
def enum(*values):
    def parse_enum(source: Source, *values):
        log(f"parse_enum({values}) on {source.text[source.start:source.end]}")
        skipWhitespace(source)
        for value in values:
            pos = source.start
            if source.text.startswith(value, source.start):
                source.start += len(value)
                return { "_val": value, "_pos": pos }
            else:
                source.start = pos
        log("    returning None")
        return None
    return lambda source: parse_enum(source, *values) 

# and list(parserFn) returns a function that calls parse_list with the parserFn
def list(parserFn):
    def parse_list(source: Source, parserFn):
        log(f'parse_list on "{source.text[source.start:source.end]}"')
        results = []
        count = 10
        while count > 0:
            log(f'  applying parserFn to "{source.text[source.start:source.end]}"')
            count -= 1
            pos = source.start
            result = parserFn(source)
            log("    result:", result)
            if result is None:
                log('    result is None!!')
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
        log(f'after: "{source.text[source.start:source.end]}"')
        log_disable()
        return result
    return lambda source: debugFn(source)

# label(type) just adds { "_type": type } to the result
def label(type: str, parserFn):
    def parse_label(type: str, parserFn, source: Source):
        out = { "_type": type }
        result = parserFn(source)
        if result is None:
            return None
        out.update(result)
        return out
    return lambda source: parse_label(type, parserFn, source)

# toUndent() scans forward to outermost undent assuming we're in one already
def toUndent():
    def parse_toUndent(source: Source):
        depth = 1
        skipWhitespace(source)
        pos = source.start
        i = source.start
        while i < source.end:
            if source.text[i] == "{":
                depth += 1
            elif source.text[i] == "}":
                depth -= 1
                if depth == 0:
                    match = source.text[source.start:i]
                    source.start = i
                    return { "_val": match, "_pos": pos }
            i += 1
        return { "_val": source.text[source.start:], "_pos": pos }
    return lambda source: parse_toUndent(source)

#---------------------------------------------------------------------------------
# defining syntax for our target languages: ts, py, cpp

class Language:
    def __init__(self):
        return
    
class Typescript(Language):
    def indent(self):
        return literal("{")
    def undent(self):
        return literal("}")
    def feature(self):
        return label("feature", 
                      sequence(literal("feature"), 
                        set("name", word()),
                        optional(sequence(
                            literal("extends"),
                            set("parent", word()) )),
                        self.indent(),
                        set("components", list(self.component())), 
                        self.undent())
                        )
    def component(self): 
        return anyof(self.variable(), self.struct(), self.function())
    
    def variable(self):
        return label("variable",
                        sequence(
                            optional(set("modifier", enum("const", "var"))),
                            set("name", word()),
                            optional(sequence(literal(":"), 
                                          set("type", word()))),
                            optional(sequence(literal("="),
                                          set("value", word()))),
                            optional(enum(";", ","))))
    
    def struct(self):
        return label("struct",
                     sequence(set("modifier", enum("struct", "extend")),
                              set("name", word()),
                              self.indent(),
                              set("properties", list(self.variable())),
                              self.undent()))
    
    def function(self):
        return label("function",
                     sequence(set("modifier", enum("on", "after", "before", "replace")),
                                literal("("),
                                set("resultName", word()),
                                optional(sequence(literal(":"), 
                                           set("resultType", word()))),
                                literal(")"),
                                literal("="),
                                set("name", word()),
                                literal("("),
                                set("parameters", list(self.variable())),
                                literal(")"),
                                self.indent(),
                                set("body", toUndent()),
                                self.undent()))
    
#---------------------------------------------------------------------------------
def testParser():
    source = Source("""
                    feature MyFeature extends Another { 
                        var x: number = 42;
                        struct Colour {
                            r: number =0;
                            g: number =0;
                            b: number =0;
                        }
                        on (r: number) = add(a: number, b: number) {
                            r = a + b;
                        }
                    }
                    """)
    ts = Typescript()
    parser = debug(ts.feature())
    result = parser(source)
    log_enable()
    log("-----------")
    log("result:", result)
    log("source:", source)

#---------------------------------------------------------------------------------
def test():
    testParser()

if __name__ == "__main__":
    log_enable()
    log("----------------------------------------------")
    log("ᕦ(ツ)ᕤ fnf.py")
    log_disable()
    result = test()
    log_enable()
    log("done.")