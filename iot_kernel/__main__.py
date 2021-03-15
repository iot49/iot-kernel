from ipykernel.kernelapp import IPKernelApp
from .kernel import IoTKernel

IPKernelApp.launch_instance(kernel_class=IoTKernel)
