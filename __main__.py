import mylang

module, grammar = mylang.load('test')

mylang.execute(module, grammar, print=print)
