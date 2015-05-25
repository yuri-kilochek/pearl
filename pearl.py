from collections import namedtuple as _namedtuple
from collections import defaultdict as _defaultdict


class Grammar:
    class Rule(_namedtuple('Rule', ['head', 'body', 'grammar_transforms', 'argument_selectors', 'build_result'])):
        @property
        def __key(self):
            return self.head, self.body

        def __hash__(self):
            return hash(self.__key)

        def __eq__(self, other):
            return self is other or self.__key == other.__key

    def __init__(self, *, _rule_sets={}):
        self.__rule_sets = _rule_sets
        self.__cached_key = None
        self.__cached_hash = None

    @property
    def __key(self):
        if self.__cached_key is None:
            self.__cached_key = frozenset(self.__rule_sets.values())
        return self.__cached_key

    def __hash__(self):
        if self.__cached_hash is None:
            self.__cached_hash = hash(self.__key)
        return self.__cached_hash

    def __eq__(self, other):
        return self is other or self.__key == other.__key

    def __getitem__(self, head):
        assert head.__class__ == str and len(head) > 1
        return self.__rule_sets.get(head, frozenset())

    def put(self, head, body_and_grammar_transforms, build_result=None):
        assert head.__class__ == str and len(head) > 1

        body = []
        grammar_transforms = [[]]
        argument_selectors = []
        for x in body_and_grammar_transforms:
            if x.__class__ in (set, str):
                if x.__class__ == set:
                    assert len(x) == 1
                    x = next(iter(x))
                    assert x.__class__ == str
                    argument_selectors.append(True)
                else:
                    argument_selectors.append(False)
                assert x
                body.append(x)
                grammar_transforms.append([])
            else:
                assert callable(x)
                grammar_transforms[-1].append(x)

        assert build_result is None or callable(build_result)

        rule = Grammar.Rule(head, tuple(body), tuple(map(tuple, grammar_transforms)), tuple(argument_selectors), build_result)

        rule_sets = self.__rule_sets.copy()
        rule_set = rule_sets.get(rule.head, frozenset())
        rule_set = frozenset({r for r in rule_set if r != rule} | {rule})
        rule_sets[rule.head] = rule_set
        return Grammar(_rule_sets=rule_sets)

    def drop(self, head, body=None):
        rule_sets = self.__rule_sets.copy()
        if body is None:
            rule_sets.pop(head, None)
        else:
            body = tuple(body)
            rule_set = rule_sets.get(head, frozenset())
            rule_set = frozenset(r for r in rule_set if r.body != body)
            rule_sets[head] = rule_set
        return Grammar(_rule_sets=rule_sets)

    def is_terminal(self, symbol):
        assert symbol.__class__ == str and symbol
        return symbol not in self.__rule_sets


class _TextSegment(_namedtuple('_TextSegment', ['text', 'start', 'stop'])):
    def __str__(self):
        return self.text[self.start:self.stop]


