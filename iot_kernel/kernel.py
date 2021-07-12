from iot_device import DeviceRegistry
from iot_device import RemoteError
import iot_device

from .nb_conf import NbConf
from .kernel_logger import logger
from .magics.magic import LINE_MAGIC, CELL_MAGIC
from .version import __version__

from serial import SerialException
from websocket import WebSocketException
from ipykernel.ipkernel import IPythonKernel
from termcolor import colored
import traceback, re, os, time, logging


class StopDoExecute(Exception):
    pass

class IoTKernel(IPythonKernel):
    """
    IoT kernel evaluates code on (remote) IoT devices.
    """

    implementation = 'iot-kernel'
    implementation_version = __version__
    language_info = {
        'name': 'python',
        'version': '3',
        'mimetype': 'text/x-python',
        'file_extension': '.py',
        'pygments_lexer': 'python3',
        'codemirror_mode': {'name': 'python', 'version': 3},
    }
    banner = "IoT Kernel - Python on a Microcontroller"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"libraries: iot_kernel {__version__}, {iot_device.__version__}")
        self.__device_registry = DeviceRegistry()
        # current device
        self.__device = None
        # set initial host cwd
        os.chdir(self.nb_conf.get("cwd", os.path.expanduser('~')))

    @property
    def device_registry(self):
        return self.__device_registry

    @property
    def nb_conf(self):
        return NbConf

    @property
    def device(self):
        if not self.__device:
            self.__device = self.device_registry.get_device(self.nb_conf.get("device"))
            if self.__device:
                self.print(f"Connected to {self.__device.name} @ {self.__device.url}", 'grey', 'on_cyan')
            else:
                raise RemoteError("no device connected")
        return self.__device

    @device.setter
    def device(self, dev):
        self.__device = dev

    def set_default_device(self, uid_or_name_or_path):
        self.nb_conf.set("device", uid_or_name_or_path)

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.silent = silent
        self.store_history = store_history
        self.user_expressions = user_expressions
        self.allow_stdin = allow_stdin
        try:
            # transform all code sections into %%name ... + body
            for cell in ('connect\n' + code).split('\n%%'):
                self.__execute_section('%%' + cell)
        except StopDoExecute:
            pass
        except KeyboardInterrupt:
            self.error('Interrupted')
            with self.device as repl:
                repl.abort()
        except (SerialException, ConnectionResetError, ConnectionRefusedError) as e:
            # no exclusive access (serial) or connection reset (network)
            self.error(f"{self.device.name}: {e}")
        except WebSocketException as e:
            self.error(f"Webrepl: {e}")
        except TimeoutError:
            self.error(f"Timeout connecting to {self.device.name} @ {self.device.url}")
        except RemoteError as e:
            self.error(str(e))
            logger.exception(str(e))
        except Exception as ex:
            self.error(f"***** {ex}\n")
            self.print("\n\nDetails:\n")
            self.exception(ex, display_trace=True)
            time.sleep(0.5)
        return {
            'status': 'ok',
            'execution_count': self.execution_count,
        }

    def __execute_section(self, cell):
        # handle cell (starts with %%name ...)
        head, code = (cell + '\n').split('\n', 1)
        code = code.strip()
        magic, args = (head + ' ').split(' ', 1)
        args = args.strip()
        logger.debug(f"cell_magic {magic} args={args} code={code}")
        method = CELL_MAGIC.get(magic[2:])
        if method:
            method[0](self, args, code)
        else:
            # let ipython handle the cell magic
            return self.execute_ipython(cell)

    def execute_cell(self, code):
        # evaluate IoT Python cell
        while code:
            code = code.strip()
            if code.startswith('%') or code.startswith('!'):
                split = code.split('\n', maxsplit=1)
                line = split[0]
                code = split[1] if len(split) > 1 else None
                self.__line_magic(line)
            else:
                # eval on mcu ...
                idx = min((code+'\n%').find('\n%'), (code+'\n!').find('\n!'))
                with self.device as repl:
                    repl.exec(code[:idx], self.data_consumer)
                    code = code[idx:]

    def __line_magic(self, line):
        if line.startswith('!'):
            logger.debug(f"shell escape: {line}")
            self.execute_ipython(line)
            return
        m = re.match(r'%([^ ]*)( .*)?', line)
        if not m:
            self.error(f"Syntax error: '{line.encode()}'\n")
            return
        name = m.group(1)
        rest = m.group(2)
        rest = (rest or '').strip()
        method = LINE_MAGIC.get(name)
        logger.debug(f"line_magic name={name} rest={rest} method={name}")
        if method:
            method[0](self, rest)
        else:
            # pass line magic to ipython
            logger.debug(f"pass to IPython: {line}")
            self.execute_ipython(line)

    def execute_ipython(self, code):
        # evaluate code with IPython
        super().do_execute(code, self.silent, self.store_history, self.user_expressions, self.allow_stdin)

    def data_consumer(self, data:bytes):
        if not data or self.silent: return
        if isinstance(data, bytes):
            try:
                data = data.decode()
            except UnicodeDecodeError:
                pass
        data = str(data)
        # Remove '\r' - output on mac at least comes garbled otherwise
        # Probably because \r\n don't always arrive from micropython in same bytes object
        data = data.replace('\r', '')
        data = data.replace('\x04', '')
        if data: self.print(data, end='')

    def print(self, text="", *color, end='\n'):
        text = colored(str(text), *color)
        if end: text += end
        stream_content = {'name': 'stdout', 'text': text}
        self.send_response(self.iopub_socket, 'stream', stream_content)

    def error(self, text="", *color, end='\n'):
        text = str(text)
        if not len(text.strip()): return
        text = colored(str(text), *color)
        if end: text += end
        stream_content = {'name': 'stderr', 'text': text}
        self.send_response(self.iopub_socket, 'stream', stream_content)

    def stop(self, text=""):
        # abort do_execute
        if text:
            self.error(text)
        raise StopDoExecute()

    def exception(self, ex, display_trace=False):
        self.error(f"kernel.exception: {type(ex).__name__}: {ex}\n")
        if display_trace:
            self.error(f"\n{traceback.format_exc()}\n")
