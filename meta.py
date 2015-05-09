from collections import namedtuple as _namedtuple
import string as _string

import pearl as _pearl


class _СharacterToken(_namedtuple('_СharacterToken', ['symbol', 'position'])):
    @property
    def values(self):
        return [self.symbol]


def _tokenize(text):
    line = 1
    column = 1
    for character in text:
        yield _СharacterToken(character, (line, column))
        if character == '\n':
            line += 1
            column = 1
        else:
            column += 1

Nothing = _namedtuple('Nothing', [])
Import = _namedtuple('Import', ['name', 'next'])
UnusedExpression = _namedtuple('UnusedExpression', ['expression', 'next'])
VariableDeclaration = _namedtuple('VariableDeclaration', ['name', 'next'])
VariableAssignment = _namedtuple('VariableAssignment', ['name', 'value', 'next'])
AttributeAssignment = _namedtuple('AttributeAssignment', ['object', 'attribute_name', 'value', 'next'])
IfElse = _namedtuple('IfElse', ['condition', 'true_clause', 'false_clause', 'next'])
Loop = _namedtuple('Loop', ['body', 'next'])
Continue = _namedtuple('Continue', [])
Break = _namedtuple('Break', [])
Return = _namedtuple('Return', ['value'])
Block = _namedtuple('Block', ['body', 'next'])
MacroDeclaration = _namedtuple('MacroDeclaration', ['rule', 'transformer', 'next'])
MacroUse = _namedtuple('MacroUse', ['rule', 'nodes'])

AttributeAccess = _namedtuple('AttributeAccess', ['object', 'attribute_name'])
Invocation = _namedtuple('Invocation', ['invocable', 'arguments'])

VariableUse = _namedtuple('VariableUse', ['name'])
NumberLiteral = _namedtuple('NumberLiteral', ['value'])
StringLiteral = _namedtuple('StringLiteral', ['value'])
FunctionLiteral = _namedtuple('FunctionLiteral', ['arguments', 'body'])


