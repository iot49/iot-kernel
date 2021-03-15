from .magic import line_magic, arg

from iot_device import RemoteError
from iot_device import cd
import contextlib
import os
import sys


@arg("destination", help="Name of destination file/directory")
@arg("sources", nargs="+", help="Names of source files")
@line_magic
def cp_magic(kernel, args):
    """Copy files between host and microcontroller.
File/directory names starting with colon (:) refer to the microcontroller.

CircuitPython: By default, CircuitPython disables writing to the
               microcontroller filesystem. To enable, add the line

                   storage.remount("/", readonly=False)"

               to boot.py.

Examples:
    # copy file from host microcontroller, changing the name
    %cp a.txt :b.txt

    # same, filename on microcontroller is same as on host (a.txt)
    %cp a.txt :

    # copy several files to microcontroller
    %cp a.txt b.txt :/

    # copy files to subfolder
    %mkdirs x/y
    %cp a.txt b.txt :x/y/

    # copy file from microcontroller to host
    %cp :a.txt :b.txt ./
    """
    # see https://github.com/micropython/micropython/blob/master/tools/pyboard.py
    def fname_remote(src):
        if src.startswith(":"):
            src = src[1:]
        return src

    def fname_cp_dest(src, dest):
        src = src.rsplit("/", 1)[-1]
        if dest is None or dest == "":
            dest = src
        elif dest == ".":
            dest = "./" + src
        elif dest.endswith("/"):
            dest += src
        return dest

    srcs = args.sources
    dest = args.destination
    with kernel.device as repl:
        if srcs[0].startswith("./") or dest.startswith(":"):
            xfer = repl.fput
            dest = fname_remote(dest)
        else:
            xfer = repl.fget
        for src in srcs:
            src = fname_remote(src)
            dst = fname_cp_dest(src, dest)
            try:
                xfer(src, dst)
            except RemoteError as e:
                kernel.error(f"Error in 'cp {src} {dst}'")
                kernel.stop(f"\n{e.msg}")
            except FileNotFoundError as e:
                kernel.stop(f"\n{e}")


@arg("path", help="path to file")
@line_magic
def cat_magic(kernel, args):
    "Print contents of named file on microcontroller"
    with kernel.device as repl:
        try:
            repl.cat(args.path, kernel.data_consumer)
            kernel.print('')
        except RemoteError:
            kernel.stop(f'File not found: {args.path}')


@arg('-r', '--recursive', action='store_true', help="recursively scan directories relative to path")
@arg('-f', '--force', action='store_true', help="delete directories")
@arg("path", nargs='*', help="path to file/directory")
@line_magic
def rm_magic(kernel, args):
    """Delete files relative to path.

If path is a directory and -f is not specified, the path is not deleted without feedback.

Examples:
    %rm a             # delete file a if it exists, no action if it's a directory, error otherwise
    %rm -f a          # delete file or directory a
    %rm -rf a         # delete a, if it's a directory, also delete contents
    %rm -r a          # delete a, if it's a directory, also delete all files but not directories recursively
    %rm -rf /         # tabula rasa
"""
    try:
        with kernel.device as repl:
            for p in args.path:
                repl.rm_rf(p, r=args.recursive, f=args.force)
    except RemoteError as e:
        kernel.stop(f"{str(e).splitlines()[-1]}")


@arg("path", help="path of directories to create")
@line_magic
def mkdirs_magic(kernel, args):
    """Create all directories specified by the path, as needed.
Example:
    # create /a and subfolder /a/b on microcontroller
    %mkdirs a/b
"""
    with kernel.device as repl:
        repl.makedirs(args.path)
