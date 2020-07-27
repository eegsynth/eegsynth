import sys

from .vumeter import _setup, _start, _loop_once, _loop_forever, _stop

class Executable:
    def __init__(self, args=None):
        if args!=None:
            # override the command line arguments
            sys.argv = [sys.argv[0]] + args

        # the Qt application does not restart upon a raised exception
        _setup()
        _start()
        _loop_forever()
