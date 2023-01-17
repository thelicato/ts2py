import keyword
from functools import lru_cache
import re
from typing import Tuple, List, Any, Set, Dict, Sequence, cast
from DHParser import (
    Compiler,
    Node,
    get_config_value,
    ErrorCode,
    ThreadLocalSingletonFactory,
    pick_from_path,
    md5,
    as_list,
)

# TODO: check source hash
def source_hash(source_text: str) -> str:
    try:
        with open(__file__, "r", encoding="utf-8") as current_file:
            script_hash = md5(current_file.read())
    except (FileNotFoundError, IOError):
        script_hash = "source of ts2pyParser.py not found!?"
    return " ".join([md5(source_text), script_hash])


TYPING_TYPES = [
    "NotRequired",
    "Literal",
    "Union",
    "Optional",
    "Any",
    "Generic",
    "TypeVar",
    "Callable",
    "Coroutine",
    "List",
    "Tuple",
    "Dict",
]


def get_typing_imports(python_code: Any):
    initial_import_line = "from typing import"
    typing_types_to_add = ["TypedDict"]
    for typing_type in TYPING_TYPES:
        typing_match = re.search(rf"\b({typing_type})\b", python_code)
        if typing_match:
            typing_types_to_add.append(typing_type)
    typing_types_str = ", ".join(typing_types_to_add)
    return f"{initial_import_line} {typing_types_str}"


def to_typename(varname: str) -> str:
    # assert varname[-1:] != '_' or keyword.iskeyword(varname[:-1]), varname  # and varname[0].islower()
    return varname[0].upper() + varname[1:] + "_"


def to_varname(typename: str) -> str:
    assert typename[0].isupper() or typename[-1:] == "_", typename
    return typename[0].lower() + (
        typename[1:-1] if typename[-1:] == "_" else typename[1:]
    )


NOT_YET_IMPLEMENTED_WARNING = ErrorCode(310)
UNSUPPORTED_WARNING = ErrorCode(320)

TYPE_NAME_SUBSTITUTION = {
    "object": "Dict",
    "array": "List",
    "string": "str",
    "number": "float",
    "decimal": "float",
    "integer": "int",
    "uinteger": "int",
    "boolean": "bool",
    "null": "None",
    "undefined": "None",
    "unknown": "Any",
    "any": "Any",
    "void": "None",
    "Thenable": "Coroutine",
    "Array": "List",
    "ReadonlyArray": "List",
    "Uint32Array": "List[int]",
    "Error": "Exception",
    "RegExp": "str",
}


