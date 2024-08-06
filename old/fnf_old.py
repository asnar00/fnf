# ᕦ(ツ)ᕤ
# fnf.py
# the eminently reasonable .fnf.md => anything convertor

import os
import re
import json
from typing import List

#----------------------------------------------------------------------------------------
# logging: easy to turn off and on

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


#----------------------------------------------------------------------------------------
# SourceLine contains a line of source code and the index of the line in the source file

class SourceLine:
    def __init__(self, line, index, tag=""):
        self.index = index                  # 1-based index in the source md file
        self.line = line                    # the code itself
        self.tag = tag                       # what tag we decided this line should have
    def toString(self):
        return f"{self.index}: [{self.tag}] {self.line}"
    def fromString(self, s):
        iColon = s.index(":")
        self.index = int(s[:iColon])
        iBracket = s.index("[")
        jBracket = s.index("]")
        self.tag = s[iBracket+1:jBracket]
        self.line = s[jBracket+2:]
        return self
    


#----------------------------------------------------------------------------------------
# target language classes output code in the target language

class TargetLanguage:
    def __init__(self):
        pass
    def extension(self):
        pass
    def functionDeclarationRegex(self, modifiers: str):
        pass
    def extractFunctionBody(self, sourcePos, code):
        pass
    def structDeclarationRegex(self):
        pass
    def variableDeclarationRegex(self):
        pass

class Typescript(TargetLanguage):
    def __init__(self):
        pass

    def extension(self):
        return "ts"

    def outputStruct(self, block: List[SourceLine]) -> List[SourceLine]:
        out : List[SourceLine] = []
        vars: List[Variable] = []
        for line in block:
            code = line.line
            if line.tag == "struct":
                code = code.replace("struct", "export class")
            vs = self.parseVariables(line.line)
            out.append(SourceLine(code, line.index, line.tag))
            vars += vs
        out = self.outputConstructor(out, vars)
        return out
    
    def outputConstructor(self, lines: List[SourceLine], vars) -> List[SourceLine]:
        # remove last "}"
        lastLine = lines[-1].line.rstrip()
        if lastLine.endswith("}"):
            lines[-1].line = lastLine[:-1].rstrip()
        # add constructor signature
        con = "    constructor("
        for i, v in enumerate(vars):
            con += v.toString()
            if i < len(vars) - 1:
                con += ", "
        con += ") {"
        # and innards
        lines.append(SourceLine(con, lines[-1].index))
        for v in vars:
            lines.append(SourceLine(f"        this.{v.name} = {v.name};",lines[-1].index))
        # don't forget to close it off
        lines.append(SourceLine("    }", 0))
        lines.append(SourceLine("}", 0))
        return lines

    # examines a single string and returns one or more variable declarations
    def parseVariables(self, code: str):     # returns list of variables
        log("parseVariables:", code)
        # Define the complete regex pattern, where the entire modifier pattern is optional
        pattern = r"(?:(var|const)\s+)?(\w+)\s*(?::\s*(\w+))?(?:\s*=\s*(.*?))?(?=[;\n])"
        # Compile the regex pattern for better performance if it's used multiple times
        regex = re.compile(pattern)
        variables = []
        for match in regex.finditer(code):
            modifier = match.group(1)
            name = match.group(2)
            type = match.group(3)
            defaultValue = match.group(4)
            if not (name != None and modifier == None and type == None and defaultValue == None):
                log("match:", "modifier:", modifier, "name:", name, "type:", type, "defaultValue:", defaultValue)
                if defaultValue and defaultValue.endswith(";"):
                    defaultValue = defaultValue[:-1]
                variables.append(Variable(modifier, name, type, defaultValue))
        return variables
    
    # outputs a feature declaration
    def outputFeatureDecl(self, block: List[SourceLine]) -> List[SourceLine]:
        out : List[SourceLine] = []
        if len(block) != 1:
            raise Exception("expected exactly one feature declaration")
        line = block[0]
        code = line.line
        pattern = r"feature (\w+)(?: extends (\w+))?"
        matches = re.findall(pattern, code)
        if len(matches) != 1:
            raise Exception("expected exactly one feature declaration")
        name = matches[0][0]
        parent = matches[0][1]
        if parent == None: parent = "Feature"
        out.append(SourceLine(f"export class _{name} extends _{parent} {{" , line.index, line.tag))
        return out
    
    # outputs a variable declaration
    def outputVariables(self, block: List[SourceLine]) -> List[SourceLine]:
        out : List[SourceLine] = []
        for line in block:
            vars = self.parseVariables(line.line)
            for v in vars:
                out.append(SourceLine("    " + v.toString() + ";", line.index, line.tag))
        return out
    
    # outputs a function declaration/definition
    def outputFunction(self, block: List[SourceLine]) -> List[SourceLine]:
        log_enable()
        log("outputFunction")
        out : List[SourceLine] = []

        # first identify name, params of the function
        if len(block) < 1:
            raise Exception("expected at least one line in function block")
        code = block[0].line
        pattern = r"(\w+)\s*\((.*?)\)"
        match = re.search(pattern, code)
        if match == None:
            raise Exception("function declaration not found")
        name = match.group(1)
        params = match.group(2).strip()
        log("name:", name, "params:", params)

        # now replace all function calls fn(...) with _cx.fn(_cx, ...)
        for line in block:
            code = self.replaceFunctionCalls(line.line, name)
            out.append(SourceLine("    " + code, line.index, line.tag))

        # finally, add "cx: any" to the parameter list, and replace the modifier with "static"
        code = out[0].line
        iSpace = code.index(" ", 4)
        log("iSpace:", iSpace)
        code = "    static" + code[iSpace:]
        iBracket = code.index("(")
        out[0].line = code[:iBracket+1] + "_cx: any" + (", " if params != "" else "") + code[iBracket+1:]
        return out
    
    # Replace function calls with _cx.<functionName>(_cx, ...)
    def replaceFunctionCalls(self, code, exceptName):
        # Simple pattern to capture function names followed by an opening parenthesis
        pattern = r"\b(\w+)\("
        def replace_function_call(match):
            # Get the start position of the match
            start = match.start()
            # Check if the preceding character is a dot
            if start > 0 and code[start - 1] == '.':
                # It's a method call, so return it unchanged
                return match.group(0)
            else:
                # It's a standalone function, modify it (if allowed)
                fn_name = match.group(1)
                if fn_name == exceptName:
                    return match.group(0)
                return f"_cx.{fn_name}(_cx, "
        # Perform the replacement
        return re.sub(pattern, replace_function_call, code)
    
    # outputs a test
    def outputTest(self, block: List[SourceLine], mdFile) -> List[SourceLine]:
        out : List[SourceLine] = []
        out.append(SourceLine("    _test() {", 0))
        out.append(SourceLine(f'        _source("{mdFile}", 0);', 0))
        for line in block:
            code = line.line
            parts = code.split("==>")
            lhs = parts[0].strip()
            rhs = parts[1].strip() if len(parts) > 1 else ""
            outcode = ""
            if rhs == "":
                outcode = f'        _output({lhs}, {line.index});'
            else:
                outcode = f'        _assert({lhs}, {rhs}, {line.index});'
            out.append(SourceLine(outcode, line.index, line.tag))
        out.append(SourceLine("    }", 0))
        return out
    
