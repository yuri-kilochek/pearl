from collections import namedtuple as _namedtuple


class Nothing(_namedtuple('Nothing', [])):
    def execute(self, context):
        pass


class UnusedExpression(_namedtuple('UnusedExpression', ['expression', 'next'])):
    def execute(self, context):
        self.expression.execute(context)
        self.next.execute(context)


class Import(_namedtuple('UnusedExpression', ['exported', 'module_path', 'next'])):
    def execute(self, context):
        from ._Module import Module

        module = Module(self.module_path)

        for name, value in module.exported_variables.items():
            context.declare_variable(name)
            context.assign_variable(name, value)

        for rule, definition in module.exported_macro_definitions.items():
            context.define_macro(rule, definition)

        self.next.execute(context)


class VariableDeclaration(_namedtuple('VariableDeclaration', ['exported', 'name', 'next'])):
    def execute(self, context):
        context.declare_variable(self.name)
        self.next.execute(context)


class MacroParameterTerminal(_namedtuple('MacroParameterTerminal', ['symbols'])): pass


class MacroParameterNonterminal(_namedtuple('MacroParameterNonterminal', ['used', 'symbol'])): pass


class MacroDefinition(_namedtuple('MacroDeclaration', ['exported', 'nonterminal', 'parameters', 'definition', 'next'])):
    def execute(self, context):
        definition = self.definition.execute(context)
        context.define_macro((self.nonterminal, self.parameters), definition)
        self.next.execute(context)


class MacroUse(_namedtuple('MacroUse', ['nonterminal', 'parameters', 'nodes'])):
    def execute(self, context):
        definition = context.get_macro_definition((self.nonterminal, self.parameters))
        return definition(context, *self.nodes)


class Block(_namedtuple('Block', ['body', 'next'])):
    def execute(self, context):
        local_context = Context(context)
        self.body.execute(local_context)
        self.next.execute(context)


class IfElse(_namedtuple('IfElse', ['condition', 'true_clause', 'false_clause', 'next'])):
    def execute(self, context):
        if self.condition.execute(context):
            local_context = Context(context)
            self.true_clause.execute(local_context)
        else:
            local_context = Context(context)
            self.false_clause.execute(local_context)
        self.next.execute(context)


class Forever(_namedtuple('Forever', ['body', 'next'])):
    def execute(self, context):
        while True:
            try:
                local_context = Context(context)
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
        context.assign_variable(self.name, value)
        self.next.execute(context)


class AttributeAssignment(_namedtuple('AttributeAssignment', ['object', 'attribute_name', 'value', 'next'])):
    def execute(self, context):
        value = self.value.execute(context)
        object = self.object.execute(context)
        setattr(object, self.attribute_name, value)
        self.next.execute(context)


class VariableAccess(_namedtuple('VariableAccess', ['name'])):
    def execute(node, context):
        value = context.access_variable(node.name)
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
            local_context = Context(context)
            for name, value in zip(self.arguments, arguments):
                local_context.declare_variable(name)
                local_context.assign_variable(name, value)
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


class Context:
    UNASSIGNED_VARIABLE = object()

    def __init__(self, parent=None):
        self.__parent = parent
        self.variables = {}
        self.macro_definitions = {}

    def declare_variable(self, name):
        self.variables.setdefault(name, Context.UNASSIGNED_VARIABLE)

    def assign_variable(self, name, value):
        if name in self.variables:
            self.variables[name] = value
        elif self.__parent is not None:
            self.__parent.assign_variable(name, value)
        else:
            raise Exception('Assignment to undeclared variable \'{}\''.format(name))

    def access_variable(self, name):
        if name in self.variables:
            value = self.variables[name]
            if value is Context.UNASSIGNED_VARIABLE:
                raise Exception('Use of unassigned variable \'{}\''.format(name))
            return value
        elif self.__parent is not None:
            return self.__parent.access_variable(name)
        else:
            raise Exception('Use of undeclared variable \'{}\''.format(name))

    def define_macro(self, rule, definition):
        self.macro_definitions[rule] = definition

    def get_macro_definition(self, rule):
        try:
            return self.macro_definitions[rule]
        except KeyError:
            assert self.__parent is not None
            return self.__parent.get_macro_definition(rule)