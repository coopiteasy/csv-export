# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# Heavily inspired from:
# https://github.com/OCA/storage/blob/12.0/storage_backend_sftp/components/sftp_adapter.py  # noqa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import errno
import os
from contextlib import contextmanager

import paramiko
from openerp import _
from openerp.exceptions import UserError


def sftp_mkdirs(client, path, mode=511):
    try:
        client.mkdir(path, mode)
    except IOError as e:
        if e.errno == errno.ENOENT and path:
            sftp_mkdirs(client, os.path.dirname(path), mode=mode)
            client.mkdir(path, mode)
        else:
            raise  # pragma: no cover


@contextmanager
def sftp(collection):
    transport = paramiko.Transport((collection.hostname, collection.port))

    try:
        transport.start_client()
    except paramiko.SSHException:
        raise UserError(_("""SSH negotiation failed"""))

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if not agent_keys:
        raise UserError(_("Could not load RSA key from ssh agent"))
    transport.auth_publickey(collection.username, agent_keys[0])
    if not transport.is_authenticated():
        raise UserError(_("""Could not authenticate to sftp server"""))
    client = paramiko.SFTPClient.from_transport(transport)
    yield client
    transport.close()


class SftpAdapter:
    def __init__(self, username, hostname, port=22):
        self.username = username
        self.hostname = hostname
        self.port = port

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
