# ᕦ(ツ)ᕤ
# backends/base.py
# author: asnaroo
# Backend is the base class for all supported backends

from util import *

class Backend:
    def __init__(self): pass
    def check_version(self) -> str: pass
    def get_latest_version(self) -> str: pass
    def install_latest_version(self): pass
    def ensure_latest_version(self) -> bool: pass
    def setup(self, project_path: str): pass
    def preamble(self) -> str: pass
    def postamble(self, context: str) -> str: pass
    def run(self, filename: str, options: List[str] =[], processLineFn=None) -> str : pass
