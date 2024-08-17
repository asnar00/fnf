# ᕦ(ツ)ᕤ
# deno.py
# author: asnaroo
# everything needed to setup, build, test and run a deno project

import os
import sys
import json
import subprocess
import re
import requests
import shutil

from backends.base import Backend
from util import *

#---------------------------------------------------------------------------------
# Deno backend class

class Deno(Backend):
    def __init__(self):
        super().__init__()

    def check_version(self) -> str:
        try:
            # Check both the system PATH and the user's .deno/bin directory
            deno_path = shutil.which("deno")
            if deno_path:
                result = subprocess.run([deno_path, "--version"], check=True, capture_output=True, text=True)
            else:
                home_dir = os.path.expanduser("~")
                deno_bin = os.path.join(home_dir, ".deno", "bin", "deno")
                if os.path.exists(deno_bin):
                    result = subprocess.run([deno_bin, "--version"], check=True, capture_output=True, text=True)
                else:
                    return None
            version_output = result.stdout
            version_match = re.search(r"deno (\d+\.\d+\.\d+)", version_output)
            if version_match:
                return version_match.group(1)
            else:
                return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        
    def get_latest_version(self) ->str:
        try:
            response = requests.get("https://github.com/denoland/deno/releases/latest")
            latest_version = response.url.split('/')[-1].lstrip('v')
            return latest_version
        except requests.RequestException:
            log("Failed to fetch the latest version. Please check your internet connection.")
            return None
        
    def install_latest_version(self):
        try:
            log("Starting Deno installation...")
            # Using curl to download and run the Deno installer
            install_command = "curl -fsSL https://deno.land/x/install/install.sh | sh"
            result = subprocess.run(install_command, shell=True, check=True, capture_output=True, text=True)
            log("Installer output:")
            log(result.stdout)
            # Update PATH
            deno_path = os.path.expanduser("~/.deno/bin")
            update_PATH(deno_path)
            log("Deno installation completed and PATH updated.")
            return True
        except subprocess.CalledProcessError as e:
            log(f"Failed to install Deno: {e}")
            log("Error output:")
            log(e.stderr)
            return False

    def ensure_latest_version(self) -> bool:
        current_version = self.check_version()
        latest_version = self.get_latest_version()
        if latest_version == None:
            log("failed to determine latest version of Deno")
            return False 
        if current_version == None or current_version != latest_version:
            log(f"deno: current version is {current_version}, latest version is {latest_version}")
            log(f"installing Deno version {latest_version}")
            self.install_latest_version()
            return True
        log("deno is up to date :-)")

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
            "compilerOptions": {
                "allowJs": True,
                "lib": ["deno.window"]
            },
            "lint": {
                "files": {
                    "include": ["src/"]
                },
                "rules": {
                    "tags": ["recommended"]
                }
            },
            "fmt": {
                "files": {
                    "include": ["src/"]
                },
                "options": {
                    "useTabs": False,
                    "lineWidth": 80,
                    "indentWidth": 4,
                    "singleQuote": True,
                    "proseWrap": "always"
                }
            }
        }
        with open('deno.json', 'w') as f:
            json.dump(deno_config, f, indent=2)
        # Create import_map.json file
        import_map = {
            "imports": {}
        }
        with open('import_map.json', 'w') as f:
            json.dump(import_map, f, indent=2)
        log(f"Deno project initialized in {project_path}")

    def preamble(self) -> str:
        return """
var _file = "";
function _output(value: any, loc: string) { console.log(`${loc}:OUTPUT: ${value}`); }
function _assert(lhs: any, rhs: any, loc: string) { if (lhs !== rhs) console.log(`${loc}:FAIL: ${lhs}`); else console.log(`${loc}:PASS`); }"""
    
    def postamble(self, context: str) -> str:
        return f"""
function main() {{
    if (Deno.args.indexOf("-test") >= 0) {{
        console.log("testing {context}...");
        {context}._test();
        return;
    }}
}}

main();"""

    def run(self, filename: str, options: List[str]=[])->str:
        if not os.path.exists(filename):
            return f"Error: File not found: {filename}", ""
        try:
            # Run the Deno file
            result = subprocess.run(['deno', 'run', '--allow-all', filename, *options], 
                                    capture_output=True,
                                    text=True,
                                    check=True)
            if result.stderr:
                return result.stderr.strip()
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return e.stderr.strip()
        except FileNotFoundError:
            return "Error: Deno is not installed or not in the system PATH.", ""
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}", ""

