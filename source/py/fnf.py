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
        return ".ts"

    def functionDeclarationRegex(self, modifiers: str):
        # pattern: <modifier> <name>(<params>) [: <returnType>] { ... }
        mod_pattern = r'\b(' + '|'.join(modifiers) + r')\b'
        pattern = rf"{mod_pattern}\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*(\w+))?\s*{{"
        regex = re.compile(pattern, re.DOTALL)
        return regex
    
    # given a position in the source, extract a function body "{" ... "}"
    def extractFunctionBody(self, sourcePos, code):
        # Start with a count of 1 because we start after the first opening brace
        nBraces = 1
        i = sourcePos
        while i < len(code) and nBraces > 0:
            if code[i] == '{':
                nBraces += 1
            elif code[i] == '}':
                nBraces -= 1
            i += 1
        return code[sourcePos-1:i]
    
    # return regex to match a struct declaration: 
    def structDeclarationRegex(self):
        # pattern: struct <name> { ... }
        pattern = r"(struct|extend) (\w+)\s*{"
        regex = re.compile(pattern, re.DOTALL)
        return regex
    
    # return regex to match a variable declaration:
    def variableDeclarationRegex(self):
        modifiers = ["const", "var", "client", "server"]
        # Regex pattern for optional single modifier:
        mod_pattern = r'\b(?:' + '|'.join(modifiers) + r')\b'
        # Pattern: <modifier>? <name> : <type> = <defaultValue>; ": <type>" and "= <defaultValue>" are optional:
        pattern = rf"({mod_pattern})?\s+(\w+)\s*(?::\s*(\w+))?(?:\s*=\s*(.*))?;"
        regex = re.compile(pattern, re.DOTALL)
        return regex
    
#----------------------------------------------------------------------------------------
# Feature, Function, Struct and Variable classes represent the feature graph

# represents a feature, containing vars, structs and functions
class Feature:
    def __init__(self, mdPath):
        # extract the feature name from the path, without extensions
        self.name = os.path.basename(mdPath).split(".")[0]
        log("feature name:", self.name)
        self.mdPath = mdPath    # the path to the .fnf.md file
        self.text = ""          # the text of the feature
        self.sourceMap = []     # maps output line numbers to source line numbers
        self.functions = []     # list of functions declared by the feature
        self.language = Typescript()    # for now

    # return the feature as a dict
    def toDict(self):
        return {
            "name": self.name,
            "functions": [f.toDict() for f in self.functions],
            "structs": [s.toDict() for s in self.structs],
            "variables": [v.toDict() for v in self.variables]
        }

    # dance and sing get up and do your thing
    def process(self):
        self.readSource()
        self.extractCode()
        self.processCode()
        self.saveJson()

    # save the feature as a json file
    def saveJson(self):
        jsonPath = self.mdPath.replace(".fnf.ts.md", ".json").replace("/source/", "/build/")
        with open(jsonPath, "w") as file:
            json.dump(self.toDict(), file, indent=4)
        log("saved:", jsonPath)

    # read source file into self.text
    def readSource(self):
        with open(self.mdPath, "r") as file:
            self.text = file.read()
        log("source:", self.text)

    # extract code from text, get source-map
    def extractCode(self):
        log("extractCode", self.mdPath)
        self.code = ""
        self.sourceMap = []
        lines = self.text.split("\n")
        inCodeBlock = False
        for i, line in enumerate(lines):
            if not inCodeBlock:
                if line.startswith("    "):
                    codeLine = line[4:].rstrip()
                    self.code += codeLine + "\n"
                    self.sourceMap.append(i+1)
                else:
                    if line.startswith("```"):
                        inCodeBlock = True
            else:
                if line.startswith("```"):
                    inCodeBlock = False
                else:
                    codeLine = line.rstrip()
                    self.code += codeLine + "\n"
                    self.sourceMap.append(i+1)
        # strip any empty or blank lines from the end of (code)
        self.code = self.code.rstrip()
        codeSplit = self.code.split("\n")
        for i, line in enumerate(codeSplit):
            log(i+1,":", line, "=>", self.sourceMap[i])

    # process code to extract a list of variables, functions and structs
    def processCode(self):
        self.findFeatureDeclaration()
        self.findFunctionDeclarations()
        self.findStructDeclarations()
        self.findFeatureVarables()

    # find the feature declaration
    def findFeatureDeclaration(self):
        pattern = r"feature (\w+)(?: extends (\w+))?"
        matches = re.findall(pattern, self.code)
        results = [(name, parent if parent else None) for name, parent in matches]
        if len(results)==0:
            raise Exception("Feature declaration not found")
        if len(results)>1:
            raise Exception("Multiple feature declarations found")
        self.name = results[0][0]
        self.parent = results[0][1]
        log("feature name:", self.name)
        log("parent name:", self.parent)
    
    # find function declarations
    def findFunctionDeclarations(self):
        log("findFunctionDeclarations")
        log("code:", self.code)
        self.functions = []
        modifiers = ["def", "replace", "on", "before", "after"]
        regex = self.language.functionDeclarationRegex(modifiers)
        for match in regex.finditer(self.code):
            sourcePos = match.end()
            body = self.language.extractFunctionBody(sourcePos, self.code)
            if body is not None:
                modifier = match.group(1)
                name = match.group(2)
                params = "(" + match.group(3) + ")"
                returnType = match.group(4)
                self.functions.append(Function(modifier, name, params, returnType, body))
            else:
                log("body: None")
        for f in self.functions:
            log(f.toString())

    # find struct declarations
    def findStructDeclarations(self):
        log("findStructDeclarations")
        self.structs = []
        regex = self.language.structDeclarationRegex()
        for match in regex.finditer(self.code):
            sourcePos = match.end()
            body = self.language.extractFunctionBody(sourcePos, self.code)
            if body is not None:
                modifier = match.group(1)
                name = match.group(2)
                self.structs.append(Struct(modifier, name, body))
            else:
                log("body: None")
        for s in self.structs:
            log(s.toString())
            s.members = self.findVariableDeclarations(s.body)

    # find feature-scoped variable declarations
    def findFeatureVarables(self):
        log("findFeatureVarables")
        # first find all code outside "{" ... "}" blocks
        outerCode = self.findOuterCode(self.code)
        # then find all variable declarations in that code
        self.variables = self.findVariableDeclarations(outerCode)

    # find all code lines that aren't inside a { block }
    def findOuterCode(self, code):
        outerCode = ""
        inBlock = False
        for i, c in enumerate(self.code):
            if c == '{':
                inBlock = True
            elif c == '}':
                inBlock = False
            elif not inBlock:
                outerCode += c
        return outerCode

    # find variable declarations in a given code block
    def findVariableDeclarations(self, code):
        log("findVariableDeclarations---------------------------------------")
        variables = []
        regex = self.language.variableDeclarationRegex()
        for match in regex.finditer(code):
            modifier = match.group(1)
            name = match.group(2)
            type = match.group(3)
            defaultValue = match.group(4)
            variables.append(Variable(modifier, name, type, defaultValue))
        for v in variables:
            log(v.toString())
        return variables
    
    # print an error message given an index in the code
    def error(self, index, message):
        line = self.sourceMap[index]
        print(f"Error in {self.mdPath} at line {line}: {message}")

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
            "params": self.params,
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
        return f"{self.modifier if self.modifier is not None else ""} {self.name} : {self.type} = {self.defaultValue}"

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