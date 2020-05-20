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


class SFTPBackend(models.Model):
    _name = "backend.sftp"

    name = fields.Char(string="Name", compute="_compute_name")
    username = fields.Char(
        string="Username",
        required=True,
        help="Username to connect to sftp server",
    )
    host = fields.Char(string="SFTP Host", required=True)
    port = fields.Integer(string="Port", required=True, default=22)
    auth_method = fields.Selection(
        string="Authentication Method",
        selection=[("rsa_key", "Private RSA key")],
        default="rsa_key",
        required=True,
    )
    active = fields.Boolean(string="Active", default=True)
    export_ids = fields.One2many(
        comodel_name="backend.sftp.export",
        inverse_name="backend_id",
        string="Exports",
    )

    @api.multi
    def _compute_name(self):
        for backend in self:
            if backend.username and backend.host and backend.port:
                backend.name = "{}@{}:{}".format(
                    backend.username, backend.host, backend.port
                )
            else:
                backend.name = False


class BackendSFTPLine(models.Model):
    _name = "backend.sftp.export"

    backend_id = fields.Many2one(
        comodel_name="backend.sftp", string="Backend", required=True
    )
    path = fields.Char(string="Path", required=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        required=True,
        domain=[
            ("model", "ilike", "csv.export.%"),
            ("model", "!=", "csv.export.base"),
        ],
        help="""only csv.export.* models """,
    )
    active = fields.Boolean(string="Active", default=True)

    @api.multi
    def add(self, filename, data):
        for export in self:
            backend = export.backend_id
            adapter = SftpAdapter(backend.username, backend.host, backend.port)
            path = join(export.path, filename)
            _logger.info("{} - add to {}".format(backend.name, path))
            adapter.add(path, data)

    @api.multi
    def get(self, filename):
        self.ensure_one()
        backend = self.backend_id
        adapter = SftpAdapter(backend.username, backend.host, backend.port)
        path = join(self.path, filename)
        _logger.info("{} - get {}".format(self.name, path))
        return adapter.get(path)

    def list(self, path):
        self.ensure_one()
        backend = self.backend_id
        adapter = SftpAdapter(backend.username, backend.host, backend.port)
        _logger.info("{} - list {}".format(self.name, path))
        return adapter.get(path)

    def delete(self, filename):
        for export in self:
            backend = export.backend_id
            adapter = SftpAdapter(backend.username, backend.host, backend.port)
            path = join(export.path, filename)
            _logger.info("{} - delete {}".format(self.name, path))
            adapter.delete(path)
