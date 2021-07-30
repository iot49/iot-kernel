from .magic import line_magic, cell_magic, arg

# %connect, %%connect

@arg('-q', '--quiet', action='store_true', help="no output (except errors)")
@arg('schemes', nargs='*', default=None, help="connection scheme")
@arg('hostname', help="hostname, uid, or url")
@line_magic
def connect_magic(kernel, args):
    """Connect to device by name, uid, or url

The device must be "registered" before a connection can be made. 
Execute the %discover magic to automatially register devices connected to
USB ports and devices advertised with broadcast messages.

Use the URL form to connect to a serial device (USB). E.g.

    %connect 'serial:///dev/serial2'

This will automatically register the device and connect to it.

Examples:
    # connect to a device by name defined in configuration file
    %connect device_name
    # connect to the serial port 
    # useful when the device is available by several means, e.g. serial and webrepl
    %connect my_esp32 serial
    # connect specifically to webrepl
    %connect my_esp32 wp
    %connect 37:ae:a4:39:84:34
    # connect to serial device at /dev/cu.usbserial-0160B5B8
    %connect 'serial:///dev/cu.usbserial-0160B5B8'
    # connect to a device via the mp protocol
    %connect 'mp://10.39.40.135:8266'
    """
    dev = kernel.device_registry.get_device(args.hostname, schemes=args.schemes)
    if dev:
        kernel.device = dev
        if not args.quiet:
            kernel.print(f"Connected to {dev.name} @ {dev.url}", 'grey', 'on_cyan')
        kernel.set_default_device(args.hostname)
    else:
        kernel.stop(f"Device not available: '{args.hostname}'")


@arg("-q", "--quiet", action="store_true", help="suppress terminal output")
@arg("--all", action="store_true", help="run code on all connected microcontrollers")
@arg('names', nargs='*', help="microcontroller names or UIDs")
@cell_magic
def connect_magic(kernel, args, code):
    """Generalization of %connect to run code on several devices sequentially
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
            # execute on currently connected device
            kernel.execute_cell(code)
