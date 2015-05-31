from functools import lru_cache as _lru_cache

from ._read import read as _read
from . import ast as _ast


@_lru_cache(maxsize=None)
class Module:
    def __init__(self, path):
        self.__path = path
        self.__body = _read(path)
        self.__exported_variables = {}
        self.__exported_macro_definitions = {}

        context = _ast.Context()

        self.__body.execute(context)

        def glean_exports(s):
            if s.__class__ == _ast.Import and s.exported:
                module = Module(s.module_path)
                self.__exported_variables.update(module.__exported_variables)
                self.__exported_macro_definitions.update(module.__exported_macro_definitions)
            elif s.__class__ == _ast.VariableDeclaration and s.exported:
                name = s.name
                self.__exported_variables[name] = context.variables[name]
            elif s.__class__ == _ast.MacroDefinition and s.exported:
                rule = s.nonterminal, s.parameters
                self.__exported_macro_definitions[rule] = context.macro_definitions[rule]
            if s.__class__ not in (_ast.Nothing, _ast.MacroUse):
                glean_exports(s.next)
        glean_exports(self.__body)

    @property
    def path(self):
        return self.__path

    @property
    def body(self):
        return self.__body

    @property
    def exported_variables(self):
        return self.__exported_variables

    @property
    def exported_macro_definitions(self):
        return self.__exported_macro_definitions