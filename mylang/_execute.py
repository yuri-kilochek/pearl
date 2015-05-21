from functools import singledispatch as _singledispatch

import pearl as _pearl
from ._tokenize import tokenize as _tokenize
from . import ast as _ast


def execute(module, grammar, **variables):
    assert module.__class__ == _ast.Module

    context = _Context()

    for name, value in variables.items():
        context.declare_and_assign(name, value)

    @_singledispatch
    def execute(node, context):
        raise NotImplementedError()

    @execute.register(_ast.Module)
    def _(node, context):
        execute(node.body, context)

    @execute.register(_ast.Nothing)
    def _(node, context):
        pass

    @execute.register(_ast.UnusedExpression)
    def _(node, context):
        execute(node.expression, context)
        execute(node.next, context)

    @execute.register(_ast.VariableDeclaration)
    def _(node, context):
        context.declare(node.name)
        execute(node.next, context)

    @execute.register(_ast.MacroDeclaration)
    def _(node, context):
        rule = node.rule
        transform = execute(node.transform, context)

        @_singledispatch
        def render_macro(node):
            return node

        @render_macro.register(_ast.UnusedExpression)
        def _(node):
            return _ast.UnusedExpression(render_macro(node.expression), render_macro(node.next))

        @render_macro.register(_ast.VariableDeclaration)
        def _(node):
            return _ast.VariableDeclaration(node.name, render_macro(node.next))

        @render_macro.register(_ast.MacroDeclaration)
        def _(node):
            return _ast.MacroDeclaration(node.rule, render_macro(node.transform), render_macro(node.next))

        @render_macro.register(_ast.Block)
        def _(node):
            return _ast.Block(render_macro(node.body), render_macro(node.next))

        @render_macro.register(_ast.IfElse)
        def _(node):
            return _ast.IfElse(render_macro(node.condition), render_macro(node.true_clause), render_macro(node.false_clause), render_macro(node.next))

        @render_macro.register(_ast.Forever)
        def _(node):
            return _ast.Forever(render_macro(node.body), render_macro(node.next))

        @render_macro.register(_ast.Return)
        def _(node):
            return _ast.Return(render_macro(node.value))

        @render_macro.register(_ast.VariableAssignment)
        def _(node):
            return _ast.VariableAssignment(render_macro(node.value), render_macro(node.next))

        @render_macro.register(_ast.AttributeAssignment)
        def _(node):
            return _ast.AttributeAssignment(render_macro(node.object), render_macro(node.value), node.attribute_name, render_macro(node.next))

        @render_macro.register(_ast.Import)
        def _(node):
            return _ast.Import(node.name, render_macro(node.next))

        @render_macro.register(_ast.FunctionLiteral)
        def _(node):
            return _ast.FunctionLiteral(node.arguments, render_macro(node.body))

        @render_macro.register(_ast.AttributeAccess)
        def _(node):
            return _ast.AttributeAccess(render_macro(node.object), node.attribute_name)

        @render_macro.register(_ast.Invocation)
        def _(node):
            return _ast.Invocation(render_macro(node.invocable), tuple(map(render_macro, node.arguments)))

        @render_macro.register(_ast.MacroUse)
        def _(node):
            if node.rule != rule:
                return _ast.MacroUse(node.rule, tuple(map(render_macro, node.nodes)))

            nont = node.rule[0]
            nontws = nont + '-with-whitespace-at-end'

            text = transform(*node.nodes)
            node_ast, _ = _pearl.parse(grammar.put(nontws, [nont, {'whitespace'}]), _tokenize(text), start=nontws)

            return node_ast

        execute(render_macro(node.next), context)

    @execute.register(_ast.Block)
    def _(node, context):
        local_context = _Context(context)
        execute(node.body, local_context)
        execute(node.next, context)

    @execute.register(_ast.IfElse)
    def _(node, context):
        if execute(node.condition, context):
            local_context = _Context(context)
            execute(node.true_clause, local_context)
        else:
            local_context = _Context(context)
            execute(node.false_clause, local_context)
        execute(node.next, context)

    @execute.register(_ast.Forever)
    def _(node, context):
        while True:
            try:
                local_context = _Context(context)
                execute(node.body, local_context)
            except _Continue:
                continue
            except _Break:
                break
        execute(node.next, context)

    @execute.register(_ast.Continue)
    def _(node, context):
        raise _Continue()

    @execute.register(_ast.Break)
    def _(node, context):
        raise _Break()

    @execute.register(_ast.Return)
    def _(node, context):
        value = execute(node.value, context)
        raise _Return(value)

    @execute.register(_ast.VariableAssignment)
    def _(node, context):
        value = execute(node.value, context)
        context.assign(node.name, value)
        execute(node.next, context)

    @execute.register(_ast.AttributeAssignment)
    def _(node, context):
        value = execute(node.value, context)
        object = execute(node.object, context)
        setattr(object, node.attribute_name, value)
        execute(node.next, context)

    @execute.register(_ast.Import)
    def _(node, context):
        raise NotImplementedError()

    @execute.register(_ast.VariableUse)
    def _(node, context):
        value = context.use(node.name)
        return value

    @execute.register(_ast.NumberLiteral)
    def _(node, context):
        return node.value

    @execute.register(_ast.StringLiteral)
    def _(node, context):
        return node.value

    @execute.register(_ast.FunctionLiteral)
    def _(node, context):
        def value(*arguments):
            local_context = _Context(context)
            for argument_name, argument_value in zip(node.arguments, arguments):
                local_context.declare_and_assign(argument_name, argument_value)
            try:
                execute(node.body, local_context)
            except _Return as j:
                return j.value
        return value

    @execute.register(_ast.AttributeAccess)
    def _(node, context):
        object = execute(node.object, context)
        value = getattr(object, node.attribute_name)
        return value

    @execute.register(_ast.Invocation)
    def _(node, context):
        arguments = [execute(a, context) for a in node.arguments]
        invocable = execute(node.invocable, context)
        value = invocable(*arguments)
        return value

    @execute.register(_ast.ParenthesizedExpression)
    def _(node, context):
        value = execute(node.expression, context)
        return value

    @execute.register(_ast.MacroUse)
    def _(node, context):
        raise NotImplementedError()

    execute(module, context)

    return context.variables


class _Continue(Exception):
    pass


class _Break(Exception):
    pass


class _Return(Exception):
    def __init__(self, value):
        self.value = value


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

    def use(self, name):
        if name in self.__variables:
            value = self.__variables[name]
            if value is _Context.UNASSIGNED_VARIABLE_PLACEHOLDER:
                raise Exception('Use of unassigned variable \'{}\''.format(name))
            return value
        elif self.__parent is not None:
            return self.__parent.use(name)
        else:
            raise Exception('Use of undeclared variable \'{}\''.format(name))
