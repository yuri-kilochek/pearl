from collections import namedtuple
from itertools import chain
from collections import OrderedDict


def normalize_symbol(symbol):
    if isinstance(symbol, str):
        if symbol == '':
            raise ValueError('Symbol cannot be empty.')
        return symbol
    raise TypeError('Symbol must be a strings.')


def normalize_production(production):
    if isinstance(production, tuple):
        return tuple(map(normalize_symbol, production))
    if isinstance(production, str):
        return (normalize_symbol(production),)
    raise TypeError('Production must be a tuple or a string.')


def normalize_productions(productions):
    if isinstance(productions, set):
        return set(map(normalize_production, productions))
    if isinstance(productions, tuple):
        return {normalize_production(productions)}
    if isinstance(productions, str):
        return {(normalize_symbol(productions),)}
    raise TypeError('Productions must be a set, a tuple or a string.')


def normalize_grammar(grammar):
    if isinstance(grammar, dict):
        return dict(zip(map(normalize_symbol, grammar.keys()), map(normalize_productions, grammar.values())))
    raise TypeError('Grammar must be a dict.')


def compute_nullables(grammar):
    def should_add(new_symbol, grammar, current_nullables):
        return any(all(symbol in current_nullables for symbol in production) for production in grammar[new_symbol])

    nullables = {symbol for symbol in grammar if () in grammar[symbol]}

    added = True
    while added:
        added = False
        for symbol in grammar:
            if not symbol in nullables and should_add(symbol, grammar, nullables):
                nullables.add(symbol)
                added = True

    return nullables


Trace = namedtuple('Trace', ['origin', 'symbol', 'production', 'progress'])


def next_symbol(trace):
    if trace.progress == len(trace.production):
        return None
    return trace.production[trace.progress]


def advance(trace, ground):
    origin = trace.origin
    symbol = trace.symbol
    production = trace.production[:trace.progress] + (ground,) + trace.production[trace.progress + 1:]
    progress = trace.progress + 1
    return Trace(origin, symbol, production, progress)


def parse(tokens, grammar, start=None, get_terminal=None):
    if start is None:
        start = 'start'

    if get_terminal is None:
        get_terminal = lambda x: x.terminal

    grammar = normalize_grammar(grammar)
    nullables = compute_nullables(grammar)

    start_trace = Trace(0, '', (start,), 0)
    states = [OrderedDict.fromkeys([start_trace])]
    for i, token in enumerate(chain(tokens, [object()])):
        states.append(OrderedDict())
        for trace in states[i]:
            if next_symbol(trace) is None:
                if trace.progress == len(trace.production):
                    for parent_trace in states[trace.origin]:
                        if next_symbol(parent_trace) == trace.symbol:
                            states[i].setdefault(advance(parent_trace, (trace.symbol,) + trace.production))
            elif next_symbol(trace) in grammar:
                if next_symbol(trace) in nullables:
                    states[i].setdefault(advance(trace, ()))
                for production in grammar[next_symbol(trace)]:
                    states[i].setdefault(Trace(i, next_symbol(trace), production, 0))
            elif next_symbol(trace) == get_terminal(token):
                states[i + 1].setdefault(advance(trace, token))
            if trace.symbol == '' and trace.progress == 1:
                yield trace.production[0]