class TS2PyCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ts2py source file."""

    def reset(self):
        super().reset()
        bcn = get_config_value("ts2py.BaseClassName", "TypedDict")
        i = bcn.rfind(".")
        if i >= 0:
            self.additional_imports = f"\nfrom {bcn[:i]} import {bcn[i + 1:]}\n"
            bcn = bcn[i + 1 :]
        else:
            self.additional_imports = ""
        self.base_class_name = bcn
        self.class_decorator = get_config_value("ts2py.ClassDecorator", "").strip()
        if self.class_decorator:
            if self.class_decorator[0] != "@":
                self.class_decorator = "@" + self.class_decorator
            self.class_decorator += "\n"
        self.use_enums = get_config_value("ts2py.UseEnum", True)
        self.use_type_union = get_config_value("ts2py.UseTypeUnion", False)
        self.use_literal_type = get_config_value("ts2py.UseLiteralType", True)
        self.use_not_required = get_config_value("ts2py.UseNotRequired", False)

        self.overloaded_type_names: Set[str] = set()
        self.known_types: List[Set[str]] = [
            {
                "Union",
                "List",
                "Tuple",
                "Optional",
                "Dict",
                "Any",
                "Generic",
                "Coroutine",
                "list",
            }
        ]
        self.local_classes: List[List[str]] = [[]]
        self.base_classes: Dict[str, List[str]] = {}
        self.typed_dicts: Set[str] = {
            "TypedDict"
        }  # names of classes that are TypedDicts
        # self.default_values: Dict = {}
        # self.referred_objects: Dict = {}
        self.basic_type_aliases: Set[str] = set()
        self.obj_name: List[str] = ["TOPLEVEL_"]
        self.scope_type: List[str] = [""]
        self.optional_keys: List[List[str]] = [[]]
        self.func_name: str = ""  # name of the current functions header or ''
        self.strip_type_from_const = False

    def compile(self, node) -> str:
        result = super().compile(node)
        if isinstance(result, str):
            return result
        raise TypeError(
            f"Compilation of {node.name} yielded a result of "
            f"type {str(type(result))} and not str as expected!"
        )

    def is_toplevel(self) -> bool:
        return self.obj_name == ["TOPLEVEL_"]

    def is_known_type(self, typename: str) -> bool:
        for type_set in self.known_types:
            if typename in type_set:
                return True
        return False

    # def qualified_obj_name(self, pos: int=0, varname: bool=False) -> str:
    #     obj_name = self.obj_name[1:] if len(self.obj_name) > 1 else self.obj_name
    #     if pos < 0:  obj_name = obj_name[:pos]
    #     if varname:  obj_name = obj_name[:-1] + [to_varname(obj_name[-1])]
    #     return '.'.join(obj_name)

    def prepare(self, root: Node) -> None:
        # Using 'str(nd["identifier"])' instead of 'nd["identifier"].content'
        type_aliases = {
            str(nd["identifier"]) for nd in root.select_children("type_alias")
        }
        namespaces = {str(nd["identifier"]) for nd in root.select_children("namespace")}
        self.overloaded_type_names = type_aliases & namespaces

    def finalize(self, python_code: Any) -> Any:
        code_blocks = []
        if self.tree.name == "document":
            code_blocks.append(get_typing_imports(python_code))
        code_blocks.append(python_code)
        cooked = "\n\n".join(code_blocks)
        cooked = re.sub(" +(?=\n)", "", cooked)
        return re.sub(r"\n\n\n+", "\n\n\n", cooked)

    def on_EMPTY__(self) -> str:
        return ""

    def on_ZOMBIE__(self, node) -> str:
        self.tree.new_error(
            node, "Malformed syntax-tree! Possibly caused by a parsing error."
        )
        return ""
        # raise ValueError('Malformed syntax-tree!')

    def on_document(self, node) -> str:
        if "module" in node and isinstance(node["module"], Sequence) > 1:
            self.tree.new_error(
                node,
                "Transpiling more than a single ambient module "
                "is not yet implemented! Only the first ambient module will "
                "be transpiled for now.",
                NOT_YET_IMPLEMENTED_WARNING,
            )
            return self.compile(node["module"][0]["document"])
        self.mark_overloaded_functions(node)
        return "\n\n".join(
            self.compile(child)
            for child in node.children
            if child.name != "declaration"
        )

    def on_module(self, node) -> str:
        # name = self.compile(node["identifier"])
        return self.compile(node["document"])

    def render_class_header(
        self, name: str, base_classes: str, force_base_class: str = ""
    ) -> str:
        optional_key_list = self.optional_keys.pop()
        decorator = self.class_decorator
        base_class_name = (force_base_class or self.base_class_name).strip()
        if base_class_name == "TypedDict":
            total = not bool(optional_key_list) or self.use_not_required
            if base_classes:
                if base_classes.find("Generic[") >= 0:
                    td_name = "GenericTypedDict"
                else:
                    td_name = "TypedDict"
                if self.use_not_required:
                    return decorator + f"class {name}({base_classes}, {td_name}):\n"
                return (
                    decorator + f"class {name}({base_classes}, "
                    f"{td_name}, total={total}):\n"
                )
            if self.use_not_required:
                return decorator + f"class {name}(TypedDict):\n"
            return decorator + f"class {name}(TypedDict, total={total}):\n"
        if base_classes:
            if base_class_name:
                return decorator + f"class {name}({base_classes}, {base_class_name}):\n"
            return decorator + f"class {name}({base_classes}):\n"
        if base_class_name:
            return decorator + f"class {name}({base_class_name}):\n"
        return decorator + f"class {name}:\n"

    def render_local_classes(self) -> str:
        self.func_name = ""
        classes = self.local_classes.pop()
        return "\n".join(lc for lc in classes) + "\n" if classes else ""

    def process_type_parameters(self, node: Node) -> Tuple[str, str]:
        try:
            nd_type_parameters = cast(Node, node["type_parameters"])
            type_parameters = self.compile(nd_type_parameters)
            type_parameters = type_parameters.strip("'")
            preface = f"{type_parameters} = TypeVar('{type_parameters}')\n"
            self.known_types[-1].add(type_parameters)
        except KeyError:
            type_parameters = ""
            preface = ""
        return type_parameters, preface

    def on_interface(self, node) -> str:
        name = self.compile(node["identifier"])
        self.obj_name.append(name)
        self.scope_type.append("interface")
        self.local_classes.append([])
        self.optional_keys.append([])
        type_parameters, preface = self.process_type_parameters(node)
        preface += "\n"
        preface += node.get_attr("preface", "")
        self.known_types.append(set())
        base_class_list = []
        try:
            base_class_list = self.bases(node["extends"])
            base_classes = self.compile(node["extends"])
            if type_parameters:
                base_classes += f", Generic[{type_parameters}]"
        except KeyError:
            base_classes = f"Generic[{type_parameters}]" if type_parameters else ""
        if any(bc not in self.typed_dicts for bc in base_class_list):
            force_base_class = " "
        elif "function" in node["declarations_block"]:
            force_base_class = " "  # do not derive from TypeDict
        else:
            force_base_class = ""
            self.typed_dicts.add(name)
        decls = self.compile(node["declarations_block"])
        interface = self.render_class_header(name, base_classes, force_base_class)
        self.base_classes[name] = base_class_list
        interface += (
            "    " + self.render_local_classes().replace("\n", "\n    ")
        ).rstrip(" ")
        self.known_types.pop()
        self.known_types[-1].add(name)
        self.scope_type.pop()
        self.obj_name.pop()
        return preface + interface + "    " + decls.replace("\n", "\n    ")

    # def on_type_parameter(self, node) -> str:  # OBSOLETE, see on_type_parameters()
    #     return self.compile(node['identifier'])

    @lru_cache(maxsize=4)
    def bases(self, node) -> List[str]:
        assert node.name == "extends"
        bases = [self.compile(nd) for nd in node.children]
        return [TYPE_NAME_SUBSTITUTION.get(bc, bc) for bc in bases]

    def on_extends(self, node) -> str:
        return ", ".join(self.bases(node))

    def on_type_alias(self, node) -> str:
        alias = self.compile(node["identifier"])
        if all(typ[0].name in ("basic_type", "literal") for typ in node.select("type")):
            self.basic_type_aliases.add(alias)
        self.obj_name.append(alias)
        if alias not in self.overloaded_type_names:
            self.known_types[-1].add(alias)
            self.local_classes.append([])
            self.optional_keys.append([])
            types = self.compile(node["types"])
            preface = self.render_local_classes()
            code = preface + f"{alias} = {types}"
        else:
            code = ""
        self.obj_name.pop()
        return code

    def mark_overloaded_functions(self, scope: Node):
        is_interface = self.scope_type[-1] == "interface"
        first_use: Dict[str, Node] = {}
        try:
            for func_decl in as_list(scope["function"]):
                name = func_decl["identifier"].content
                if keyword.iskeyword(name):
                    name += "_"
                if name in first_use:
                    first_use[name].attr["decorator"] = (
                        "@singledispatchmethod" if is_interface else "@singledispatch"
                    )
                    func_decl.attr["decorator"] = f"@{name}.register"
                else:
                    first_use[name] = func_decl
        except KeyError:
            pass  # no functions in declarations block

    def on_declarations_block(self, node) -> str:
        self.mark_overloaded_functions(node)
        declarations = "\n".join(
            self.compile(nd) for nd in node if nd.name in ("declaration", "function")
        )
        return declarations or "pass"

    def on_declaration(self, node) -> str:
        identifier = self.compile(node["identifier"])
        self.obj_name.append(to_typename(identifier))
        python_type = (
            self.compile_type_expression(node, node["types"])
            if "types" in node
            else "Any"
        )
        typename = self.obj_name.pop()
        if python_type[0:5] == "class":
            self.local_classes[-1].append(python_type)
            python_type = typename  # substitute typename for type
        if "optional" in node:
            self.optional_keys[-1].append(identifier)
            if self.use_not_required:
                python_type = f"NotRequired[{python_type}]"
            else:
                if python_type.startswith("Union["):
                    if python_type.find("None") < 0:
                        python_type = python_type[:-1] + ", None]"
                elif python_type.find("|") >= 0:
                    if python_type.find("None") < 0:
                        python_type += "|None"
                else:
                    python_type = f"Optional[{python_type}]"
        if self.is_toplevel() and bool(self.local_classes[-1]):
            preface = self.render_local_classes()
            self.local_classes.append([])
            self.optional_keys.append([])
            return preface + f"{identifier}: {python_type}"
        return f"{identifier}: {python_type}"

    def on_function(self, node) -> str:
        is_constructor = False
        if "identifier" in node:
            name = self.compile(node["identifier"])
            self.func_name = name
            if name == "constructor" and self.scope_type[-1] == "interface":
                name = self.obj_name[-1] + "Constructor"
                is_constructor = True
        else:  # anonymous function
            name = "__call__"
        _tp, preface = self.process_type_parameters(node)
        try:
            arguments = self.compile(node["arg_list"])
            if self.scope_type[-1] == "interface":
                arguments = "self, " + arguments
        except KeyError:
            arguments = "self" if self.scope_type[-1] == "interface" else ""
        try:
            return_type = self.compile(node["types"])
        except KeyError:
            return_type = "Any"
        decorator = node.get_attr("decorator", "")
        if decorator:
            if decorator.endswith(".register"):
                name = "_"
            decorator += "\n"
        pyfunc = (
            f"{preface}\n{decorator}def {name}({arguments}) -> {return_type}:\n    pass"
        )
        if is_constructor:
            interface = pick_from_path(self.path, "interface", reverse=True)
            assert interface
            interface.attr["preface"] = "".join(
                [interface.get_attr("preface", ""), pyfunc, "\n"]
            )
            return ""
        return pyfunc

    def on_arg_list(self, node) -> str:
        breadcrumb = "/".join(nd.name for nd in self.path)
        if breadcrumb.rfind("func_type") > breadcrumb.rfind("function"):
            arg_list = [self.compile(nd) for nd in node.children]
            if any(arg[0:1] == "*" for arg in arg_list):
                return "..."
            return ", ".join(re.sub(r"^\w+\s*:\s*", "", arg) for arg in arg_list)
        return ", ".join(self.compile(nd) for nd in node.children)

    def on_arg_tail(self, node):
        argname = self.compile(node["identifier"])
        if "array_of" in node:
            typename = self.compile(node["array_of"])[5:-1]
            return f"*{argname}: {typename}"
        return "*" + argname

    def on_argument(self, node) -> str:
        argname = self.compile(node["identifier"])
        if "types" in node:
            # types = self.compile(node['types'])
            self.obj_name.append(to_typename(argname))
            types = self.compile_type_expression(node, node["types"])
            self.obj_name.pop()
            if "optional" in node:
                types = f"Optional[{types}] = None"
            return f"{argname}: {types}"
        return f"{argname} = None" if "optional" in node else argname

    def on_optional(self, _node):
        assert False, "This method should never have been called!"

    def on_index_signature(self, node) -> str:
        return self.compile(node["type"])

    def on_types(self, node) -> str:
        union = []
        i = 0
        for current_node in node.children:
            obj_name_stub = self.obj_name[-1]
            name_index = obj_name_stub.rfind("_")
            ending = obj_name_stub[name_index + 1 :]
            if name_index >= 0 and (not ending or ending.isdecimal()):
                obj_name_stub = obj_name_stub[:name_index]
            fname = self.func_name[:1].upper() + self.func_name[1:]
            self.obj_name[-1] = fname + obj_name_stub + "_" + str(i)
            typ = self.compile_type_expression(node, current_node)
            if typ not in union:
                union.append(typ)
                i += 1
            self.obj_name[-1] = obj_name_stub
        for i, typ in enumerate(union):
            if typ[0:5] == "class":
                match_str = re.match(r"class\s*(\w+)[\w(){},' =]*\s*:", typ)
                cname = match_str.group(1) if match_str else ""
                self.local_classes[-1].append(typ)
                union[i] = cname
        if self.is_toplevel():
            preface = self.render_local_classes()
            self.local_classes.append([])
            self.optional_keys.append([])
        else:
            preface = ""
        if self.use_literal_type and any(
            nd[0].name == "literal" for nd in node.children
        ):
            assert all(nd[0].name == "literal" for nd in node.children)
            return f"Literal[{', '.join(union)}]"
        if self.use_type_union or len(union) <= 1:
            return preface + "|".join(union)
        return preface + f"Union[{', '.join(union)}]"

    def on_type(self, node) -> str:
        assert len(node.children) == 1
        typ = node[0]
        if typ.name == "declarations_block":
            self.local_classes.append([])
            self.optional_keys.append([])
            decls = self.compile(typ)
            return "".join(
                [
                    self.render_class_header(self.obj_name[-1], "") + "    ",
                    self.render_local_classes().replace("\n", "\n    "),
                    decls.replace("\n", "\n    "),
                ]
            )  # maybe add one '\n'?
            # return 'Dict'
        if typ.name == "literal":
            literal_typ = typ[0].name
            if self.use_literal_type:
                return f"Literal[{self.compile(typ)}]"
            if literal_typ == "array":
                return "List"
            if literal_typ == "object":
                return "Dict"
            if literal_typ in ("number", "integer"):
                literal = self.compile(typ)
                try:
                    _ = int(literal)
                    return "int"
                except ValueError:
                    return "str"
            assert literal_typ == "string", literal_typ
            literal = self.compile(typ)
            return "str"
        return self.compile(typ)

    def on_type_tuple(self, node):
        return "Tuple[" + ", ".join(self.compile(nd) for nd in node) + "]"

    def on_mapped_type(self, node) -> str:
        return self.compile(node["map_signature"])

    def on_map_signature(self, node) -> str:
        node_index_signature = self.compile(node["index_signature"])
        node_types = self.compile(node["types"])
        return f"Dict[{node_index_signature}, {node_types}]"

    def on_func_type(self, node) -> str:
        if "arg_list" in node:
            arg_list = self.compile(node["arg_list"])
            if arg_list.find("= None") >= 0 or arg_list.find("*") >= 0:
                # See https://docs.python.org/3/library/typing.html#typing.Callable
                args = "..."
            else:
                args = f"[{arg_list}]"
        else:
            args = "[]"
        types = self.compile(node["types"])
        return f"Callable[{args}, {types}]"

    def on_intersection(self, node) -> str:
        # ignore intersection
        self.tree.new_error(
            node,
            "Type intersections are not yet implemented",
            NOT_YET_IMPLEMENTED_WARNING,
        )
        return "Any"

    def on_virtual_enum(self, node) -> str:
        name = self.compile(node["identifier"])
        if self.is_known_type(name):
            # self.tree.new_error(node,
            #     f'Name {name} has already been defined earlier!', WARNING)
            return ""
        self.known_types[-1].add(name)
        save = self.strip_type_from_const
        if all(child.name == "const" for child in node.children[1:]):
            if all(
                nd["literal"][0].name == "integer"
                for nd in node.select_children("const")
                if "literal" in nd
            ):
                header = f"class {name}(IntEnum):"
            else:
                header = f"class {name}(Enum):"
            self.strip_type_from_const = True
        else:
            header = ""
        namespace = []
        for child in node.children[1:]:
            namespace.append(self.compile(child))
        if not header:
            header = self.render_class_header(name, "")[
                :-1
            ]  # leave out the trailing "\n"
        namespace.insert(0, header)
        self.strip_type_from_const = save
        return "\n    ".join(namespace)

    def on_namespace(self, node) -> str:
        # errmsg = "Transpilation of namespaces that contain more than just " \
        #          "constant definitions has not yet been implemented."
        # self.tree.new_error(node, errmsg, NOT_YET_IMPLEMENTED_WARNING)
        # return "# " + errmsg
        name = self.compile(node["identifier"])
        declarations = [f"class {name}:"]
        assert len(node.children) >= 2
        declaration = self.compile(node[1])
        declaration = declaration.lstrip("\n")
        declarations.extend(declaration.split("\n"))
        for current_node in node[2:]:
            declaration = self.compile(current_node)
            declarations.extend(declaration.split("\n"))
        return "\n    ".join(declarations)

    def on_enum(self, node) -> str:
        if self.use_enums:
            if all(
                nd["literal"][0].name == "integer"
                for nd in node.select_children("item")
                if "literal" in nd
            ):
                base_class = "(IntEnum)"
            else:
                base_class = "(Enum)"
        else:
            base_class = ""
        name = self.compile(node["identifier"])
        self.known_types[-1].add(name)
        enum = ["class " + name + base_class + ":"]
        for item in node.select_children("item"):
            enum.append(self.compile(item))
        return "\n    ".join(enum)

    def on_item(self, node) -> str:
        if len(node.children) == 1:
            identifier = self.compile(node[0])
            if self.use_enums:
                return identifier + " = enum.auto()"
            return identifier + " = " + repr(identifier)
        return self.compile(node["identifier"]) + " = " + self.compile(node["literal"])

    def on_const(self, node) -> str:
        if "literal" in node or "identifier" in node:
            if self.strip_type_from_const:
                return (
                    self.compile(node["declaration"]["identifier"])
                    + " = "
                    + self.compile(node[-1])
                )
            return self.compile(node["declaration"]) + " = " + self.compile(node[-1])
        # const without assignment, e.g. "export const version: string;"
        return self.compile(node["declaration"])

    def on_assignment(self, node) -> str:
        return self.compile(node["variable"]) + " = " + self.compile(node[1])

    def on_literal(self, node) -> str:
        assert len(node.children) == 1
        return self.compile(node[0])

    def on_integer(self, node) -> str:
        return node.content

    def on_number(self, node) -> str:
        return node.content

    def on_boolean(self, node) -> str:
        return {"true": "True", "false": "False"}[node.content]

    def on_string(self, node) -> str:
        return node.content

    def on_array(self, node) -> str:
        return "[" + ", ".join(self.compile(nd) for nd in node.children) + "]"

    def on_object(self, node) -> str:
        return (
            "{\n    " + ",\n    ".join(self.compile(nd) for nd in node.children) + "\n}"
        )

    def on_association(self, node) -> str:
        return f'"{self.compile(node["name"])}": ' + self.compile(node["literal"])

    def on_name(self, node) -> str:
        return node.content

    def on_basic_type(self, node) -> str:
        return TYPE_NAME_SUBSTITUTION[node.content]

    def on_generic_type(self, node) -> str:
        base_type = self.compile(node["type_name"])
        parameters = self.compile(node["type_parameters"])
        if parameters == "None":
            return base_type
        return "".join([base_type, "[", parameters, "]"])

    def on_type_parameters(self, node) -> str:
        type_parameters = [self.compile(nd) for nd in node.children]
        return ", ".join(type_parameters)

    def on_parameter_types(self, node) -> str:
        return self.on_types(node)

    def on_parameter_type(self, node) -> str:
        if len(node.children) > 1:
            node.result = (node[0],)  # ignore extends_type and equals_type for now
        return self.on_type(node)

    def on_extends_type(self, node) -> str:
        # TODO: generate TypeVar with restrictions
        self.tree.new_error(
            node,
            "restrictied generics not yet implemented",
            NOT_YET_IMPLEMENTED_WARNING,
        )
        return ""

    def on_equals_type(self, node) -> str:
        # TODO: generate TypeVar with restrictions
        self.tree.new_error(
            node,
            "restrictied generics not yet implemented",
            NOT_YET_IMPLEMENTED_WARNING,
        )
        return ""

    def on_type_name(self, node) -> str:
        name = self.compile(node["identifier"])
        return TYPE_NAME_SUBSTITUTION.get(name, name)

    def compile_type_expression(self, node, type_node):
        unknown_types = set(
            tn.content
            for tn in node.select("type_name")
            if not self.is_known_type(tn.content)
        )
        type_expression = self.compile(type_node)
        for typ in unknown_types:
            rx_pattern = re.compile(r"(?:(?<=[^\w'])|^)" + typ + r"(?:(?=[^\w'])|$)")
            segments = type_expression.split("'")
            for i in range(0, len(segments), 2):
                segments[i] = rx_pattern.sub(f"'{typ}'", segments[i])
            type_expression = "'".join(segments)
            # type_expression = rx.sub(f"'{typ}'", type_expression)
        if type_expression[0:1] == "'":
            type_expression = "".join(["'", type_expression.replace("'", ""), "'"])
        return type_expression

    def on_array_of(self, node) -> str:
        assert len(node.children) == 1
        element_type = self.compile_type_expression(node, node[0])
        return "List[" + element_type + "]"

    def on_array_types(self, node) -> str:
        return self.on_types(node)

    def on_array_type(self, node) -> str:
        return self.on_type(node)

    def on_qualifiers(self, node):
        assert (
            False
        ), "Qualifiers should be ignored and this method should never be called!"

    def on_variable(self, node) -> str:
        return node.content

    def on_identifier(self, node) -> str:
        identifier = node.content
        if keyword.iskeyword(identifier):
            identifier += "_"
        return identifier


get_compiler = ThreadLocalSingletonFactory(TS2PyCompiler, ident="1")


def compile_ts2py(ast):
    return get_compiler()(ast)
