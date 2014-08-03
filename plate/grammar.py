from itertools import groupby as _groupby


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
        for symbol, rules in _groupby(rules, lambda rule: rule[0]):
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
