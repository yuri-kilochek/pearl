import argparse
import sys

import core
import pearl

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('source_file', help='(without extension)')

args = arg_parser.parse_args()

try:
    module = core.Module(args.source_file)
except Exception as e:
    if e.__cause__.__class__ != pearl.AmbiguousParse:
        raise
    print(e, file=sys.stderr)
    for x in e.__cause__.args[0]:
        print(x, file=sys.stderr)
