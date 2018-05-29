"""
File transfer via SFTP and/or SCP.
"""

import os
import posixpath
import stat

from .util import log_in_process


class Transfer(object):

    def __init__(self, connection):
        self.connection = connection

    def get(self, remote, local=None, preserve_mode=True):
        sftp = self.connection.sftp()

        # Massage remote path
        if not remote:
            raise ValueError("Remote path must not be empty!")
        orig_remote = remote
        remote = posixpath.join(sftp.getcwd() or sftp.normalize("."), remote)

        # Massage local path:
        orig_local = local
        if not local:
            local = posixpath.basename(remote)
        local = os.path.abspath(local)

        sftp.get(remotepath=remote, localpath=local, callback=log_in_process)
        # Set mode to same as remote end
        # TODO: Push this down into SFTPClient sometime (requires backwards
        # incompat release.)
        if preserve_mode:
            remote_mode = sftp.stat(remote).st_mode
            mode = stat.S_IMODE(remote_mode)
            os.chmod(local, mode)
        # Return something useful
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )

    def put(self, local, remote=None, preserve_mode=True):
        sftp = self.connection.sftp()

        if not local:
            raise ValueError("Local path must not be empty!")

        # Massage remote path
        orig_remote = remote
        if not remote:
            remote = os.path.basename(local)
        prejoined_remote = remote
        remote = posixpath.join(sftp.getcwd() or sftp.normalize("."), remote)

        # Massage local path
        orig_local = local
        local = os.path.abspath(local)

        sftp.put(localpath=local, remotepath=remote, callback=log_in_process)
        # Set mode to same as local end
        # TODO: Push this down into SFTPClient sometime (requires backwards
        # incompat release.)
        if preserve_mode:
            local_mode = os.stat(local).st_mode
            mode = stat.S_IMODE(local_mode)
            sftp.chmod(remote, mode)
        # Return something useful
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )


class Result(object):

    def __init__(self, local, orig_local, remote, orig_remote, connection):
        self.local = local
        self.orig_local = orig_local
        self.remote = remote
        self.orig_remote = orig_remote
        self.connection = connection

