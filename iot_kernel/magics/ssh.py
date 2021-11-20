from .magic import cell_magic, arg
import paramiko, time, os


@arg("--out", type=str, default=None, help="store stdout in shell environment variable")
@arg("--err", type=str, default=None, help="store stderr in shell environment variable")
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
    ssh_exec(kernel, host, port, user, pwd, code, args.out, args.err)


@arg("-u", "--user", type=str, default="iot", help="Username or UID (format: <name|uid>[:<group|gid>])")
@arg("--out", type=str, default=None, help="store stdout in shell environment variable")
@arg("--err", type=str, default=None, help="store stderr in shell environment variable")
@arg('container', nargs=1, help="name of container to ssh into")
@cell_magic
def service_magic(kernel, args, code):
    """Send code to bash in named container for execution
This specifically supports docker/balena apps.

Before running the instructions, the file .init_${container}.sh
is sourced, if it exists. ${container} is the name of the service given.

Note: Code submitted to bash for evaluation. Execution fails if 
      container does not have bash installed.

Example:
    %%service esp-idf
    printenv | grep BALENA_SERVICE_NAME
    which idf.py

    # lookup mdns address and assign to $OUT
    %%service host --out OUT
    ping -c 2 pi4server.local | awk -F"[()]" '{print $2}'
"""
    # ssh into container name
    service = args.container[0]

    if service == 'host':
        ssh_exec(kernel, '172.17.0.1', 22222, 'root', '', code, args.out, args.err)
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
    container_name = container_names.get(service)
    if not container_name:
        kernel.error(f"No container with name '{service}'")
        kernel.error(f"Available containers: host, {', '.join(container_names.keys())}")
        return

    # 3) ssh into container
    c = \
"""cd $HOME
if [ -f .init_{}.sh ]; then
    . .init_{}.sh
fi
""".format(service, service) + code
    cmd = f"balena-engine exec -u {args.user} {container_name} bash -c '{c}'"
    ssh_exec(kernel, '172.17.0.1', 22222, 'root', '', cmd, args.out, args.err)


def ssh_exec(kernel, host, port, user, pwd, cmd, out, err):
    """exec command on host, print results"""
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, user, pwd)
        channel = ssh.get_transport().open_session()
        channel.exec_command(cmd)
        # fix for truncated output?
        last = time.monotonic()
        # stdout and stderr
        stdout = b''
        stderr = b''
        while (time.monotonic()-last) < 1:
            if channel.exit_status_ready():
                continue
            buf = b''
            while channel.recv_ready():
                buf += channel.recv(1)
            if len(buf):
                stdout += buf
                if not out: kernel.print(buf.decode(), end='')
            buf = b''
            while channel.recv_stderr_ready():
                buf += channel.recv_stderr(1)
            if len(buf):
                stderr += buf
                if not err: kernel.error(buf.decode(), end='')
            last = time.monotonic()
            time.sleep(0.01)
        if out: os.environ[out] = stdout.decode()
        if err: os.environ[err] = stderr.decode()
