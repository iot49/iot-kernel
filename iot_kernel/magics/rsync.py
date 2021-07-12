from .magic import line_magic, arg
import shlex


def _rsync(kernel, args, dry_run):
    with kernel.device as repl:
        try:
            repl.rsync(kernel.data_consumer,
                upload_only=args.upload_only,
                dry_run=dry_run)
        except (FileNotFoundError, ValueError) as e:
            kernel.error(e)


@line_magic
def rlist_magic(kernel, _):
    "List files on microcontroller"
    with kernel.device as repl:
        repl.rlist('/', kernel.data_consumer, show=True)

@arg('-u', '--upload_only', default=False, action='store_true', help="do not delete files on microcontroller that are not also on host")
@line_magic
def rdiff_magic(kernel, args):
    "Show differences between microcontroller and host directories"
    _rsync(kernel, args, True)


@arg('-u', '--upload_only', default=False, action='store_true', help="do not delete files on microcontroller that are not also on host")
@line_magic
def rsync_magic(kernel, args):
    """Synchronize microcontroller to host directories
Adds files on host but not on microcontroller, updates changed files,
and deletes files on microcontroller but not on hosts. Ignores files
starting with a period.

The list of files to upload is taken from the yaml device configuration.

%rsync synchronizes the time on the microcontroller to the host if
they differ by more than a few seconds to ensure correct updates.
"""
    _rsync(kernel, args, False)
