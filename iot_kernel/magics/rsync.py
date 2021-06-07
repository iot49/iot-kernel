from .magic import line_magic, arg
import shlex


def _rsync(kernel, args, dry_run):
    with kernel.device as repl:
        # if not args.projects: args.projects = kernel.device.projects
        # if not args.implementation: args.implementation = repl.implementation
        try:
            repl.rsync(kernel.data_consumer,
                # projects=args.projects,
                # include_patterns=args.include_patterns,
                # exclude_patterns=args.exclude_patterns,
                # implementation=args.implementation,
                upload_only=args.upload_only,
                dry_run=dry_run)
        except (FileNotFoundError, ValueError) as e:
            kernel.error(e)


@line_magic
def rlist_magic(kernel, _):
    "List files on microcontroller"
    with kernel.device as repl:
        repl.rlist('/', kernel.data_consumer, show=True)

@arg('-p', '--projects', nargs='*', default=None, help="host projects, defaults to specifiation in hosts.py")
# @arg('--include_patterns', nargs='*', default=include_patterns, help="unix-style patterns of files to include")
# @arg('--exclude_patterns', nargs='*', default=exclude_patterns, help="unix-style patterns of files to exclude")
@arg('--implementation', default=None, help="sys.implementation.name of current device")
@arg('-u', '--upload_only', default=False, action='store_true', help="do not delete files on microcontroller but not on host")
@line_magic
def rdiff_magic(kernel, args):
    "Show differences between microcontroller and host directories"
    _rsync(kernel, args, True)


@arg('-p', '--projects', nargs='*', default=None, help="host projects, defaults to specifiation in hosts.py")
# @arg('--include_patterns', nargs='*', default=include_patterns, help="unix-style patterns of files to include")
# @arg('--exclude_patterns', nargs='*', default=exclude_patterns, help="unix-style patterns of files to exclude")
@arg('--implementation', default=None, help="sys.implementation.name of current device")
@arg('-u', '--upload_only', default=False, action='store_true', help="do not delete files on microcontroller but not on host")
@line_magic
def rsync_magic(kernel, args):
    """Synchronize microcontroller to host directories
Adds files on host but not on microcontroller, updates changed files,
and deletes files on microcontroller but not on hosts. Ignores files
starting with a period.

On the host, files are organized into projects (subfolders of $IOT49).
Projects for each microcontroller can be specified in `devices.py` or
with the `--projects` option.

%rsync synchronizes the time on the microcontroller to the host if
they differ by more than a few seconds to ensure correct updates.
"""
    _rsync(kernel, args, False)
