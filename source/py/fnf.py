# ᕦ(ツ)ᕤ
# fnf.py
# author: asnaroo
# reads .md files and builds features

from typing import List
import os
import re
import json

#-------------------------------------------------------------------------------------------
# classes that represent the program: super lightweight, just serialisation and store

class Variable:
    def __init__(self, modifier= None, name=None, type=None, defaultValue=None):
        self.modifier = modifier
        self.name = name
        self.type = type
        self.defaultValue = defaultValue
    def toString(self):
        out = ""
        if self.modifier != None: out += self.modifier + " "
        out += self.name
        if self.type != None: out += ": " + self.type
        if self.defaultValue != None: out += " = " + self.defaultValue
        return out
    def toDict(self) -> dict:
        return {
            "modifier": self.modifier,
            "name": self.name,
            "type": self.type,
            "defaultValue": self.defaultValue
        }
    def fromDict(self, dict: dict):
        self.modifier = dict["modifier"]
        self.name = dict["name"]
        self.type = dict["type"]
        self.defaultValue = dict["defaultValue"]

class Struct:
    def __init__(self, modifier = "", name ="", members=[]):
        self.modifier: str = modifier
        self.name: str = name
        self.members: List[Variable] = members
    def toDict(self) -> dict:
        return {
            "modifier": self.modifier,
            "name": self.name,
            "members": [x.toDict() for x in self.members]
        }
    def fromDict(self, dict: dict):
        self.modifier = dict["modifier"]
        self.name = dict["name"]
        self.members = [Variable().fromDict(x) for x in dict["members"]]

class Function:
    def __init__(self, modifier="", name="", returnType="", parameters: List[Variable]=[], body=""):
        self.modifier = modifier
        self.name = name
        self.returnType = returnType
        self.parameters = parameters
        self.body = body
    def toDict(self) -> dict:
        return {
            "modifier": self.modifier,
            "name": self.name,
            "returnType": self.returnType,
            "parameters": [x.toDict() for x in self.parameters],
            "body": self.body
        }
    def fromDict(self, dict: dict):
        self.modifier = dict["modifier"]
        self.name = dict["name"]
        self.returnType = dict["returnType"]
        self.parameters = [Variable().fromDict(x) for x in dict["parameters"]]
        self.body = dict["body"]

class Feature:
    def __init__(self, path):
        self.path = path
        parts = path.split("/")
        fname = parts[-1].split(".")
        self.name = fname[0]
        self.ext = fname[2]
        self.parent = parts[-2]
        if self.parent == "fnf": self.parent = "Feature"
        self.variables: List[Variable] = []
        self.structs: List[Struct] = []
        self.functions: List[Function] = []
        self.inBlocks: List[SourceBlock] = []
        self.outBlocks: List[SourceBlock] = []

    def toDict(self) -> dict:
        return {
            "name": self.name,
            "parent": self.parent,
            "language": self.ext,
            "variables": [x.toDict() for x in self.variables],
            "structs": [x.toDict() for x in self.structs],
            "functions": [x.toDict() for x in self.functions]
        }
    def fromDict(self, dict: dict):
        self.name = dict["name"]
        self.parent = dict["parent"]
        self.ext = dict["language"]
        self.variables = [Variable().fromDict(x) for x in dict["variables"]]
        self.structs = [Struct().fromDict(x) for x in dict["structs"]]
        self.functions = [Function().fromDict(x) for x in dict["functions"]]

class Context:
    def __init__(self):
        self.features = []
        self.functions = {}
        self.sourceBlocks = []

    def toDict(self) -> dict:
        return {
            "features": [x.toDict() for x in self.features],
            "functions": {k: v.toDict() for k, v in self.functions.items()}
        }
    def fromDict(self, dict: dict):
        self.features = [Feature().fromDict(x) for x in dict["features"]]
        self.functions = {k: Function().fromDict(v) for k, v in dict["functions"].items()}

#-----------------------------------------------------------------------------------------------
# SourceLine holds a line of source code, a tag, and the source line number

