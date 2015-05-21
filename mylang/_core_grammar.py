import string as _string

import pearl as _pearl
from . import ast as _ast


g = _pearl.Grammar()

g = g.put('_start_', ['module',
                      {'whitespace'}])

g = g.put('module', ['statements'], lambda body: [_ast.Module(body)])

# nothing
g = g.put('statements', [], lambda: [_ast.Nothing()])

# unused expression
g = g.put('statements', ['expression',
                         {'whitespace'}, {';'},
                         'statements'], lambda expression, next: [_ast.UnusedExpression(expression, next)])

# variable declaration
g = g.put('statements', [{'whitespace'}, {'v'}, {'a'}, {'r'},
                         'identifier',
                         {'whitespace'}, {';'},
                         'statements'], lambda name, next: [_ast.VariableDeclaration(name, next)])


def _build_macro_declaration_body(arguments):
    body = []
    for tag, symbol in arguments:
        if tag == 'lit':
            for c in symbol:
                body.append({c})
            continue

        if len(symbol) == 1:
            symbol += '-single-char-rule'

        if tag == 'did':
            symbol = {symbol}

        body.append(symbol)
    return body

# macro declaration
g = g.put('statements', [{'whitespace'}, {'m'}, {'a'}, {'c'}, {'r'}, {'o'},
                         'identifier',
                         {'whitespace'}, {':'},
                         'macro_declaration_arguments',
                         {'whitespace'}, {'-'}, {'>'},
                         'expression',
                         {'whitespace'}, {';'}, (lambda g, nonterminal, arguments, _: g.put(nonterminal, _build_macro_declaration_body(arguments), lambda *nodes: [_ast.MacroUse((nonterminal, arguments), nodes)])),
                         'statements'], lambda nonterminal, body_symbols, transform, next: [_ast.MacroDeclaration((nonterminal, body_symbols), transform, next)])

g = g.put('macro_declaration_arguments', [], lambda: [()])
g = g.put('macro_declaration_arguments', ['macro_declaration_argument'], lambda argument: [(argument,)])
g = g.put('macro_declaration_arguments', ['macro_declaration_argument',
                                          {'whitespace'}, {','},
                                          'macro_declaration_arguments'], lambda first, rest: [(first,) + rest])

g = g.put('macro_declaration_argument', ['string'], lambda literal: [('lit', literal)])
g = g.put('macro_declaration_argument', ['identifier'], lambda rule: [('did', rule)])
g = g.put('macro_declaration_argument', [{'whitespace'}, {'$'},
                                         'identifier'], lambda rule: [('uid', rule)])

# block
g = g.put('statements', [{'whitespace'}, {'{'},
                         'statements',
                         {'whitespace'}, {'}'},
                         'statements'], lambda body, next: [_ast.Block(body, next)])

# if else
g = g.put('statements', [{'whitespace'}, {'i'}, {'f'},
                         'expression',
                         {'whitespace'}, {'{'},
                         'statements',
                         {'whitespace'}, {'}'},
                         {'whitespace'}, {'e'}, {'l'}, {'s'}, {'e'},
                         {'whitespace'}, {'{'},
                         'statements',
                         {'whitespace'}, {'}'},
                         'statements'], lambda condition, true_clause, false_clause, next: [_ast.IfElse(condition, true_clause, false_clause, next)])

# forever
g = g.put('statements', [{'whitespace'}, {'f'}, {'o'}, {'r'}, {'e'}, {'v'}, {'e'}, {'r'},
                         'forever_body',
                         'statements'], lambda body, next: [_ast.Forever(body, next)])

g = g.put('forever_body', [{'whitespace'}, {'{'},
                           'statements',
                           {'whitespace'}, {'}'}])

# continue
g = g.put('statements', [{'whitespace'}, {'c'}, {'o'}, {'n'}, {'t'}, {'i'}, {'n'}, {'u'}, {'e'},
                         {'whitespace'}, {';'}], lambda: [_ast.Continue()])

# break
g = g.put('statements', [{'whitespace'}, {'b'}, {'r'}, {'e'}, {'a'}, {'k'},
                         {'whitespace'}, {';'}], lambda: [_ast.Break()])

# return
g = g.put('statements', [{'whitespace'}, {'r'}, {'e'}, {'t'}, {'u'}, {'r'}, {'n'},
                         'expression',
                         {'whitespace'}, {';'}], lambda value: [_ast.Return(value)])

# variable assignment
g = g.put('statements', ['identifier',
                         {'whitespace'}, {'='},
                         'expression',
                         {'whitespace'}, {';'},
                         'statements'], lambda name, value, next: [_ast.VariableAssignment(name, value, next)])

# attribute assignment
g = g.put('statements', ['postfix_expression',
                         {'whitespace'}, {'.'},
                         'identifier',
                         {'whitespace'}, {'='},
                         'expression',
                         {'whitespace'}, {';'},
                         'statements'], lambda object, attribute_name, value, next: [_ast.AttributeAssignment(object, attribute_name, value, next)])

