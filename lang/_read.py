import os.path as _os_path
from functools import lru_cache as _lru_cache
from hashlib import sha512 as _sha512
import pickle as _pickle

import pearl as _pearl
from ._core_grammar import core_grammar as _core_grammar
from . import ast as _ast


def read(module_path):
    ast, _ = _read(module_path)
    return ast


@_lru_cache(maxsize=256)
def _read(module_path, origin='./'):
    if _os_path.isabs(module_path):
        module_path = _os_path.join('lang', 'libraries', _os_path.relpath(module_path, '/'))

    with open(module_path + '.lang', 'rb') as file:
        content = file.read()
    digest = _sha512(content).digest()

    try:
        with open(module_path + '.langc', 'rb') as cache_file:
            cache_ast, cache_digest = _pickle.load(cache_file)
        if cache_digest == digest and not any(changed for _, changed in map(_read, _get_imports(cache_ast))):
            return cache_ast, False
    except IOError:
        pass

    try:
        ast = _pearl.parse(_core_grammar, str(content, 'UTF-8'), allow_ambiguous=False)
    except _pearl.AmbiguousParse as e:
        raise Exception('In file {}.lang'.format(module_path)) from e

    with open(module_path + '.langc', 'wb') as cache_file:
        _pickle.dump((ast, digest), cache_file)

    return ast, True


def _get_imports(ast):
    imports = set()

    def glean_imports(s):
        if s.__class__ == _ast.Import:
            imports.add(s.module_path)
        if s.__class__ != _ast.Nothing:
            glean_imports(s.next)
    glean_imports(ast)

    return imports
