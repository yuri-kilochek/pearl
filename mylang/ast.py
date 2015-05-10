from collections import namedtuple as _namedtuple

# top level node
Module = _namedtuple('Module', ['body'])

# statements
Nothing = _namedtuple('Nothing', [])
UnusedExpression = _namedtuple('UnusedExpression', ['expression', 'next'])
VariableDeclaration = _namedtuple('VariableDeclaration', ['name', 'next'])
MacroDeclaration = _namedtuple('MacroDeclaration', ['rule', 'transformer', 'next'])
Block = _namedtuple('Block', ['body', 'next'])
IfElse = _namedtuple('IfElse', ['condition', 'true_clause', 'false_clause', 'next'])
Forever = _namedtuple('Forever', ['body', 'next'])
Continue = _namedtuple('Continue', [])
Break = _namedtuple('Break', [])
Return = _namedtuple('Return', ['value'])
VariableAssignment = _namedtuple('VariableAssignment', ['name', 'value', 'next'])
AttributeAssignment = _namedtuple('AttributeAssignment', ['object', 'attribute_name', 'value', 'next'])
Import = _namedtuple('Import', ['name', 'next'])

# expressions
VariableUse = _namedtuple('VariableUse', ['name'])
NumberLiteral = _namedtuple('NumberLiteral', ['value'])
StringLiteral = _namedtuple('StringLiteral', ['value'])
FunctionLiteral = _namedtuple('FunctionLiteral', ['arguments', 'body'])
AttributeAccess = _namedtuple('AttributeAccess', ['object', 'attribute_name'])
Invocation = _namedtuple('Invocation', ['invocable', 'arguments'])

# unknown
MacroUse = _namedtuple('MacroUse', ['rule', 'nodes'])