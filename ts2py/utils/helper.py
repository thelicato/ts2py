import os
import sys
from typing import List
from ts2py import types
from ts2py.utils.logger import Logger
from ts2py.utils.config import GRAMMAR_FILE


def banner(version: str):
    print(
        f"""
    ████████╗███████╗██████╗ ██████╗ ██╗   ██╗
    ╚══██╔══╝██╔════╝╚════██╗██╔══██╗╚██╗ ██╔╝
       ██║   ███████╗ █████╔╝██████╔╝ ╚████╔╝ 
       ██║   ╚════██║██╔═══╝ ██╔═══╝   ╚██╔╝  
       ██║   ███████║███████╗██║        ██║   
       ╚═╝   ╚══════╝╚══════╝╚═╝        ╚═╝   
    ts2py {version}
    """
    )


def check_path(path: str) -> None:
    if not os.path.exists(path):
        Logger().error(f"Defined path does not exist")
        sys.exit(1)


def check_grammar_file() -> None:
    if not os.path.exists(GRAMMAR_FILE) or not os.path.isfile(GRAMMAR_FILE):
        Logger().error(f"Grammar was not found at: {GRAMMAR_FILE}")
        sys.exit(1)


def use_type_union(compatibility: types.args.PythonCompatibilityArg) -> bool:
    use_type_union_list = [
        types.args.PythonCompatibilityArg.python310,
        types.args.PythonCompatibilityArg.python311,
    ]
    return True if compatibility in use_type_union_list else False


def check_ts_extension(filenames: List[str]) -> None:
    for filename in filenames:
        if not filename.lower().endswith(".ts"):
            Logger().error(f"File '{filename}' does not end with the '.ts' extension")
            sys.exit(1)
