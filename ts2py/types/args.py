from enum import Enum


class PythonCompatibilityArg(str, Enum):
    PYTHON36 = "3.6"
    PYTHON37 = "3.7"
    PYTHON38 = "3.8"
    PYTHON39 = "3.9"
    PYTHON310 = "3.10"
    PYTHON311 = "3.11"


class PepArg(str, Enum):
    PEP435 = "435"
    PEP584 = "584"
    PEP604 = "604"
    PEP655 = "655"
