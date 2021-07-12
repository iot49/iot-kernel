from .magic import line_magic, arg
from .micropip import install_pkg as upip_install
from iot_device import Env
import subprocess, shlex, shutil, glob
import os, sys

def pip_install(kernel, package, target):
    # use system pip for intallation & perform some cleanup:
    # ['*.egg-info', '*.dist-info', '__pycache__']
    # ??? --no-dependencies ???
    cmd = f"pip install {package} -t {target} --upgrade --no-deps"
    # run pip
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = process.communicate()
    kernel.print(f"{stdout.decode().strip()}\n")
    if process.returncode != 0:
        kernel.error(f"installation of {package} failed")
    # cleanup
    for p in ['*.egg-info', '*.dist-info', '__pycache__', 'ez_setup.py']:
        files = glob.glob(f"{target}/**/{p}", recursive=True)
        for f in files: shutil.rmtree(f)


@arg("-t", "--target", default="libs", help="target directory relative to $IOT_PROJECTS")
@arg('packages', nargs="+", help="names (on PyPi) of packages to install")
@arg('operation', help="only supported value is 'install'")
@line_magic
def pip_magic(kernel, args):
    """Install packages from PyPi
The directory is created if it does not exist.

Examples:

    %pip install adafruit-io Adafruit-BME280
    %pip install -t my_project/code/lib Adafruit-BME280
    """
    for package in args.packages:
        target = args.target
        target = os.path.join(Env.iot_projects(), target)
        os.makedirs(target, exist_ok=True)
        pip_install(kernel, package, target)


@arg("-t", "--target", default="libs", help="target directory relative to $IOT_PROJECTS")
@arg('packages', nargs="+", help="names of packages to install")
@arg('operation', help="only supported value is 'install'")
@line_magic
def upip_magic(kernel, args):
    """Install MicroPython packages.
MicroPython uses a special package format that is not compatible with standard
`pip`. `%upip` first searches for packages on micropython.org
(see https://github.com/micropython/micropython-lib/ for available packages).
If that fails it searches PyPi.
The directory is created if it does not exist.

Examples:

    %upip install micropython-copy micropython-abc

The install is delegated to "micropip.py" described at
https://github.com/peterhinch/micropython-samples/tree/master/micropip.
    """
    target = os.path.join(Env.iot_projects(), args.target)
    if not target.endswith('/'): target += '/'
    os.makedirs(target, exist_ok=True)
    for p in args.packages:
        if not p.startswith('micropython-'):
            p = 'micropython-' + p
        upip_install(p, target)
