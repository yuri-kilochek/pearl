from functools import lru_cache as _lru_cache
import string as _string

import pearl as _pearl
from . import ast as _ast


g = _pearl.Grammar()

g = g.put('__start__', [{'statement_sequence'}, 'whitespace'])


# statement sequence
g = g.put('statement_sequence', [{'statements'}], _ast.StatementSequence)

g = g.put('statements', [], lambda: ())
g = g.put('statements', [{'statement'},
                         {'statements'}], lambda first, rest: (first,) + rest)


# unused expression
g = g.put('statement', [{'expression'},
                        'whitespace', ';'])


# export
g = g.put('export', [], lambda: False)
g = g.put('export', ['whitespace', 'e', 'x', 'p', 'o', 'r', 't'], lambda: True)


@_lru_cache(maxsize=256)
def _get_grammar_patch(module_path):
    from ._read import read

    module_body = read(module_path)

    patches = []

    for s in module_body.statements:
        if s.__class__ == _ast.MacroDefinition and s.exported:
            patches.append((lambda s: lambda g: _add_macro_use_rule(g, s.nonterminal, s.parameters))(s))
        if s.__class__ == _ast.MacroUndefinition and s.exported:
            patches.append((lambda s: lambda g: _drop_unmacro_rule(g, s.nonterminal, s.parameters))(s))

    def patch_grammar(g):
        for patch in patches:
            g = patch(g)
        return g

    return patch_grammar


# import
g = g.put('statements', [{'export'},
                         'whitespace', 'i', 'm', 'p', 'o', 'r', 't',
                         {'string'},
                         'whitespace', ';', (lambda g, exported, module_path: _get_grammar_patch(module_path)(g)),
                         {'statements'}], lambda exported, module_path, rest: (_ast.Import(exported, module_path),) + rest)


# variable declaration
g = g.put('statement', [{'export'},
                        'whitespace', 'v', 'a', 'r',
                        {'identifier'},
                        'whitespace', ';'], _ast.VariableDeclaration)


def _build_macro_body_symbols(parameters):
    body_symbols = []
    for parameter in parameters:
        if parameter.__class__ == _ast.MacroParameterTerminal:
            body_symbols.extend(parameter.symbols)
        else:
            assert parameter.__class__ == _ast.MacroParameterNonterminal
            body_symbol = parameter.symbol
            if len(body_symbol) == 1:
                body_symbol += '-one-char-nonterminal'
            if parameter.name is not None:
                body_symbol = {body_symbol}
            body_symbols.append(body_symbol)
    return body_symbols


def _add_macro_use_rule(g, head, body):
    return g.put(head, _build_macro_body_symbols(body), lambda *nodes: _ast.MacroUse(head, body, nodes))


def _build_macro_transform(parameters, transform_body):
    arguments = ['__usage_context__']
    for parameter in parameters:
        if parameter.__class__ == _ast.MacroParameterNonterminal and parameter.name is not None:
            arguments.append(parameter.name)
    return _ast.FunctionLiteral(tuple(arguments), transform_body)


# macro definition
g = g.put('statements', [{'export'},
                         'whitespace', 'm', 'a', 'c', 'r', 'o',
                         {'identifier'},
                         'whitespace', '-', '>',
                         {'macro_parameters'},
                         'whitespace', '{',
                         {'statement_sequence'},
                         'whitespace', '}', (lambda g, exported, head, body, _: _add_macro_use_rule(g, head, body)),
                         {'statements'}], lambda exported, head, body, transform_body, rest: (_ast.MacroDefinition(exported, head, body, _build_macro_transform(body, transform_body)),) + rest)

g = g.put('macro_parameters', [], lambda: ())
g = g.put('macro_parameters', [{'macro_parameter'}], lambda parameter: (parameter,))
g = g.put('macro_parameters', [{'macro_parameter'},
                               'whitespace', ',',
                               {'macro_parameters'}], lambda first, rest: (first,) + rest)

g = g.put('macro_parameter', [{'string'}], lambda symbols: _ast.MacroParameterTerminal(tuple(symbols)))
g = g.put('macro_parameter', [{'identifier'},
                              {'macro_parameter_nonterminal_name'}], _ast.MacroParameterNonterminal)

g = g.put('macro_parameter_nonterminal_name', [], lambda: None)
g = g.put('macro_parameter_nonterminal_name', ['whitespace', '/',
                                               {'identifier'}])


def _drop_unmacro_rule(g, head, body):
    return g.drop(head, _build_macro_body_symbols(body))