class _Item:
    __slots__ = [
        '__start',
        '__parent_items',
        '__grammar',
        '__rule',
        '__child_results',
        '__cached_key',
        '__cached_hash',
    ]

    def __init__(self, start, parent_items, grammar, rule, child_results):
        grammar_transforms = rule.grammar_transforms[len(child_results)]
        if grammar_transforms:
            selected_arguments = []
            new_child_results = []
            for child_result, selected in zip(child_results, rule.argument_selectors):
                if selected:
                    if child_result.__class__ == _TextSegment:
                        child_result = str(child_result)
                    selected_arguments.append(child_result)
                new_child_results.append(child_result)
            child_results = tuple(new_child_results)
            for transform_grammar in grammar_transforms:
                grammar = transform_grammar(grammar, *selected_arguments)

        self.__start = start
        self.__parent_items = parent_items
        self.__grammar = grammar
        self.__rule = rule
        self.__child_results = child_results
        self.__cached_key = None
        self.__cached_hash = None

    @property
    def __key(self):
        if self.__cached_key is None:
            self.__cached_key = id(self.__parent_items), self.__grammar, self.__rule, self.__child_results
        return self.__cached_key

    def __hash__(self):
        if self.__cached_hash is None:
            self.__cached_hash = hash(self.__key)
        return self.__cached_hash

    def __eq__(self, other):
        return self is other or self.__key == other.__key

    @property
    def start(self):
        return self.__start

    @property
    def parent_items(self):
        return self.__parent_items

    @property
    def grammar(self):
        return self.__grammar

    @property
    def rule(self):
        return self.__rule

    def get_result(self, text, stop):
        assert self.is_complete
        selected_arguments = [a for a, s in zip(self.__child_results, self.__rule.argument_selectors) if s]
        if self.__rule.build_result:
            for i, selected_argument in enumerate(selected_arguments):
                if selected_argument.__class__ == _TextSegment:
                    selected_arguments[i] = str(selected_argument)
            return self.__rule.build_result(*selected_arguments)
        if len(selected_arguments) == 0:
            return _TextSegment(text, self.__start, stop)
        assert len(selected_arguments) == 1
        return selected_arguments[0]

    @property
    def progress(self):
        return len(self.__child_results)

    @property
    def is_complete(self):
        return self.progress == len(self.__rule.body)

    @property
    def expected_symbol(self):
        assert not self.is_complete
        return self.__rule.body[self.progress]

    def consume(self, next_child_result):
        assert not self.is_complete
        return _Item(self.__start, self.__parent_items, self.__grammar, self.rule, self.__child_results + (next_child_result,))


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


class AmbiguousParse(ParseError):
    pass

_END = object()


def parse(grammar, text, *, start='__start__', allow_partial=False, allow_ambiguous=True):
    from itertools import chain
    from itertools import repeat

    assert grammar.__class__ == Grammar
    assert text.__class__ == str

    results = []

    state = _State()

    for rule in grammar[start]:
        state.put(_Item(0, None, grammar, rule, ()))

    for index, char in enumerate(chain(text, repeat(None))):
        while True:
            new_items = False
            for item in state:
                if item.is_complete:
                    if item.parent_items is not None:
                        item_result = item.get_result(text, index)
                        for parent_item in item.parent_items:
                            new_items |= state.put(parent_item.consume(item_result))
                elif not item.grammar.is_terminal(item.expected_symbol):
                    for rule in item.grammar[item.expected_symbol]:
                        new_items |= state.put(_Item(index, state[item.expected_symbol], item.grammar, rule, ()))
            if not new_items:
                break

        next_state = _State()

        for item in state:
            if item.is_complete:
                if item.parent_items is None:
                    if allow_partial or char is None:
                        item_result = item.get_result(text, index)
                        results.append(item_result)
            elif item.grammar.is_terminal(item.expected_symbol) and char is not None:
                if char == item.expected_symbol:
                    next_state.put(item.consume(char))

        if len(results) > 1 and not allow_ambiguous:
            raise AmbiguousParse()

        if not next_state:
            if not results:
                raise ParseError(_build_error_report(text, state, index, char))
            break

        state = next_state

    if not allow_ambiguous:
        return results[0]

    return results


def _build_error_report(text, state, index, char):
    from bisect import bisect

    line_starts = [0]
    for i, c in enumerate(text):
        if c == '\n':
            line_starts.append(i + 1)

    def get_position(i):
        line = bisect(line_starts, i) - 1
        column = i - line_starts[line]
        return line + 1, column + 1

    reports = []
    for item in state:
        if not item.is_complete:
            reports.append('{} in {} starting at {}'.format(repr(item.expected_symbol), repr(item.rule.head), get_position(item.start)))
    if char is None:
        return 'Got unexpected end of input at {}. Expected:\n\t{}'.format(get_position(index), '\n\t'.join(reports))
    else:
        return 'Got {} at {}. Expected:\n\t{}'.format(repr(char), get_position(index), ' or \n\t'.join(reports))
