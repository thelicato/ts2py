import os

GRAMMAR_FILE = (
    f"{os.path.dirname(os.path.abspath(__package__))}/ts2python/assets/ts2python.ebnf"
)
GRAMMAR_FILE = (
    f"{os.path.dirname(os.path.abspath(__package__))}/ts2python/assets/ts2python.ini"
)

# Colors
SUCCESS_C = "\033[92m"
DEBUG_C = "\033[93m"
ERROR_C = "\033[91m"
END_C = "\033[0m"