def _build_default_grammar():
    g = _pearl.Grammar[
        '_start_': ['statements', {'whitespace'}],

        # nothing
        'statements': []: lambda: [Nothing()],

        # import
        'statements': [{'whitespace'}, {'i'}, {'m'}, {'p'}, {'o'}, {'r'}, {'t'},
                       'string',
                       {'whitespace'}, {';'},
                       'statements']: lambda name, next: [Import(name, next)],

        # variable declaration
        'statements': [{'whitespace'}, {'v'}, {'a'}, {'r'},
                       'identifier',
                       {'whitespace'}, {';'},
                       'statements']: lambda name, next: [VariableDeclaration(name, next)],

        # variable assignment
        'statements': ['identifier',
                       {'whitespace'}, {'='},
                       'expression',
                       {'whitespace'}, {';'},
                       'statements']: lambda name, value, next: [VariableAssignment(name, value, next)],

        # attribute assignment
        'statements': ['postfix_expression',
                       {'whitespace'}, {'.'},
                       'identifier',
                       {'whitespace'}, {'='},
                       'expression',
                       {'whitespace'}, {';'},
                       'statements']: lambda object, attribute_name, value, next: [AttributeAssignment(object, attribute_name, value, next)],

        # if else
        'statements': [{'whitespace'}, {'i'}, {'f'},
                       'expression',
                       {'whitespace'}, {'{'},
                       'statements',
                       {'whitespace'}, {'}'},
                       {'whitespace'}, {'e'}, {'l'}, {'s'}, {'e'},
                       {'whitespace'}, {'{'},
                       'statements',
                       {'whitespace'}, {'}'},
                       'statements']: lambda condition, true_clause, false_clause, next: [IfElse(condition, true_clause, false_clause, next)],

        # loop
        'statements': [{'whitespace'}, {'l'}, {'o'}, {'o'}, {'p'},
                       {'whitespace'}, {'{'},
                       'statements',
                       {'whitespace'}, {'}'},
                       'statements']: lambda body, next: [Loop(body, next)],

        # continue
        'statements': [{'whitespace'}, {'c'}, {'o'}, {'n'}, {'t'}, {'i'}, {'n'}, {'u'}, {'e'},
                       {'whitespace'}, {';'}]: lambda: [Continue()],

        # break
        'statements': [{'whitespace'}, {'b'}, {'r'}, {'e'}, {'a'}, {'k'},
                       {'whitespace'}, {';'}]: lambda: [Break()],

        # return
        'statements': [{'whitespace'}, {'r'}, {'e'}, {'t'}, {'u'}, {'r'}, {'n'},
                       'expression',
                       {'whitespace'}, {';'}]: lambda value: [Return(value)],

        # block
        'statements': [{'whitespace'}, {'{'},
                       'statements',
                       {'whitespace'}, {'}'},
                       'statements']: lambda body, next: [Block(body, next)],

        # macro declaration
        'statements': [{'whitespace'}, {'m'}, {'a'}, {'c'}, {'r'}, {'o'},
                       'identifier',
                       {'whitespace'}, {'('},
                       'macro_declaration_arguments',
                       {'whitespace'}, {')'},
                       {'whitespace'}, {'-'}, {'>'},
                       'expression',
                       {'whitespace'}, {';'}, (lambda g, nonterminal, arguments, _: g.put(nonterminal, [s if u else {s} for s, u in arguments], lambda *nodes: [MacroUse((nonterminal, tuple(s for s, _ in arguments)), nodes)])),
                       'statements']: lambda nonterminal, arguments, transformer, next: [MacroDeclaration((nonterminal, tuple(s for s, _ in arguments)), transformer, next)],

        'macro_declaration_arguments': []: lambda: [()],
        'macro_declaration_arguments': ['macro_declaration_argument']: lambda symbols: [symbols],
        'macro_declaration_arguments': ['macro_declaration_argument',
                                        {'whitespace'}, {','},
                                        'macro_declaration_arguments']: lambda firsts, rest: [firsts + rest],


        'macro_declaration_argument': ['string']: lambda literal: [tuple((s, False) for s in literal)],
        'macro_declaration_argument': ['identifier']: lambda symbol: [((symbol, False),)],
        'macro_declaration_argument': [{'whitespace'}, {'@'},
                                       'identifier']: lambda symbol: [((symbol, True),)],

        # unused expression
        'statements': ['expression',
                       {'whitespace'}, {';'},
                       'statements']: lambda expression, next: [UnusedExpression(expression, next)],


        'expression': ['postfix_expression'],

        'postfix_expression': ['primary_expression'],

        # attribute access
        'postfix_expression': ['postfix_expression',
                               {'whitespace'}, {'.'},
                               'identifier']: lambda object, attribute_name: [AttributeAccess(object, attribute_name)],

        # invocation
        'postfix_expression': ['postfix_expression',
                               {'whitespace'}, {'('},
                               'invocation_arguments',
                               {'whitespace'}, {')'}]: lambda invocable, arguments: [Invocation(invocable, arguments)],

        'invocation_arguments': []: lambda: [()],
        'invocation_arguments': ['expression']: lambda argument: [(argument,)],
        'invocation_arguments': ['expression',
                                 {'whitespace'}, {','},
                                 'invocation_arguments']: lambda argument, rest: [(argument,) + rest],

        # variable use
        'primary_expression': ['identifier']: lambda name: [VariableUse(name)],

        # number literal
        'primary_expression': ['number']: lambda value: [NumberLiteral(value)],

        # string literal
        'primary_expression': ['string']: lambda value: [StringLiteral(value)],

        # function literal
        'primary_expression': [{'whitespace'}, {'f'}, {'u'}, {'n'}, {'c'},
                               {'whitespace'}, {'('},
                               'function_literal_arguments',
                               {'whitespace'}, {')'},
                               {'whitespace'}, {'{'},
                               'statements',
                               {'whitespace'}, {'}'}]: lambda arguments, body: [FunctionLiteral(arguments, body)],

        'function_literal_arguments': []: lambda: [()],
        'function_literal_arguments': ['identifier']: lambda argument: [(argument,)],
        'function_literal_arguments': ['identifier',
                                       {'whitespace'}, {','},
                                       'function_literal_arguments']: lambda first, rest: [(first,) + rest],

        # parenthesized expression
        'primary_expression': [{'whitespace'}, {'('},
                               'expression',
                               {'whitespace'}, {')'}],


        'string': [{'whitespace'}, {'\''}, 'string_items', {'\''}]: lambda *cs: [''.join(cs)],

        'string_items': [],
        'string_items': ['string_item', 'string_items'],

        'string_item': ['letter'],
        'string_item': ['digit'],
        'string_item': ['punctuation_without_quote'],
        'string_item': ['whitespace'],
        'string_item': [{'\\'}, '\\'],
        'string_item': [{'\\'}, '\''],
        'string_item': [{'\\'}, {'t'}]: lambda: ['\t'],
        'string_item': [{'\\'}, {'v'}]: lambda: ['\v'],
        'string_item': [{'\\'}, {'f'}]: lambda: ['\f'],
        'string_item': [{'\\'}, {'n'}]: lambda: ['\n'],
        'string_item': [{'\\'}, {'r'}]: lambda: ['\r'],


        'number': [{'whitespace'},
                   'number_sign_opt',
                   'number_integer',
                   'number_fraction_opt',
                   'number_exponent_opt']: lambda *cs: [float(''.join(cs))],

        'number_sign_opt': [],
        'number_sign_opt': ['+'],
        'number_sign_opt': ['-'],

        'number_integer': ['digit'],
        'number_integer': ['digit', 'number_integer'],

        'number_fraction_opt': [],
        'number_fraction_opt': ['.', 'number_integer'],

        'number_exponent_opt': [],
        'number_exponent_opt': ['e', 'number_sign_opt', 'number_integer'],
        'number_exponent_opt': ['E', 'number_sign_opt', 'number_integer'],


        'identifier': [{'whitespace'},
                       'identifier_head',
                       'identifier_tail']: lambda *cs: [''.join(cs)],

        'identifier_head': ['_'],
        'identifier_head': ['letter'],

        'identifier_tail': [],
        'identifier_tail': ['_', 'identifier_tail'],
        'identifier_tail': ['letter', 'identifier_tail'],
        'identifier_tail': ['digit', 'identifier_tail'],


        # comment
        'whitespace': ['#', 'comment_chars', '\n', 'whitespace'],

        'comment_chars': [],
        'comment_chars': ['comment_char', 'comment_chars'],

        'comment_char': ['letter'],
        'comment_char': ['digit'],
        'comment_char': ['punctuation'],
        'comment_char': ['whitespace_without_newline'],
    ]

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

default_grammar = _build_default_grammar()


def _read_characters(path):
    with open(path) as file:
        while True:
            c = file.read(1)
            if not c:
                break
            yield c

def load(module_path, grammar=default_grammar):
    for (module,), grammar in _pearl.parse(grammar, _tokenize(_read_characters(module_path + '.meta'))):
        yield module, grammar

for module, grammar in load('test'):
    print(module)