# import
g = g.put('statements', [{'whitespace'}, {'i'}, {'m'}, {'p'}, {'o'}, {'r'}, {'t'},
                         'string',
                         {'whitespace'}, {';'},
                         'statements'], lambda name, next: [_ast.Import(name, next)])


g = g.put('expression', ['postfix_expression'])


g = g.put('postfix_expression', ['primary_expression'])

# attribute access
g = g.put('postfix_expression', ['postfix_expression',
                                 {'whitespace'}, {'.'},
                                 'identifier'], lambda object, attribute_name: [_ast.AttributeAccess(object, attribute_name)])

# invocation
g = g.put('postfix_expression', ['postfix_expression',
                                 {'whitespace'}, {'('},
                                 'invocation_arguments',
                                 {'whitespace'}, {')'}], lambda invocable, arguments: [_ast.Invocation(invocable, arguments)])

g = g.put('invocation_arguments', [], lambda: [()])
g = g.put('invocation_arguments', ['expression'], lambda argument: [(argument,)])
g = g.put('invocation_arguments', ['expression',
                                   {'whitespace'}, {','},
                                   'invocation_arguments'], lambda argument, rest: [(argument,) + rest])

# variable use
g = g.put('primary_expression', ['identifier'], lambda name: [_ast.VariableUse(name)])

# number literal
g = g.put('primary_expression', ['number'], lambda value: [_ast.NumberLiteral(value)])

# string literal
g = g.put('primary_expression', ['string'], lambda value: [_ast.StringLiteral(value)])

# function literal
g = g.put('primary_expression', [{'whitespace'}, {'f'}, {'u'}, {'n'}, {'c'},
                                 {'whitespace'}, {'('},
                                 'function_literal_arguments',
                                 {'whitespace'}, {')'},
                                 {'whitespace'}, {'{'},
                                 'statements',
                                 {'whitespace'}, {'}'}], lambda arguments, body: [_ast.FunctionLiteral(arguments, body)])

g = g.put('function_literal_arguments', [], lambda: [()])
g = g.put('function_literal_arguments', ['identifier'], lambda argument: [(argument,)])
g = g.put('function_literal_arguments', ['identifier',
                                         {'whitespace'}, {','},
                                         'function_literal_arguments'], lambda first, rest: [(first,) + rest])

# parenthesized expression
g = g.put('primary_expression', [{'whitespace'}, {'('},
                                 'expression',
                                 {'whitespace'}, {')'}], lambda expression: [_ast.ParenthesizedExpression(expression)])


g = g.put('string', [{'whitespace'}, {'\''}, 'string_items', {'\''}], lambda *cs: [''.join(cs)])

g = g.put('string_items', [])
g = g.put('string_items', ['string_item', 'string_items'])

g = g.put('string_item', ['letter'])
g = g.put('string_item', ['digit'])
g = g.put('string_item', ['punctuation_without_slash_and_quote'])
g = g.put('string_item', ['whitespace_char'])
g = g.put('string_item', [{'\\'}, '\\'])
g = g.put('string_item', [{'\\'}, '\''])
g = g.put('string_item', [{'\\'}, {'t'}], lambda: ['\t'])
g = g.put('string_item', [{'\\'}, {'v'}], lambda: ['\v'])
g = g.put('string_item', [{'\\'}, {'f'}], lambda: ['\f'])
g = g.put('string_item', [{'\\'}, {'n'}], lambda: ['\n'])
g = g.put('string_item', [{'\\'}, {'r'}], lambda: ['\r'])


g = g.put('number', [{'whitespace'},
                     'number_sign_opt',
                     'number_integer',
                     'number_fraction_opt',
                     'number_exponent_opt'], lambda *cs: [float(''.join(cs))])

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


g = g.put('identifier', [{'whitespace'},
                         'identifier_head',
                         'identifier_tail'], lambda *cs: [''.join(cs)])

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
g = g.put('comment_char', ['whitespace_without_newline'])


for c in _string.ascii_letters:
    g = g.put('letter', [c])

for c in _string.digits:
    g = g.put('digit', [c])

for c in _string.punctuation:
    if c not in '\\\'':
        g = g.put('punctuation_without_slash_and_quote', [c])
g = g.put('punctuation', ['punctuation_without_slash_and_quote'])
g = g.put('punctuation', ['\\'])
g = g.put('punctuation', ['\''])

g = g.put('whitespace_without_newline', [])
g = g.put('whitespace_without_newline', ['whitespace_char_without_newline', 'whitespace_without_newline'])
for c in _string.whitespace:
    if c != '\n':
        g = g.put('whitespace_char_without_newline', [c])
g = g.put('whitespace', [])
g = g.put('whitespace', ['whitespace_char', 'whitespace'])
g = g.put('whitespace_char', ['whitespace_without_newline'])
g = g.put('whitespace_char', ['\n'])

core_grammar = g

del g
