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
                        set("name", word()),
                        keyword("("),
                        set("parameters", list(self.variable())),
                        keyword(")"),
                        optional(sequence(keyword(":"), 
                                        set("returnType", word()))),
                        self.indent(),
                        set("body", toUndent()),
                        self.undent()))
    
    def test(self):
        return label("test", sequence(keyword(">"),
                                set("code", toEnd("\n"))))
    
    #---------------------------------------------------------------------------------
    # output code ... eventually should just use the parser stuff above !
    
    def output_openContext(self, out: SourceFile, name: str):
        out.pushLine(f"export namespace {name} {{")
    
    def output_closeContext(self, out: SourceFile):
        out.pushLine("}")
    
    def output_struct(self, out: SourceFile, struct: dict):
        out.pushLine(f'    class {struct["name"]} {{', struct["name"].line())
        for prop in struct["properties"]:
            decl = f'        {prop["name"]}'
            decl += f': {prop["type"]}' if "type" in prop else ""
            decl += f' = {prop["value"]}' if "value" in prop else ""
            decl += ";"
            out.pushLine(decl, prop["name"].line())
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
        out.pushLine(decl, var["name"].line())
    
    def output_function(self, out: SourceFile, fnName: str, functions: List[dict]):
        def paramDeclStr(fn: dict) -> str:
            params = ""
            for i, param in enumerate(fn["parameters"]):
                params += f'{param["name"]}'
                params += f': {param["type"]}' if "type" in param else ""
                params += f' = {param["value"]}' if "value" in param else ""
                params += ", " if i < len(fn["parameters"])-1 else ""
            return params
        def returnTypeStr(fn: dict) -> str:
            return f' : {fn["returnType"]}' if "returnType" in fn else ""
        def paramCallStr(fn: dict) -> str:
            params = ""
            for i, param in enumerate(fn["parameters"]):
                params += f'{param["name"]}'
                params += ", " if i < len(fn["parameters"])-1 else ""
            return params
        
        #function hello(name: string) : number {
        #var _result: number;
        fn = functions[0]
        decl = f'    function {fnName}({paramDeclStr(fn)}){returnTypeStr(fn)} {{'
        out.pushLine(decl, fnName.line())
        resultType = fn["returnType"] if "returnType" in fn else "void"
        if resultType != "void":
            out.pushLine(f'        var _result: {resultType};')

        for i, fn in enumerate(functions):
            feature = fn["_feature"]
            decl = f'        const _{feature}_{fnName} = ({paramDeclStr(fn)}){returnTypeStr(fn)} => {{'
            out.pushLine(decl, fn["name"].line())
            body = fn["body"]
            lines = body.file.code[body.start:body.end].split("\n")
            if lines[-1]=="": lines.pop()
            bodyLine = body.line()
            for i, line in enumerate(lines):
                out.pushLine(f'            {line}', bodyLine+i)
            out.pushLine(f'        }};')

        call = ""
        if resultType == "void":
            call = f'        _{feature}_{fnName}({paramCallStr(fn)});'
        else:
            call = f'        _result = _{feature}_{fnName}({paramCallStr(fn)});'

        out.pushLine(call)
        
        # right at the end
        if resultType != "void":
            out.pushLine("        return _result;")
        out.pushLine("    }")

    def output_tests(self, out: SourceFile, features: List[dict]):
        out.pushLine(f'    function _test() {{')
        for feature in features:
            tests = []
            for component in feature["components"]:
                if component["_type"] == "test":
                    tests.append(component)
            if len(tests) == 0: continue
            out.pushLine(f'        const _{feature["name"]}_test = () => {{')
            
            if "_mdFile" in feature:
                out.pushLine(f'            _source("{feature["_mdFile"]}");')
            for test in tests:
                testCode = str(test["code"])
                testLine = test["code"].line()
                if "==>" in testCode:
                    lhs = testCode.split("==>")[0].strip()
                    rhs = testCode.split("==>")[1].strip()
                    if rhs == "":
                        out.pushLine(f'            _output({lhs}, {testLine});', testLine)
                    else:
                        out.pushLine(f'            _assert({lhs}, {rhs}, {testLine});', testLine)
                else:
                    out.pushLine(f'            {testCode}', testLine)
            out.pushLine(f'        }};')
        for feature in features:
            out.pushLine(f'        try {{ _{feature["name"]}_test(); }} catch (e) {{ console.error(e); }}')

        out.pushLine(f'    }}')
        