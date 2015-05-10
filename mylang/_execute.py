from functools import singledispatch as _singledispatch

from . import ast as _ast
from ._builtins import builtins as _builtins


def execute(module, **context):
    assert module.__class__ == _ast.Module

    variables = _builtins.copy()
    variables.update(context)

    context = _Context()
    for name, value in variables.items():
        context.declare_and_assign(name, value)

    _execute(module, context)

    return context.variables


@_singledispatch
def _execute(node, context):
    raise NotImplementedError()


@_execute.register(_ast.Module)
def _(node, context):
    _execute(node.body, context)


@_execute.register(_ast.Nothing)
def _(node, context):
    pass


@_execute.register(_ast.UnusedExpression)
def _(node, context):
    _execute(node.expression, context)
    _execute(node.next, context)


@_execute.register(_ast.VariableDeclaration)
def _(node, context):
    context.declare(node.name)
    _execute(node.next, context)


@_execute.register(_ast.MacroDeclaration)
def _(node, context):
    raise NotImplementedError()


@_execute.register(_ast.Block)
def _(node, context):
    local_context = _Context(context)
    _execute(node.body, local_context)
    _execute(node.next, context)


@_execute.register(_ast.IfElse)
def _(node, context):
    if _execute(node.condition, context):
        local_context = _Context(context)
        _execute(node.true_clause, local_context)
    else:
        local_context = _Context(context)
        _execute(node.false_clause, local_context)
    _execute(node.next, context)

@_execute.register(_ast.Forever)
def _(node, context):
    while True:
        try:
            local_context = _Context(context)
            _execute(node.body, local_context)
        except _Continue:
            continue
        except _Break:
            break
    _execute(node.next, context)


@_execute.register(_ast.Continue)
def _(node, context):
    raise _Continue()


@_execute.register(_ast.Break)
def _(node, context):
    raise _Break()


@_execute.register(_ast.Return)
def _(node, context):
    value = _execute(node.value, context)
    raise _Return(value)


@_execute.register(_ast.VariableAssignment)
def _(node, context):
    value = _execute(node.value, context)
    context.assign(node.name, value)
    _execute(node.next, context)


@_execute.register(_ast.AttributeAssignment)
def _(node, context):
    value = _execute(node.value, context)
    object = _execute(node.object, context)
    setattr(object, node.attribute_name, value)
    _execute(node.next, context)


@_execute.register(_ast.Import)
def _(node, context):
    raise NotImplementedError()


@_execute.register(_ast.VariableUse)
def _(node, context):
    value = context.use(node.name)
    return value


@_execute.register(_ast.NumberLiteral)
def _(node, context):
    return node.value


@_execute.register(_ast.StringLiteral)
def _(node, context):
    return node.value


@_execute.register(_ast.FunctionLiteral)
def _(node, context):
    def value(*arguments):
        local_context = _Context(context)
        for argument_name, argument_value in zip(node.arguments, arguments):
            local_context.declare_and_assign(argument_name, argument_value)
        try:
            _execute(node.body, local_context)
        except _Return as j:
            return j.value
    return value


@_execute.register(_ast.AttributeAccess)
def _(node, context):
    object = _execute(node.object, context)
    value = getattr(object, node.attribute_name)
    return value


@_execute.register(_ast.Invocation)
def _(node, context):
    arguments = [_execute(a, context) for a in node.arguments]
    invocable = _execute(node.invocable, context)
    value = invocable(*arguments)
    return value


@_execute.register(_ast.MacroUse)
def _(node, context):
    raise NotImplementedError()


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
