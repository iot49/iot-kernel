from .magic import cell_magic, arg
import paramiko, time


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
    ssh_exec(kernel, host, port, user, pwd, code)


@arg('container', nargs=1, help="name of container to ssh into")
@cell_magic
def service_magic(kernel, args, code):
    """Evaluate in named container using ssh.
This specifically supports balena apps.

Example:
    %%service gcc
    printenv
    ls /
    which gcc
"""
    # ssh into container name
    container = args.container[0]

    if container == 'host':
        ssh_exec(kernel, '172.17.0.1', 22222, 'root', '', code)
        return

    # 1) get container names
    container_names = {}
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 'localhost' works only for network-mode: host, not bridge; 172.17.0.1 works always (?)
        # ssh.connect('localhost', 22222, 'root', '')
        ssh.connect('172.17.0.1', 22222, 'root', '')
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
    cmd = f"balena-engine exec {container_name} bash -c '{code}'"
    ssh_exec(kernel, '172.17.0.1', 22222, 'root', '', cmd)


def ssh_exec(kernel, host, port, user, pwd, cmd):
    """exec command on host, print results"""
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, user, pwd)
        channel = ssh.get_transport().open_session()
        channel.exec_command(cmd)
        while True:
            if channel.exit_status_ready():
                break
            buf = b''
            while channel.recv_ready():
                buf += channel.recv(1)
            if len(buf):
                kernel.print(buf.decode(), end='')
            buf = b''
            while channel.recv_stderr_ready():
                buf += channel.recv_stderr(1)
            if len(buf):
                kernel.error(buf.decode(), end='')
            time.sleep(0.001)

