from collections import namedtuple as _namedtuple
import string

import pearl

UnusedExpression = _namedtuple('UnusedExpression', ['expression'])
VariableDeclaration = _namedtuple('VariableDeclaration', ['name'])
VariableAssignment = _namedtuple('VariableAssignment', ['name', 'value'])
IfElse = _namedtuple('IfElse', ['condition', 'true_clause', 'false_clause'])
While = _namedtuple('While', ['condition', 'body'])
Continue = _namedtuple('Continue', [])
Break = _namedtuple('Break', [])
Return = _namedtuple('Return', ['value'])
Block = _namedtuple('Block', ['statements'])

Invocation = _namedtuple('Invocation', ['invocable', 'arguments'])

Variable = _namedtuple('Variable', ['name'])
NumberLiteral = _namedtuple('NumberLiteral', ['value'])
StringLiteral = _namedtuple('StringLiteral', ['value'])
ClosureLiteral = _namedtuple('ClosureLiteral', ['arguments', 'body'])


def build_grammar():
    g = pearl.Grammar[
        '_start_': ['statements', {'whitespace'}],


        'statements': []: lambda: [()],
        'statements': ['statement', 'statements']: lambda first, rest: [(first,) + rest],


        'statement': ['unused_expression'],
        'unused_expression': ['expression',
                              {'whitespace'}, {';'}]: lambda expression: [UnusedExpression(expression)],

        'statement': ['variable_declaration'],
        'variable_declaration': [{'whitespace'}, {'v'}, {'a'}, {'r'},
                                 'identifier',
                                 {'whitespace'}, {';'}]: lambda name: [VariableDeclaration(name)],

        'statement': ['variable_assignment'],
        'variable_assignment': ['identifier',
                                {'whitespace'}, {'='},
                                'expression',
                                {'whitespace'}, {';'}]: lambda name, value: [VariableAssignment(name, value)],

        'statement': ['if_else'],
        'if_else': [{'whitespace'}, {'i'}, {'f'},
                    'expression',
                    'block',
                    {'whitespace'}, {'e'}, {'l'}, {'s'}, {'e'},
                    'block']: lambda condition, true_clause, false_clause: [IfElse(condition, true_clause, false_clause)],

        'statement': ['while'],
        'while': [{'whitespace'}, {'w'}, {'h'}, {'i'}, {'l'}, {'e'},
                  'expression',
                  'block']: lambda condition, body: [While(condition, body)],

        'statement': ['continue'],
        'continue': [{'whitespace'}, {'c'}, {'o'}, {'n'}, {'t'}, {'i'}, {'n'}, {'u'}, {'e'},
                     {'whitespace'}, {';'}]: lambda: [Continue()],

        'statement': ['break'],
        'break': [{'whitespace'}, {'b'}, {'r'}, {'e'}, {'a'}, {'k'},
                  {'whitespace'}, {';'}]: lambda: [Break()],

        'statement': ['return'],
        'return': [{'whitespace'}, {'r'}, {'e'}, {'t'}, {'u'}, {'r'}, {'n'},
                   'expression',
                   {'whitespace'}, {';'}]: lambda value: [Return(value)],

        'statement': ['block'],
        'block': [{'whitespace'}, {'{'},
                  'statements',
                  {'whitespace'}, {'}'}]: lambda statements: [Block(statements)],


        'expression': ['postfix_expression'],

        'postfix_expression': ['primary_expression'],

        'postfix_expression': ['invocation'],
        'invocation': ['postfix_expression',
                       {'whitespace'}, {'('},
                       'invocation_arguments',
                       {'whitespace'}, {')'}]: lambda invocable, arguments: [Invocation(invocable, arguments)],

        'invocation_arguments': []: lambda: [()],
        'invocation_arguments': ['expression']: lambda argument: [(argument,)],
        'invocation_arguments': ['expression',
                                 {'whitespace'}, {','},
                                 'invocation_arguments']: lambda argument, rest: [(argument,) + rest],


        'primary_expression': ['variable'],
        'variable': ['identifier']: lambda name: [Variable(name)],

        'primary_expression': ['number_literal'],
        'number_literal': ['number']: lambda value: [NumberLiteral(value)],

        'primary_expression': ['string_literal'],
        'string_literal': ['string']: lambda value: [StringLiteral(value)],

        'primary_expression': ['closure_literal'],
        'closure_literal': [{'whitespace'}, {'('},
                            'closure_literal_arguments',
                            {'whitespace'}, {')'},
                            {'whitespace'}, {'-'}, {'>'},
                            'block']: lambda arguments, body: [ClosureLiteral(arguments, body)],

        'closure_literal_arguments': []: lambda: [()],
        'closure_literal_arguments': ['identifier']: lambda argument: [(argument,)],
        'closure_literal_arguments': ['identifier',
                                      {'whitespace'}, {','},
                                      'closure_literal_arguments']: lambda first, rest: [(first,) + rest],

        'primary_expression': [{'whitespace'}, {'('},
                               'expression',
                               {'whitespace'}, {')'}],


        # 'expression': [{'whitespace'}, {'m'}, {'a'}, {'c'}, {'r'}, {'o'},
        #                {'ws1'}, 'identifier',
        #                {'whitespace'}, 'symbol_list', (lambda g, nt, bs: g.put('macro_replacement', [nt.text], lambda *x: [x])),
        #                {'whitespace'}, {'-'}, {'>'},
        #                {'whitespace'}, 'macro_replacement',
        #                {'whitespace'}, {';'}, (lambda g, nt, bs, r: g),
        #                {'whitespace'}, 'expression']: lambda nt, bs, r, next: [MacroDeclaration(nt, bs, r, next)],

        # 'symbol_list': []: lambda: [()],
        # 'symbol_list': [{'whitespace'}, 'symbol', {'whitespace'}, 'symbol0']: lambda first, rest: [(first,) + rest],
        #
        # 'symbol': ['identifier'],
        # 'symbol': ['string_literal'],


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
    ]

    for c in string.ascii_letters:
        g = g.put('letter', [c])

    for c in string.digits:
        g = g.put('digit', [c])

    for c in string.punctuation:
        if c != '\'':
            g = g.put('punctuation_without_quote', [c])
    g = g.put('punctuation', ['\''])
    g = g.put('punctuation', ['punctuation_without_quote'])

    g = g.put('whitespace', [])
    for c in string.whitespace:
        g = g.put('whitespace', [c, 'whitespace'])

    return g

grammar = build_grammar()

text = r'''
    var clamp;
    clamp = (a, x, b) -> {
        return x;
    };

    var x;
    x = foo(1);
    if le(x, 0) {
        while x {
            bar(baz(x), 4);
        }
    } else {
        quix(kek);
    }
'''


class СharacterToken(_namedtuple('_СharacterToken', ['symbol', 'position'])):
    @property
    def values(self):
        return [self.symbol]


def tokenize(text):
    line = 1
    column = 1
    for character in text:
        yield СharacterToken(character, (line, column))
        if character == '\n':
            line += 1
            column = 1
        else:
            column += 1


for r, in pearl.parse(grammar, tokenize(text)):
    print(r)