from itertools import groupby
from itertools import chain


class Rule:
    def __init__(self, tag, bodies, nullable):
        self.__tag = tag
        self.__bodies = bodies
        self.__nullable = nullable

    @property
    def tag(self):
        return self.__tag

    def __len__(self):
        return len(self.__bodies)

    def __iter__(self):
        yield from self.__bodies

    @property
    def nullable(self):
        return self.__nullable


class Grammar:
    def __init__(self, raw_productions):
        def cook(raw_productions):
            def get_tag(raw_production):
                return raw_production[0]

            def get_body(raw_production):
                return tuple(raw_production[1:])

            productions = {}

            raw_productions = list(raw_productions)
            raw_productions.sort(key=get_tag)
            for tag, raw_production_group in groupby(raw_productions, get_tag):
                bodies = {get_body(raw_production) for raw_production in raw_production_group}
                productions[tag] = bodies

            return productions

        def compute_nullable(productions):
            nullable = {tag for tag in productions if () in productions[tag]}

            def should_be_nullable(tag):
                def nullable_body(body):
                    for tag in body:
                        if tag not in nullable:
                            return False
                    return True

                for body in productions[tag]:
                    if nullable_body(body):
                        return True
                return False

            nullable_added = True
            while nullable_added:
                nullable_added = False
                for tag in productions:
                    if tag not in nullable and should_be_nullable(tag):
                        nullable.add(tag)
                        nullable_added = True

            return nullable

        productions = cook(raw_productions)
        nullable = compute_nullable(productions)
        self.__rules = {tag: Rule(tag, productions[tag], tag in nullable) for tag in productions}
        self.__start_rule = self.__rules[raw_productions[0][0]]

    def __len__(self):
        return len(self.__rules)

    def __getitem__(self, tag):
        return self.__rules[tag]

    def __iter__(self):
        yield from self.__rules

    def __contains__(self, tag):
        return tag in self.__rules

    @property
    def start_rule(self):
        return self.__start_rule


class Item:
    def __init__(self, base_state, rule_tag, rule_body, progress):
        self.__base_state = base_state
        self.__rule_tag = rule_tag
        self.__rule_body = rule_body
        self.__progress = progress

    @property
    def base_state(self):
        return self.__base_state

    @property
    def rule_tag(self):
        return self.__rule_tag

    @property
    def rule_body(self):
        return self.__rule_body

    @property
    def progress(self):
        return self.__progress

    @property
    def expected_tag(self):
        if self.progress == len(self.rule_body):
            return None
        return self.rule_body[self.progress]

    @property
    def next(self):
        if self.progress == len(self.rule_body):
            return None
        return Item(self.base_state, self.rule_tag, self.rule_body, self.progress + 1)

    @property
    def __key(self):
        return self.base_state, self.rule_tag, self.rule_body, self.progress

    def __eq__(self, other):
        return self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

    def __repr__(self):
        return str(self.__key)


def parse(raw_productions, tokens, get_tag=lambda t: t.tag):
    grammar = Grammar(raw_productions)
    start_item = Item(0, None, (grammar.start_rule.tag,), 0)
    states = [[start_item]]
    for i, token in enumerate(chain(tokens, [None])):
        states.append([])
        for item in states[i]:
            if item.expected_tag is None:
                for base_item in states[item.base_state]:
                    if base_item.expected_tag == item.rule_tag and base_item.next not in states[i]:
                        states[i].append(base_item.next)
            elif item.expected_tag in grammar:
                if grammar[item.expected_tag].nullable:
                    if item.next not in states[i]:
                        states[i].append(item.next)
                for body in grammar[item.expected_tag]:
                    new_item = Item(i, item.expected_tag, body, 0)
                    if new_item not in states[i]:
                        states[i].append(new_item)
            elif item.expected_tag == get_tag(token):
                states[i + 1].append(item.next)
    return start_item.next in states[i]
