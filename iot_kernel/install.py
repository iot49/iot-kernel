import argparse
import json
import os
import sys
import shutil

from jupyter_client.kernelspec import KernelSpecManager   # pylint: disable=import-error
from IPython.utils.tempdir import TemporaryDirectory      # pylint: disable=import-error


def install(target_dir, kernel_name):
    """Install an iot kernel kernel with the given name in the target_dir."""
    if target_dir is None:
        #
        # use jupyter system path if the caller didn't specify
        #
        target_dir = os.path.join(SYSTEM_JUPYTER_PATH[0], "kernels", kernel_name)

    os.makedirs(target_dir, exist_ok=True)
    src_dir = os.path.join(os.path.dirname(__file__), "images")
    for file in [ "logo-32x32.png", "logo-64x64.png" ]:
        shutil.copy(os.path.join(src_dir, file), os.path.join(target_dir, file))

    #
    # create and write the kernel.json file
    #
    argv = [ sys.executable, "-m", "iot_kernel" ]
    if kernel_name != "iot_kernel":
        argv += [ "-k", kernel_name ]
    argv += [ "-f", "{connection_file}" ]
    kernel_spec = {
        "argv": argv,
        "display_name": "IoT",
        "language": "python",
    }

    with open(os.path.join(target_dir, "kernel.json"), "w") as ofd:
        json.dump(kernel_spec, ofd, indent=2, sort_keys=True)

    print(f"Installed {kernel_name} kernel in {target_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--kernel-name", type=str,
        help="kernel name", default="iot_kernel", dest="kernel_name"
    )
    args = parser.parse_args(argv)

    kernels = KernelSpecManager().find_kernel_specs()
    #
    # use existing target_dir; otherwise install alongside python3 or python
    #
    target_dir = kernels.get(args.kernel_name, None)
    if target_dir is None:
        for other in [ "python3", "python" ]:
            if other in kernels:
                target_dir = os.path.join(os.path.dirname(kernels[other]), args.kernel_name)
                break

    install(target_dir, args.kernel_name)


if __name__ == '__main__':
    main()
