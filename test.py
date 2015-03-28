import pearl


def join(items):
    if isinstance(items, str):
        return items
    return ''.join(map(join, items))

def simple_math(**c):
    g = pearl.Grammar()

    g = g.put('__start__', ['expr'])

    g = g.put('expr', ['add/sub'])

    g = g.put('add/sub', ['add/sub', '+', 'mul/div'], lambda g, x, op, y: [g, c['add'](x, y)])
    g = g.put('add/sub', ['add/sub', '-', 'mul/div'], lambda g, x, op, y: [g, c['sub'](x, y)])
    g = g.put('add/sub', ['mul/div'])

    g = g.put('mul/div', ['mul/div', '*', 'pref'], lambda g, x, op, y: [g, c['mul'](x, y)])
    g = g.put('mul/div', ['mul/div', '/', 'pref'], lambda g, x, op, y: [g, c['div'](x, y)])
    g = g.put('mul/div', ['pref'])

    g = g.put('pref', ['+', 'prim'], lambda g, op, x: [g, c['pos'](x)])
    g = g.put('pref', ['-', 'prim'], lambda g, op, x: [g, c['neg'](x)])
    g = g.put('pref', ['prim'])

    g = g.put('prim', ['(', 'expr', ')'], lambda g, lp, x, rp: [g, x])
    g = g.put('prim', ['num'])


    g = g.put('num', ['sgn?', 'int', 'frac?', 'exp?'], lambda g, *cs: [g, c['num'](join(cs))])

    g = g.put('int', ['dig', 'int'])
    g = g.put('int', ['dig'])

    g = g.put('frac?', ['.', 'int'])
    g = g.put('frac?', [])

    g = g.put('exp?', ['eE', 'sgn?', 'int'])
    g = g.put('exp?', [])

    g = g.put('eE', ['e'])
    g = g.put('eE', ['E'])

    g = g.put('sgn?', ['sgn'])
    g = g.put('sgn?', [])

    g = g.put('sgn', ['+'])
    g = g.put('sgn', ['-'])

    g = g.put('dig', ['0'])
    g = g.put('dig', ['1'])
    g = g.put('dig', ['2'])
    g = g.put('dig', ['3'])
    g = g.put('dig', ['4'])
    g = g.put('dig', ['5'])
    g = g.put('dig', ['6'])
    g = g.put('dig', ['7'])
    g = g.put('dig', ['8'])
    g = g.put('dig', ['9'])

    return g

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
    num=float
)


expression = '3*(1/2)'

for r, in pearl.parse(sexpress, expression):
    print(r)  # (* 3 (/ 1 2))

for r, in pearl.parse(evaluate, expression):
    print(r)  # 1.5


def ambiguous():
    g = pearl.Grammar()

    g = g.put('__start__', ['S'])

    g = g.put('S', ['S', '+', 'S'], lambda g, x, op, y: [g, '({} + {})'.format(x, y)])
    g = g.put('S', ['a'])

    return g

for r, in pearl.parse(ambiguous(), 'a+a+a+a'):
    print(r)


def dynamic():
    g = pearl.Grammar()

    g = g.put('__start__', ['actions'])

    g = g.put('actions', [])
    g = g.put('actions', ['action', 'actions'])

    g = g.put('action', ['define-action'])

    g = g.put('define-action', ['!', 'char'], lambda g, _, c: [g.put('action', [c]), '!', c])

    g = g.put('char', ['a'])
    g = g.put('char', ['b'])
    g = g.put('char', ['c'])
    g = g.put('char', ['d'])
    g = g.put('char', ['e'])
    g = g.put('char', ['f'])
    g = g.put('char', ['g'])
    g = g.put('char', ['h'])
    g = g.put('char', ['i'])
    g = g.put('char', ['j'])
    g = g.put('char', ['k'])
    g = g.put('char', ['l'])
    g = g.put('char', ['m'])
    g = g.put('char', ['n'])
    g = g.put('char', ['o'])
    g = g.put('char', ['p'])
    g = g.put('char', ['q'])
    g = g.put('char', ['r'])
    g = g.put('char', ['s'])
    g = g.put('char', ['t'])
    g = g.put('char', ['u'])
    g = g.put('char', ['v'])
    g = g.put('char', ['w'])
    g = g.put('char', ['x'])
    g = g.put('char', ['y'])
    g = g.put('char', ['z'])

    return g

