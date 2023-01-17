#!/usr/bin/env python3

"""ts2py - compiles typescript dataclasses to Python
        TypedDicts <https://www.python.org/dev/peps/pep-0589/>

Copyright 2023  by
                Angelo Delicato (thelicato@duck.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import os
from typing import List, Tuple, Optional, Any
import typer
from DHParser import (
    compile_source,
    set_config_value,
    finalize_presets,
    Error,
    canonical_error_strings,
    has_errors,
    FATAL,
    set_preset_value,
    StringView,
    read_local_config,
    access_presets,
)
from ts2py.syntax import preprocessor, ast, parser, compiler
from ts2py import __version__, types
from ts2py.utils import helper
from ts2py.utils.config import INI_FILE
from ts2py.utils.logger import Logger

app = typer.Typer(
    add_completion=False, context_settings={"help_option_names": ["-h", "--help"]}
)


def compile_src(source: str) -> Tuple[Any, List[Error]]:
    """
    Compiles ``source`` and returns (result, errors).
    """
    result_tuple = compile_source(
        source,
        preprocessor.get_preprocessor(),
        parser.get_grammar(),
        ast.get_transformer(),
        compiler.get_compiler(),
    )
    return result_tuple[:2]  # drop the AST at the end of the result tuple


def serialize_result(result: Any) -> str:
    """
    Serialize the result
    """
    if isinstance(result, (str, StringView)):
        return str(result)
    return repr(result)


def process_file(source: str, target: str) -> None:
    """
    Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    returned in the terminal output.
    """
    if os.path.isfile(target):
        Logger().info(f"Target file '{target}' already exists, deleting it...")
        os.remove(target)
    result, errors = compile_src(source)
    if not has_errors(errors, FATAL):
        with open(target, "w", encoding="utf-8") as results_file:
            results_file.write(serialize_result(result))
    if errors:
        Logger().error("\n".join(canonical_error_strings(errors)))
    else:
        Logger().success(f"Conversion for file '{source}' completed succesfully")


@app.command()
def convert(
    path: str = typer.Argument(
        ..., help="Define the path to the file or the folder to process"
    ),
    compatibility: types.args.PythonCompatibilityArg = typer.Option(
        "3.11",
        "--compatibility",
        "-c",
        help="Minimal required Python version (must be >= 3.6)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    peps: List[types.args.PepArg] = typer.Option(
        ["655"], "--pep", "-p", help="Assume Python-PEPs, e.g. 655"
    ),
    decorator: Optional[str] = typer.Option(
        None, "--decorator", help="Add the given decorator"
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
):
    """
    Convert from TypeScript interface/type to Python TypedDict
    """
    helper.check_path(path)
    helper.check_grammar_file()
    read_local_config(INI_FILE)
    access_presets()

    # Set verbose
    Logger().set_verbose(verbose)
    # Set PEPS
    for pep in peps:
        kwargs = {"value": True, "allow_new_key": True}
        if pep == types.args.PepArg.PEP435:
            set_preset_value("ts2py.UseEnum", **kwargs)
        if pep == types.args.PepArg.PEP584:
            set_preset_value("ts2py.UseLiteralType", **kwargs)
        if pep == types.args.PepArg.PEP604:
            set_preset_value("ts2py.TypeUnion", **kwargs)
        if pep == types.args.PepArg.PEP655:
            set_preset_value("ts2py.UseNotRequired", **kwargs)
    # Set compatibility
    if helper.use_type_union(compatibility):
        set_preset_value("ts2py.UseTypeUnion", True, allow_new_key=True)
    # Set decorator
    if decorator:
        set_preset_value("ts2py.ClassDecorator", decorator)
    # Set debug mode
    if debug:
        set_preset_value("history_tracking", True)
        set_preset_value("resume_notices", True)
        set_preset_value(
            "log_syntax_trees", frozenset(["cst", "ast"])
        )  # don't use a set literal, here
    finalize_presets()
    set_config_value("batch_processing_parallelization", False)

    if os.path.isdir(path):
        filenames = [
            os.path.join(path, fn)
            for fn in os.listdir(path)
            if os.path.isfile(os.path.join(path, fn))
        ]
    else:
        filenames = [path]

    helper.check_ts_extension(filenames)
    for filename in filenames:
        process_file(filename, f"{filename[:-3]}.py")


def main():
    helper.banner(__version__)
    app()


if __name__ == "__main__":
    main()
