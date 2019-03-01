import logging, os, distutils.util
from collections.abc import Iterable
from functools import wraps

from logging import DEBUG, INFO, CRITICAL, WARN, ERROR, NOTSET
from pprint import pprint

DEFAULT_NAMESPACE = "__lace__"
TRACE_OBJECTS, TRACE_PUBLIC, TRACE_ALL = 7, 6, 5
[logging.addLevelName(l,n) for l,n in [(TRACE_ALL, "TLONG"), (TRACE_PUBLIC, "TSHORT"), (TRACE_OBJECTS, "TNEW")]]


def getLogger(name=DEFAULT_NAMESPACE): return logging.getLogger(name)

class trace(object):
    class filter(object):
        def filter(self, record):
            return record.levelno < DEBUG

    def enabled(v=None):
        if not isinstance(v, type(None)):
            if trace._active:
                getLogger().warning("Tracing already generated on {}, unable to add/remove".format(trace._active))
            trace._enabled = v
        return bool(distutils.util.strtobool(os.environ.get('LACE_TRACE_ON', 'false'))) or trace._enabled
    _pad, _show_pad, _show_return = 0, False, False
    _interactive, _breakpoints = False, []
    _enabled, _active = False, False

    def _buildlogger(n, level):
        def _wrapper(f):
            logger = getLogger("{}.{}".format(n, f.__name__))
            return trace._do(logger, level, f)
        def _ident(f): return f
        
        trace._active = n
        return _wrapper if trace.enabled() else _ident
    
    def _fn_desc(args, kwargs):
        def shorten(v):
            if isinstance(v, (int, float, str)): return v
            elif isinstance(v, Iterable): return "{}[{}]".format(type(v), len(v))
            elif isinstance(v, type): return "class_{}".format(v.__name__)
            elif isinstance(v, object): return "obj_{}".format(type(v).__name__)
            else: return v
            
        args = ["args=[{}]".format(", ".join([repr(shorten(a)) if a else '""' for a in args]))] if args else []
        kwargs = ["kwargs={{{}}}".format(", ".join(["{}: {}".format(k,repr(shorten(v) if v else '""')) for k,v in kwargs.items()]))] if kwargs else []
        return ", ".join(args + kwargs)

    def showCallDepth(v):
        trace._show_pad = v
    def showReturn(v):
        trace._show_return = v
    def runInteractive(v):
        trace._interactive = v
    def setBreakpoint(v):
        trace._breakpoints.append(v)
    def removeBreakpoint(v):
        try:
            trace._breakpoints.remove(v)
        except ValueError:
            pass
    def tlong(cls): return trace._buildlogger(cls, TRACE_ALL)
    def tshort(cls): return trace._buildlogger(cls, TRACE_PUBLIC)
    def tobj(cls): return trace._buildlogger(cls, TRACE_OBJECTS)
    def info(cls): return trace._buildlogger(cls, INFO)
    def debug(cls): return trace._buildlogger(cls, DEBUG)
    def error(cls): return trace._buildlogger(cls, ERROR)
    def critical(cls): return trace._buildlogger(cls, CRITICAL)
    def warn(cls): return trace._buildlogger(cls, WARN)
    
    def _do_interactive(args, kwargs):
        v = 'none'
        while v not in ['n', 'c']:
            v = input("[h|help for commands]: ") or v
            if v in ['h', 'help']:
                print("""
                [enter] | n: next
                a: display args
                #: display arg by index
                k <[OPTIONAL] name>: display kwargs <by name>
                i: increase log level  (Temporarily unavailable)
                d: decrease log level  (Temporarily unavailable)
                c: continue
                r: toggle return values
                +b <name>: set breakpoint
                -b <name>: remove breakpoint
                """)
            elif v == "a": pprint(args)
            elif v[0] == "k":
                try: pprint(kwargs[v.split()[1]])
                except IndexError: pprint(kwargs)
                except KeyError: print("Unknown keyword")
            elif v == 'c': trace._interactive = False
            elif v == 'r': trace._show_return = not trace._show_return
            elif v[:2] == '+b': trace._breakpoints.append(v.split()[1])
            elif v[:2] == '-b':
                try: trace._breakpoints.remove(v.split()[1])
                except ValueError: pass
            elif v.isdigit():
                try: pprint(args[int(v)])
                except IndexError: print("index out of bound")
            elif v in kwargs: pprint(kwargs[v])
            elif v != 'n' and v != '': print("keyword not in function")

    def _do(logger, level, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not (logger.isEnabledFor(level) or logger.name in trace._breakpoints):
                return f(*args, **kwargs)

            if logger.name in trace._breakpoints:
                trace._interactive = True
            trace._pad += 2
            logger.log(level, "{}{}".format("-" * trace._pad if trace._show_pad else "", trace._fn_desc(args, kwargs)))
            
            if trace._interactive:
                trace._do_interactive(args, kwargs)
            try:
                # This is the actual function
                result = f(*args, **kwargs)
                if trace._show_return:
                    logger.log(level, "{}{}".format("<" * trace._pad if trace._show_pad else "", result))
                return result
            except:
                raise
            finally:
                trace._pad -= 2
        return wrapper

    def __init__(self, ns="trace"):
        self.ns = ns
    def __call__(self, subject):
        for n,fn in {k:v for k,v in subject.__dict__.items() if callable(v)}.items():
            ns = "{}.New".format(self.ns, "New" if n == "__init__" else subject.__name__)
            if not n.startswith("__") or n == "__init__":
                if n == "__init__": setattr(subject, n, trace._buildlogger(ns, TRACE_OBJECTS)(fn))
                if n.startswith("_"): setattr(subject, n, trace._buildlogger(ns, TRACE_ALL)(fn))
                else: setattr(subject, n, trace._buildlogger(ns, TRACE_PUBLIC)(fn))
        return subject

_colors = {CRITICAL: "\033[1;31m", ERROR: "\033[0;31m", WARN: "\033[0;33m", INFO: "\033[0;32m", DEBUG: "\033[0;34m",
           TRACE_PUBLIC: "\033[0;32m", TRACE_ALL: "\033[0;34m"}
record_factory = logging.getLogRecordFactory()
def _record_factory(name, level, fn, lno, msg, args, exc_info, func=None, sinfo=None, **kwargs):
    record = record_factory(name, level, fn, lno, msg, args, exc_info, func, sinfo, **kwargs)
    record.__dict__["color"] = _colors.get(level, "")
    record.__dict__["reset"] = "\033[0m"
    return record
logging.setLogRecordFactory(_record_factory)
