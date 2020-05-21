# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# Heavily inspired from:
# https://github.com/OCA/storage/blob/12.0/storage_backend_sftp/components/sftp_adapter.py  # noqa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from os.path import join

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError

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
        selection=[("agent", "SSH Agent"), ("key_file", "Key File")],
        default="rsa_key",
        required=True,
        help="""
        * Agent: will use ssh agent to retrieve private keys
        * Key File: load a key at given path.
        """,
    )
    key_file = fields.Char(string="Key File")
    active = fields.Boolean(string="Active", default=True)
    export_ids = fields.One2many(
        comodel_name="backend.sftp.export",
        inverse_name="backend_id",
        string="Exports",
    )

    @api.multi
    @api.constrains("auth_method", "key_file")
    def _check_key_file_auth(self):
        for backend in self:
            if backend.auth_method == "key_file" and not backend.key_file:
                raise ValidationError(
                    _(
                        """Key file must be set for this authentication
                        method """
                    )
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

    def get_adapter(self):
        return SftpAdapter(
            username=self.username,
            hostname=self.host,
            port=self.port,
            auth_method=self.auth_method,
            key_file=self.key_file,
        )


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
            ("model", "!=", "csv.export.history"),
        ],
        help="""only csv.export.* models """,
    )
    active = fields.Boolean(string="Active", default=True)

    @api.multi
    def add(self, filename, data):
        for export in self:
            backend = export.backend_id
            adapter = backend.get_adapter()
            path = join(export.path, filename)
            _logger.info("{} - add to {}".format(backend.name, path))
            adapter.add(path, data)

    @api.multi
    def get(self, filename):
        self.ensure_one()
        backend = self.backend_id
        adapter = backend.get_adapter()
        path = join(self.path, filename)
        _logger.info("{} - get {}".format(backend.name, path))
        return adapter.get(path)

    def list(self, path):
        self.ensure_one()
        backend = self.backend_id
        adapter = backend.get_adapter()
        _logger.info("{} - list {}".format(self.name, path))
        return adapter.get(path)

    def delete(self, filename):
        for export in self:
            backend = export.backend_id
            adapter = backend.get_adapter()
            path = join(export.path, filename)
            _logger.info("{} - delete {}".format(backend.name, path))
            adapter.delete(path)
