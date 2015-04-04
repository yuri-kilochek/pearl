from collections import defaultdict as _defaultdict
from itertools import chain as _chain


class _GrammarMeta(type):
    def __getitem__(cls, rules):
        if rules.__class__ != tuple:
            rules = rules,

        grammar = cls({})
        for rule in rules:
            assert rule.__class__ == slice
            grammar = grammar.put(rule.start, rule.stop, rule.step)
        return grammar


class Grammar(metaclass=_GrammarMeta):
    class Rule:
        __slots__ = [
            '__nonterminal',
            '__body_symbols',
            '__grammar_transforms',
            '__value_retainer',
            '__result_builder',
        ]

        def __init__(self, nonterminal, body_symbols, grammar_transforms, value_retainer, result_builder):
            self.__nonterminal = nonterminal
            self.__body_symbols = body_symbols
            self.__grammar_transforms = grammar_transforms
            self.__value_retainer = value_retainer
            self.__result_builder = result_builder

        @property
        def __key(self):
            return self.__nonterminal, self.__body_symbols

        def __hash__(self):
            return hash(self.__key)

        def __eq__(self, other):
            return self.__key == other.__key

        @property
        def nonterminal(self):
            return self.__nonterminal

        @property
        def body_symbols(self):
            return self.__body_symbols

        @property
        def grammar_transforms(self):
            return self.__grammar_transforms

        @property
        def value_retainer(self):
            return self.__value_retainer

        @property
        def result_builder(self):
            return self.__result_builder

    def __init__(self, rule_sets):
        self.__rule_sets = rule_sets
        self.__key_cache = None
        self.__hash_cache = None

    @property
    def __key(self):
        if self.__key_cache is None:
            self.__key_cache = frozenset(self.__rule_sets.values())
        return self.__key_cache

    def __hash__(self):
        if self.__hash_cache is None:
            self.__hash_cache = hash(self.__key)
        return self.__hash_cache

    def __eq__(self, other):
        return self.__key == other.__key

    def __getitem__(self, head_symbol):
        assert type(head_symbol) == str and head_symbol
        return self.__rule_sets.get(head_symbol, frozenset())

    def put(self, nonterminal, body_symbols_and_grammar_transforms, result_builder=None):
        assert nonterminal.__class__ == str and nonterminal

        assert body_symbols_and_grammar_transforms.__class__ == list
        body_symbols = []
        grammar_transforms = []
        value_retainer = []
        for x in body_symbols_and_grammar_transforms:
            if x.__class__ in (set, str):
                if x.__class__ == set:
                    assert len(x) == 1
                    x = x.pop()
                    assert x.__class__ == str
                    value_retainer.append(False)
                else:
                    value_retainer.append(True)
                assert x
                body_symbols.append(x)
                if len(grammar_transforms) < len(body_symbols):
                    grammar_transforms.append(None)
            else:
                assert callable(x)
                assert len(grammar_transforms) == len(body_symbols)
                grammar_transforms.append(x)
        assert len(grammar_transforms) == len(body_symbols)
        body_symbols = tuple(body_symbols)
        grammar_transforms = tuple(grammar_transforms)
        value_retainer = tuple(value_retainer)

        assert result_builder is None or callable(result_builder)

        rule = Grammar.Rule(nonterminal, body_symbols, grammar_transforms, value_retainer, result_builder)

        rule_sets = self.__rule_sets.copy()
        rule_set = rule_sets.get(rule.nonterminal, frozenset())
        rule_set = frozenset({r for r in rule_set if r != rule} | {rule})
        rule_sets[rule.nonterminal] = rule_set
        return Grammar(rule_sets)

    def is_terminal(self, symbol):
        assert type(symbol) == str and symbol
        return symbol not in self.__rule_sets

_NO_RESULT = object()


class _Item:
    __slots__ = [
        '__grammar',
        '__rule',
        '__parents',
        '__values',
        '__progress',
        '__result',
        '__key_cache',
        '__hash_cache',
    ]

    def __init__(self, grammar, rule, parents=frozenset(), values=(), progress=0):
        if progress < len(rule.grammar_transforms):
            grammar_transform = rule.grammar_transforms[progress]
            if grammar_transform:
                grammar = grammar_transform(grammar, *values)
                assert rule in grammar[rule.nonterminal]

        self.__grammar = grammar
        self.__rule = rule
        self.__parents = parents
        self.__values = values
        self.__progress = progress
        self.__result = _NO_RESULT
        self.__key_cache = None
        self.__hash_cache = None

    @property
    def __key(self):
        if self.__key_cache is None:
            self.__key_cache = self.__grammar, self.__rule, id(self.__parents), self.__values, self.__progress
        return self.__key_cache

    def __hash__(self):
        if self.__hash_cache is None:
            self.__hash_cache = hash(self.__key)
        return self.__hash_cache

    def __eq__(self, other):
        return self.__key == other.__key

    @property
    def grammar(self):
        return self.__grammar

    @property
    def rule(self):
        return self.__rule

    @property
    def parents(self):
        return self.__parents

    @property
    def is_complete(self):
        return self.__progress == len(self.__rule.body_symbols)

    @property
    def expected_symbol(self):
        assert not self.is_complete
        return self.__rule.body_symbols[self.__progress]

    def consume(self, new_values):
        assert not self.is_complete
        values = self.__values
        if self.__rule.value_retainer[self.__progress]:
            values += new_values
        return _Item(self.__grammar, self.__rule, self.__parents, values, self.__progress + 1)

    @property
    def results(self):
        assert self.is_complete
        if self.__result is _NO_RESULT:
            result_builder = self.__rule.result_builder
            if result_builder:
                self.__result = tuple(result_builder(*self.__values))
            else:
                self.__result = self.__values
        return self.__result


class _State:
    def __init__(self):
        self.__complete = set()
        self.__expecting = _defaultdict(set)
        self.__order = []

    def __bool__(self):
        return bool(self.__order)

    def __iter__(self):
        i = 0
        while i < len(self.__order):
            yield self.__order[i]
            i += 1

    def __getitem__(self, expected_symbol):
        return self.__expecting[expected_symbol]

    def put(self, item):
        if item.is_complete:
            required_set = self.__complete
        else:
            required_set = self.__expecting[item.expected_symbol]
        if item in required_set:
            return False
        required_set.add(item)
        self.__order.append(item)
        return True


class ParseError(Exception):
    pass


_END = object()


def default_match(token, terminal):
    if token == terminal:
        return [token]
    return None


def parse(grammar, tokens, *, match=default_match, allow_partial=False):
    state = _State()

    for rule in grammar['_start_']:
        state.put(_Item(grammar, rule))

    for token in _chain(tokens, [_END]):
        new_items = True
        while new_items:
            new_items = False
            for item in state:
                if item.is_complete:
                    for parent in item.parents:
                        new_items |= state.put(parent.consume(item.results))
                elif not item.grammar.is_terminal(item.expected_symbol):
                    for rule in item.grammar[item.expected_symbol]:
                        new_items |= state.put(_Item(item.grammar, rule, state[item.expected_symbol]))

        next_state = _State()

        for item in state:
            if item.is_complete:
                if not item.parents and (allow_partial or token is _END):
                    yield list(item.results)
            elif item.grammar.is_terminal(item.expected_symbol) and token is not _END:
                results = match(token, item.expected_symbol)
                if results is not None:
                    next_state.put(item.consume(tuple(results)))

        if not next_state and token is not _END:
            raise ParseError()

        state = next_state
