import pearl


def flatten_symbols(*items):
    items = list(items)
    i = 0
    while i < len(items):
        if items[i].__class__ != str:
            try:
                items[i:i+1] = items[i]
            except TypeError:
                i += 1
        else:
            i += 1
    return items

def simple_math(**c):
    return pearl.Grammar[
        '_start_': ['expr'],

        'expr': ['add/sub'],

        'add/sub': ['add/sub', {'+'}, 'mul/div']: lambda x, y: [c['add'](x, y)],
        'add/sub': ['add/sub', {'-'}, 'mul/div']: lambda x, y: [c['sub'](x, y)],
        'add/sub': ['mul/div'],

        'mul/div': ['mul/div', {'*'}, 'pref']: lambda x, y: [c['mul'](x, y)],
        'mul/div': ['mul/div', {'/'}, 'pref']: lambda x, y: [c['div'](x, y)],
        'mul/div': ['pref'],

        'pref': [{'+'}, 'prim']: lambda x: [c['pos'](x)],
        'pref': [{'-'}, 'prim']: lambda x: [c['neg'](x)],
        'pref': ['prim'],

        'prim': [{'('}, 'expr', {')'}],
        'prim': ['num'],

        'num': ['sgn?', 'int', 'frac?', 'exp?']: lambda *cs: [c['num'](''.join(cs))],

        'int': ['dig', 'int'],
        'int': ['dig'],

        'frac?': ['.', 'int'],
        'frac?': [],

        'exp?': ['eE', 'sgn?', 'int'],
        'exp?': [],

        'eE': ['e'],
        'eE': ['E'],

        'sgn?': ['sgn'],
        'sgn?': [],

        'sgn': ['+'],
        'sgn': ['-'],

        'dig': ['0'],
        'dig': ['1'],
        'dig': ['2'],
        'dig': ['3'],
        'dig': ['4'],
        'dig': ['5'],
        'dig': ['6'],
        'dig': ['7'],
        'dig': ['8'],
        'dig': ['9'],
    ]

sexpress = simple_math(
    add='(+ {} {})'.format,
    sub='(- {} {})'.format,
    mul='(* {} {})'.format,
    div='(/ {} {})'.format,
    pos='(+ {})'.format,
    neg='(- {})'.format,
    num=lambda t: t,
)

evaluate = simple_math(
    add=lambda x, y: x + y,
    sub=lambda x, y: x - y,
    mul=lambda x, y: x * y,
    div=lambda x, y: x / y,
    pos=lambda x: +x,
    neg=lambda x: -x,
    num=float,
)


expression = '3*(1/2)'

for r, in pearl.parse(sexpress, expression):
    print(r)  # (* 3 (/ 1 2))

for r, in pearl.parse(evaluate, expression):
    print(r)  # 1.5


ambiguous = pearl.Grammar[
    '_start_': ['S'],

    'S': ['S', {'+'}, 'S']: lambda x, y: ['({} + {})'.format(x, y)],
    'S': ['a'],
]

for r, in pearl.parse(ambiguous, 'a+a+a+a'):
    print(r)


dynamic = pearl.Grammar[
    '_start_': ['action'],

    'action': ['.'],
    'action': [{'!'}, 'char', (lambda g, c: g.put('action', [c, 'action'])), 'action'],

    'char': ['a'],
    'char': ['b'],
    'char': ['c'],
    'char': ['d'],
    'char': ['e'],
    'char': ['f'],
    'char': ['g'],
    'char': ['h'],
    'char': ['i'],
    'char': ['j'],
    'char': ['k'],
    'char': ['l'],
    'char': ['m'],
    'char': ['n'],
    'char': ['o'],
    'char': ['p'],
    'char': ['q'],
    'char': ['r'],
    'char': ['s'],
    'char': ['t'],
    'char': ['u'],
    'char': ['v'],
    'char': ['w'],
    'char': ['x'],
    'char': ['y'],
    'char': ['z'],
]

for r in pearl.parse(dynamic, '!aaa!bbababa.'):
    print(r)

var_math = pearl.Grammar[
    '_start_': ['expr'],

    'expr': ['add/sub'],

    'expr': ['id', {'='}, 'expr', {';'}, (lambda g, n, v: g.put('var', [{n}], lambda: [v])), 'expr']: lambda n, v, r: [r],

    'id': ['ch+']: lambda *cs: ''.join(cs),

    'ch+': ['ch'],
    'ch+': ['ch', 'ch+'],

    'ch': ['a'],
    'ch': ['b'],
    'ch': ['c'],
    'ch': ['d'],
    'ch': ['e'],
    'ch': ['f'],
    'ch': ['g'],
    'ch': ['h'],
    'ch': ['i'],
    'ch': ['j'],
    'ch': ['k'],
    'ch': ['l'],
    'ch': ['m'],
    'ch': ['n'],
    'ch': ['o'],
    'ch': ['p'],
    'ch': ['q'],
    'ch': ['r'],
    'ch': ['s'],
    'ch': ['t'],
    'ch': ['u'],
    'ch': ['v'],
    'ch': ['w'],
    'ch': ['x'],
    'ch': ['y'],
    'ch': ['z'],

    'add/sub': ['add/sub', {'+'}, 'mul/div']: lambda x, y: [x + y],
    'add/sub': ['add/sub', {'-'}, 'mul/div']: lambda x, y: [x - y],
    'add/sub': ['mul/div'],

    'mul/div': ['mul/div', {'*'}, 'pref']: lambda x, y: [x * y],
    'mul/div': ['mul/div', {'/'}, 'pref']: lambda x, y: [x / y],
    'mul/div': ['pref'],

    'pref': [{'+'}, 'prim']: lambda x: [+x],
    'pref': [{'-'}, 'prim']: lambda x: [-x],
    'pref': ['prim'],

    'prim': [{'('}, 'expr', {')'}],
    'prim': ['num'],
    'prim': ['var'],

    'num': ['sgn?', 'int', 'frac?', 'exp?']: lambda *cs: [float(''.join(cs))],

    'int': ['dig', 'int'],
    'int': ['dig'],

    'frac?': ['.', 'int'],
    'frac?': [],

    'exp?': ['eE', 'sgn?', 'int'],
    'exp?': [],

    'eE': ['e'],
    'eE': ['E'],

    'sgn?': ['sgn'],
    'sgn?': [],

    'sgn': ['+'],
    'sgn': ['-'],

    'dig': ['0'],
    'dig': ['1'],
    'dig': ['2'],
    'dig': ['3'],
    'dig': ['4'],
    'dig': ['5'],
    'dig': ['6'],
    'dig': ['7'],
    'dig': ['8'],
    'dig': ['9'],
]

for r, in pearl.parse(var_math, 'a=2;b=(c=a+1;c*c);a+b'):
    print(r)
