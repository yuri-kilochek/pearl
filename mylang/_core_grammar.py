import string as _string

import pearl as _pearl
from . import ast as _ast


g = _pearl.Grammar()

g = g.put('__start__', [{'module'}])

g = g.put('module', [{'statements'}], _ast.Module)

# nothing
g = g.put('statements', ['whitespace'], _ast.Nothing)

# unused expression
g = g.put('statements', [{'expression'},
                         'whitespace', ';',
                         {'statements'}], _ast.UnusedExpression)

# variable declaration
g = g.put('statements', ['whitespace', 'v', 'a', 'r',
                         {'identifier'},
                         'whitespace', ';',
                         {'statements'}], _ast.VariableDeclaration)


def _build_macro_body_symbols(parameters):
    body_symbols = []
    for parameter in parameters:
        if parameter.__class__ == _ast.MacroDeclarationTerminalParameter:
            body_symbols.extend(parameter.symbols)
        else:
            assert parameter.__class__ == _ast.MacroDeclarationNonterminalParameter
            body_symbol = parameter.symbol
            if len(body_symbol) == 1:
                body_symbol += '-one-char-nonterminal'
            if parameter.used:
                body_symbol = {body_symbol}
            body_symbols.append(body_symbol)
    return body_symbols

# macro declaration
g = g.put('statements', ['whitespace', 'm', 'a', 'c', 'r', 'o',
                         {'identifier'},
                         'whitespace', ':',
                         {'macro_declaration_parameters'},
                         'whitespace', '-', '>',
                         {'expression'},
                         'whitespace', ';', (lambda g, head, body, _: g.put(head, _build_macro_body_symbols(body), lambda *nodes: _ast.MacroUse(head, body, nodes))),
                         {'statements'}], _ast.MacroDeclaration)

g = g.put('macro_declaration_parameters', [], lambda: ())
g = g.put('macro_declaration_parameters', [{'macro_declaration_parameter'}])
g = g.put('macro_declaration_parameters', [{'macro_declaration_parameter'},
                                           'whitespace', ',',
                                           {'macro_declaration_parameters'}], lambda first, rest: (first,) + rest)

g = g.put('macro_declaration_parameter', [{'string'}], lambda symbols: _ast.MacroDeclarationTerminalParameter(tuple(symbols)))
g = g.put('macro_declaration_parameter', [{'macro_declaration_parameter_nonterminal_prefix'},
                                          {'identifier'}], _ast.MacroDeclarationNonterminalParameter)

g = g.put('macro_declaration_parameter_nonterminal_prefix', [], lambda: False)
g = g.put('macro_declaration_parameter_nonterminal_prefix', ['whitespace', '$'], lambda: True)

# block
g = g.put('statements', ['whitespace', '{',
                         {'statements'},
                         'whitespace', '}',
                         {'statements'}], _ast.Block)

# if else
g = g.put('statements', ['whitespace', 'i', 'f',
                         {'expression'},
                         'whitespace', '{',
                         {'statements'},
                         'whitespace', '}',
                         'whitespace', 'e', 'l', 's', 'e',
                         'whitespace', '{',
                         {'statements'},
                         'whitespace', '}',
                         {'statements'}], _ast.IfElse)

# forever
g = g.put('statements', ['whitespace', 'f', 'o', 'r', 'e', 'v', 'e', 'r',
                         'whitespace', '{',
                         {'statements'},
                         'whitespace', '}',
                         {'statements'}], _ast.Forever)

# continue
g = g.put('statements', ['whitespace', 'c', 'o', 'n', 't', 'i', 'n', 'u', 'e',
                         'whitespace', ';'], _ast.Continue)

# break
g = g.put('statements', ['whitespace', 'b', 'r', 'e', 'a', 'k',
                         'whitespace', ';'], _ast.Break)

# return
g = g.put('statements', ['whitespace', 'r', 'e', 't', 'u', 'r', 'n',
                         {'expression'},
                         'whitespace', ';'], _ast.Return)

# variable assignment
g = g.put('statements', [{'identifier'},
                         'whitespace', '=',
                         {'expression'},
                         'whitespace', ';',
                         {'statements'}], _ast.VariableAssignment)

# attribute assignment
g = g.put('statements', [{'postfix_expression'},
                         'whitespace', '.',
                         {'identifier'},
                         'whitespace', '=',
                         {'expression'},
                         'whitespace', ';',
                         {'statements'}], _ast.AttributeAssignment)


g = g.put('expression', [{'postfix_expression'}])


g = g.put('postfix_expression', [{'primary_expression'}])

# attribute access
g = g.put('postfix_expression', [{'postfix_expression'},
                                 'whitespace', '.',
                                 {'identifier'}], _ast.AttributeAccess)

# invocation
g = g.put('postfix_expression', [{'postfix_expression'},
                                 'whitespace', '(',
                                 {'invocation_arguments'},
                                 'whitespace', ')'], _ast.Invocation)

g = g.put('invocation_arguments', [], lambda: ())
g = g.put('invocation_arguments', [{'expression'}], lambda argument: (argument,))
g = g.put('invocation_arguments', [{'expression'},
                                   'whitespace', ',',
                                   {'invocation_arguments'}], lambda argument, rest: (argument,) + rest)

# variable use
g = g.put('primary_expression', [{'identifier'}], _ast.VariableUse)

# number literal
g = g.put('primary_expression', [{'number'}], _ast.NumberLiteral)

# string literal
g = g.put('primary_expression', [{'string'}], _ast.StringLiteral)

# function literal
g = g.put('primary_expression', ['whitespace', '(',
                                 {'function_literal_parameters'},
                                 'whitespace', ')',
                                 'whitespace', '=', '>',
                                 'whitespace', '{',
                                 {'statements'},
                                 'whitespace', '}'], _ast.FunctionLiteral)

g = g.put('function_literal_parameters', [], lambda: ())
g = g.put('function_literal_parameters', [{'identifier'}], lambda parameter: (parameter,))
g = g.put('function_literal_parameters', [{'identifier'},
                                          'whitespace', ',',
                                          {'function_literal_parameters'}], lambda first, rest: (first,) + rest)

# parenthesized expression
g = g.put('primary_expression', ['whitespace', '(',
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
