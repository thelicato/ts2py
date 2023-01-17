from importlib import metadata

__title__ = "ts2py"
__description__ = "Python-Interoperability for Typescript-Interfaces"

try:
    __version__ = f"v{metadata.version(__package__)}"
except:
    __version__ = ""
