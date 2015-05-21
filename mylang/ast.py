from collections import namedtuple as _namedtuple


class Module(_namedtuple('Module', ['body'])):
    def __str__(self):
        return str(self.body)


class Nothing(_namedtuple('Nothing', [])):
    def __str__(self):
        return ''


class UnusedExpression(_namedtuple('UnusedExpression', ['expression', 'next'])):
    def __str__(self):
        return '{}; {}'.format(self.expression, self.next)


class VariableDeclaration(_namedtuple('VariableDeclaration', ['name', 'next'])):
    def __str__(self):
        return 'var {}; {}'.format(self.name, self.next)


class MacroDeclaration(_namedtuple('MacroDeclaration', ['rule', 'transform', 'next'])):
    def __str__(self):
        nonterminal, arguments = self.rule
        argument_strings = []
        for tag, symbol in arguments:
            if tag == 'lit':
                argument_strings.append(_quote_string_literal(symbol))
            elif tag == 'did':
                argument_strings.append(symbol)
            elif tag == 'uid':
                argument_strings.append('$' + symbol)
        return 'macro {}: {} -> {}; {}'.format(nonterminal, ', '.join(argument_strings), self.transform, self.next)


class Block(_namedtuple('Block', ['body', 'next'])):
    def __str__(self):
        return '{{ {} }} {}'.format(self.body, self.next)


class IfElse(_namedtuple('IfElse', ['condition', 'true_clause', 'false_clause', 'next'])):
    def __str__(self):
        return 'if {} {{ {} }} else {{ {} }} {}'.format(self.condition, self.true_clause, self.false_clause, self.next)


class Forever(_namedtuple('Forever', ['body', 'next'])):
    def __str__(self):
        return 'forever {{ {} }} {}'.format(self.body, self.next)


class Continue(_namedtuple('Continue', [])):
    def __str__(self):
        return 'continue;'


class Break(_namedtuple('Break', [])):
    def __str__(self):
        return 'break;'


class Return(_namedtuple('Return', ['value'])):
    def __str__(self):
        return 'return {};'.format(self.value)


class VariableAssignment(_namedtuple('VariableAssignment', ['name', 'value', 'next'])):
    def __str__(self):
        return '{} = {}; {}'.format(self.name, self.value, self.next)


class AttributeAssignment(_namedtuple('AttributeAssignment', ['object', 'attribute_name', 'value', 'next'])):
    def __str__(self):
        return '{}.{} = {}; {}'.format(self.object, self.attribute_name, self.value, self.next)


class Import(_namedtuple('Import', ['name', 'next'])):
    def __str__(self):
        return 'import {}; {}'.format(self.name, self.next)


class VariableUse(_namedtuple('VariableUse', ['name'])):
    def __str__(self):
        return self.name


class NumberLiteral(_namedtuple('NumberLiteral', ['value'])):
    def __str__(self):
        return str(self.value)


class StringLiteral(_namedtuple('StringLiteral', ['value'])):
    def __str__(self):
        return _quote_string_literal(self.value)


class FunctionLiteral(_namedtuple('FunctionLiteral', ['arguments', 'body'])):
    def __str__(self):
        return 'func ({}) {{ {} }}'.format(', '.join(map(str, self.arguments)), self.body)


class AttributeAccess(_namedtuple('AttributeAccess', ['object', 'attribute_name'])):
    def __str__(self):
        return '{}.{}'.format(self.object, self.attribute_name)


class Invocation(_namedtuple('Invocation', ['invocable', 'arguments'])):
    def __str__(self):
        return '{}({})'.format(self.invocable, ', '.join(map(str, self.arguments)))


class ParenthesizedExpression(_namedtuple('ParenthesizedExpression', ['expression'])):
    def __str__(self):
        return '({})'.format(self.expression)


class MacroUse(_namedtuple('MacroUse', ['rule', 'nodes'])):
    def __str__(self):
        raise NotImplementedError()


def _quote_string_literal(text):
    text = text. \
        replace('\\', '\\\\'). \
        replace('\'', '\\\''). \
        replace('\t', '\\\t'). \
        replace('\v', '\\\v'). \
        replace('\f', '\\\f'). \
        replace('\n', '\\\n'). \
        replace('\r', '\\\r')
    return '\'{}\''.format(text)