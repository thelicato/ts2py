from pathlib import Path

FILE_PATH = Path(__file__)
MAIN_DIR = FILE_PATH.parent.parent.absolute()

GRAMMAR_FILE = f"{MAIN_DIR}/assets/ts2python.ebnf"
INI_FILE = f"{MAIN_DIR}/assets/ts2pythonParser.ini"

# Colors
SUCCESS_C = "\033[92m"
DEBUG_C = "\033[93m"
ERROR_C = "\033[91m"
END_C = "\033[0m"
