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
        return "ts"

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
    def variableDeclarationRegex(self, modifiers =[]):
        # Create a regex pattern that matches only the modifiers in the list, including optional whitespace after
        modifier_pattern = r"(?:" + "|".join(modifiers) + r")\s*"
        # Define the complete regex pattern, where the entire modifier pattern is optional
        pattern = rf"^({modifier_pattern})?\s*(\w+)\s*(?::\s*(\w+))?(?:\s*=\s*(.*))?"
        # Compile the regex pattern for better performance if it's used multiple times
        regex = re.compile(pattern, re.MULTILINE)
        return regex
    
    # output a feature to a string
    def featureToCode(self, feature):
        code = ""
        for s in feature.structs:
            code += self.structToCode(s) + "\n"
        if len(feature.structs) > 0: code += "\n"
        code += f"class _{feature.name}"
        if feature.parent:
            code += f" extends _{feature.parent}"
        code += " {\n"
        inner = ""
        for v in feature.variables:
            inner += self.variableToCode(v) + ";\n"
        inner += "\n"
        for f in feature.functions:
            inner += self.functionToCode(f) + "\n"
        code += self.indent(inner) + "}\n"
        return code
    
    # output a function to a string
    def functionToCode(self, function):
        out : str = ""
        out += f"static {function.name}("
        out += "_cx: any"
        if len(function.params) > 0:
            out += ", "
            for i, p in enumerate(function.params):
                out += self.variableToCode(p)
                if i < len(function.params)-1:
                    out += ", "
        out += f") "
        out += f": {function.returnType} "
        out += f"{self.replaceFunctionCalls(function.body)}"
        return out
    
    # Replace function calls with _cx.<functionName>(_cx, ...)
    def replaceFunctionCalls(self, code):
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
                # It's a standalone function, modify it
                fn_name = match.group(1)
                return f"_cx.{fn_name}(_cx, "
        # Perform the replacement
        return re.sub(pattern, replace_function_call, code)
    
    # output a struct to a string
    def structToCode(self, struct):
        out = f"class {struct.name} {{\n"
        inner = ""
        for m in struct.members:
            inner += self.variableToCode(m) + ";\n"
        inner += f"constructor("
        for i, m in enumerate(struct.members):
            inner += self.variableToCode(m)
            if i < len(struct.members)-1:
                inner += ", "
        inner += ") {\n"
        for m in struct.members:
            inner += f"    this.{m.name} = {m.name};\n"
        inner += "}\n"
        out += self.indent(inner)
        out += "}"
        return out
    
    # output a variable to a string
    def variableToCode(self, variable):
        out : str = ""
        if variable.modifier:
            out += f"{variable.modifier} "
        out += f"{variable.name}"
        if variable.type:
            out +=  " : " + variable.type
        if variable.defaultValue:
            out += " = " + variable.defaultValue
        return out
    
    # indent a string by 4 spaces
    def indent(self, s):
        out = "    " + s.replace("\n", "\n    ")
        if out.endswith("\n    "):
            out = out[:-4]
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
        self.text = ""                                  # the text of the feature
        self.sourceMap: List[int] = []                  # maps output line numbers to source line numbers
        self.functions: List[Function] = []             # list of functions declared by the feature
        self.parent: str = "Feature"                   # the parent feature; by default, _Feature

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
        self.saveAsLanguage(Typescript())

    # save the feature as a file in the given language
    def saveAsLanguage(self, language):
        log_enable()
        code = language.featureToCode(self)
        targetPath = self.mdPath.replace(".fnf.ts.md", ".fnf."+language.extension())
        targetPath = targetPath.replace("/source/fnf/", "/build/"+language.extension()+"/")
        os.makedirs(os.path.dirname(targetPath), exist_ok=True)
        with open(targetPath, "w") as file:
            file.write(code)
        log("saved:", targetPath)
        log_disable()

    # save the feature as a json file
    def saveJson(self):
        jsonPath = self.mdPath.replace(".fnf.ts.md", ".json").replace("/source/fnf/", "/build/json/")
        os.makedirs(os.path.dirname(jsonPath), exist_ok=True)
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
        self.findFeatureVariables()

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
        if results[0][1]: self.parent = results[0][1]
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
                log_enable()
                params = self.processParams(match.group(3))
                log_disable()
                returnType = match.group(4)
                self.functions.append(Function(modifier, name, params, returnType, body))
            else:
                log("body: None")
        for f in self.functions:
            log(f.toString())

    # separate a list of parameters and return a list of vars
    def processParams(self, params):
        log("processParams")
        ps = params.split(",")
        vs = []
        for p in ps:
            vars = self.findVariableDeclarations(p.strip())
            vs += vars
        return vs

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
    def findFeatureVariables(self):
        log_enable()
        log("findFeatureVariables")
        # first find all code outside "{" ... "}" blocks
        outerCode = self.findOuterCode(self.code)
        log("outerCode:", outerCode)
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
        log("input:", code)
        variables = []
        modifiers = ["const", "var", "static", "shared", "client", "server"]
        regex = self.language.variableDeclarationRegex(modifiers)
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