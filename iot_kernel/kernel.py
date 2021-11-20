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
from subprocess import Popen, PIPE, STDOUT
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
        # initial host is location of notebook
        # os.chdir(self.nb_conf.get("cwd", os.path.expanduser('~')))

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
        try:
            if not code.startswith('%%'):
                code = '%%connect\n' + code
            head, code = (code + '\n').split('\n', 1)
            magic, args = (head + ' ').split(' ', 1)
            if magic == '%%host':
                # pass directly to host
                return super().do_execute(code, silent, store_history, user_expressions, allow_stdin)
            method = CELL_MAGIC.get(magic[2:])
            if not method:
                self.error(f"Cell magic {magic} not defined")
            else:
                res = method[0](self, args, code)
                if res: return res
        # error handling is a mess ... could this be moved lower down?
        except StopDoExecute:
            pass
        except KeyboardInterrupt:
            self.error('Interrupted')
            with self.device as repl:
                repl.abort()
        except (SerialException, ConnectionResetError, ConnectionRefusedError) as e:
            # no exclusive access (serial) or connection reset (network)
            self.error(f"{self.device.name}: {e}", end="")
        except WebSocketException as e:
            self.error(f"Webrepl: {e}")
        except TimeoutError:
            self.error(f"Timeout connecting to {self.device.name} @ {self.device.url}")
        except RemoteError as e:
            self.error(str(e), end="")
        except Exception as ex:
            self.error(f"***** {ex}\n")
            self.print("\n\nDetails:\n")
            self.exception(ex, display_trace=True)
            time.sleep(0.5)
        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
                'text': ''
               }

    def execute_cell(self, code):
        # evaluate cell - code on MCU, magics in IoT Kernel
        # called from %%connect
        while code:
            code = code.strip()
            if code.startswith('%') or code.startswith('!'):
                split = code.split('\n', maxsplit=1)
                line = split[0]
                code = split[1] if len(split) > 1 else None
                self._execute_line_magic(line)
            else:
                # eval on mcu ...
                idx = min((code+'\n%').find('\n%'), (code+'\n!').find('\n!'))
                with self.device as repl:
                    repl.exec(code[:idx], data_consumer=self.data_consumer, timeout=1000000000)
                    code = code[idx:]

    def _execute_line_magic(self, line):
        if line.startswith('!'):
            logger.debug(f"shell escape: {line}")
            with Popen(line[1:], stdout=PIPE, shell=True, stderr=STDOUT, close_fds=True, executable='/bin/bash') as process:
                for line in iter(process.stdout.readline, b''):
                    self.print(line.rstrip().decode('utf-8'))
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
            self.error(f"Line magic {name} not defined")

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
        if len(color) > 0 and len(text.strip()) > 0:
            text = colored(str(text), *color)
        if end: text += end
        if not len(text): return
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