# unmacro
g = g.put('statements', [{'export'},
                         'whitespace', 'u', 'n', 'm', 'a', 'c', 'r', 'o',
                         {'identifier'},
                         'whitespace', '-', '>',
                         {'unmacro_parameters'},
                         'whitespace', ';', (lambda g, exported, head, body: _drop_unmacro_rule(g, head, body)),
                         {'statements'}], lambda exported, head, body, rest: (_ast.MacroUndefinition(exported, head, body),) + rest)

g = g.put('unmacro_parameters', [], lambda: ())
g = g.put('unmacro_parameters', [{'unmacro_parameter'}], lambda parameter: (parameter,))
g = g.put('unmacro_parameters', [{'unmacro_parameter'},
                                  'whitespace', ',',
                                 {'unmacro_parameters'}], lambda first, rest: (first,) + rest)

g = g.put('unmacro_parameter', [{'string'}], lambda symbols: _ast.MacroParameterTerminal(tuple(symbols)))
g = g.put('unmacro_parameter', [{'identifier'}], lambda symbol: _ast.MacroParameterNonterminal(symbol, None))


# block
g = g.put('statement', [{'block'}])
g = g.put('block', ['whitespace', '{',
                    {'statement_sequence'},
                    'whitespace', '}'], _ast.Block)

# if
g = g.put('statement', [{'if'}])

g = g.put('if', ['whitespace', 'i', 'f',
                 {'expression'},
                 {'block'},
                 {'if_else'}], _ast.If)

g = g.put('if_else', ['whitespace', 'e', 'l', 's', 'e',
                      {'block'}])

# forever
g = g.put('statement', [{'forever'}])
g = g.put('forever', ['whitespace', 'f', 'o', 'r', 'e', 'v', 'e', 'r',
                      {'block'}], _ast.Forever)

# continue
g = g.put('statement', [{'continue'}])
g = g.put('continue', ['whitespace', 'c', 'o', 'n', 't', 'i', 'n', 'u', 'e',
                       'whitespace', ';'], _ast.Continue)

# break
g = g.put('statement', [{'break'}])
g = g.put('break', ['whitespace', 'b', 'r', 'e', 'a', 'k',
                    'whitespace', ';'], _ast.Break)

# return
g = g.put('statement', [{'return'}])
g = g.put('return', ['whitespace', 'r', 'e', 't', 'u', 'r', 'n',
                     {'expression'},
                     'whitespace', ';'], _ast.Return)

# variable assignment
g = g.put('statement', [{'variable_assignment'}])
g = g.put('variable_assignment', [{'identifier'},
                                   'whitespace', '=',
                                   {'expression'},
                                   'whitespace', ';'], _ast.VariableAssignment)

# attribute assignment
g = g.put('statement', [{'attribute_assignment'}])
g = g.put('attribute_assignment', [{'postfix_expression'},
                                   'whitespace', '.',
                                   {'identifier'},
                                   'whitespace', '=',
                                   {'expression'},
                                   'whitespace', ';'], _ast.AttributeAssignment)


g = g.put('expression', [{'postfix_expression'}])


# attribute access
g = g.put('postfix_expression', [{'attribute_access'}])
g = g.put('attribute_access', [{'postfix_expression'},
                               'whitespace', '.',
                               {'identifier'}], _ast.AttributeAccess)

# call
g = g.put('postfix_expression', [{'call'}])
g = g.put('call', [{'postfix_expression'},
                   'whitespace', '(',
                   {'call_arguments'},
                   'whitespace', ')'], _ast.Call)

g = g.put('call_arguments', [], lambda: ())
g = g.put('call_arguments', [{'expression'}], lambda argument: (argument,))
g = g.put('call_arguments', [{'expression'},
                             'whitespace', ',',
                             {'call_arguments'}], lambda argument, rest: (argument,) + rest)


g = g.put('postfix_expression', [{'primary_expression'}])


# variable access
g = g.put('primary_expression', [{'variable_access'}])
g = g.put('variable_access', [{'identifier'}], _ast.VariableAccess)

# number literal
g = g.put('primary_expression', [{'number_literal'}])
g = g.put('number_literal', [{'number'}], _ast.NumberLiteral)

# string literal
g = g.put('primary_expression', [{'string_literal'}])
g = g.put('string_literal', [{'string'}], _ast.StringLiteral)

# function literal
g = g.put('primary_expression', [{'function_literal'}])
g = g.put('function_literal', ['whitespace', '(',
                               {'function_literal_parameters'},
                               'whitespace', ')',
                               'whitespace', '=', '>',
                               'whitespace', '{',
                               {'statement_sequence'},
                               'whitespace', '}'], _ast.FunctionLiteral)

