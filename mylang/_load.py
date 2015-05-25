import pearl as _pearl
from ._core_grammar import core_grammar as _core_grammar


def _read_characters(path):
    with open(path) as file:
        while True:
            c = file.read(1)
            if not c:
                break
            yield c


def load(module_path, *, grammar=_core_grammar):
    with open(module_path + '.meta') as file:
        text = file.read()
    try:
        return _pearl.parse(grammar, text, allow_ambiguous=False)
    except _pearl.AmbiguousParse as e:
        raise Exception('In file {}.meta'.format(module_path)) from e
