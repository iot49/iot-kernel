from .magic import line_magic, arg
from iot_device import Env, cd

from glob import glob
import os, shlex, shutil, subprocess


@arg('-p', '--packages', nargs='*', default=None, help="packages to compile (Default: packages used by connected device)")
@arg('-c', '--compiler', default=None, help="Path to the compiler, defaults to `~/bin/{implementation}/mpy-cross`")
@arg('-a', '--args', default="", help="Arguments passed to `mpy-cross`")
@line_magic
def mpycross_magic(kernel, args):
    """Compile .py files.

Compiles files in each `package` to a new folder `.compiled/{implementation}`.

Examples:

    %mpycross
    %mpycross --packages secrets airlift-client boards/esp32/code/boot.py
    %mpycross --compiler /usr/local/mpy-cross --args="-O2 -mno-unicode"
"""
    packages = args.packages
    if not packages: packages = kernel.device.packages
    with kernel.device as repl: implementation = repl.implementation
    compiler = args.compiler
    if not compiler: compiler = os.path.join('~/bin', implementation, 'mpy-cross')
    compiler_args = args.args

    n = 0
    with cd(Env.iot_projects()):
        for package in packages:
            for name, path in package.files().items():
                if not name.endswith('.py'): continue
                src = os.path.join(path, name)
                dst = os.path.join('.compiled', implementation, path, name.replace('.py', '.mpy'))
                if not os.path.isfile(dst) or (os.path.getmtime(src) > os.path.getmtime(dst)):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    kernel.print(f"compiling   {os.path.normpath(os.path.join(path, name))}")
                    cmd = f"{compiler} {compiler_args} -s {os.path.basename(src)} -o {dst} {src}"
                    try:
                        result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        kernel.error(result.stdout.decode('utf-8'))
                    except FileNotFoundError as e:
                        kernel.stop(e)
                    n += 1

    if n == 0:
        kernel.print("all mpy files are up-to-date")
