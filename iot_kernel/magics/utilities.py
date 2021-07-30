from .magic import line_magic, cell_magic, arg, CELL_MAGIC, LINE_MAGIC
from ..kernel_logger import logger

from iot_device import Env
from termcolor import colored

import logging
import os

# %cd, %lsmagic, %%writefile


@arg("path", nargs="?", default="~", help="new working directory on host")
@line_magic
def cd_magic(kernel, args):
    """Change current working directory on host
Expands ~ and shell variables (e.g. $IOT_PROJECTS) as expected."""
    path =  Env.expand_path(args.path)
    if not os.path.isdir(path):
        raise ValueError(f"directory '{path}' does not exist")
    os.chdir(path)
    kernel.print(f"cwd = {os.getcwd()}")
    kernel.nb_conf.set("cwd", path)


@arg('-v', '--verbose', action='store_true', help="Show detailed help for each line magic.")
@line_magic
def lsmagic_magic(kernel, args):
    """List all magic functions"""
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
    kernel.print("  {:11s}  {}".format('!', "Pass line to bash shell for evaluation"))
    kernel.print("\nCell Magic:    -h shows help (e.g. %%connect -h)")
    for k, v in sorted(CELL_MAGIC.items()):
        if not v[1]: continue
        kernel.print("  %%{:10s} {}".format(k, v[1]))

@arg('-a', '--append', action='store_true', help="Append to file. Default is overwrite.")
@arg("path", help="file path")
@cell_magic
def writefile(kernel, args, code):
    """Write cell contents to file
Example:
    %%writefile $IOT_PROJECTS/devices/mcu.yaml
    my_mcu:
        uid: 50:02:21:a1:a7:2c"""
    path = Env.expand_path(args.path)
    kernel.print(f"Writing {path}")
    with open(path, "a" if args.append else "w") as f:
        f.write(code)
