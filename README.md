# Lace: Diagnostic logging and tracing tools for python

## Introduction

Lace provides a small but powerful set of tools for inspecting and diagnosing
programmatic problems in place without modifying pre-existing code.  With the
use of decorators, functions can be modified unobtrusively to present active
trace information at runtime along with arguments and keyword arguments.

In addition to tracing utilities, Lace includes hooks to the built in python
logging module with a easy to read formatter installed.

## Installation

Installation is done using `setuptools`.  If you do not already have
`setuptools` on your machine, run the following:
```
pip install setuptools
```

All that is needed to use Lace is to run the setup script.
```
python setup.py build install
```

You should now have Lace available to your python environment

## Usage

### Logging

Logging utilities in Lace are available in the logging module
```
from lace import logging
```

If you are familiar with the built-in python logging module, lace logging
functions exactly the same way.
> TODO: Lace currently only supports the `getLogger` function at the root level
> in the future, lace will present the same interface as the built-in module
> and can be used interchangably.

For anyone **not** familiar with the built-in python logging module, you can
get a logger with:
```
logger = logging.getLogger()
```

This provides you with the default lace logger (named "lacedefault"), you can
change the logger name by passing it as an optional argument:
```
logger = logging.getLogger("foo")
```

The logger object exposes `info`, `debug`, `warn`, `error`, and `critial`, all
of which take a single argument which is a message to be displayed.
```
logger.info("This is an informative message")
```

The displayed level is set with the `setLevel` function of the logger (all 
levels are the capitalized version of their call e.g. INFO for info, ERROR for 
error):
```
logger.setLevel(logging.DEBUG)
```

See https://docs.python.org/3/library/logging.html for more

### Tracing

Lace includes a trace version of every logging level, these are found in the
`logging` module in the `trace` class
```
from lace.logging import trace
```

By decorating a function with the trace.<level> function which takes one 
argument (the module the function is contained in), diagnostic information
can be selectively included in the output.

```
class MyClass(object):
      @trace.info("MyClass")
      def __init__(self, value):
      	  self.foo(10, y=5)
      	  
      @trace.debug("MyClass")
      def foo(self, x, y):
      	  pass
```

The level and type of trace can then be changed with the `setLevel` function
of the `trace` object:
```
trace.setLevel(logging.INFO, showdepth=False)
```
`trace.setLevel` takes two arguments, the first is the level as per the logging
module, the second - `showdepth` default `False` - sets whether the output
should be padded to show the trace depth on calls.

The above two pieces of code, when `mc = MyClass(5)` was called, would print:
```
[I 2017-04-24 14:09:05,530 MyClass.__init__] args=[5]
[D 2017-04-24 14:09:05,531 MyClass.foo] args=[10], kwargs={y: 5}
```

If `showdepth` was set to `True`, it would instead display
```
--[I 2017-04-24 14:09:05,530 MyClass.__init__] args=[5]
----[D 2017-04-24 14:09:05,531 MyClass.foo] args=[10], kwargs={y: 5}
```
