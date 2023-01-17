from typing import Union, Callable, Tuple, List
from functools import partial
from typing_extensions import TypeAlias
from DHParser import Error, PreprocessorResult, IncludeInfo, RootNode

FindIncludeFunc: TypeAlias = Union[
    Callable[[str, int], IncludeInfo], partial  # (document: str,  start: int)
]
DeriveFileNameFunc: TypeAlias = Union[
    Callable[[str], str], partial
]  # include name -> file name
PreprocessorFunc: TypeAlias = Union[
    Callable[[str, str], PreprocessorResult], partial  # text: str, filename: str
]
Tokenizer: TypeAlias = Union[Callable[[str], Tuple[str, List[Error]]], partial]
TransformerCallable: TypeAlias = Union[Callable[[RootNode], RootNode], partial]
