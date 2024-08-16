# ᕦ(ツ)ᕤ
# deno.py
# author: asnaroo
# everything needed to setup, build, test and run a deno project

import os
import sys
import json

from backends.base import Backend
from util import *

#---------------------------------------------------------------------------------
# Deno backend class

class Deno(Backend):
    def __init__(self):
        super().__init__()

    def setup(self, project_path: str):
        # Create the project directory if it doesn't exist
        os.makedirs(project_path, exist_ok=True)

        # Change to the project directory
        os.chdir(project_path)

        # Create main.ts file
        with open('main.ts', 'w') as f:
            f.write('console.log("Hello, Deno!");')

        # Create deno.json configuration file
        deno_config = {
            "tasks": {
                "start": "deno run --allow-net main.ts"
            },
            "importMap": "import_map.json"
        }
        with open('deno.json', 'w') as f:
            json.dump(deno_config, f, indent=2)

        # Create import_map.json file
        import_map = {
            "imports": {}
        }
        with open('import_map.json', 'w') as f:
            json.dump(import_map, f, indent=2)

        print(f"Deno project initialized in {project_path}")

