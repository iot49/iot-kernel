from .magic import cell_magic
from subprocess import Popen, PIPE, STDOUT

# %%bash

@cell_magic
def bash_magic(kernel, _, code):
    """Pass cell to bash shell for evaluation

Example:
  %%bash
  printenv
    """
    with Popen(code, stdout=PIPE, shell=True, stderr=STDOUT, close_fds=True, executable='/bin/bash') as process:
        for line in iter(process.stdout.readline, b''):
            kernel.print(line.rstrip().decode('utf-8'))
