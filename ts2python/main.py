#!/usr/bin/env python3

"""ts2python.py - compiles typescript dataclasses to Python
        TypedDicts <https://www.python.org/dev/peps/pep-0589/>

Copyright 2021  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences and Humanities (badw.de)

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
import sys
import re
from typing import Tuple, List, Union, Any
from DHParser import (
    start_logging,
    is_filename,
    compile_source,
    set_config_value,
    access_presets,
    finalize_presets,
    Error,
    canonical_error_strings,
    has_errors,
    FATAL,
    set_preset_value,
    get_config_values,
    StringView,
)
from ts2python.utils.config import GRAMMAR_FILE, INI_FILE
from ts2python.utils import logger
from ts2python.syntax import preprocessor, ast, parser, compiler


def compile_src(source: str) -> Tuple[Any, List[Error]]:
    """Compiles ``source`` and returns (result, errors)."""
    result_tuple = compile_source(
        source,
        preprocessor.get_preprocessor(),
        parser.get_grammar(),
        ast.get_transformer(),
        compiler.get_compiler(),
    )
    return result_tuple[:2]  # drop the AST at the end of the result tuple


def serialize_result(result: Any) -> Union[str, bytes]:
    if isinstance(result, (str, StringView)):
        return str(result)
    return repr(result)


def process_file(source: str, result_filename: str = "") -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors of warnings occurred.
    """
    source_filename = source if is_filename(source) else ""
    if os.path.isfile(result_filename):
        with open(result_filename, "r", encoding="utf-8") as results_file:
            result = results_file.read()
        if source_filename == source:
            with open(source_filename, "r", encoding="utf-8") as source_file:
                source = source_file.read()
        match = re.search('source_hash__ *= *"([\w.!? ]*)"', result)
        if match and match.groups()[-1] == compiler.source_hash(source):
            return ""  # no re-compilation necessary, because source hasn't changed
    result, errors = compile_src(source)
    if not has_errors(errors, FATAL):
        if os.path.abspath(source_filename) != os.path.abspath(result_filename):
            with open(result_filename, "w", encoding="utf-8") as results_file:
                results_file.write(serialize_result(result))
        else:
            errors.append(
                Error(
                    f"Source and destination have the same name '{result_filename}'!",
                    0,
                    FATAL,
                )
            )
    if errors:
        logger.error("\n".join(canonical_error_strings(errors)))
    return ""


def main():
    if not os.path.exists(GRAMMAR_FILE) or not os.path.isfile(GRAMMAR_FILE):
        logger.error(f"Grammar was not found at: {GRAMMAR_FILE}")
        sys.exit(1)

    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Parses a ts2python-file and shows its syntax-tree."
    )
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "-D",
        "--debug",
        action="store_const",
        const="debug",
        help="Store debug information in LOGS subdirectory",
    )
    parser.add_argument(
        "-o",
        "--out",
        nargs=1,
        default=["out"],
        help="Output directory for batch processing",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_const", const="verbose", help="Verbose output"
    )
    parser.add_argument(
        "--singlethread",
        action="store_const",
        const="singlethread",
        help="Run batch jobs in a single thread (recommended only for debugging)",
    )
    parser.add_argument(
        "-c",
        "--compatibility",
        nargs=1,
        action="extend",
        type=str,
        help="Minimal required python version (must be >= 3.6)",
    )
    parser.add_argument(
        "-b",
        "--base",
        nargs=1,
        action="extend",
        type=str,
        help="Base class name, e.g. TypedDict (default) or BaseModel (pydantic)",
    )
    parser.add_argument(
        "-d",
        "--decorator",
        nargs=1,
        action="extend",
        type=str,
        help="addes the given decorator ",
    )
    parser.add_argument(
        "-p",
        "--peps",
        nargs="+",
        action="extend",
        type=str,
        help="Assume Python-PEPs, e.g. 655 or ~655",
    )

    args = parser.parse_args()
    file_names, log_dir = args.files, ""

    from DHParser.configuration import read_local_config

    read_local_config(INI_FILE)

    if args.debug or args.compatibility or args.base or args.decorator or args.peps:
        access_presets()
        if args.debug is not None:
            log_dir = "LOGS"
            set_preset_value("history_tracking", True)
            set_preset_value("resume_notices", True)
            set_preset_value(
                "log_syntax_trees", frozenset(["cst", "ast"])
            )  # don't use a set literal, here
        if args.compatibility:
            version_info = tuple(int(part) for part in args.compatibility[0].split("."))
            if version_info >= (3, 10):
                set_preset_value("ts2python.UseTypeUnion", True, allow_new_key=True)
        if args.base:
            set_preset_value("ts2python.BaseClassName", args.base[0].strip())
        if args.decorator:
            set_preset_value("ts2python.ClassDecorator", args.decorator[0].strip())
        if args.peps:
            args_peps = [pep.strip() for pep in args.peps]
            all_peps = {"435", "584", "604", "655", "~435", "~584", "~604", "~655"}
            if not all(pep in all_peps for pep in args_peps):
                print(
                    f"Unsupported PEPs specified: {args_peps}\n"
                    "Allowed PEP arguments are:\n"
                    "  435  - use Enums (Python 3.4)\n"
                    "  604  - use type union (Python 3.10)\n"
                    "  584  - use Literal type (Python 3.8)\n"
                    "  655  - use NotRequired instead of Optional\n"
                )
                sys.exit(1)
            for pep in args_peps:
                kwargs = {"value": pep[0] != "~", "allow_new_key": True}
                if pep == "435":
                    set_preset_value("ts2python.UseEnum", **kwargs)
                if pep == "584":
                    set_preset_value("ts2python.UseLiteralType", **kwargs)
                if pep == "604":
                    set_preset_value("ts2python.TypeUnion", **kwargs)
                if pep == "655":
                    set_preset_value("ts2python.UseNotRequired", **kwargs)
        finalize_presets()
        _ = get_config_values("ts2python.*")  # fill config value cache

    start_logging(log_dir)

    set_config_value("batch_processing_parallelization", False)

    def echo(message: str):
        if args.verbose:
            print(message)

    if len(file_names) == 1:
        if os.path.isdir(file_names[0]):
            dir_name = file_names[0]
            echo("Processing all files in directory: " + dir_name)
            file_names = [
                os.path.join(dir_name, fn)
                for fn in os.listdir(dir_name)
                if os.path.isfile(os.path.join(dir_name, fn))
            ]

    assert file_names[0].lower().endswith(".ts")
    error_filename = process_file(file_names[0], file_names[0][:-3] + ".py")
    if error_filename:
        with open(error_filename, "r", encoding="utf-8") as error_file:
            print(error_file.read())


if __name__ == "__main__":
    main()
