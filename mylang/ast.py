from collections import namedtuple as _namedtuple


class Module(_namedtuple('Module', ['body'])):
    def execute(self, variables):
        context = _Context()

        for name, value in variables.items():
            context.declare_and_assign(name, value)

        self.body.execute(context)

        return context.variables


class Nothing(_namedtuple('Nothing', [])):
    def execute(self, context):
        pass


class UnusedExpression(_namedtuple('UnusedExpression', ['expression', 'next'])):
    def execute(self, context):
        self.expression.execute(context)
        self.next.execute(context)


class VariableDeclaration(_namedtuple('VariableDeclaration', ['name', 'next'])):
    def execute(self, context):
        context.declare(self.name)
        self.next.execute(context)


class MacroDeclarationTerminalParameter(_namedtuple('MacroDeclarationTerminalParameter', ['symbols'])): pass


class MacroDeclarationNonterminalParameter(_namedtuple('MacroDeclarationNonterminalParameter', ['used', 'symbol'])): pass


class MacroDeclaration(_namedtuple('MacroDeclaration', ['nonterminal', 'parameters', 'transform', 'next'])): pass


class MacroUse(_namedtuple('MacroUse', ['nonterminal', 'parameters', 'nodes'])): pass
    # def execute(self, context):
    #     local_context = _Context(context)
    #     self.body.execute(local_context)
    #     self.next.execute(context)


class Block(_namedtuple('Block', ['body', 'next'])):
    def execute(self, context):
        local_context = _Context(context)
        self.body.execute(local_context)
        self.next.execute(context)


class IfElse(_namedtuple('IfElse', ['condition', 'true_clause', 'false_clause', 'next'])):
    def execute(self, context):
        if self.condition.execute(context):
            local_context = _Context(context)
            self.true_clause.execute(local_context)
        else:
            local_context = _Context(context)
            self.false_clause.execute(local_context)
        self.next.execute(context)


class Forever(_namedtuple('Forever', ['body', 'next'])):
    def execute(self, context):
        while True:
            try:
                local_context = _Context(context)
                self.body.execute(local_context)
            except Continue.Exception:
                continue
            except Break.Exception:
                break
        self.next.execute(context)


class Continue(_namedtuple('Continue', [])):
    class Exception(Exception):
        pass

    def execute(self, context):
        raise Continue.Exception()


class Break(_namedtuple('Break', [])):
    class Exception(Exception):
        pass

    def execute(self, context):
        raise Break.Exception()


class Return(_namedtuple('Return', ['value'])):
    class Exception(Exception):
        def __init__(self, value):
            self.__value = value

        @property
        def value(self):
            return self.__value

    def execute(self, context):
        value = self.value.execute(context)
        raise Return.Exception(value)


class VariableAssignment(_namedtuple('VariableAssignment', ['name', 'value', 'next'])):
    def execute(self, context):
        value = self.value.execute(context)
        context.assign(self.name, value)
        self.next.execute(context)


class AttributeAssignment(_namedtuple('AttributeAssignment', ['object', 'attribute_name', 'value', 'next'])):
    def execute(self, context):
        value = self.value.execute(context)
        object = self.object.execute(context)
        setattr(object, self.attribute_name, value)
        self.next.execute(context)


class VariableAccess(_namedtuple('VariableAccess', ['name'])):
    def execute(node, context):
        value = context.access(node.name)
        return value


class AttributeAccess(_namedtuple('AttributeAccess', ['object', 'attribute_name'])):
    def execute(self, context):
        object = self.object.execute(context)
        value = getattr(object, self.attribute_name)
        return value


class NumberLiteral(_namedtuple('NumberLiteral', ['value'])):
    def execute(self, context):
        return self.value


class StringLiteral(_namedtuple('StringLiteral', ['value'])):
    def execute(self, context):
        return self.value


class FunctionLiteral(_namedtuple('FunctionLiteral', ['arguments', 'body'])):
    def execute(self, context):
        def value(*arguments):
            local_context = _Context(context)
            for name, value in zip(self.arguments, arguments):
                local_context.declare_and_assign(name, value)
            try:
                self.body.execute(local_context)
            except Return.Exception as j:
                return j.value
        return value


class Call(_namedtuple('Call', ['callable', 'arguments'])):
    def execute(self, context):
        arguments = [a.execute(context) for a in self.arguments]
        invocable = self.callable.execute(context)
        value = invocable(*arguments)
        return value


class _Context:
    UNASSIGNED_VARIABLE_PLACEHOLDER = object()

    def __init__(self, parent=None):
        self.__parent = parent
        self.__variables = {}

    @property
    def variables(self):
        return self.__variables

    def declare(self, name):
        self.__variables.setdefault(name, _Context.UNASSIGNED_VARIABLE_PLACEHOLDER)

    def assign(self, name, value):
        if name in self.__variables:
            self.__variables[name] = value
        elif self.__parent is not None:
            self.__parent.assign(name, value)
        else:
            raise Exception('Assignment to undeclared variable \'{}\''.format(name))

    def declare_and_assign(self, name, value):
        self.declare(name)
        self.assign(name, value)

    def access(self, name):
        if name in self.__variables:
            value = self.__variables[name]
            if value is _Context.UNASSIGNED_VARIABLE_PLACEHOLDER:
                raise Exception('Use of unassigned variable \'{}\''.format(name))
            return value
        elif self.__parent is not None:
            return self.__parent.access(name)
        else:
            raise Exception('Use of undeclared variable \'{}\''.format(name))
