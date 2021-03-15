from .magic import line_magic, arg
from .micropip import install_pkg as upip_install
import subprocess, shlex, shutil, glob
import os, sys

def pip_install(kernel, package, target):
    # use system pip for intallation & perform some cleanup:
    # ['*.egg-info', '*.dist-info', '__pycache__']
    cmd = f"pip install {package} -t {target} --upgrade --no-deps"
    # run pip
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    kernel.print(f"{stdout.decode().strip()}\n")
    if process.returncode != 0:
        kernel.error(f"installation of {package} failed")
    # cleanup
    for p in ['*.egg-info', '*.dist-info', '__pycache__', 'ez_setup.py']:
        files = glob.glob(f"{target}/**/{p}", recursive=True)
        for f in files: shutil.rmtree(f)


@arg("-l", "--lib", default='lib', help="target directory within the project folder")
@arg("-p", "--project", default=None, help="project directory to install in")
@arg('packages', nargs="+", help="names (on PyPi) of packages to install")
@arg('operation', help="only supported value is 'install'")
@line_magic
def pip_magic(kernel, args):
    """Install packages from PyPi
Installs to project/lib, as set by -p and -l options.
The directory is created if it does not exist.

Examples:

    %pip install adafruit-io Adafruit-BME280
    %pip install -p my_pkg -l my_lib Adafruit-BME280
    """
    path = args.project
    if not path: path = kernel.device.projects[-1]
    path = os.path.join(path, args.lib)
    os.makedirs(path, exist_ok=True)
    for p in args.packages:
        pip_install(kernel, p, path)



@arg("-l", "--lib", default='lib', help="target directory within the project folder")
@arg("-p", "--project", default=None, help="project directory to install in")
@arg('packages', nargs="+", help="names (on PyPi) of packages to install")
@arg('operation', help="only supported value is 'install'")
@line_magic
def upip_magic(kernel, args):
    """Install MicroPython packages.
MicroPython uses a special package format that is not compatible with standard
`pip`. `%upip` first searches for packages on micropython.org
(see https://github.com/micropython/micropython-lib/ for available packages).
If that fails it searches PyPi.

Installs to project/lib, as set by -p and -l options.
The directory is created if it does not exist.

Examples:

    %upip install micropython-copy micropython-abc
    %upip install -p my_pkg -l my_lib collections

The install is delegated to "micropip.py" described at
https://github.com/peterhinch/micropython-samples/tree/master/micropip.
    """
    path = args.project
    if not path: path = kernel.device.projects[-1]
    path = os.path.abspath(os.path.join(path, args.lib))
    if not path.endswith('/'): path += '/'
    os.makedirs(path, exist_ok=True)
    for p in args.packages:
        if not p.startswith('micropython-'):
            p = 'micropython-' + p
        upip_install(p, path)
