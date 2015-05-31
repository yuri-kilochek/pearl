import lang
import pearl

try:
    module = lang.Module('test')
except Exception as e:
    if e.__cause__.__class__ != pearl.AmbiguousParse:
        raise
    print(e)
    for x in e.__cause__.args[0]:
        print(x)



