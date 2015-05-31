import lang
import pearl

try:
    module = lang.Module('test')
except Exception as e:
    for x in e.__cause__.args[0]:
        print(x)



