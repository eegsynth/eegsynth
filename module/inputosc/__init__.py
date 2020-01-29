import sys

class Executable:
    def __init__(self, args=None):
        if args!=None:
            # override the command line arguments
            sys.argv = [sys.argv[0]] + args
        # the module is implemented as a Python script and starts as soon as it is imported
        from . import inputosc