g = g.put('function_literal_parameters', [], lambda: ())
g = g.put('function_literal_parameters', [{'identifier'}], lambda parameter: (parameter,))
g = g.put('function_literal_parameters', [{'identifier'},
                                          'whitespace', ',',
                                          {'function_literal_parameters'}], lambda first, rest: (first,) + rest)

# parenthesized expression
g = g.put('primary_expression', [{'parenthesized_expression'}])
g = g.put('parenthesized_expression', ['whitespace', '(',
                                       {'expression'},
                                       'whitespace', ')'])


def parse_string(text):
    return text[1:-1]. \
        replace('\\\\', '\\'). \
        replace('\\\'', '\''). \
        replace('\\\t', '\t'). \
        replace('\\\v', '\v'). \
        replace('\\\f', '\f'). \
        replace('\\\n', '\n'). \
        replace('\\\r', '\r')

g = g.put('string', ['whitespace', {'string_without_whitespace'}], parse_string)

g = g.put('string_without_whitespace', ['\'', 'string_items', '\''])

g = g.put('string_items', [])
g = g.put('string_items', ['string_item', 'string_items'])

g = g.put('string_item', ['letter'])
g = g.put('string_item', ['digit'])
g = g.put('string_item', ['punctuation_without_backslash_and_quote'])
g = g.put('string_item', ['\\', '\\'])
g = g.put('string_item', ['\\', '\''])
g = g.put('string_item', ['whitespace_char'])
g = g.put('string_item', ['\\', 't'])
g = g.put('string_item', ['\\', 'v'])
g = g.put('string_item', ['\\', 'f'])
g = g.put('string_item', ['\\', 'n'])
g = g.put('string_item', ['\\', 'r'])


g = g.put('number', ['whitespace', {'number_without_whitespace'}], float)

g = g.put('number_without_whitespace', ['number_sign_opt',
                                        'number_integer',
                                        'number_fraction_opt',
                                        'number_exponent_opt'])

g = g.put('number_sign_opt', [])
g = g.put('number_sign_opt', ['+'])
g = g.put('number_sign_opt', ['-'])

g = g.put('number_integer', ['digit'])
g = g.put('number_integer', ['digit', 'number_integer'])

g = g.put('number_fraction_opt', [])
g = g.put('number_fraction_opt', ['.', 'number_integer'])

g = g.put('number_exponent_opt', [])
g = g.put('number_exponent_opt', ['e', 'number_sign_opt', 'number_integer'])
g = g.put('number_exponent_opt', ['E', 'number_sign_opt', 'number_integer'])


g = g.put('identifier', ['whitespace', {'identifier_without_whitespace'}])

g = g.put('identifier_without_whitespace', ['identifier_head',
                                            'identifier_tail'])

g = g.put('identifier_head', ['_'])
g = g.put('identifier_head', ['letter'])

g = g.put('identifier_tail', [])
g = g.put('identifier_tail', ['_', 'identifier_tail'])
g = g.put('identifier_tail', ['letter', 'identifier_tail'])
g = g.put('identifier_tail', ['digit', 'identifier_tail'])


# comment
g = g.put('whitespace', ['#', 'comment_chars', '\n', 'whitespace'])

g = g.put('comment_chars', [])
g = g.put('comment_chars', ['comment_char', 'comment_chars'])

g = g.put('comment_char', ['letter'])
g = g.put('comment_char', ['digit'])
g = g.put('comment_char', ['punctuation'])
g = g.put('comment_char', ['whitespace_char_without_newline'])


for c in _string.ascii_letters:
    g = g.put('letter', [c])

for c in _string.digits:
    g = g.put('digit', [c])

for c in _string.punctuation:
    if c not in '\\\'':
        g = g.put('punctuation_without_backslash_and_quote', [c])
g = g.put('punctuation', ['punctuation_without_backslash_and_quote'])
g = g.put('punctuation', ['\\'])
g = g.put('punctuation', ['\''])

g = g.put('whitespace_without_newline', [])
g = g.put('whitespace_without_newline', ['whitespace_char_without_newline', 'whitespace_without_newline'])
for c in _string.whitespace:
    if c != '\n':
        g = g.put('whitespace_char_without_newline', [c])
g = g.put('whitespace', [])
g = g.put('whitespace', ['whitespace_char', 'whitespace'])
g = g.put('whitespace_char', ['whitespace_char_without_newline'])
g = g.put('whitespace_char', ['\n'])

core_grammar = g

del g
