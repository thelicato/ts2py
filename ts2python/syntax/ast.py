from functools import partial
from DHParser import (
    traverse,
    change_name,
    ThreadLocalSingletonFactory,
)
from ts2python import types

ts2python_AST_transformation_table = {
    # AST Transformations for the ts2python-grammar
    # "<": flatten,
    ":Text": change_name("TEXT", "")
    # "*": replace_by_single_child
}


def ts2python_transformer() -> types.dhparser.TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(
        traverse, transformation_table=ts2python_AST_transformation_table.copy()
    )


get_transformer = ThreadLocalSingletonFactory(ts2python_transformer, ident="1")


def transform_ts2python(cst):
    get_transformer()(cst)
