# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# Heavily inspired from:
# https://github.com/OCA/storage/blob/12.0/storage_backend_sftp/components/sftp_adapter.py  # noqa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import errno
import logging
import os
from binascii import hexlify
from contextlib import contextmanager

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError as err:
    _logger.debug(err)


def agent_auth(transport, username):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent.
    """

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if not agent_keys:
        raise UserError(_("Could not load private key from agent"))

    for key in agent_keys:
        _logger.info("Trying ssh-agent key %s" % hexlify(key.get_fingerprint()))
        try:
            transport.auth_publickey(username, key)
            if transport.is_authenticated():
                return
        except paramiko.SSHException:
            _logger.info("... failed.")

    raise UserError(_("""Could not authenticate to sftp server"""))


def key_file_auth(transport, key_file, username):
    key_file = os.path.expanduser(key_file)

    for pkey_class in (
        paramiko.RSAKey,
        paramiko.Ed25519Key,
        paramiko.DSSKey,
        paramiko.ECDSAKey,
    ):
        try:
            _logger.info("Try loading key with %s" % str(pkey_class))
            key = pkey_class.from_private_key_file(key_file)
            transport.auth_publickey(username, key)
            if transport.is_authenticated():
                return
        except paramiko.SSHException:
            _logger.info("... failed")

    raise UserError(_("""Could not authenticate to sftp server"""))


@contextmanager
def sftp(collection):
    transport = paramiko.Transport((collection.hostname, collection.port))

    try:
        transport.start_client(timeout=10)
    except paramiko.SSHException:
        raise UserError(_("""SSH negotiation failed"""))

    if collection.auth_method == "agent":
        agent_auth(transport, collection.username)
    elif collection.auth_method == "key_file":
        # try t.connect(username=SSH_USERNAME,pkey=pk) ?
        key_file_auth(transport, collection.key_file, collection.username)
    else:
        raise NotImplementedError

    client = paramiko.SFTPClient.from_transport(transport)
    yield client
    transport.close()


def sftp_mkdirs(client, path, mode=511):
    try:
        client.mkdir(path, mode)
    except IOError as e:
        if e.errno == errno.ENOENT and path:
            sftp_mkdirs(client, os.path.dirname(path), mode=mode)
            client.mkdir(path, mode)
        else:
            raise  # pragma: no cover


class SftpAdapter:
    def __init__(self, username, hostname, port=22, auth_method="agent", key_file=None):
        self.username = username
        self.hostname = hostname
        self.port = port
        self.auth_method = auth_method
        self.key_file = key_file

    def add(self, path, data):
        with sftp(self) as client:
            dirname = os.path.dirname(path)
            if dirname:
                try:
                    client.stat(dirname)
                except IOError as e:
                    if e.errno == errno.ENOENT:
                        sftp_mkdirs(client, dirname)
                    else:
                        raise  # pragma: no cover
            remote_file = client.open(path, "w+b")
            remote_file.write(data)
            remote_file.close()

    def get(self, path):
        with sftp(self) as client:
            file_data = client.open(path, "rb")
            data = file_data.read()
        return data

    def list(self, path):
        with sftp(self) as client:
            try:
                return client.listdir(path)
            except IOError as e:
                if e.errno == errno.ENOENT:
                    # The path do not exist return an empty list
                    return []
                else:
                    raise  # pragma: no cover

    def delete(self, path):
        with sftp(self) as client:
            return client.remove(path)
