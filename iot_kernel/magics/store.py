from .magic import line_magic, arg
from ..kernel_logger import logger

import os, json


def mcu2storage(kernel, name):
    with kernel.device as repl:
        res = repl.exec(f"import json\nprint(json.dumps({name}))")
        logger.debug(f"{name} = {res}")
        kernel.shell.db['autorestore/' + name] = json.loads(res)

def storage2mcu(kernel, name):
    try:
        obj = kernel.shell.db['autorestore/' + name]
    except KeyError:
        kernel.error(f"no variable with name '{name}' in storage")
    else:
        with kernel.device as repl:
            try:
                repl.exec(f"import json\n{name} = json.loads({repr(json.dumps(obj))})")
            except TypeError as te:
                kernel.error(f"Cannot serialize '{name}': {te}")

@arg('-d', '--delete', nargs='+', default=None, help="remove variables from storage")
@arg('-r', '--refresh', nargs='+', default=None, help="load variables from store into microcontroller")
@arg('-z', '--clear', default=False, action='store_true', help="remove all variables from storage")
@arg('names', nargs='*', help="variable names")
@line_magic
def store_magic(kernel, args):
    """Copy variables between microcontroller and storage.
The storage is also available from ipyton via it's %store magic.

Examples:
    %store           - show list of all variables in storage
    %store a b       - copy a, b from MCU to storage
    %store -d a      - remove a from storage
    %store -z        - clear storage (remove all entries)
    %store -r a b    - copy a, b from storage to MCU
"""

    AR = 'autorestore/'
    db = kernel.shell.db

    if args.delete:
        for d in args.delete:
            try:
                db['autorestore/' + d]
            except KeyError:
                kernel.error(f"no variable with name '{d}' in storage")
            else:
                try:
                    del db[AR + d]
                except BaseException:
                    # never happens ... del on non-existing variable raises no exception
                    # let's keep the exception handler anyway, if ever the api changes ...
                    kernel.error(f"variable '{d}' not in storage")
    if args.clear:
        for k in db.keys(AR + '*'):
            del db[k]
    if args.refresh:
        for n in args.refresh:
            storage2mcu(kernel, n)
    if args.names:
        for n in args.names:
            mcu2storage(kernel, n)
    elif not (args.clear or args.refresh or args.delete):
        vars = db.keys(AR + '*')
        if vars:
            vars.sort()
            size = max(map(lambda x: len(os.path.basename(x)), vars))

            fmt = '%-'+str(size)+'s -> %s'
            for var in vars:
                kernel.print(fmt % (os.path.basename(var), repr(db.get(var, '<unavailable>'))[:70]))
        else:
            kernel.error("storage is empty")
