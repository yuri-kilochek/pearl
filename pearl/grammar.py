from itertools import compress as _compress
from itertools import chain as _chain


class _BracketConstructible(type):
    def __getitem__(cls, args):
        return cls(args)


def _validate_symbol(symbol):
    if not isinstance(symbol, str):
        raise TypeError('Each symbol must be a string, not ' + symbol.__class__.__name__ + '.')
    if symbol == '':
        raise ValueError('A symbol must not be empty string.')


def _validate_rule(symbol, sequence, folder):
    _validate_symbol(symbol)

    if isinstance(sequence, list):
        for element in sequence:
            if isinstance(element, str):
                _validate_symbol(symbol)
            elif isinstance(element, set):
                if len(element) != 1:
                    raise ValueError('Suppressed elements can comprise only one symbol.')
                _validate_symbol(next(iter(element)))
            else:
                raise TypeError('Each body element must be a string or a set, not' + element.__class__.__name__ + '.')
    else:
        raise TypeError('Each rule body must be a list, not ' + sequence.__class__.__name__ + '.')

    if folder is not None and not callable(folder):
        raise TypeError('If folder is specified, it must be a callable, not ' + folder.__class__.__name__ + '.')


def _validate_rules(rules):
    if not isinstance(rules, tuple):
        rules = rules,

    for rule in rules:
        if not isinstance(rule, slice):
            raise TypeError('Each rule must be a slice, not ' + rule.__class__.__name__ + '.')
        _validate_rule(rule.start, rule.stop, rule.step)


def _build_rule(sequence, folder):
    selector = tuple(not isinstance(element, set) for element in sequence)
    sequence = tuple(element if selector[i] else next(iter(element)) for i, element in enumerate(sequence))

    def transform(*children):
        children = _compress(children, selector)
        children = _chain(*children)
        if folder is None:
            return tuple(children)
        return folder(*children),

    return sequence, transform


def _build_rules(rules):
    if not isinstance(rules, tuple):
        rules = rules,
    rules = list((rule.start, rule.stop, rule.step) for rule in rules)
    symbols = [rule[0] for rule in rules]
    start_symbol = symbols[0]
    rules = {symbol: dict(_build_rule(*rule[1:]) for rule in rules if rule[0] == symbol) for symbol in set(symbols)}
    nullables = _compute_nullables(rules)
    return start_symbol, rules, nullables


def _compute_nullables(rules):
    nullables = {symbol for symbol in rules if () in rules[symbol]}

    def is_nullable(symbol):
        return symbol in nullables

    def add_nullable(symbol):
        nullables.add(symbol)

    def should_be_nullable(symbol):
        return any(all(is_nullable(symbol) for symbol in sequence) for sequence in rules[symbol])

    new = True
    while new:
        new = False
        for symbol in rules:
            if not is_nullable(symbol) and should_be_nullable(symbol):
                add_nullable(symbol)
                new = True

    return nullables


class Grammar(metaclass=_BracketConstructible):
    class Rule:
        def __init__(self, transforms, nullable):
            self._transforms = transforms
            self._nullable = nullable

        def __len__(self):
            return len(self._transforms)

        def __getitem__(self, sequence):
            return self._transforms[sequence]

        def __iter__(self):
            return iter(self._transforms)

        def __contains__(self, sequence):
            return sequence in self._transforms

        @property
        def nullable(self):
            return self._nullable

    def __init__(self, rules):
        _validate_rules(rules)
        start_symbol, rules, nullables = _build_rules(rules)
        self._start_symbol = start_symbol
        self._rules = {symbol: Grammar.Rule(rules[symbol], symbol in nullables) for symbol in rules}

    @property
    def start_symbol(self):
        return self._start_symbol

    def __len__(self):
        return len(self._rules)

    def __getitem__(self, symbol):
        return self._rules[symbol]

    def __iter__(self):
        return iter(self._rules)

    def __contains__(self, symbol):
        return symbol in self._rules
