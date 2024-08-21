# ᕦ(ツ)ᕤ
# typescript.py
# author: asnaroo
# everything needed to parse and generate feature-modular typescript code

from languages.base import Language
from util import *

#---------------------------------------------------------------------------------
    
class Typescript(Language):
    def extension(self): return "ts"
    def indent(self):
        return keyword("{")
    def undent(self):
        return keyword("}")
    def feature(self):
        return label("feature", 
                      sequence(keyword("feature"), 
                        set("name", word()),
                        optional(sequence(
                            keyword("extends"),
                            set("parent", word()) )),
                        self.indent(),
                        set("components", list(self.component())), 
                        self.undent())
                        )
    
    def component(self): 
        return anyof(self.function(), self.struct(), self.local(), self.test())
    
    def local(self):
        return label("local",
                    sequence(
                        keyword("local"),
                        optional(set("modifier", enum("const", "var"))),
                        set("name", word()),
                        optional(sequence(keyword(":"), 
                                        set("type", word()))),
                        optional(sequence(keyword("="),
                                        set("value", toEnd()))),
                        optional(enum(";", ","))))
    
    def variable(self):
        return label("variable",
                        sequence(
                            optional(set("modifier", enum("const", "var"))),
                            set("name", word()),
                            optional(sequence(keyword(":"), 
                                          set("type", word()))),
                            optional(sequence(keyword("="),
                                          set("value", toEnd()))),
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
                    sequence(
                        set("modifier", enum("on", "after", "before", "replace")),
                        optional(set("async", keyword("async"))),
                        set("name", word()),
                        keyword("("),
                        set("parameters", list(self.variable())),
                        keyword(")"),
                        optional(sequence(keyword(":"), 
                                        set("returnType", toEnd("{")))),
                        self.indent(),
                        set("body", toUndent()),
                        self.undent()))
    
    def test(self):
        return label("test", sequence(keyword(">"),
                                set("code", toEnd("\n"))))
    #---------------------------------------------------------------------------------
    # concurrency: figure out whether a function is async

    def is_function_async(self, fn: dict) -> bool:
        if "async" in fn:
            return True
        if "returnType" in fn and "Promise" in str(fn["returnType"]):
            return True
        if "body" in fn and "await" in str(fn["body"]):
            return True
        return False
    
    # replace all calls to async functions with (await xyz) calls
    def add_awaits(self, body: str, asyncFns: dict) -> str:
        for fn in asyncFns:
            # rexep that matches fn, open-bracket, anything, close-bracket
            pattern = f'({fn}\\s*\\([^\\)]*\\))'
            # find all matches and replace with "await xxx"
            body = re.sub(pattern, r'(await \1)', body)
            
        return body
        
    #---------------------------------------------------------------------------------
    # output code ... eventually should just use the parser stuff above !
    
    def output_openContext(self, out: SourceFile, name: str):
        out.pushLine(f"namespace {name} {{")
    
    def output_closeContext(self, out: SourceFile):
        out.pushLine("}")
    
    def output_struct(self, out: SourceFile, struct: dict):
        out.pushLine(f'    class {struct["name"]} {{', struct["name"].sourceLocation())
        for prop in struct["properties"]:
            decl = f'        {prop["name"]}'
            decl += f': {prop["type"]}' if "type" in prop else ""
            decl += f' = {prop["value"]}' if "value" in prop else ""
            decl += ";"
            out.pushLine(decl, prop["name"].sourceLocation())
        decl = "        constructor("
        for i, prop in enumerate(struct["properties"]):
            decl += f'{prop["name"]}'
            decl += f': {prop["type"]}' if "type" in prop else ""
            decl += f' = {prop["value"]}' if "value" in prop else ""
            decl += ", " if i < len(struct["properties"])-1 else ""
        decl += ") {"
        out.pushLine(decl)
        for prop in struct["properties"]:
            initCode = f'            this.{prop["name"]} = {prop["name"]};'
            out.pushLine(initCode)
        out.pushLine("        }")
        out.pushLine("    }")

    def output_variable(self, out: SourceFile, var: dict):
        decl = "    "
        decl += f'{var["modifier"]} ' if "modifier" in var else "var "
        decl += f'{var["name"]}'
        decl += f' : {var["type"]}' if "type" in var else ""
        decl += f' = {var["value"]};' if "value" in var else ";"
        out.pushLine(decl, var["name"].sourceLocation())
    
    def output_function(self, out: SourceFile, fnName: str, functions: List[dict], asyncFunctions: dict):
        def paramDeclStr(fn: dict) -> str:
            params = ""
            for i, param in enumerate(fn["parameters"]):
                params += f'{param["name"]}'
                params += f': {param["type"]}' if "type" in param else ""
                params += f' = {param["value"]}' if "value" in param else ""
                params += ", " if i < len(fn["parameters"])-1 else ""
            return params
        def returnTypeStr(fn: dict, isAsync: bool) -> str:
            if isAsync:
                rtype = str(fn["returnType"]).strip() if "returnType" in fn else "void"
                if not rtype.startswith("Promise<"):
                    rtype = f'Promise<{rtype}>'
                return f' : {rtype}'
            else:
                return f' : {fn["returnType"]}' if "returnType" in fn else ""
        def paramCallStr(fn: dict) -> str:
            params = ""
            for i, param in enumerate(fn["parameters"]):
                params += f'{param["name"]}'
                params += ", " if i < len(fn["parameters"])-1 else ""
            return params
        
        # preamble
        fn = functions[0]
        isAsync = fnName in asyncFunctions
        asyncKeyword = "async " if isAsync else ""
        returnType = str(functions[0]["returnType"]).strip() if "returnType" in functions[0] else None
        if returnType and returnType.startswith("Promise<"):
            returnType = returnType[8:-1]
        out.pushLine(f'    export {asyncKeyword}function {fn["name"]}({paramDeclStr(fn)}){returnTypeStr(fn, isAsync)} {{')
        
        if returnType!="":
            out.pushLine(f'        var _result: {returnType+"|" if returnType else ""}undefined;')

        existing = SourceFile()
        for fn in functions:
            modifier = fn["modifier"]
            newBlock = SourceFile()
            newBlock.pushLine(f'        // ------------------------ {fn["_feature"]} ------------------------', fn["name"].sourceLocation())
            call = '        '
            if returnType: call += f'_result = '
            awaitKeyword = "await " if "_async" in fn else ""
            asyncKeyword = "async " if "_async" in fn else ""
            call += f'{awaitKeyword}({asyncKeyword}() => {{'
            newBlock.pushLine(call)
            body = str(fn["body"])
            body = self.add_awaits(body, asyncFunctions)
            lines = body.split("\n")[:-1]
            loc = fn["body"].sourceLocation()
            path = loc.path
            lineIndex = loc.lineIndex
            for i, line in enumerate(lines):
                newBlock.pushLine(f'{'        '}{'    ' if i==0 else ''}{line}', SourceLocation(path, lineIndex+i))
            newBlock.pushLine(f'        }})();')

            if modifier == "on":
                if existing.code == "":
                    existing = newBlock
            elif modifier == "after":            
                existing.appendSource(newBlock)
            elif modifier == "before":
                if returnType:
                    newBlock.pushLine(f'        if (_result != undefined) return _result;')
                newBlock.appendSource(existing)
                existing = newBlock
            elif modifier == "replace":
                existing = newBlock

        out.appendSource(existing)

        # post-amble
        if returnType:
            out.pushLine(f'        return _result;')
        out.pushLine(f'    }}')
        
    def output_tests(self, out: SourceFile, features: List[dict], asyncFunctions: dict):
        asyncKeyword = "async " if len(asyncFunctions) > 0 else ""
        out.pushLine(f'    export {asyncKeyword}function _test() {{')
        for feature in features:
            tests = []
            for component in feature["components"]:
                if component["_type"] == "test":
                    tests.append(component)
            asyncCodes = []
            isAsync = False
            for test in tests:
                code = str(test["code"])
                asyncCode = self.add_awaits(code, asyncFunctions)
                asyncCodes.append(asyncCode)
                if code != asyncCode:
                    isAsync = True
            asyncKeyword = "async " if isAsync else ""
            feature["_isTestAsync"] = isAsync
            out.pushLine(f'        const _{feature["name"]}_test = {asyncKeyword}() => {{')
            for test in tests:
                code = str(test["code"])
                code = self.add_awaits(code, asyncFunctions)
                loc = test["code"].sourceLocation()
                if "==>" in code:
                    lhs = code.split("==>")[0].strip()
                    rhs = code.split("==>")[1].strip()
                    if rhs == "":
                        out.pushLine(f'            _output({lhs}, "{loc}");', loc)
                    else:
                        out.pushLine(f'            _assert({lhs}, {rhs}, "{loc}");', loc)
                else:
                    out.pushLine(f'            {code.strip()}', loc)
            out.pushLine(f'        }};')
        for feature in features:
            awaitKeyword = "await " if feature["_isTestAsync"] else ""
            out.pushLine(f'        try {{ {awaitKeyword}_{feature["name"]}_test(); }} catch (e) {{ console.error(e); }}')

        out.pushLine(f'    }}')
        