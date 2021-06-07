from .magic import line_magic, arg
import time

@arg("-q", "--quiet", action="store_true", help="suppress terminal output")
@line_magic
def softreset_magic(kernel, args):
    """Reset microcontroller. Similar to pressing the reset button.
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
            kernel.print("\n")


@line_magic
def name_magic(kernel, _):
    """Name of currently connected microcontroller."""
    kernel.print(kernel.device.name)


@line_magic
def uid_magic(kernel, _):
    """UID of currently connected microcontroller."""
    kernel.print(kernel.device.uid)


@line_magic
def url_magic(kernel, _):
    """URL of currently connected microcontroller."""
    kernel.print(kernel.device.url)


@line_magic
def platform_magic(kernel, _):
    """sys.platform of currently connected device."""
    kernel.print(platform(kernel.device))

@line_magic
def info_magic(kernel, _):
    fmt = "{:10} {}"
    kernel.print(fmt.format('name', kernel.device.name))
    kernel.print(fmt.format('platform', platform(kernel.device)))
    kernel.print(fmt.format('uid', kernel.device.uid))
    kernel.print(fmt.format('url', kernel.device.url))
    kernel.print(kernel.device.config)

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

def platform(device):
    with device as repl:
        return repl.platform
