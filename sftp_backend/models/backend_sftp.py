# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# Heavily inspired from:
# https://github.com/OCA/storage/blob/12.0/storage_backend_sftp/components/sftp_adapter.py  # noqa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from os.path import join

from openerp import api, fields, models

from .sftp_adapter import SftpAdapter

_logger = logging.getLogger(__name__)


class SFTPBackend(models.AbstractModel):
    _name = "backend.sftp"

    name = fields.Char(string="Name", compute="_compute_name")
    username = fields.Char(
        string="Username",
        required=True,
        help="Username to connect to sftp server",
    )
    host = fields.Char(string="SFTP Host", required=True)
    port = fields.Integer(string="Port", required=True, default=22)
    path = fields.Char(string="Path", required=True)
    auth_method = fields.Selection(
        string="Authentication Method",
        selection=[("rsa_key", "Private RSA key")],
        default="rsa_key",
        required=True,
    )
    active = fields.Boolean(string="Active", default=True)

    @api.multi
    def _compute_name(self):
        for backend in self:
            if backend.username and backend.host:
                backend.name = "{}@{}:{}".format(
                    backend.username, backend.host, backend.port
                )

    @api.multi
    def add(self, filename, data):
        for backend in self:
            adapter = SftpAdapter(backend.username, backend.host, backend.port)
            path = join(backend.path, filename)
            _logger.info("{} - add to {}".format(self.name, path))
            adapter.add(path, data)

    @api.multi
    def get(self, filename):
        self.ensure_one()
        adapter = SftpAdapter(self.username, self.host, self.port)
        path = join(self.path, filename)
        _logger.info("{} - get {}".format(self.name, path))
        return adapter.get(path)

    def list(self, path):
        self.ensure_one()
        adapter = SftpAdapter(self.username, self.host, self.port)
        _logger.info("{} - list {}".format(self.name, path))
        return adapter.get(path)

    def delete(self, filename):
        for backend in self:
            adapter = SftpAdapter(backend.username, backend.host, backend.port)
            path = join(backend.path, filename)
            _logger.info("{} - delete {}".format(self.name, path))
            adapter.delete(path)
