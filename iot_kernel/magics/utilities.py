from .magic import line_magic, arg, CELL_MAGIC, LINE_MAGIC
from ..kernel_logger import logger

from iot_device import Env
from termcolor import colored

import logging
import os


@arg('path', nargs="?", default=Env.iot49_dir(), help="New working directory. Default: $IOT49.")
@line_magic
def cd_magic(kernel, args):
    """Change the working directory."""
    os.chdir(args.path)
    kernel.print(os.getcwd())


@arg('-v', '--verbose', action='store_true', help="Show detailed help for each line magic.")
@line_magic
def lsmagic_magic(kernel, args):
    """List all magic functions."""
    if args.verbose:
        for k, v in sorted(LINE_MAGIC.items()):
            if not v[1]: continue
            kernel.print(f"MAGIC %{k} {'-'*(70-len(k))}")
            v[0](kernel, "-h")
            kernel.print("\n")
        return

    kernel.print("Line Magic:    -h shows help (e.g. %discover -h)")
    for k, v in sorted(LINE_MAGIC.items()):
        if not v[1]: continue
        kernel.print("  %{:10s}  {}".format(k, v[1]))
    kernel.print("  {:11s}  {}".format('!', "Pass line to bash shell for evaluation."))
    kernel.print("\nCell Magic:    -h shows help (e.g. %%connect -h)")
    for k, v in sorted(CELL_MAGIC.items()):
        if not v[1]: continue
        kernel.print("  %%{:10s} {}".format(k, v[1]))


@arg('level', nargs='?', default='INFO', const='INFO', choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="logging levels")
@arg('logger', nargs='?', help="name of logger to apply level to")
@line_magic
def loglevel_magic(kernel, args):
    """Set logging level.
Without arguments lists name and level of all available loggers.

Example:
    %loglevel device_registry INFO
    """
    if args.logger:
        logger = logging.getLogger(args.logger)
        logger.setLevel(args.level)
        for h in logging.getLogger().handlers:
            h.setLevel(args.level)
        kernel.print(f"Logger {args.logger} level set to {args.level}")
    else:
        fmt = "{:30}  {}"
        kernel.print(fmt.format('Logger', 'Level'))
        kernel.print('')
        colors = {
            'DEBUG': 'green',
            'INFO': 'blue',
            'WARNING': 'cyan',
            'ERROR': 'red',
            'CRITICAL': 'magenta',
        }
        for k, v in logging.root.manager.loggerDict.items():
            s = str(v)
            if '(' in s:
                level = fmt.format(k, s[s.find("(")+1:s.find(")")])
                kernel.print(level, colors.get(level.split(' ')[-1], 'grey'))
