from iot_device import RemoteError
from .magic import line_magic, arg
import serial.tools.list_ports


@arg('-v', '--verbose', action='store_true', help="show uid")
@arg('-a', '--all', action='store_true', help="list all devices connected to USB ports")
@line_magic
def discover_magic(kernel, args):
    "Discover available devices"
    if args.all:
        for port in serial.tools.list_ports.comports():
            kernel.print(port.device)
            for a in ["hwid", "manufacturer", "product", "interface"]:
                if getattr(port, a):
                    kernel.print(f"  {a:12} {getattr(port, a)}")
            kernel.print()
    else:
        devices = kernel.device_registry.devices
        n_width = max([len(dev.name) for dev in devices], default=0)
        u_width = max([len(dev.url)  for dev in devices], default=0)
        if len(devices):
            for dev in devices:
                uid = dev.uid if args.verbose else ''
                kernel.print(f"{dev.name:{n_width}}  {dev.url:{u_width}}  {uid}")
        else:
            kernel.print("No devices available")


@arg('-q', '--quiet', action='store_true', help="no output (except errors)")
@arg('schemes', nargs='*', default=None, help="connection scheme")
@arg('hostname', help="hostname, uid, or url")
@line_magic
def connect_magic(kernel, args):
    """Connect to device

Examples:
    %connect my_esp32 serial
    %connect my_esp32 mp
    %connect 37:ae:a4:39:84:34
    %connect 'serial:///dev/cu.usbserial-0160B5B8'
    %connect 'mp://10.39.40.135:8266'

Note: device must be registered for connect to work (see %discover and %register).
    """
    dev = kernel.device_registry.get_device(args.hostname, schemes=args.schemes)
    if dev:
        kernel.device = dev
        if not args.quiet:
            kernel.print(f"Connected to {dev.name} @ {dev.url}", 'grey', 'on_cyan')
        kernel.set_default_device(args.hostname)
    else:
        kernel.stop(f"Device not available: '{args.hostname}'")


@arg('url', help="register device by url")
@line_magic
def register_magic(kernel, args):
    """Register device

    Examples:
        %register 'serial:///dev/cu.usbserial-0160B5B8'
        %register 'mp://10.39.40.135:8266'
    """
    try:
        kernel.device_registry.register(args.url)
    except ValueError:
        kernel.stop("invalid url")
    except RemoteError as e:
        kernel.stop(e)


@arg('name', help="unregister device")
@line_magic
def unregister_magic(kernel, args):
    """Unregister device

    Examples:
        %unregister my_esp32
        %unregister 30:ae:a4:32:84:34
        %unregister 'serial:///dev/cu.usbserial-0160B5B8'
    """
    try:
        kernel.device_registry.unregister(args.name)
    except ValueError as e:
        kernel.stop(e)
