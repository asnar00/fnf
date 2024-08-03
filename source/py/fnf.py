# ᕦ(ツ)ᕤ
# fnf.py
# the eminently reasonable .fnf.md => anything convertor

import os
import re
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
    def __init__(self, name, extension):
        self.name = name
        self.extension = extension

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

    def process(self):
        self.readSource()
        self.extractCode()
        self.processCode()

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
        # find the sequence "feature <name> extends <parent>;"
        (name, parent) = self.findFeatureDeclaration()

    # find the feature declaration
    def findFeatureDeclaration(self):
        log_enable()
        pattern = r"feature (\w+)(?: extends (\w+))?"
        matches = re.findall(pattern, self.code)
        results = [(name, parent if parent else None) for name, parent in matches]
        if len(results)==0:
            raise Exception("Feature declaration not found")
        if len(results)>1:
            raise Exception("Multiple feature declarations found")
        name = results[0][0]
        parent = results[0][1]
        log("feature name:", name)
        log("parent name:", parent)
        log_disable()
        return (name, parent)



        

# represents a function declared by a feature
class Function:
    def __init__(self, name, params, returnType):
        self.name = name
        self.params = params
        self.returnType = returnType

# represents a structure declared by a feature
class Struct:
    def __init__(self, name, members):
        self.name = name
        self.members = members

# represents a variable declared by a feature
class Variable:
    def __init__(self, name, type):
        self.name = name
        self.type = type

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
                if file.endswith(".fnf.md"):
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