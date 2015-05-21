import pearl as _pearl
from ._core_grammar import core_grammar as _core_grammar
from ._tokenize import tokenize as _tokenize


def _read_characters(path):
    with open(path) as file:
        while True:
            c = file.read(1)
            if not c:
                break
            yield c


def load(module_path, *, grammar=_core_grammar):
    text = _read_characters(module_path + '.meta')
    tokens = _tokenize(text)
    try:
        return _pearl.parse(grammar, tokens)
    except _pearl.AmbiguousParse as e:
        raise Exception('In file {}.meta'.format(module_path)) from e