#--------------------------------------------------------------------------------------

# global dict mapping extension "ts" to language class Typescript
global targetLanguages
targetLanguages = {
    "ts": Typescript()
}

#----------------------------------------------------------------------------------------
# Feature, Function, Struct and Variable classes represent the feature graph

# represents a feature, containing vars, structs and functions
class Feature:
    def __init__(self, mdPath):
        # extract the feature name from the path, without extensions
        parts = os.path.basename(mdPath).split(".")     # should be {"blah", "fnf", "ts", "md"}
        self.name : str = parts[0]                      # the name of the feature
        self.extension : str = parts[2]                 # the language extension of the feature
        log("feature name:", self.name)
        log("extension:", self.extension)
        global targetLanguages
        self.language = targetLanguages[self.extension] # the language of the feature
        if self.language is None:
            raise Exception(f"{mdPath}: unknown language extension {self.extension}")
        self.mdPath = mdPath                            # the path to the .fnf.md file
        self.source : List[SourceLine] = []             # the source code extracted from the md file

    # dance and sing get up and do your thing
    def process(self):
        self.readText()
        self.extractSource()
        self.processCode()
        self.saveAnnotatedText()
        self.saveTargetLanguage()

    # save the feature as a file in the given language
    def saveTargetLanguage(self):
        log_enable()
        targetPath = self.mdPath.replace(".fnf.ts.md", ".fnf."+self.language.extension())
        targetPath = targetPath.replace("/source/fnf/", "/build/"+self.language.extension()+"/")
        os.makedirs(os.path.dirname(targetPath), exist_ok=True)
        code = ""
        for line in self.source:
            code += line.line + "\n"
        with open(targetPath, "w") as file:
            file.write(code)
        log("saved:", targetPath)
        log_disable()

    # save the feature as annotated text
    def saveAnnotatedText(self):
        path = self.mdPath.replace("/source/fnf/", "/build/tmp/")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out= ""
        for line in self.source:
            out += line.toString() + "\n"
        with open(path  + ".txt", "w") as file:
            file.write(out)

    # read source file into self.text
    def readText(self):
        with open(self.mdPath, "r") as file:
            self.text = file.read()
        log("text:", self.text)

    # extract source code from text, as List[SourceLine]
    def extractSource(self):
        log("extractSource", self.mdPath)
        self.source = []
        lines = self.text.split("\n")
        inCodeBlock = False
        for i, line in enumerate(lines):
            if not inCodeBlock:
                if line.startswith("    "):
                    codeLine = line[4:].rstrip()
                    self.source.append(SourceLine(codeLine, i+1))
                else:
                    if line.startswith("```"):
                        inCodeBlock = True
            else:
                if line.startswith("```"):
                    inCodeBlock = False
                else:
                    codeLine = line.rstrip()
                    self.source.append(SourceLine(codeLine, i+1))

    # show the source code
    def showSource(self, lines):
        for i, line in enumerate(lines):
            log(f"{i+1} => {line.toString()}")

    # show blocks
    def showBlocks(self, name, blocks):
        log("showing", name, len(blocks))   
        for i, block in enumerate(blocks):
            log("--------------------------------")
            self.showSource(block)


    # process code to extract a list of variables, functions and structs
    def processCode(self):
        self.tagSource()
        self.extractBlocks()
        self.translateSource()

    # for each line, figure out what kind of line it is
    def tagSource(self):
        tags = ["feature", "def", "replace", "on", "before", "after", "struct", "extend", "var", "const"]
        for line in self.source:
            firstWord = line.line.strip().split(" ")[0]
            if firstWord in tags:
                line.tag = firstWord
            elif "==>" in line.line:
                line.tag = "test"

    # structs first, then feature, then vars, then functions
    def extractBlocks(self):
        self.structs: List[List[SourceLine]] = []
        self.functions: List[List[SourceLine]] = []
        self.variables: List[List[SourceLine]] = []
        self.tests: List[List[SourceLine]] = []
        self.featureDecl: List[List[SourceLine]] = []

        for i, line in enumerate(self.source):
            if line.tag == "":
                continue
            j = i+1
            while j < len(self.source) and self.source[j].tag == "":
                j += 1
            block = self.source[i:j]
            if line.tag in ["struct", "extend"]:
                self.structs.append(block)
            elif line.tag == "feature":
                self.featureDecl.append(block)
            elif line.tag in ["var", "const", "let"]:
                self.variables.append(block)
            elif line.tag in ["def", "replace", "on", "before", "after"]:
                self.functions.append(block)
            elif line.tag == "test":
                self.tests.append(block)

        if len(self.featureDecl) != 1:
            raise Exception(f"expected exactly one feature declaration, found {len(self.featureDecl)}")


    def translateSource(self):
        out : List[SourceLine] = []
        for block in self.structs:
            out += self.language.outputStruct(block)
        for block in self.featureDecl:
            out += self.language.outputFeatureDecl(block)
        for block in self.variables:
            out += self.language.outputVariables(block)
        for block in self.functions:
            out += self.language.outputFunction(block)
        # join self.tests into a single block:
        testBlock = []
        for block in self.tests:
            testBlock += block
        out += self.language.outputTest(testBlock, self.mdPath)
        out += [SourceLine("}", 0)]

        log_enable()
        log("-----------------> output:")
        self.showSource(out)
        self.source = out
        
            
       
            

        
            


        

   

