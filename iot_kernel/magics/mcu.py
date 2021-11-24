from .magic import line_magic, arg
from iot_device import Env
import time, os

# %softreset
# %synctime, %gettime
# %info, %name, %uid

@arg("-q", "--quiet", action="store_true", help="suppress terminal output")
@line_magic
def softreset_magic(kernel, args):
    """Reset microcontroller.
Purges all variables and releases all devices (e.g. I2C, UART, ...).

Example:
    a = 5
    %softreset
    print(a)   # NameError: name 'a' isn't defined
"""
    with kernel.device as repl:
        if not args.quiet:
            kernel.print("")
            kernel.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", 'red', 'on_cyan')
            kernel.print("!!!!!   softreset ...     !!!!!", 'red', 'on_cyan')
            kernel.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", 'red', 'on_cyan', end="")
        repl.softreset()
        if not args.quiet:
            kernel.print("")


@arg("-t", "--timeout", type=float, default=2.5, help="time in seconds to wait for output (default: 2.5)")
@line_magic
def hardreset_magic(kernel, args):
    """Reset microcontroller by calling 'machine.reset()'. 
Prints boot messages (output from boot.py and main.py) to console.
If there is no output, does not wait for main.py to finish.
Note: there may be errors (cannot enter raw repl) from subsequent 
      instructions due to unexpected output.
    
Example:
    %hardreset                 
"""
    with kernel.device as repl:
        kernel.print("")
        kernel.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",   'red', 'on_cyan')
        kernel.print("!!!!!   hardreset ...     !!!!!",   'red', 'on_cyan')
        kernel.print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", 'red', 'on_cyan')
        repl.hardreset(kernel, args.timeout)
        kernel.print("")

@line_magic
def uid_magic(kernel, _):
    """Print the uid of the currently connected device"""
    kernel.print(kernel.device.uid)


@line_magic
def name_magic(kernel, _):
    """Print the name of the currently connected device"""
    kernel.print(kernel.device.name)


@arg("-v", "--verbose", action="store_true", help="also show resource size and location (on mcu and host)")
@line_magic
def info_magic(kernel, args):
    """Summary about connected device"""
    fmt = "{:15} {}"
    kernel.print(fmt.format('name', kernel.device.name))
    kernel.print(fmt.format('platform', kernel.device.platform))
    kernel.print(fmt.format('implementation', kernel.device.implementation))
    kernel.print(fmt.format('uid', kernel.device.uid))
    kernel.print(fmt.format('url', kernel.device.url))
    try:
        config = kernel.device.config
        iot_projects = Env.expand_path(Env.iot_projects())
        kernel.print(fmt.format('configuration', config.file))
        if args.verbose:
            kernel.print("resources:")
            for k, v in config.resource_files.items():
                if v[1] < 0: continue
                path = os.path.relpath(v[2], iot_projects)
                kernel.print(f"{v[1]:6d} {k:30} {path}")
    except ValueError:
        pass

@line_magic
def synctime_magic(kernel, _):
    "Synchronize microcontroller time to host"
    with kernel.device as repl:
        repl.sync_time()
        t = time.mktime(repl.get_time())
        kernel.print(f"{time.strftime('%Y-%b-%d %H:%M:%S', time.localtime(t))}")

@line_magic
def gettime_magic(kernel, _):
    "Query microcontroller time"
    with kernel.device as repl:
        t = time.mktime(repl.get_time())
        kernel.print(f"{time.strftime('%Y-%b-%d %H:%M:%S', time.localtime(t))}")
