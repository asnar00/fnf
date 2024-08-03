# ᕦ(ツ)ᕤ
# fnf.py
# the eminently reasonable .fnf.md => anything convertor

import os

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
    def __init__(self, name, mdPath):
        self.name = name
        self.mdPath = mdPath

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
    def __init__(self):
        self.cwd = os.getcwd() + "/source/fnf"
        print("cwd: " + self.cwd)
        self.scan()

    def scan(self):
        print("scan")
        # scan the directory for .fnf.md files
        filesFound = []
        for root, dirs, files in os.walk(self.cwd):
            for file in files:
                if file.endswith(".fnf.md"):
                    filesFound.append(os.path.join(root, file))
        # sort files into ascending order of creation-date
        filesFound.sort(key=os.path.getctime)
        # print a list of the files found
        for file in filesFound:
            print(file)

        

#----------------------------------------------------------------------------------------
def main():
    print("ᕦ(ツ)ᕤ fnf.py")
    fm = FeatureManager()

if __name__ == "__main__":
    main()