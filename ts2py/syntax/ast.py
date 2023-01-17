from functools import partial
from DHParser import (
    traverse,
    change_name,
    ThreadLocalSingletonFactory,
)
from ts2py import types

ts2py_AST_transformation_table = {
    # AST Transformations for the ts2py-grammar
    # "<": flatten,
    ":Text": change_name("TEXT", "")
    # "*": replace_by_single_child
}


def ts2py_transformer() -> types.dhparser.TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=ts2py_AST_transformation_table.copy())


get_transformer = ThreadLocalSingletonFactory(ts2py_transformer, ident="1")


def transform_ts2py(cst):
    get_transformer()(cst)
