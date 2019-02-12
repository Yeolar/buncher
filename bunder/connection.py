import getpass
import os

from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.config import SSHConfig

from .transfer import Transfer


class Connection(object):

    host = None
    original_host = None
    user = None
    port = None
    ssh_config = None
    connect_timeout = None
    connect_kwargs = None
    client = None
    transport = None
    _sftp = None

    def __init__(
        self,
        host,
        user=None,
        port=None,
        connect_timeout=None,
        connect_kwargs=None,
    ):
        shorthand = self.derive_shorthand(host)
        host = shorthand['host']
        err = (
            'You supplied the {} via both shorthand and kwarg! Please pick one.'  # noqa
        )
        if shorthand['user'] is not None:
            if user is not None:
                raise ValueError(err.format('user'))
            user = shorthand['user']
        if shorthand['port'] is not None:
            if port is not None:
                raise ValueError(err.format('port'))
            port = shorthand['port']

        self.ssh_config = self.load_ssh_config(host)

        self.original_host = host
        self.host = host
        if 'hostname' in self.ssh_config:
            self.host = self.ssh_config['hostname']

        self.user = user or self.ssh_config.get('user', getpass.getuser())
        self.port = port or int(self.ssh_config.get('port', '22'))

        if connect_timeout is None:
            connect_timeout = self.ssh_config.get('connecttimeout')
        if connect_timeout is not None:
            connect_timeout = int(connect_timeout)
        self.connect_timeout = connect_timeout

        if connect_kwargs is None:
            connect_kwargs = {}
        if 'identityfile' in self.ssh_config:
            connect_kwargs.setdefault('key_filename', [])
            connect_kwargs['key_filename'].extend(
                self.ssh_config['identityfile']
            )
        self.connect_kwargs = connect_kwargs

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        self.client = client

        self.transport = None

    def derive_shorthand(self, host_string):
        user_hostport = host_string.rsplit('@', 1)
        hostport = user_hostport.pop()
        user = user_hostport[0] if user_hostport and user_hostport[0] else None

        # IPv6: can't reliably tell where addr ends and port begins, so don't
        # try (and don't bother adding special syntax either, user should avoid
        # this situation by using port=).
        if hostport.count(':') > 1:
            host = hostport
            port = None
        # IPv4: can split on ':' reliably.
        else:
            host_port = hostport.rsplit(':', 1)
            host = host_port.pop(0) or None
            port = host_port[0] if host_port and host_port[0] else None

        if port is not None:
            port = int(port)

        return {'user': user, 'host': host, 'port': port}

    def load_ssh_config(self, host):
        ssh_config = SSHConfig()

        for path in (
            os.path.expanduser('~/.ssh/config'),
            '/etc/ssh/ssh_config'
        ):
            if os.path.isfile(path):
                with open(path) as fd:
                    ssh_config.parse(fd)

        return ssh_config.lookup(host)

    @property
    def is_connected(self):
        return self.transport.active if self.transport else False

    def open(self):
        if self.is_connected:
            return
        err = (
            "Refusing to be ambiguous: connect() kwarg '{}' was given both via regular arg and via connect_kwargs!"  # noqa
        )
        for key in 'hostname port username'.split():
            if key in self.connect_kwargs:
                raise ValueError(err.format(key))
        if (
            'timeout' in self.connect_kwargs
            and self.connect_timeout is not None
        ):
            raise ValueError(err.format('timeout'))
        # No conflicts -> merge 'em together
        kwargs = dict(
            self.connect_kwargs,
            username=self.user,
            hostname=self.host,
            port=self.port,
        )
        if self.connect_timeout:
            kwargs['timeout'] = self.connect_timeout
        if 'key_filename' in kwargs and not kwargs['key_filename']:
            del kwargs['key_filename']

        self.client.connect(**kwargs)
        self.transport = self.client.get_transport()

    def close(self):
        if self.is_connected:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def run(self, command, **kwargs):
        self.open()
        return self.client.exec_command(command, **kwargs)

    def sudo(self, command, **kwargs):
        self.open()
        return self.client.exec_command('sudo -S -p ' + command, **kwargs)

    def local(self, command, **kwargs):
        return subprocess.call(command, shell=True, **kwargs)

    def sftp(self):
        self.open()
        if self._sftp is None:
            self._sftp = self.client.open_sftp()
        return self._sftp

    def get(self, *args, **kwargs):
        return Transfer(self).get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return Transfer(self).put(*args, **kwargs)

