from .magic import cell_magic, arg
import paramiko


@arg("--password", type=str, default=None, help="password")
@arg("-p", "--port", type=int, default=22, help="suppress terminal output")
@arg('host', nargs=1, help="host address and login name: user@ssh.com")
@cell_magic
def ssh_magic(kernel, args, code):
    """Pass cell body to ssh.

Example:
    %%ssh -p 22 root@localhost
    printenv
"""
    user = 'root'
    host = args.host[0]
    if '@' in host:
        user, host = host.split('@', 1)
    port = args.port
    pwd = args.password or ''
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(host, port, user, pwd)
            _, stdout, stderr = ssh.exec_command(code)
            for line in stdout.readlines():
                kernel.print(line, end='')
            for line in stderr.readlines():
                kernel.error(line, end='')
        except Exception as e:
            kernel.error(f"***** {e}")


@arg('container', nargs=1, help="name of container to ssh into")
@cell_magic
def balena_magic(kernel, args, code):
    """Evaluate in named container using ssh.
Available only in Balena OS.

Example:
    %%balena gcc
    printenv
    ls /
    which gcc
"""
    # ssh into container name
    container = args.container[0]

    # 1) get container names
    container_names = {}
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('localhost', 22222, 'root', '')
        _, stdout, stderr = ssh.exec_command("balena-engine ps")
        for line in stdout.readlines()[1:]:
            key = name = line.split()[-1]
            if name.count('_') > 1:
                key = name.rsplit('_', 2)[0]
            container_names[key] = name

    # 2) lookup container
    container_name = container_names.get(container)
    if not container_name:
        kernel.error(f"No container with name '{container}'")
        kernel.error(f"Available containers: {', '.join(container_names.keys())}")
        return

    # 3) ssh into container
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('localhost', 22222, 'root', '')
        _, stdout, stderr = ssh.exec_command(f'balena-engine exec {container_name} bash -c "{code}"')
        for line in stdout.readlines():
            kernel.print(line, end='')
        for line in stderr.readlines():
            kernel.error(line, end='')
