from .magic import cell_magic, arg
import paramiko, time, os, select


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
@arg("-s", "--shell", type=str, default="/bin/bash", help="Shell to use in target container. Default: /bin/bash")
@arg("--out", type=str, default=None, help="store stdout in shell environment variable")
@arg("--err", type=str, default=None, help="store stderr in shell environment variable")
@arg('container', nargs=1, help="name of container to ssh into")
@cell_magic
def service_magic(kernel, args, code):
    """Send code to bash in named container for execution
This specifically supports docker/balena apps.

Before running the instructions, the file .init_${container}.sh
is sourced, if it exists. ${container} is the name of the service given.

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
            name = line.split()[-1]
            key = name.rsplit('_')[0]
            if key == "balena": key = "balena-supervisor"
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
    cmd = f"balena-engine exec -u {args.user} {container_name} {args.shell} -c '{c}'"
    ssh_exec(kernel, '172.17.0.1', 22222, 'root', '', cmd, args.out, args.err)


def ssh_exec(kernel, host, port, user, pwd, cmd, out, err):
    """exec command on host, print results"""
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, user, pwd)
        ssh_io(kernel, ssh, cmd, 1, out, err)
        return


# https://stackoverflow.com/questions/23504126/do-you-have-to-check-exit-status-ready-if-you-are-going-to-check-recv-ready
def ssh_io(kernel, ssh, cmd, timeout=1, out=None, err=None):
    # one channel per command
    stdin, stdout, stderr = ssh.exec_command(cmd) 
    # get the shared channel for stdout/stderr/stdin
    channel = stdout.channel

    # we do not need stdin.
    stdin.close()                 
    # indicate that we're not going to write to that channel anymore
    channel.shutdown_write()      

    # read stdout/stderr in order to prevent read block hangs
    data = stdout.channel.recv(len(stdout.channel.in_buffer)).decode()
    if out:
        out.append(data)
    else:
        kernel.print(data, end='')
    
    # chunked read to prevent stalls
    while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready(): 
        # stop if channel was closed prematurely, and there is no data in the buffers.
        got_chunk = False
        readq, _, _ = select.select([stdout.channel], [], [], timeout)
        for c in readq:
            if c.recv_ready():
                data = stdout.channel.recv(len(c.in_buffer)).decode()
                if out:
                    out.append(data)
                else:
                    kernel.print(data, end='')
                got_chunk = True
            if c.recv_stderr_ready(): 
                # make sure to read stderr to prevent stall    
                data = stderr.channel.recv_stderr(len(c.in_stderr_buffer))  
                if err:
                    err.append(data)
                else:
                    kernel.error(data, end='')
                got_chunk = True  
        '''
        1) make sure that there are at least 2 cycles with no data in the input buffers in order to not exit too early (i.e. cat on a >200k file).
        2) if no data arrived in the last loop, check if we already received the exit code
        3) check if input buffers are empty
        4) exit the loop
        '''
        if not got_chunk \
            and stdout.channel.exit_status_ready() \
            and not stderr.channel.recv_stderr_ready() \
            and not stdout.channel.recv_ready(): 
            # indicate that we're not going to read from this channel anymore
            stdout.channel.shutdown_read()  
            # close the channel
            stdout.channel.close()
            break    # exit as remote side is finished

    # close all the pseudofiles
    stdout.close()
    stderr.close()