class SourceLine:
    def __init__(self, code: str, index=0, tag=""):
        self.code = code
        self.index = index
        self.tag = tag

    def toString(self):
        def pad(s, n):
            return s + " " * (n - len(s))
        return pad(f"{self.index}: [{self.tag}]", 14) + self.code

    def fromString(self, s):
        iColon = s.find(":")
        iBracket = s.find("[", iColon)
        iBracketEnd = s.find("]", iBracket)
        index = int(s[:iColon])
        tag = s[iBracket+1:iBracketEnd]
        code = s[iBracketEnd+1:]
        return SourceLine(code, index, tag)

class SourceBlock:
    def __init__(self, lines: List[SourceLine]):
        self.lines = lines
        self.entity = None

    def tag(self):
        return self.lines[0].tag
    
    # indent a block by 4 spaces
    def indent(self):
        for line in self.lines:
            line.code = "    " + line.code
        return self
    
    @staticmethod
    # save blocks to text file
    def saveBlocks(blocks, savePath):
        log("saveBlocks: " + savePath)
        # make sure folder exists:
        os.makedirs(os.path.dirname(savePath), exist_ok=True)
        with open(savePath, "w") as f:
            for block in blocks:
                for line in block.lines:
                    f.write(line.toString())
                    f.write("\n")

    @staticmethod
    # load blocks from text file
    def loadBlocks(loadPath):
        log("loadBlocks: " + loadPath)
        blocks = []
        if not os.path.exists(loadPath): return blocks
        with open(loadPath, "r") as f:
            lines = f.readlines()
            for line in lines:
                sourceLine = SourceLine().fromString(line)
                if (sourceLine.tag != ""):
                    block = SourceBlock([sourceLine])
                    blocks.append(block)
                else:
                    blocks[-1].lines.append(sourceLine)
        return blocks

    
#-----------------------------------------------------------------------------------------------
# logging: turn on and offable

# global boolean log_enabled, initially False
global log_enabled
log_enabled = False

# log_enable() sets log_enabled to True
def log_enable():
    global log_enabled
    log_enabled = True

# log_disable() sets log_enabled to False
def log_disable():
    global log_enabled
    log_enabled = False

# log() takes arbitrary arguments and passes them to print
def log(*args):
    global log_enabled
    if log_enabled:
        print(*args)

#-----------------------------------------------------------------------------------------------
# regex builder takes a class and a human-readable descriptor array, and builds a regex

class Term:
    def __init__(self, optional=False, wordList =[], orList=[]):
        self.optional = optional
        self.wordList = wordList
        self.orList = orList

class Matcher:
    def __init__(self, cls, descriptor):
        self.cls = cls
        self.descriptor = descriptor
        self.members = []
        self.end = 0
        self.buildRegex()

    # builds a regex from the human-readable descriptor
    def buildRegex(self):
        log("buildRegex", self.cls.__name__, self.descriptor)
        # make an instance of the class
        instance = self.cls()
        # read out all the instance property names, but not methods
        properties = [attr for attr in dir(instance) if not callable(getattr(instance, attr)) and not attr.startswith("__")]
        log("class properties:")
        for property in properties:
            log("    ", property)
        log("terms")
        self.fullRegex = ""
        wordPattern = r'\b[a-zA-Z]\w*'
        numberPattern = r'\b\d+(?:\.\d+)?'
        stringPattern = r'"[^"]*"|\'[^\']*\''
        combinedPattern = fr'({numberPattern}|{wordPattern}|{stringPattern})'
        endPattern = r'[^;\r]+'  # match anything except semicolon, or newline
        endBracketPattern = r'[^\)]*'  # match anything except closing bracket
        patterns = { "word": wordPattern, "number": numberPattern, "string": stringPattern, "any": combinedPattern, "toEnd": endPattern, "toEndBracket": endBracketPattern }
        for term in self.descriptor:
            regex = ""
            parsedTerm = self.parseDescriptor(term)
            for i, word in enumerate(parsedTerm.wordList):
                if word.startswith("'") and word.endswith("'"):
                    log("word:", word)
                    word = word[1:-1]
                    log("literal", word)
                    escaped = re.escape(word)
                    log("escaped", escaped)
                    regex += escaped                        # match specific word, discard
                else:
                    if not word in properties:
                        log("ERROR: word", word, "not in class properties")
                    self.members.append(word)                           # word is name of class member to write
                    if i == len(parsedTerm.wordList)-1:
                        if len(parsedTerm.orList) > 1:  # it's an "or" list
                            regex += "(" + r'|'.join(re.escape(s[1:-1]) for s in parsedTerm.orList) + ")"   # match option-list, capture
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
            self.fullRegex += regex + r'\s*'
        log("fullRegex:", self.fullRegex)
        log("members:", self.members)
        self.pattern = re.compile(self.fullRegex)

    # find all matches, write them into instances of the class
    def findMatches(self, code):
        results = []
        for match in self.pattern.finditer(code):
            self.end = match.end()
            #print(f"Match: {match.group(0)}, Start: {match.start()}, End: {match.end()}")
            instance = self.cls()
            for i, group in enumerate(match.groups()):
                #log("  group", i, group)
                setattr(instance, self.members[i], group)
            log("    instance:", instance.__dict__)
            results.append(instance)
        return results

    # parse a descriptor into a Term
    def parseDescriptor(self, desc):
        log("parseDescriptor", desc)
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
        log("  orList", orList)
        log("  optional", optional)
        log("  wordList", wordList)
        return Term(optional, wordList, orList)

