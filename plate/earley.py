from itertools import chain as _chain
from collections import namedtuple as _namedtuple
from collections import OrderedDict as _OrderedDict


_Trace = _namedtuple('_Trace', ['origin', 'symbol', 'sequence', 'progress', 'children'])


def _next_symbol(trace):
    if trace.progress == len(trace.sequence):
        return None
    return trace.sequence[trace.progress]


def _advance(trace, child):
    return _Trace(
        origin=trace.origin,
        symbol=trace.symbol,
        sequence=trace.sequence,
        progress=trace.progress + 1,
        children=trace.children + (child,)
    )


def parse(grammar, tokens, token_symbol=None):
    if token_symbol is None:
        token_symbol = lambda token: token.symbol

    start_trace = _Trace(0, '', (grammar.start_symbol,), 0, ())
    states = [_OrderedDict.fromkeys([start_trace])]
    for i, token in enumerate(_chain(tokens, [object()])):
        states.append(_OrderedDict())
        for trace in states[i]:
            if _next_symbol(trace) is None:
                if trace.progress == len(trace.sequence):
                    for parent_trace in states[trace.origin]:
                        if _next_symbol(parent_trace) == trace.symbol:
                            child = grammar[trace.symbol][trace.sequence](trace.children)
                            states[i].setdefault(_advance(parent_trace, child))
            elif _next_symbol(trace) in grammar:
                if grammar[_next_symbol(trace)].nullable:
                    states[i].setdefault(_advance(trace, ()))
                for sequence in grammar[_next_symbol(trace)]:
                    states[i].setdefault(_Trace(i, _next_symbol(trace), sequence, 0, ()))
            elif _next_symbol(trace) == token_symbol(token):
                states[i + 1].setdefault(_advance(trace, (token,)))
            if trace.symbol == '' and trace.progress == 1:
                yield trace.children[0][0]
