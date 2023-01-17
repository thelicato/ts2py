import re
from typing import List
from DHParser import (
    Grammar,
    Whitespace,
    Drop,
    Alternative,
    Text,
    Synonym,
    Interleave,
    Option,
    OneOrMore,
    RegExp,
    Series,
    TreeReduction,
    ZeroOrMore,
    Forward,
    NegativeLookahead,
    CombinedParser,
    mixin_comment,
    get_config_value,
    set_tracer,
    resume_notices_on,
    trace_history,
    ThreadLocalSingletonFactory,
)


class ts2pyGrammar(Grammar):
    r"""Parser for a ts2py source file."""
    arg_list = Forward()
    declaration = Forward()
    declarations_block = Forward()
    document = Forward()
    function = Forward()
    generic_type = Forward()
    literal = Forward()
    type = Forward()
    types = Forward()
    source_hash__ = "1df05a5e0419bbeccb6a6dc0d26a756f"
    disposable__ = re.compile(
        "INT$|NEG$|FRAC$|DOT$|EXP$|EOF$|_array_ellipsis$|_top_level_assignment$|_top_level_literal$|_quoted_identifier$|_root$|_namespace$|_part$"
    )
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r"(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)"
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r"\s*"
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp(".")))
    EXP = Option(
        Series(
            Alternative(Text("E"), Text("e")),
            Option(Alternative(Text("+"), Text("-"))),
            RegExp("[0-9]+"),
        )
    )
    DOT = Text(".")
    FRAC = Option(Series(DOT, RegExp("[0-9]+")))
    NEG = Text("-")
    INT = Series(Option(NEG), Alternative(RegExp("[1-9][0-9]+"), RegExp("[0-9]")))
    _part = RegExp("(?!\\d)\\w+")
    identifier = Series(
        NegativeLookahead(Alternative(Text("true"), Text("false"))),
        _part,
        ZeroOrMore(Series(Text("."), _part)),
        dwsp__,
    )
    _quoted_identifier = Alternative(
        identifier,
        Series(
            Series(Drop(Text('"')), dwsp__),
            identifier,
            Series(Drop(Text('"')), dwsp__),
            mandatory=2,
        ),
        Series(
            Series(Drop(Text("'")), dwsp__),
            identifier,
            Series(Drop(Text("'")), dwsp__),
            mandatory=2,
        ),
    )
    variable = Series(identifier, ZeroOrMore(Series(Text("."), identifier)))
    basic_type = Series(
        Alternative(
            Text("object"),
            Text("array"),
            Text("string"),
            Text("number"),
            Text("boolean"),
            Text("null"),
            Text("integer"),
            Text("uinteger"),
            Text("decimal"),
            Text("unknown"),
            Text("any"),
            Text("void"),
        ),
        dwsp__,
    )
    name = Alternative(
        identifier,
        Series(
            Series(Drop(Text('"')), dwsp__), identifier, Series(Drop(Text('"')), dwsp__)
        ),
    )
    association = Series(name, Series(Drop(Text(":")), dwsp__), literal)
    object = Series(
        Series(Drop(Text("{")), dwsp__),
        Option(
            Series(
                association,
                ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), association)),
            )
        ),
        Option(Series(Drop(Text(",")), dwsp__)),
        Series(Drop(Text("}")), dwsp__),
    )
    array = Series(
        Series(Drop(Text("[")), dwsp__),
        Option(
            Series(
                literal, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), literal))
            )
        ),
        Series(Drop(Text("]")), dwsp__),
    )
    string = Alternative(
        Series(RegExp('"[^"\\n]*"'), dwsp__), Series(RegExp("'[^'\\n]*'"), dwsp__)
    )
    boolean = Series(Alternative(Text("true"), Text("false")), dwsp__)
    number = Series(INT, FRAC, EXP, dwsp__)
    integer = Series(INT, NegativeLookahead(RegExp("[.Ee]")), dwsp__)
    type_tuple = Series(
        Series(Drop(Text("[")), dwsp__),
        types,
        ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), types)),
        Series(Drop(Text("]")), dwsp__),
    )
    _top_level_literal = Drop(Synonym(literal))
    _array_ellipsis = Drop(
        Series(
            literal,
            Drop(ZeroOrMore(Drop(Series(Series(Drop(Text(",")), dwsp__), literal)))),
        )
    )
    assignment = Series(
        variable,
        Series(Drop(Text("=")), dwsp__),
        Alternative(literal, variable),
        Series(Drop(Text(";")), dwsp__),
    )
    _top_level_assignment = Drop(Synonym(assignment))
    const = Series(
        Option(Series(Drop(Text("export")), dwsp__)),
        Series(Drop(Text("const")), dwsp__),
        declaration,
        Option(
            Series(Series(Drop(Text("=")), dwsp__), Alternative(literal, identifier))
        ),
        Series(Drop(Text(";")), dwsp__),
        mandatory=2,
    )
    item = Series(
        _quoted_identifier, Option(Series(Series(Drop(Text("=")), dwsp__), literal))
    )
    enum = Series(
        Option(Series(Drop(Text("export")), dwsp__)),
        Series(Drop(Text("enum")), dwsp__),
        identifier,
        Series(Drop(Text("{")), dwsp__),
        item,
        ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), item)),
        Option(Series(Drop(Text(",")), dwsp__)),
        Series(Drop(Text("}")), dwsp__),
        mandatory=3,
    )
    type_name = Synonym(identifier)
    equals_type = Series(
        Series(Drop(Text("=")), dwsp__), Alternative(basic_type, type_name)
    )
    extends_type = Series(
        Series(Drop(Text("extends")), dwsp__), Alternative(basic_type, type_name)
    )
    func_type = Series(
        Series(Drop(Text("(")), dwsp__),
        Option(arg_list),
        Series(Drop(Text(")")), dwsp__),
        Series(Drop(Text("=>")), dwsp__),
        types,
    )
    readonly = Series(Text("readonly"), dwsp__)
    index_signature = Series(
        Option(readonly),
        Series(Drop(Text("[")), dwsp__),
        identifier,
        Alternative(
            Series(Drop(Text(":")), dwsp__),
            Series(
                Series(Drop(Text("in")), dwsp__), Series(Drop(Text("keyof")), dwsp__)
            ),
        ),
        type,
        Series(Drop(Text("]")), dwsp__),
    )
    map_signature = Series(index_signature, Series(Drop(Text(":")), dwsp__), types)
    array_type = Alternative(
        basic_type,
        generic_type,
        type_name,
        Series(Series(Drop(Text("(")), dwsp__), types, Series(Drop(Text(")")), dwsp__)),
        type_tuple,
        declarations_block,
    )
    extends = Series(
        Series(Drop(Text("extends")), dwsp__),
        Alternative(generic_type, type_name),
        ZeroOrMore(
            Series(
                Series(Drop(Text(",")), dwsp__), Alternative(generic_type, type_name)
            )
        ),
    )
    array_types = Synonym(array_type)
    array_of = Series(
        Option(Series(Drop(Text("readonly")), dwsp__)),
        array_types,
        Series(Drop(Text("[]")), dwsp__),
    )
    arg_tail = Series(
        Series(Drop(Text("...")), dwsp__),
        identifier,
        Option(Series(Series(Drop(Text(":")), dwsp__), array_of)),
    )
    parameter_type = Alternative(
        array_of,
        basic_type,
        generic_type,
        Series(type_name, Option(extends_type), Option(equals_type)),
        declarations_block,
        type_tuple,
    )
    parameter_types = Series(
        parameter_type,
        ZeroOrMore(Series(Series(Drop(Text("|")), dwsp__), parameter_type)),
    )
    type_parameters = Series(
        Series(Drop(Text("<")), dwsp__),
        parameter_types,
        ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), parameter_types)),
        Series(Drop(Text(">")), dwsp__),
        mandatory=1,
    )
    interface = Series(
        Option(Series(Drop(Text("export")), dwsp__)),
        Alternative(
            Series(Drop(Text("interface")), dwsp__), Series(Drop(Text("class")), dwsp__)
        ),
        identifier,
        Option(type_parameters),
        Option(extends),
        declarations_block,
        mandatory=2,
    )
    type_alias = Series(
        Option(Series(Drop(Text("export")), dwsp__)),
        Series(Drop(Text("type")), dwsp__),
        identifier,
        Option(type_parameters),
        Series(Drop(Text("=")), dwsp__),
        types,
        Series(Drop(Text(";")), dwsp__),
        mandatory=2,
    )
    module = Series(
        Series(Drop(Text("declare")), dwsp__),
        Series(Drop(Text("module")), dwsp__),
        _quoted_identifier,
        Series(Drop(Text("{")), dwsp__),
        document,
        Series(Drop(Text("}")), dwsp__),
    )
    namespace = Series(
        Option(Series(Drop(Text("export")), dwsp__)),
        Series(Drop(Text("namespace")), dwsp__),
        identifier,
        Series(Drop(Text("{")), dwsp__),
        ZeroOrMore(
            Alternative(
                interface,
                type_alias,
                enum,
                const,
                Series(
                    Option(Series(Drop(Text("export")), dwsp__)),
                    declaration,
                    Series(Drop(Text(";")), dwsp__),
                ),
                Series(
                    Option(Series(Drop(Text("export")), dwsp__)),
                    function,
                    Series(Drop(Text(";")), dwsp__),
                ),
            )
        ),
        Series(Drop(Text("}")), dwsp__),
        mandatory=2,
    )
    intersection = Series(
        type, OneOrMore(Series(Series(Drop(Text("&")), dwsp__), type, mandatory=1))
    )
    virtual_enum = Series(
        Option(Series(Drop(Text("export")), dwsp__)),
        Series(Drop(Text("namespace")), dwsp__),
        identifier,
        Series(Drop(Text("{")), dwsp__),
        ZeroOrMore(
            Alternative(
                interface,
                type_alias,
                enum,
                const,
                Series(declaration, Series(Drop(Text(";")), dwsp__)),
            )
        ),
        Series(Drop(Text("}")), dwsp__),
    )
    _namespace = Alternative(virtual_enum, namespace)
    optional = Series(Text("?"), dwsp__)
    static = Series(Text("static"), dwsp__)
    mapped_type = Series(
        Series(Drop(Text("{")), dwsp__),
        map_signature,
        Option(Series(Drop(Text(";")), dwsp__)),
        Series(Drop(Text("}")), dwsp__),
    )
    qualifiers = Interleave(readonly, static, repetitions=[(0, 1), (0, 1)])
    argument = Series(
        identifier,
        Option(optional),
        Option(Series(Series(Drop(Text(":")), dwsp__), types)),
    )
    literal.set(Alternative(integer, number, boolean, string, array, object))
    generic_type.set(Series(type_name, type_parameters))
    type.set(
        Alternative(
            array_of,
            basic_type,
            generic_type,
            type_name,
            Series(
                Series(Drop(Text("(")), dwsp__), types, Series(Drop(Text(")")), dwsp__)
            ),
            mapped_type,
            declarations_block,
            type_tuple,
            literal,
            func_type,
        )
    )
    types.set(
        Series(
            Alternative(intersection, type),
            ZeroOrMore(
                Series(Series(Drop(Text("|")), dwsp__), Alternative(intersection, type))
            ),
        )
    )
    arg_list.set(
        Alternative(
            Series(
                argument,
                ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), argument)),
                Option(Series(Series(Drop(Text(",")), dwsp__), arg_tail)),
            ),
            arg_tail,
        )
    )
    function.set(
        Series(
            Option(
                Series(
                    Option(static),
                    Option(Series(Drop(Text("function")), dwsp__)),
                    identifier,
                    Option(optional),
                    Option(type_parameters),
                )
            ),
            Series(Drop(Text("(")), dwsp__),
            Option(arg_list),
            Series(Drop(Text(")")), dwsp__),
            Option(Series(Series(Drop(Text(":")), dwsp__), types)),
            mandatory=2,
        )
    )
    declaration.set(
        Series(
            qualifiers,
            Option(
                Alternative(
                    Series(Drop(Text("let")), dwsp__), Series(Drop(Text("var")), dwsp__)
                )
            ),
            identifier,
            Option(optional),
            NegativeLookahead(Text("(")),
            Option(Series(Series(Drop(Text(":")), dwsp__), types)),
        )
    )
    declarations_block.set(
        Series(
            Series(Drop(Text("{")), dwsp__),
            Option(
                Series(
                    Alternative(function, declaration),
                    ZeroOrMore(
                        Series(
                            Option(Series(Drop(Text(";")), dwsp__)),
                            Alternative(function, declaration),
                        )
                    ),
                    Option(Series(Series(Drop(Text(";")), dwsp__), map_signature)),
                    Option(Series(Drop(Text(";")), dwsp__)),
                )
            ),
            Series(Drop(Text("}")), dwsp__),
        )
    )
    document.set(
        Series(
            dwsp__,
            ZeroOrMore(
                Alternative(
                    interface,
                    type_alias,
                    _namespace,
                    enum,
                    const,
                    module,
                    _top_level_assignment,
                    _array_ellipsis,
                    _top_level_literal,
                    Series(
                        Option(Series(Drop(Text("export")), dwsp__)),
                        declaration,
                        Series(Drop(Text(";")), dwsp__),
                    ),
                    Series(
                        Option(Series(Drop(Text("export")), dwsp__)),
                        function,
                        Series(Drop(Text(";")), dwsp__),
                    ),
                )
            ),
        )
    )
    _root = Series(document, EOF)
    resume_rules__ = {
        "interface": [re.compile(r"(?=export|$)")],
        "type_alias": [re.compile(r"(?=export|$)")],
        "enum": [re.compile(r"(?=export|$)")],
        "const": [re.compile(r"(?=export|$)")],
        "declaration": [re.compile(r"(?=export|$)")],
        "_top_level_assignment": [re.compile(r"(?=export|$)")],
        "_top_level_literal": [re.compile(r"(?=export|$)")],
        "module": [re.compile(r"(?=export|$)")],
    }
    root__ = TreeReduction(_root, CombinedParser.MERGE_TREETOPS)


_raw_grammar = ThreadLocalSingletonFactory(ts2pyGrammar)


def get_grammar() -> ts2pyGrammar:
    grammar = _raw_grammar()
    if get_config_value("resume_notices"):
        resume_notices_on(grammar)
    elif get_config_value("history_tracking"):
        set_tracer(grammar, trace_history)
    try:
        if not grammar.__class__.python_src__:
            grammar.__class__.python_src__ = get_grammar.python_src__
    except AttributeError:
        pass
    return grammar


def parse_ts2py(document, start_parser="root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match=complete_match)
