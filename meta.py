from collections import namedtuple as _namedtuple
import string

import pearl


Expression = _namedtuple('Expression', ['expression'])
VariableDeclaration = _namedtuple('VariableDeclaration', ['name'])
VariableAssignment = _namedtuple('VariableAssignment', ['name', 'value'])
IfThenElse = _namedtuple('IfThenElse', ['condition', 'on_true', 'on_false'])
WhileDo = _namedtuple('WhileDo', ['condition', 'body'])
Call = _namedtuple('Call', ['function', 'arguments'])
VariableReference = _namedtuple('VariableReference', ['name'])
StringLiteral = _namedtuple('StringLiteral', ['value'])
NumberLiteral = _namedtuple('NumberLiteral', ['value'])


def build_grammar():
    g = pearl.Grammar[
        '_start_': ['statements', {'whitespace'}],

        'statements': []: lambda: [()],
        'statements': ['statement', 'statements']: lambda first, rest: [(first,) + rest],

        'statement': ['expression',
                      {'whitespace'}, {';'}]: lambda expression: [Expression(expression)],

        'statement': [{'whitespace'}, {'v'}, {'a'}, {'r'},
                      'identifier',
                      {'whitespace'}, {';'}]: lambda name: [VariableDeclaration(name)],

        'statement': ['identifier',
                      {'whitespace'}, {'<'}, {'-'},
                      'expression',
                      {'whitespace'}, {';'}]: lambda name, value: [VariableAssignment(name, value)],

        'statement': [{'whitespace'}, {'i'}, {'f'},
                      'expression',
                      {'whitespace'}, {'t'}, {'h'}, {'e'}, {'n'},
                      'statements',
                      {'whitespace'}, {'e'}, {'l'}, {'s'}, {'e'},
                      'statements',
                      {'whitespace'}, {'e'}, {'n'}, {'d'}]: lambda condition, true_clause, false_clause: [IfThenElse(condition, true_clause, false_clause)],

        'statement': [{'whitespace'}, {'w'}, {'h'}, {'i'}, {'l'}, {'e'},
                      'expression',
                      {'whitespace'}, {'d'}, {'o'},
                      'statements',
                      {'whitespace'}, {'e'}, {'n'}, {'d'}]: lambda condition, body: [WhileDo(condition, body)],


        'expression': ['postfix_expression'],


        'postfix_expression': ['primary_expression'],

        'postfix_expression': ['postfix_expression',
                               {'whitespace'}, {'('},
                               'call_arguments',
                               {'whitespace'}, {')'}]: lambda function, arguments: [Call(function, arguments)],

        'call_arguments': []: lambda: [()],
        'call_arguments': ['expression']: lambda argument: [(argument,)],
        'call_arguments': ['expression',
                           {'whitespace'}, {','},
                           'call_arguments']: lambda argument, rest: [(argument,) + rest],


        'primary_expression': ['identifier']: lambda name: [VariableReference(name)],

        'primary_expression': ['number_literal']: lambda value: [NumberLiteral(value)],

        'primary_expression': ['string_literal']: lambda value: [StringLiteral(value)],

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

        'identifier': [{'whitespace'}, 'identifier_head', 'identifier_tail0']: lambda *cs: [''.join(cs)],

        'identifier_head': ['_'],
        'identifier_head': ['letter'],

        'identifier_tail': ['_'],
        'identifier_tail': ['letter'],
        'identifier_tail': ['digit'],

        'identifier_tail0': [],
        'identifier_tail0': ['identifier_tail', 'identifier_tail0'],

        'string_literal': [{'whitespace'}, {'\''}, 'string_literal_item0', {'\''}]: lambda *cs: [''.join(cs)],

        'string_literal_item': ['letter'],
        'string_literal_item': ['digit'],
        'string_literal_item': ['punctuation_without_quote'],
        'string_literal_item': ['whitespace'],
        'string_literal_item': [{'\\'}, '\\'],
        'string_literal_item': [{'\\'}, '\''],
        'string_literal_item': [{'\\'}, {'t'}]: lambda: ['\t'],
        'string_literal_item': [{'\\'}, {'v'}]: lambda: ['\v'],
        'string_literal_item': [{'\\'}, {'f'}]: lambda: ['\f'],
        'string_literal_item': [{'\\'}, {'n'}]: lambda: ['\n'],
        'string_literal_item': [{'\\'}, {'r'}]: lambda: ['\r'],

        'string_literal_item0': [],
        'string_literal_item0': ['string_literal_item', 'string_literal_item0'],


        'number_literal': [{'whitespace'},
                           'number_literal_sign_opt',
                           'number_literal_integer',
                           'number_literal_fraction_opt',
                           'number_literal_exponent_opt']: lambda *cs: [float(''.join(cs))],

        'number_literal_sign_opt': [],
        'number_literal_sign_opt': ['+'],
        'number_literal_sign_opt': ['-'],

        'number_literal_integer': ['digit'],
        'number_literal_integer': ['digit', 'number_literal_integer'],

        'number_literal_fraction_opt': [],
        'number_literal_fraction_opt': ['.', 'number_literal_integer'],

        'number_literal_exponent_opt': [],
        'number_literal_exponent_opt': ['e', 'number_literal_sign_opt', 'number_literal_integer'],
        'number_literal_exponent_opt': ['E', 'number_literal_sign_opt', 'number_literal_integer'],
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
    var x;
    x <- foo(1);
    if le(x, 0) then
        bar(x);
    else
        quix(kek);
    end
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