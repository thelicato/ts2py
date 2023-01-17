from enum import Enum


class PythonCompatibilityArg(str, Enum):
    python36 = "3.6"
    python37 = "3.7"
    python38 = "3.8"
    python39 = "3.9"
    python310 = "3.10"
    python311 = "3.11"


class PepArg(str, Enum):
    pep435 = "435"
    pep584 = "584"
    pep604 = "604"
    pep655 = "655"
