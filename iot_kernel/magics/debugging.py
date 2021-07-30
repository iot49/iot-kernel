from .magic import line_magic, cell_magic, arg, CELL_MAGIC, LINE_MAGIC
from ..kernel_logger import logger

import logging
import os

# %loglevel, %kernel


@arg('level', nargs='?', default='INFO', const='INFO', choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="logging levels")
@arg('logger', nargs='?', help="name of logger to apply level to")
@line_magic
def loglevel_magic(kernel, args):
    """Set logging level.
Without arguments lists name and level of all available loggers

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



@cell_magic
def kernel_magic(kernel, _, code):
    # exec code in kernel contect. Debugging only.
    exec(code)
