import mylang

module = mylang.load('test')
print(repr(module))
module.execute({'print': print})

#mylang.execute(module, print=print)
