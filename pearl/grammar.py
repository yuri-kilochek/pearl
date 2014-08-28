def _validate_tag(tag):
    if tag != '':
        pass
    else:
        raise AssertionError('Tag must not be empty')


def _validate_head(head):
    if isinstance(head, str):
        _validate_tag(head)
    else:
        raise AssertionError('Head tag must be str')


def _validate_element(element):
    if isinstance(element, str):
        _validate_tag(element)
    elif isinstance(element, set):
        if len(element) == 1:
            if isinstance(next(iter(element)), str):
                _validate_tag(next(iter(element)))
            else:
                raise AssertionError('Discarded elements must be a str')
        else:
            raise AssertionError('Elements can only be discarded one by one')
    else:
        raise AssertionError('Element must be str or set')


def _validate_sequence(sequence):
    if isinstance(sequence, list):
        for element in sequence:
            _validate_element(element)
    else:
        raise AssertionError('Sequence must be list')


def _validate_fold(fold):
    if fold is None or callable(fold):
        pass
    else:
        raise AssertionError('Fold must be callable or None')


def _validate_rule(rule):
    if isinstance(rule, slice):
        _validate_head(rule.start)
        _validate_sequence(rule.stop)
        _validate_fold(rule.step)
        if len(rule.stop) == 0 and rule.step is not None:
            raise AssertionError('Rule with empty sequence must have no fold')
    else:
        raise AssertionError('Rule must be slice')


def _validate_grammar(grammar):
    if isinstance(grammar, tuple):
        for rule in grammar:
            _validate_rule(rule)
    elif isinstance(grammar, slice):
        _validate_rule(grammar)
    else:
        raise AssertionError('Grammar must be a tuple or a slice')


def _normalize_rule(rule):
    return rule.start, rule.stop, rule.step


def _normalize_grammar(grammar):
    if isinstance(grammar, slice):
        grammar = grammar,
    return list(map(_normalize_rule, grammar))


def _compile_body(sequence_and_selector, fold):
    sequence = []
    selector = []
    for element in sequence_and_selector:
        selected = not isinstance(element, set)
        if not selected:
            element = next(iter(element))
        sequence.append(element)
        selector.append(selected)
    sequence = tuple(sequence)
    selector = tuple(selector)
    return Grammar.Rule.Body(sequence, selector, fold)


def _compile_rule(tag, sequences_selectors_and_folds):
    bodies = []
    for sequence_and_selector, fold in sequences_selectors_and_folds:
        body = _compile_body(sequence_and_selector, fold)
        bodies.append(body)
    return Grammar.Rule(tag, bodies)


def _compile_grammar(grammar):
    rules = []
    for tag, _, _ in grammar:
        if any(rule.tag == tag for rule in rules):
            continue
        sequences_selectors_and_folds = []
        for some_tag, sequence_and_selector, fold in grammar:
            if some_tag == tag:
                sequences_selectors_and_folds.append((sequence_and_selector, fold))
        rule = _compile_rule(tag, sequences_selectors_and_folds)
        rules.append(rule)
    return Grammar(rules)


class _GrammarMeta(type):
    def __getitem__(self, grammar):
        if __debug__:
            _validate_grammar(grammar)
        grammar = _normalize_grammar(grammar)
        grammar = _compile_grammar(grammar)
        return grammar


class Grammar(metaclass=_GrammarMeta):
    class Rule:
        class Body:
            @property
            def sequence(self):
                return self._sequence

            @property
            def selector(self):
                return self._selector

            @property
            def fold(self):
                return self._fold

            def __init__(self, sequence, selector, fold=None):
                self._sequence = sequence
                self._selector = selector
                self._fold = fold

        @property
        def tag(self):
            return self._tag

        def __len__(self):
            return len(self._bodies)

        def __iter__(self):
            return iter(self._bodies.values())

        def __contains__(self, sequence):
            return sequence in self._bodies

        def __getitem__(self, sequence):
            return self._bodies[sequence]

        @property
        def nullable(self):
            return self._nullable

        def __init__(self, tag, bodies, nullable=None):
            self._tag = tag
            self._bodies = {body.sequence: body for body in bodies}
            self._nullable = nullable

    @property
    def start_rule(self):
        return self._start_rule

    def __len__(self):
        return len(self._rules)

    def __iter__(self):
        return iter(self._rules.values())

    def __contains__(self, tag):
        return tag in self._rules

    def __getitem__(self, tag):
        return self._rules[tag]

    def __init__(self, rules):
        nullable_tags = {rule.tag for rule in rules if () in rule}
        new_nullable = len(nullable_tags) > 0
        while new_nullable:
            new_nullable = False
            for rule in rules:
                if rule.tag not in nullable_tags:
                    if any(all(tag in nullable_tags for tag in body.sequence) for body in rule):
                        nullable_tags.add(rule.tag)
                        new_nullable = True
        rules = [Grammar.Rule(rule.tag, list(rule), rule.tag in nullable_tags) for rule in rules]
        self._start_rule = rules[0]
        self._rules = {rule.tag: rule for rule in rules}
