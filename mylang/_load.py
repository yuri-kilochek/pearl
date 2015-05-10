from collections import namedtuple as _namedtuple
import string as _string

import pearl as _pearl
from . import ast as _ast
from ._builtins import builtins as _builtins


def _put_declared_variable(g, name):
        g = g.put('declared_variable', [{'whitespace'}] + list(name), lambda *cs: [''.join(cs)])
        return g


def _build_core_grammar():
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
                             {'whitespace'}, {';'}, _put_declared_variable,
                             'statements'], lambda name, next: [_ast.VariableDeclaration(name, next)])

    # # macro declaration
    # 'statements', [{'whitespace'}, {'m'}, {'a'}, {'c'}, {'r'}, {'o'},
    #                'identifier',
    #                {'whitespace'}, {'('},
    #                'macro_declaration_arguments',
    #                {'whitespace'}, {')'},
    #                {'whitespace'}, {'-'}, {'>'},
    #                'expression',
    #                {'whitespace'}, {';'}, (lambda g, nonterminal, arguments, _: g.put(nonterminal, [s if u else {s} for s, u in arguments], lambda *nodes: [MacroUse((nonterminal, tuple(s for s, _ in arguments)), nodes)])),
    #                'statements'], lambda nonterminal, arguments, transformer, next: [MacroDeclaration((nonterminal, tuple(s for s, _ in arguments)), transformer, next)],
    #
    # 'macro_declaration_arguments', [], lambda: [()],
    # 'macro_declaration_arguments', ['macro_declaration_argument'], lambda symbols: [symbols],
    # 'macro_declaration_arguments', ['macro_declaration_argument',
    #                                 {'whitespace'}, {','},
    #                                 'macro_declaration_arguments'], lambda firsts, rest: [firsts + rest],
    #
    #
    # 'macro_declaration_argument', ['string'], lambda literal: [tuple((s, False) for s in literal)],
    # 'macro_declaration_argument', ['identifier'], lambda symbol: [((symbol, False),)],
    # 'macro_declaration_argument', [{'whitespace'}, {'@'},
    #                                'identifier'], lambda symbol: [((symbol, True),)],

    # block
    g = g.put('statements', [{'whitespace'}, {'{'},
                             'statements',
                             {'whitespace'}, {'}'},
                             'statements'], lambda body, next: [_ast.block(body, next)])

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

    def put_loop_control(g):
        g = g.put('loop_control', [{'whitespace'}, {'c'}, {'o'}, {'n'}, {'t'}, {'i'}, {'n'}, {'u'}, {'e'},
                                   {'whitespace'}, {';'}], lambda: [_ast.Continue()])
        g = g.put('loop_control', [{'whitespace'}, {'b'}, {'r'}, {'e'}, {'a'}, {'k'},
                                   {'whitespace'}, {';'}], lambda: [_ast.Break()])
        return g

    # forever
    g = g.put('statements', [{'whitespace'}, {'f'}, {'o'}, {'r'}, {'e'}, {'v'}, {'e'}, {'r'},
                             'forever_body',
                             'statements'], lambda body, next: [_ast.Forever(body, next)])

    g = g.put('forever_body', [{'whitespace'}, {'{'}, put_loop_control,
                               'statements',
                               {'whitespace'}, {'}'}])

    # loop control
    g = g.put('statements', ['loop_control'])

    # function control
    g = g.put('statements', ['function_control'])

    # variable assignment
    g = g.put('statements', ['declared_variable',
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
                             'statements'], lambda object, attribute_name, value, next: [_ast.ttributeAssignment(object, attribute_name, value, next)])

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
    g = g.put('primary_expression', ['declared_variable'], lambda name: [_ast.VariableUse(name)])

    # number literal
    g = g.put('primary_expression', ['number'], lambda value: [_ast.NumberLiteral(value)])

    # string literal
    g = g.put('primary_expression', ['string'], lambda value: [_ast.StringLiteral(value)])

    def put_function_control(g):
        g = g.put('function_control', [{'whitespace'}, {'r'}, {'e'}, {'t'}, {'u'}, {'r'}, {'n'},
                                       'expression',
                                       {'whitespace'}, {';'}], lambda value: [_ast.Return(value)])
        return g

    def put_function_arguments(g, arguments):
        for name in arguments:
            g = _put_declared_variable(g, name)
        return g

    def drop_loop_control(g):
        g = g.drop('loop_control')
        return g

    # function literal
    g = g.put('primary_expression', [{'whitespace'}, {'f'}, {'u'}, {'n'}, {'c'},
                                     {'whitespace'}, {'('},
                                     'function_literal_arguments',
                                     {'whitespace'}, {')'},
                                     {'whitespace'}, {'{'}, (lambda g, arguments: drop_loop_control(put_function_control(put_function_arguments(g, arguments)))),
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
                                     {'whitespace'}, {')'}])


    g = g.put('string', [{'whitespace'}, {'\''}, 'string_items', {'\''}], lambda *cs: [''.join(cs)])

    g = g.put('string_items', [])
    g = g.put('string_items', ['string_item', 'string_items'])

    g = g.put('string_item', ['letter'])
    g = g.put('string_item', ['digit'])
    g = g.put('string_item', ['punctuation_without_quote'])
    g = g.put('string_item', ['whitespace'])
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
        if c != '\'':
            g = g.put('punctuation_without_quote', [c])
    g = g.put('punctuation', ['punctuation_without_quote'])
    g = g.put('punctuation', ['\''])

    g = g.put('whitespace_without_newline', [])
    for c in _string.whitespace:
        if c != '\n':
            g = g.put('whitespace_without_newline', [c, 'whitespace_without_newline'])
    g = g.put('whitespace', ['whitespace_without_newline'])
    g = g.put('whitespace', [])
    g = g.put('whitespace', ['\n', 'whitespace'])

    return g

core_grammar = _build_core_grammar()


class _CharacterToken(_namedtuple('_CharacterToken', ['symbol', 'position'])):
    @property
    def values(self):
        return [self.symbol]


def _tokenize(text):
    line = 1
    column = 1
    for character in text:
        yield _CharacterToken(character, (line, column))
        if character == '\n':
            line += 1
            column = 1
        else:
            column += 1


def _read_characters(path):
    with open(path) as file:
        while True:
            c = file.read(1)
            if not c:
                break
            yield c


def load(module_path, declared_variables=(), *, grammar=core_grammar):
    for name in frozenset(declared_variables) | frozenset(_builtins):
        grammar = _put_declared_variable(grammar, name)

    text = _read_characters(module_path + '.meta')
    tokens = _tokenize(text)
    results = list(_pearl.parse(grammar, tokens))
    if len(results) == 1:
        results, grammar = results[0]
        return results[0], grammar
    raise Exception('Ambiguous source in \'{}.meta\''.format(module_path))