def testRegex():
    log_enable()
    desc = Typescript().function()
    matcher = Matcher(Function, desc)
    functions = matcher.findMatches("def hello(name: string) : number {")
    for function in functions:
        log(function.__dict__)

#-----------------------------------------------------------------------------------------------
# language classes do code generation and parsing: plug your own in here

class Language:
    def __init__(self):
        self.ext = ""

    def comment(self):
        pass

    def indent(self):
        pass

    def variable(self):
        pass

    def struct(self):
        pass

    def output_feature(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        pass

    def output_variable(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        pass

    def output_struct(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        pass

    def output_function(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        pass

    def output_test(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        pass

    def extend_function(self, existing: SourceBlock, new: Function, feature: Feature) -> SourceBlock:
        pass

    def output_classDecl(self, name) -> SourceLine:
        pass

    def output_classDeclEnd(self) -> SourceLine:
        pass

    @staticmethod
    def getLanguage(ext):
        for subclass in Language.__subclasses__():
            instance = subclass()
            if instance.ext == ext:
                return instance
        raise Exception("Language not found")

# Typescript defines variable, struct and function syntax for fnf.ts, in a human-readable way
class Typescript(Language):
    def __init__(self):
        self.ext = "ts"

    def comment(self):
        return "//"

    def indent(self):
        return "{"

    def variable(self):
        return ["optional modifier('var' or 'const')", "name(word)", "optional ':' type(word)", "optional '=' defaultValue(toEnd)"]
    
    def struct(self):
        return ["modifier('struct' or 'extend')", "name(word)"]
    
    def function(self):
        return ["modifier('def' or 'replace' or 'on' or 'after' or 'before')", "name(word)", "'('", "parameters(toEndBracket)", "')'", "optional ':' returnType(word)"]
    
    # output feature-clause as typescript code:
    def output_feature(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        out = SourceBlock([])
        if len(block.lines) != 1: raise Exception("Expected exactly one line in feature block")
        line = block.lines[0]
        out.lines.append(SourceLine(f"export class _{feature.name} extends _{feature.parent}" + " {", line.index, line.tag))
        return out

    # output variable as typescript code: var/const -> static
    def output_variable(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        out = SourceBlock([])
        for line in block.lines:
            code = line.code
            code = code.replace("var", "static").replace("const", "static")
            out.lines.append(SourceLine(code, line.index, line.tag))
        return out

    # output struct as typescript code: struct->class, auto-constructor
    def output_struct(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        struct = block.entity
        out = SourceBlock([])
        code = block.lines[0].code
        code = code.replace("struct", "export class")
        code = code.replace(struct.name, f"{struct.name}")
        out.lines.append(SourceLine(code, block.lines[0].index, block.lines[0].tag))
        for line in block.lines[1:]:
            out.lines.append(SourceLine(line.code, line.index, line.tag))
        constructorParams = [var.toString() for var in struct.members]
        constructor = "constructor(" + ", ".join(constructorParams) + ") {"
        out.lines.append(SourceLine(constructor, block.lines[0].index))
        for member in struct.members:
            out.lines.append(SourceLine(f"    this.{member.name} = {member.name};", block.lines[0].index))
        out.lines.append(SourceLine("}", block.lines[0].index))
        return out
    
    # output function as typescript code: remove modifier, add _cx: any parameter, modify all function calls
    def output_function(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        function = block.entity
        out = SourceBlock([])
        code = block.lines[0].code
        # replace the modifier with nothing
        modifiers = ["def", "replace", "on", "before", "after"]
        for m in modifiers: code = code.replace(m + " ", "static ")
        # add a new cx: any parameter to the start of the param-list
        cxParam = "_cx: any"
        if len(function.parameters) > 0: cxParam += ", "
        code = code.replace("(", f"({cxParam}")
        out.lines.append(SourceLine(code, block.lines[0].index, block.lines[0].tag))
        # replace all function calls with _cx.function(_cx, ...)
        for line in block.lines[1:]:
            code = self.replace_function_calls(line.code)
            out.lines.append(SourceLine(code, line.index, line.tag))
        return out

    def replace_function_calls(self, code):
        pattern = r'\b(?<!\.)\w+\s*\([^()]*\)'
        def replacer(match):
            func_call = match.group(0)
            func_name, params_part = func_call.split('(', 1)
            func_name = func_name.strip()
            params = params_part[:-1].strip()  # Remove the closing parenthesis and whitespace
            if params:
                return f'_cx.{func_name}(_cx, {params})'
            else:
                return f'_cx.{func_name}(_cx)'
        
        return re.sub(pattern, replacer, code)
    
    # output test function
    def output_test(self, feature: Feature, block: SourceBlock) -> SourceBlock:
        out = SourceBlock([])
        out.lines.append(SourceLine("_test(_cx: any) {", 0, block.lines[0].tag))
        out.lines.append(SourceLine(f'    _source("{feature.path}");', 0))
        for line in block.lines:
            code = line.code
            outcode = ""
            parts = code.split("==>")
            lhs = parts[0].strip()
            rhs = parts[1].strip() if len(parts) > 1 else ""
            lhs = self.replace_function_calls(lhs)
            if (rhs == ""):
                outcode = f'    _output({lhs}, {line.index});'
            else:
                outcode = f'    _assert({lhs}, {rhs}, {line.index});'
            out.lines.append(SourceLine(outcode, line.index))
        out.lines.append(SourceLine("}"))
        return out
    
    # builds a composite function from an existing function, a new function, and a modifier
    def extend_function(self, existing: SourceBlock|None, newFunc: Function, feature: Feature) -> SourceBlock:
        if existing is None or newFunc.modifier == "replace":
            block = SourceBlock([])
            params = ", ".join([var.toString() for var in newFunc.parameters])
            params = "_cx: any" + (", " if params != "" else "") + params
            returnType = "" if newFunc.returnType == None else f" : {newFunc.returnType}"
            block.lines.append(SourceLine(f"{newFunc.name}({params}){returnType} {{", 0))
            args = ", ".join([var.name for var in newFunc.parameters])
            args = "_cx" + (", " if args != "" else "") + args
            block.lines.append(SourceLine(f"    return {feature.name}.{newFunc.name}({args});", 0))
            block.lines.append(SourceLine("}", 0))
            return block
        
    # outputs a class declaration
    def output_classDecl(self, name) -> SourceLine:
        return SourceLine(f"export class {name} {{")
    
    # outputs a class declaration end
    def output_classDeclEnd(self) -> SourceLine:
        return SourceLine("}")

    
#-----------------------------------------------------------------------------------------------
# FeatureBuilder class: builds a single feature from source

class FeatureBuilder:
    def __init__(self, feature):
        self.feature = feature

    def buildFeature(self):
        feature = self.feature
        jsonPath = self.jsonPath(feature)
        log("jsonPath: " + jsonPath)
        jsonDate = os.path.getmtime(jsonPath) if os.path.exists(jsonPath) else 0
        fileDate = os.path.getmtime(feature.path)
        sourceDate = os.path.getmtime(__file__)
        if sourceDate > jsonDate or jsonDate < fileDate:
            self.buildFeatureFromSource(feature)
            self.saveFeature(feature)
        else:
            self.loadFeature(feature)

    # build feature from source
    def buildFeatureFromSource(self, feature):
        log("buildFeatureFromSource: " + feature.path)
        text = ""
        with open(feature.path, "r") as f:
            text = f.read()
        sourceLines = self.extractSource(text)
        taggedLines = self.tagSource(sourceLines)
        taggedBlocks = self.separateBlocks(taggedLines)
        orderedBlocks = self.reorderBlocks(taggedBlocks)
        feature.inBlocks = orderedBlocks
        self.parseBlocks(feature, orderedBlocks)
        outputBlocks = self.outputBlocks(feature, orderedBlocks)
        feature.outBlocks = outputBlocks

    # output blocks to target language source code
    def outputBlocks(self, feature, orderedBlocks):
        log_enable()
        log("outputBlocks")
        language : Language = Language.getLanguage(feature.ext)
        outputBlocks = []
        for block in orderedBlocks:
            if block.tag() == "feature":
                outputBlocks.append(language.output_feature(feature, block))
            if block.tag() == "var":
                outputBlocks.append(language.output_variable(feature, block).indent())
            elif block.tag() == "struct":
                outputBlocks.append(language.output_struct(feature, block))
            elif block.tag() == "func":
                outputBlocks.append(language.output_function(feature, block).indent())
            elif block.tag() == "test":
                outputBlocks.append(language.output_test(feature, block).indent())
        outputBlocks.append(SourceBlock([SourceLine("}", 0)]))
        
        for i, block in enumerate(outputBlocks):
            for line in block.lines:
                log(line.toString())
        return outputBlocks

    # parse blocks into variables, structs, functions, etc
    def parseBlocks(self, feature, orderedBlocks):
        log("parseBlocks")
        feature.variables = []
        feature.structs = []
        feature.functions = []
        language = Language.getLanguage(feature.ext)
        for block in orderedBlocks:
            if block.tag() == "var":
                feature.variables += self.parseVariables(block, language)
            elif block.tag() == "struct":
                feature.structs += self.parseStructs(block, language)
            elif block.tag() == "func":
                feature.functions += self.parseFunctions(block, language)

    # parse a variable block
    def parseVariables(self, block, language) -> Variable:
        log("parseVariable")
        variables = []
        matcher = Matcher(Variable, language.variable())
        for line in block.lines:
            variables += matcher.findMatches(line.code)
        block.entity = variables[0]
        return variables

    # parse a struct block
    def parseStructs(self, block, language) -> Struct:
        log("parseStruct")
        matcher = Matcher(Struct, language.struct())
        structs = []
        for line in block.lines:
            structs += matcher.findMatches(line.code)
        if len(structs) != 1: raise Exception("Expected exactly one struct")
        structs[0].members = self.parseVariables(block, language)[2:]
        block.entity = structs[0]
        return structs

    # parse a function block
    def parseFunctions(self, block, language) -> Function:
        log("parseFunction")
        matcher = Matcher(Function, language.function())
        functions = []
        for line in block.lines:
            log(line.toString())
            functions += matcher.findMatches(line.code)
        if len(functions) != 1: 
            print("Expected exactly one function, found", len(functions))
            exit(0)
        else:
            log("found a single function :-)")
            varMatcher = Matcher(Variable, language.variable())
            functions[0].parameters = varMatcher.findMatches(functions[0].parameters)
            functions[0].body = block.lines[0].code[matcher.end:] + "\n" + "\n".join([line.code for line in block.lines[1:]])
            log("function:", functions[0].toDict())
        block.entity = functions[0]
        return functions

    # reorder blocks: structs, feature, variables, functions, tests
    def reorderBlocks(self, taggedBlocks: List[SourceBlock]) -> List[SourceBlock]:
        log("reorderBlocks")
        orderedBlocks = []
        for tag in ["struct", "feature", "var", "func", "test"]:
            for block in taggedBlocks:
                if block.tag() == tag:
                    orderedBlocks.append(block)
        for i, block in enumerate(orderedBlocks):
            for line in block.lines:
                log(line.toString())
        return orderedBlocks

    # separate blocks of tagged lines into variables, structs, functions, etc
    def separateBlocks(self, taggedLines: List[SourceLine]) -> List[SourceBlock]:
        log("separateBlocks")
        blocks: List[SourceBlock] = []
        currentBlock: SourceBlock = None
        for line in taggedLines:
            if line.tag != "":
                currentBlock = SourceBlock([line])
                blocks.append(currentBlock)
            else:
                currentBlock.lines.append(line)
        blocks = self.consolidateTestBlocks(blocks)
        for i, block in enumerate(blocks):
            for line in block.lines:
                log(line.toString())
        return blocks
    
    # consolidate all "test" blocks into a single block
    def consolidateTestBlocks(self, blocks: List[SourceBlock]) -> List[SourceBlock]:
        testBlock = SourceBlock([])
        for block in blocks:
            if block.tag() == "test":
                testBlock.lines += block.lines
        # remove the tag from all testBlock lines except the first
        for line in testBlock.lines[1:]: line.tag = ""
        # now remove all "test" tagged blocks from blocks:
        blocks = [block for block in blocks if block.tag() != "test"]
        # add the test block to the end
        blocks.append(testBlock)
        return blocks
    
    # tag source code with function, struct, variable, etc
    def tagSource(self, source: List[SourceLine]) -> List[SourceLine]:
        log("tagSource")
        modifiers = ["feature", "def", "replace", "on", "before", "after", "struct", "extend", "var", "const"]
        tags = ["feature", "func", "func", "func", "func", "func", "struct", "struct", "var", "var"]
        taggedLines: List[SourceLine] = []
        for line in source:
            firstWord = line.code.strip().split(" ")[0]
            tag = ""
            index = modifiers.index(firstWord) if firstWord in modifiers else -1
            if index >= 0:
                tag = tags[index]
            elif "==>" in line.code:
                tag = "test"
            taggedLines.append(SourceLine(line.code, line.index, tag))
        for i, line in enumerate(taggedLines):
            log(f"{" " if i < 10 else ""}{i}: {line.toString()}")
        return taggedLines

    # extract source code from text
    def extractSource(self, text) -> List[SourceLine]:
        log("extractSource")
        source: List[SourceLine] = []
        lines = text.split("\n")
        inCodeBlock = False
        for i, line in enumerate(lines):
            if not inCodeBlock:
                if line.startswith("    "):
                    codeLine = line[4:].rstrip()
                    source.append(SourceLine(codeLine, i+1))
                else:
                    if line.startswith("```"):
                        inCodeBlock = True
            else:
                if line.startswith("```"):
                    inCodeBlock = False
                else:
                    codeLine = line.rstrip()
                    source.append(SourceLine(codeLine, i+1))
        for i, line in enumerate(source):
            log(f"{" " if i < 10 else ""}{i}: {line.toString()}")
        return source
        
    # save feature to (path)
    def saveFeature(self, feature):
        log("saveFeature: " + feature.name)
        with open(self.jsonPath(feature), "w") as f:
            json.dump(feature.toDict(), f, indent=4)
        SourceBlock.saveBlocks(feature.inBlocks, self.inBlockPath(feature))
        SourceBlock.saveBlocks(feature.outBlocks, self.outBlockPath(feature))

    # load feature from (path)
    def loadFeature(self, feature):
        log("loadFeature: " + feature.name)
        with open(self.jsonPath(feature), "r") as f:
            feature.fromDict(json.load(f))     
        feature.inBlocks = SourceBlock.loadBlocks(self.inBlockPath(feature))
        feature.outBlocks = SourceBlock.loadBlocks(self.outBlockPath(feature))
        
    # get json path for feature
    def jsonPath(self, feature) -> str:
        return feature.path.replace(f".fnf.{feature.ext}.md", f".{feature.ext}.json").replace("source/fnf/", "/build/fnf/")
    
    # get path of "incoming blocks" file
    def inBlockPath(self, feature) -> str:
        return feature.path.replace(f".fnf.{feature.ext}.md", f".{feature.ext}.in.blocks").replace("source/fnf/", "/build/fnf/")
    
    # get path of "outgoing blocks" file
    def outBlockPath(self, feature) -> str:
        return feature.path.replace(f".fnf.{feature.ext}.md", f".{feature.ext}.out.blocks").replace("source/fnf/", "/build/fnf/")
    

#-----------------------------------------------------------------------------------------------
# ContextBuilder class: builds a context from a list of features

class ContextBuilder:
    def __init__(self, name, features: List[Feature]):
        self.name = name
        self.features = features
        
    def build(self) -> List[SourceBlock]:
        outBlocks = []
        language = Language.getLanguage(self.features[0].ext)
        # add all the feature contexts
        for feature in self.features:
            outBlocks.append(SourceBlock([SourceLine(f"{language.comment()} {feature.path}", 0, "source")]))
            outBlocks += feature.outBlocks
        padding = 80 - len(self.name) - 12
        outBlocks.append(SourceBlock([SourceLine(f"{language.comment()} Context {self.name}", 0, "source")]))
        # build a list of functions
        functions = {}      # map name -> SourceBlock
        for feature in self.features:
            for func in feature.functions:
                if func.modifier == "def":
                    if func.name in functions:
                        raise Exception(f"Function {func.name} already defined")
                else:
                    if not func.name in functions:
                        raise Exception(f"Function {func.name} not defined")
                existing: SourceBlock = functions.get(func.name, None)
                newBlock = language.extend_function(existing, func, feature)
                functions[func.name] = newBlock
        cDecl = language.output_classDecl("Context_" + self.name)
        cDecl.tag = "context"
        outBlocks.append(SourceBlock([cDecl]))
        for name, block in functions.items():
            outBlocks.append(block.indent())
        outBlocks.append(SourceBlock([language.output_classDeclEnd()]))
        log("ContextBuilder.build")
        for block in outBlocks:
            for line in block.lines:
                log(line.toString())
        return outBlocks

#-----------------------------------------------------------------------------------------------
# SourceMap : maps line number to (source, line) based on context

class SourceMap:
    def __init__(self, sourceBlocks, comment):
        source = ""
        self.map = []
        sourceLines = [].join([block.lines for block in sourceBlocks])
        for i, line in enumerate(sourceLines):
            if line.tag == "source":
                source = line.code.replace(comment + " ", "")
            self.map.push((source, line.index))

    def get(self, lineIndex): # 1-based
        if lineIndex > len(self.map): return 0
        return self.map[lineIndex-1]    

#-----------------------------------------------------------------------------------------------
# FeatureManager class: manages all features

class FeatureManager:
    # constructor: finds where to look for features
    def __init__(self):
        log("FeatureManager.init")
        self.cwd = os.getcwd() + "/source/fnf"
        log("cwd: " + self.cwd)
        self.features = {}
        
    # build or maintain the feature graph, minimising work
    def buildFeatures(self):
        log("buildFeatures")
        filesFound = self.scanFolder()
        for file in filesFound:
            self.buildFeature(file)

    # build context from list, name
    def buildContext(self, name: str, features: List[Feature]):
        log_enable()
        log("buildContext: " + name)
        builder = ContextBuilder(name, features)
        blocks = builder.build()
        SourceBlock.saveBlocks(blocks, f"build/cx/Context_{name}.ts.out.blocks")

    # build feature from given file
    def buildFeature(self, file):
        log("buildFeature: " + file)
        feature = self.getFeature(file)
        builder = FeatureBuilder(feature)
        builder.buildFeature()

    # get feature for "file", or create it if it doesn't exist
    def getFeature(self, file) -> Feature:
        log("getFeature: " + file)
        if file in self.features:
            return self.features[file]
        else:
            feature = Feature(file)
            self.features[file] = feature
            return feature

    # find all files in the source folder, in order of creation-date
    def scanFolder(self) -> List[str]:
        log("scanFolder")
        # scan the directory for .fnf.md files
        filesFound = []
        for root, dirs, files in os.walk(self.cwd):
            for file in files:
                if file.endswith(".fnf.ts.md"):
                    filesFound.append(os.path.join(root, file))
        # sort files into ascending order of creation-date
        filesFound.sort(key=os.path.getctime)
        log("filesFound:", filesFound)
        return filesFound

#----------------------------------------------------------------------------------------

def main():
    print("ᕦ(ツ)ᕤ fnf.py")
    fm = FeatureManager()
    fm.buildFeatures()
    fm.buildContext("all", list(fm.features.values()))

if __name__ == "__main__":
    main()