from ..kernel_logger import logger

from iot_device import redirect_stdout_stderr
from functools import wraps
from collections import OrderedDict
from io import StringIO
import argparse, shlex, sys

# dictionaries of handlers name --> (method, descripion)
LINE_MAGIC = OrderedDict()
CELL_MAGIC = OrderedDict()


# @cell_magic decorator, use last (after all @arg's)
def cell_magic(fn):
    # function that is called when invoking the magic
    @wraps(fn)
    def wrapped(kernel, line, body):
        args = None
        out = StringIO()
        err = StringIO()
        with redirect_stdout_stderr(out, err):
            try:
                # parse line
                args = wrapped.parser.parse_args(shlex.split(line))
            except SystemExit:
                pass
        kernel.print(out.getvalue(), end="")
        kernel.error(err.getvalue(), end="")
        if args: fn(kernel, args, body)

    # extract magic name and docstring
    name = fn.__name__.rsplit('_')[0]
    doc = (fn.__doc__ or "").split('\n', 1)
    if len(doc) < 2: doc.append("")

    # construct the parser
    wrapped.parser = argparse.ArgumentParser(
        prog='%%' + name,
        description=doc[0],
        epilog=doc[1],
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=22, width=80))

    # add to dict
    CELL_MAGIC[name] = (wrapped, doc[0])
    return wrapped


# @line_magic decorator, use last (after all @arg's)
def line_magic(fn):
    # function that is called when invoking the magic
    @wraps(fn)
    def wrapped(kernel, line):
        args = None
        out = StringIO()
        err = StringIO()
        with redirect_stdout_stderr(out, err):
            try:
                # parse line
                args = wrapped.parser.parse_args(shlex.split(line))
            except SystemExit:
                pass
        kernel.print(out.getvalue(), end="")
        kernel.error(err.getvalue(), end="")
        if args: fn(kernel, args)

    # extract magic name and docstring
    name = fn.__name__.rsplit('_')[0]
    doc = (fn.__doc__ or "").split('\n', 1)
    if len(doc) < 2: doc.append("")

    # construct the parser
    wrapped.parser = argparse.ArgumentParser(
        prog='%' + name,
        description=doc[0],
        epilog=doc[1],
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=22, width=80))
        # formatter_class=argparse.RawDescriptionHelpFormatter)

    # add to dict
    LINE_MAGIC[name] = (wrapped, doc[0])
    return wrapped


# @arg decorator (may be repeated)
def arg(*args, **kwargs):
    # add argument to the parser that was construction by @line_magic
    def wrap(fn):
        fn.parser.add_argument(*args, **kwargs)
        return fn
    return wrap


# pylint: disable=unused-wildcard-import

# cell magics
from .connect import *
from .ssh import *

# line magics
from .discover import *
from .rsync import *
from .store import *
from .mcu import *
from .file_ops import *
from .utilities import *
from .pip import *

# do on-the-fly compiling by rsync instead (if desired ...)
# from .mpycross import *
