# ᕦ(ツ)ᕤ
# language/base.py
# author: asnaroo
# Language is the base class for all supported languages

from util import *

class Language:
    def __init__(self): pass
    def extension(self): pass
    def indent(self): pass
    def undent(self): pass
    def feature(self): pass
    def component(self): pass
    def variable(self): pass
    def struct(self): pass
    def function(self): pass
    def is_function_async(self, fn: dict) -> bool: pass
    def add_awaits(self, body: str, asyncFns: dict) -> str: pass
    def output_openContext(self, out: SourceFile, name: str): pass
    def output_closeContext(self, out: SourceFile): pass
    def output_struct(self, out: SourceFile, struct: dict): pass
    def output_variable(self, out: SourceFile, var: dict): pass
    def output_function(self, out: SourceFile, fnName: str, function: List[dict], asyncFns: dict): pass
    def output_tests(self, out: SourceFile, features: List[dict], asyncFns: dict): pass

    @staticmethod
    def findLanguage(ext: str) -> 'Language':
        for subclass in Language.__subclasses__():
            if subclass().extension() == ext:
                return subclass()
        return None