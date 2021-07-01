import os
import re
import setuptools
from iot_kernel import version

install_requires = [
    "ipykernel==5.5.5",
    "iot-device>=0.5.6",
    "argparse",
    "paramiko",
    "ipynbname",
]

setuptools.setup(
    name="iot-kernel",
    version=version.__version__,
    packages=[ 'iot_kernel', 'iot_kernel.magics' ],
    author="Bernhard Boser",
    description="Jupyter Kernel for MicroPython",
    long_description="Jupyter Kernel for MicroPython",
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="MicroPython,Repl",
    url="https://github.com/iot49/iot-kernel",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    install_requires=install_requires,
    include_package_data=True,
    python_requires='>=3.7',
    zip_safe = True,
)


# make publish

# pip install iot-kernel -U --no-cache-dir
# verify that latest version is installed! (pip list); usually need to run pip install twice???
# python -m iot_kernel.install
