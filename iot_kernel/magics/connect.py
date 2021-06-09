from .magic import cell_magic, arg

@arg("-q", "--quiet", action="store_true", help="suppress terminal output")
@arg("--all", action="store_true", help="run code on all connected microcontrollers")
@arg("--host", action="store_true", help="run code host (ipython)")
@arg('names', nargs='*', help="microcontroller names or UIDs")
@cell_magic
def connect_magic(kernel, args, code):
    """Evaluate code sequentially on named devices.
Examples:

  %%connect --host --all
  # evaluate on host and all connected microcontrollers
  import sys
  print(sys.platform)

  %%connect mcu1 mcu2
  # evaluate on named devics mcu1, mcu2
  print('hello world')
    """
    from .. import StopDoExecute
    def show(hostname):
        nonlocal args, kernel
        if not args.quiet:
            kernel.print(f"\n----- {hostname}\n", 'grey', 'on_cyan')
    if len(code) == 0: return
    if args.host:
        show("HOST")
        kernel.execute_ipython(code)
    if args.all:
        for d in kernel.device_registry.devices:
            kernel.device = d
            try:
                show(d.name)
                kernel.execute_cell(code)
            except StopDoExecute:
                pass
    else:
        if len(args.names) > 0:
            for hostname in args.names:
                try:
                    dev = kernel.device_registry.get_device(hostname)
                    if not dev:
                        kernel.error(f"No such device: {hostname}")
                        continue
                    kernel.device = dev
                    show(dev.name)
                    kernel.execute_cell(code)
                except StopDoExecute:
                    pass
        else:
            kernel.execute_cell(code)

@cell_magic
def host_magic(kernel, _, code):
    """Pass cell to host (cPython) for evaluation."""
    kernel.execute_ipython(code)

@cell_magic
def bash_magic(kernel, _, code):
    """Pass cell to bash shell for evaluation.

Example:
  %%bash
  printenv
    """
    from subprocess import Popen, PIPE, STDOUT
    with Popen(code, stdout=PIPE, shell=True, stderr=STDOUT, close_fds=True) as process:
        for line in iter(process.stdout.readline, b''):
            kernel.print(line.rstrip().decode('utf-8'))

@cell_magic
def kernel_magic(kernel, _, code):
    # exec code in kernel contect. Debugging only.
    exec(code)
