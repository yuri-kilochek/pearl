from itertools import chain
from collections import namedtuple
from collections import OrderedDict


Trace = namedtuple('Trace', ['origin', 'symbol', 'sequence', 'progress', 'children'])


def next_symbol(trace):
    if trace.progress == len(trace.sequence):
        return None
    return trace.sequence[trace.progress]


def advance(trace, children):
    return Trace(
        origin=trace.origin,
        symbol=trace.symbol,
        sequence=trace.sequence,
        progress=trace.progress + 1,
        children=trace.children + children
    )


def parse(grammar, tokens, token_symbol=None):
    if token_symbol is None:
        token_symbol = lambda token: token.symbol

    start_trace = Trace(0, '', next(iter(grammar[''])), 0, ())
    states = [OrderedDict.fromkeys([start_trace])]
    for i, token in enumerate(chain(tokens, [object()])):
        states.append(OrderedDict())
        for trace in states[i]:
            if next_symbol(trace) is None:
                if trace.progress == len(trace.sequence):
                    for parent_trace in states[trace.origin]:
                        if next_symbol(parent_trace) == trace.symbol:
                            children = trace.children
                            fold = grammar[trace.symbol][trace.sequence].fold
                            if fold:
                                children = (fold(*children),)
                            mask = grammar[parent_trace.symbol][parent_trace.sequence].mask[parent_trace.progress]
                            if not mask:
                                children = ()
                            states[i].setdefault(advance(parent_trace, children))
            elif next_symbol(trace) in grammar:
                if grammar[next_symbol(trace)].nullable:
                    states[i].setdefault(advance(trace, ()))
                for sequence in grammar[next_symbol(trace)]:
                    states[i].setdefault(Trace(i, next_symbol(trace), sequence, 0, ()))
            elif next_symbol(trace) == token_symbol(token):
                children = token,
                mask = grammar[trace.symbol][trace.sequence].mask[trace.progress]
                if not mask:
                    children = ()
                states[i + 1].setdefault(advance(trace, children))
            if trace.symbol == '' and trace.progress == 1:
                yield trace.children[0]
