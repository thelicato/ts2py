from functools import partial
from typing import Tuple, List
from DHParser import (
    ThreadLocalSingletonFactory,
    Error,
    NEVER_MATCH_PATTERN,
    gen_find_include_func,
    preprocess_includes,
    make_preprocessor,
    chain_preprocessors,
)
from ts2py import types

RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def ts2py_tokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> types.dhparser.PreprocessorFunc:
    # below, the second parameter must always be the same as ts2pyGrammar.COMMENT__!
    find_next_include = gen_find_include_func(
        RE_INCLUDE, "(?:\\/\\/.*)|(?:\\/\\*(?:.|\\n)*?\\*\\/)"
    )
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(ts2py_tokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident="1")
