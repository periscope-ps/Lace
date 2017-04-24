import logging
import os

from logging import DEBUG, INFO, CRITICAL, WARN, ERROR

def getLogger(name="lacedefault"):
    class ColourFormatter(logging.Formatter):
        def __init__(self, fmt, datefmt=None):
            self.colours = { 
                logging.CRITICAL: "\033[1;31m",
                logging.ERROR: "\033[0;31m",
                logging.WARNING: "\033[0;33m",
                logging.INFO: "\033[0;32m",
                logging.DEBUG: "\033[0;34m"
            }
            super(ColourFormatter, self).__init__(fmt, datefmt, '{')
        
        def _buildStr(self, args, kwargs, pad):
            lens = []
            tmpargs = []
            tmpkwargs = []
            s = 0
            for arg in args:
                if arg == "":
                    tmpStr = "\"\", "
                else:
                    tmpStr = "{}".format(repr(arg))
                lens.append((len(tmpStr), tmpargs, len(tmpargs)))
                tmpargs.append(tmpStr)
                s += len(tmpStr)
            for k, arg in kwargs.items():
                if arg == "":
                    tmpStr = "\"\", "
                else:
                    tmpStr = "{}".format(repr(arg))
                lens.append((len(tmpStr) + len(k), tmpkwargs, len(tmpkwargs)))
                tmpkwargs.append((k, tmpStr))
                s += len(tmpStr)
                
            lens = sorted(lens, key=lambda v: v[0])
            try:
                size = os.get_terminal_size().columns - 40 - pad
            except OSError:
                size = 10000000
            while s > max(0, size):
                l, ls, i = lens.pop()
                ls[i] = "..." if isinstance(ls[i], str) else (ls[0], "...")
                s -= l
            args_str = ", ".join(tmpargs)
            kwargs_str = ", ".join(["{}: {}".format(k, v) for k, v in tmpkwargs])
            base_str = "{}{}{}".format("args=[{}]" if args_str else "{}", 
                                       ", " if args_str and kwargs_str else "", 
                                       "kwargs={{{}}}" if kwargs_str else "{}")
            base_str = base_str or "No arguments passed{}{}"
            if len(base_str) + len(args_str) + len(kwargs_str) > size:
                base_str = "Arguments too long, trucating..."
                args_str = ""
                kwargs_str = ""
            return base_str.format(args_str, kwargs_str)
            
        def format(self, record):
            isfunc = True
            pad = 0
            old_fmt = self._style._fmt
            if len(record.args) and record.args[0]:
                caller = " {}".format(record.args[0])
            else:
                caller = ""
            try:
                args, kwargs, pad = record.args[1]
            except IndexError:
                isfunc = False
            record.args = []
            if isfunc:
                record.msg = self._buildStr(args, kwargs, pad)
            fmt = old_fmt.format(levelname=record.levelname[:1],
                                 pad="-" * pad,
                                 color=self.colours[record.levelno],
                                 reset="\033[0m",
                                 caller=caller)
            self._style._fmt = fmt
            result = logging.Formatter.format(self, record)
            self._style._fmt = old_fmt
            return result
    
    log = logging.getLogger(name)
    if not log.handlers:
        cout = logging.StreamHandler()
        log.addHandler(cout)
    
    for handler in log.handlers:
        handler.setFormatter(ColourFormatter("{pad}{color}[{levelname} {{asctime}}{caller}]{reset} {{message}}"))
    
    return log

class trace(object):
    _level = logging.NOTSET
    _pad = 0
    _show_pad = False
    _log = getLogger('_ltrace__')
    def setLevel(level, showdepth=False):
        trace._log.propagate = False
        trace._level = level
        trace._log.setLevel(level)
        trace._show_pad = showdepth
        
    def info(cls):
        return lambda f: trace._do(trace._log.info, INFO, f, cls)
    def debug(cls):
        return lambda f: trace._do(trace._log.debug, DEBUG, f, cls)
    def error(cls):
        return lambda f: trace._do(trace._log.error, ERROR, f, cls)
    def critical(cls):
        return lambda f: trace._do(trace._log.critical, CRITICAL, f, cls)
    def warn(cls):
        return lambda f: trace._do(trace._log.warn, WARN, f, cls)
        
    def _do(op, level, f, cls):
        def wrapper(*args, **kwargs):
            if trace._level == logging.NOTSET:
                return f(*args, **kwargs)
                
            trace._pad += 2 if level >= trace._level else 0
            compressed = (args, kwargs, trace._pad if trace._show_pad else 0)
            op("", "{}.{}".format(cls, f.__name__), compressed)
            try:
                result = f(*args, **kwargs)
            except:
                trace._pad -= 2 if level >= trace._level else 0
                raise
            trace._pad -= 2 if level >= trace._level else 0
            return result
        return wrapper
        
if __name__ == "__main__":
    @trace.warn("unittest")
    def test(a, b):
        pass
    
    @trace.info("unittest")
    def recur1(depth):
        if depth == 0:
            return
        else:
            test(a=5, b=10)
            recur2(depth)
    
    @trace.debug('unittest')
    def recur2(depth):
        recur1(depth - 1)
    
    logger = getLogger()
    logger.setLevel(DEBUG)
    logger.critical("This is a test")
    logger.warn("This is a test")
    logger.error("This is a test")
    logger.debug("This is a test")
    logger.info("This is a test")
    trace.setLevel(logging.INFO, True)
    test("1", b="2")
    recur1(10)