# represents a function declared by a feature
class Function:
    def __init__(self, modifier, name, params, returnType, body):
        self.modifier = modifier
        self.name = name
        self.params = params
        self.returnType = returnType if returnType else "void"
        self.body = body

    def toDict(self):
        return {
            "modifier": self.modifier,
            "name": self.name,
            "params": [p.toDict() for p in self.params],
            "returnType": self.returnType,
            "body": self.body
        }

    def toString(self):
        return f"{self.modifier} {self.name}{self.params} : {self.returnType} {self.body}"

# represents a structure declared by a feature
class Struct:
    def __init__(self, modifier, name, body):
        self.modifier = modifier
        self.name = name
        self.body = body
        self.members = []

    def toDict(self):
        return {
            "modifier": self.modifier,
            "name": self.name,
            "body": self.body,
            "members": [m.__dict__ for m in self.members]
        }

    def toString(self):
        return f"{self.modifier} {self.name} {self.body}"

# represents a variable declared by a feature
class Variable:
    def __init__(self, modifier, name, type=None, defaultValue=None):
        self.modifier = modifier
        self.name = name
        self.type = type
        self.defaultValue = defaultValue

    def toDict(self):
        return {
            "modifier": self.modifier,
            "name": self.name,
            "type": self.type,
            "defaultValue": self.defaultValue
        }

    def toString(self):
        return f"{self.name} : {self.type} = {self.defaultValue}"

#----------------------------------------------------------------------------------------
# FeatureManager builds the feature graph from the input code, and outputs the target code

class FeatureManager:
    # constructor: finds where to look for features
    def __init__(self):
        log("FeatureManager.init")
        self.cwd = os.getcwd() + "/source/fnf"
        log("cwd: " + self.cwd)
        self.features = {}
        
    # build or maintain the feature graph, minimising work
    def buildFeatureGraph(self):
        log("buildFeatureGraph")
        filesFound = self.scanFolder()
        for file in filesFound:
            if file in self.features:
                self.updateExistingFeature(file)
            else:
                self.createNewFeature(file)

    # create a new feature from the given file
    def createNewFeature(self, file):
        log("createNewFeature: " + file)
        feature = Feature(file)
        self.features[file] = feature
        feature.process()

    # update an existing feature from the given file
    def updateExistingFeature(self, file):
        feature = self.features[file]
        feature.process()

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
    fm.buildFeatureGraph()

if __name__ == "__main__":
    main()