for r in pearl.parse(dynamic(), '!aaaa!bbbbaa'):
    print(r)



def var_math():
    g = pearl.Grammar()

    g = g.put('__start__', ['prog'])

    g = g.put('prog', ['def', ';', 'prog'], lambda g, _, v: [g, v])
    g = g.put('prog', ['expr'])

    g = g.put('def', ['id', '=', 'expr'], lambda g, n, _, v: [g.put('var', [n], lambda g, _: (g, v))])

    g = g.put('id', ['chs'], lambda g, *cs: [g, join(cs)])

    g = g.put('chs', ['ch', 'chs'])
    g = g.put('chs', ['ch'])

    g = g.put('ch', ['a'])
    g = g.put('ch', ['b'])
    g = g.put('ch', ['c'])
    g = g.put('ch', ['d'])
    g = g.put('ch', ['e'])
    g = g.put('ch', ['f'])
    g = g.put('ch', ['g'])
    g = g.put('ch', ['h'])
    g = g.put('ch', ['i'])
    g = g.put('ch', ['j'])
    g = g.put('ch', ['k'])
    g = g.put('ch', ['l'])
    g = g.put('ch', ['m'])
    g = g.put('ch', ['n'])
    g = g.put('ch', ['o'])
    g = g.put('ch', ['p'])
    g = g.put('ch', ['q'])
    g = g.put('ch', ['r'])
    g = g.put('ch', ['s'])
    g = g.put('ch', ['t'])
    g = g.put('ch', ['u'])
    g = g.put('ch', ['v'])
    g = g.put('ch', ['w'])
    g = g.put('ch', ['x'])
    g = g.put('ch', ['y'])
    g = g.put('ch', ['z'])

    g = g.put('expr', ['add/sub'])

    g = g.put('add/sub', ['add/sub', '+', 'mul/div'], lambda g, x, _, y: [g, x + y])
    g = g.put('add/sub', ['add/sub', '-', 'mul/div'], lambda g, x, _, y: [g, x - y])
    g = g.put('add/sub', ['mul/div'])

    g = g.put('mul/div', ['mul/div', '*', 'pref'], lambda g, x, _, y: [g, x * y])
    g = g.put('mul/div', ['mul/div', '/', 'pref'], lambda g, x, _, y: [g, x / y])
    g = g.put('mul/div', ['pref'])

    g = g.put('pref', ['+', 'prim'], lambda g, _, x: [g, +x])
    g = g.put('pref', ['-', 'prim'], lambda g, _, x: [g, -x])
    g = g.put('pref', ['prim'])

    g = g.put('prim', ['(', 'expr', ')'], lambda g, _0, x, _1: [g, x])
    g = g.put('prim', ['num'])
    g = g.put('prim', ['var'])

    g = g.put('num', ['sgn?', 'int', 'frac?', 'exp?'], lambda g, *cs: [g, float(join(cs))])

    g = g.put('int', ['dig', 'int'])
    g = g.put('int', ['dig'])

    g = g.put('frac?', ['.', 'int'])
    g = g.put('frac?', [])

    g = g.put('exp?', ['eE', 'sgn?', 'int'])
    g = g.put('exp?', [])

    g = g.put('eE', ['e'])
    g = g.put('eE', ['E'])

    g = g.put('sgn?', ['sgn'])
    g = g.put('sgn?', [])

    g = g.put('sgn', ['+'])
    g = g.put('sgn', ['-'])

    g = g.put('dig', ['0'])
    g = g.put('dig', ['1'])
    g = g.put('dig', ['2'])
    g = g.put('dig', ['3'])
    g = g.put('dig', ['4'])
    g = g.put('dig', ['5'])
    g = g.put('dig', ['6'])
    g = g.put('dig', ['7'])
    g = g.put('dig', ['8'])
    g = g.put('dig', ['9'])

    return g

for r, in pearl.parse(var_math(), 'a=2;b=a*a;a+b+1'):
    print(r)  # (* 3 (/ 1 2))