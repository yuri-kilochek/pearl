from itertools import groupby, chain
from collections import namedtuple
from collections import OrderedDict


class _BracketConstructible(type):
    def __getitem__(cls, args):
        return cls(args)


class Grammar(metaclass=_BracketConstructible):
    class RuleSequences:
        class Transformation:
            def __init__(self, mask, fold):
                self._mask = mask
                self._fold = fold

            @property
            def mask(self):
                return self._mask

            @property
            def fold(self):
                return self._fold

        def __init__(self, sequences, folds):
            self._sequences = {}
            for sequence, fold in zip(sequences, folds):
                mask = tuple(not isinstance(element, set) for element in sequence)
                sequence = tuple(element if masked else next(iter(element)) for element, masked in zip(sequence, mask))
                self._sequences[sequence] = Grammar.RuleSequences.Transformation(mask, fold)
            self._nullable = None

        def __len__(self):
            return len(self._sequences)

        def __getitem__(self, sequence):
            return self._sequences[sequence]

        def __iter__(self):
            return iter(self._sequences)

        def __contains__(self, sequence):
            return sequence in self._sequences

        @property
        def nullable(self):
            return self._nullable

    def __init__(self, rules):
        if isinstance(rules, slice):
            rules = rules,
        rules = list((rule.start, rule.stop, rule.step) for rule in rules)
        rules.append(('', [rules[0][0]], None))
        rules.sort(key=lambda rule: rule[0])
        self._rules = {}
        for symbol, rules in groupby(rules, lambda rule: rule[0]):
            self._rules[symbol] = Grammar.RuleSequences(*zip(*(rule[1:] for rule in rules)))
        self._set_nullable()

    def _set_nullable(self):
        def is_nullable(symbol):
            return symbol in self and self[symbol]._nullable

        def set_nullable(symbol, nullable=True):
             self[symbol]._nullable = nullable

        def should_be_nullable(new_symbol):
            return any(all(is_nullable(symbol) for symbol in sequence) for sequence in self[new_symbol])

        for symbol in self:
            set_nullable(symbol, () in self[symbol])

        new = True
        while new:
            new = False
            for symbol in self:
                if not is_nullable(symbol) and should_be_nullable(symbol):
                    set_nullable(symbol)
                    new = True

    def __len__(self):
        return len(self._rules)

    def __getitem__(self, symbol):
        return self._rules[symbol]

    def __iter__(self):
        return iter(self._rules)

    def __contains__(self, symbol):
        return symbol in self._rules


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
