# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import logging
from datetime import datetime

from cStringIO import StringIO
from openerp import api, fields, models

from .csv_writer import CSVUnicodeWriter

_logger = logging.getLogger(__name__)


class BaseCSVExport(models.AbstractModel):
    _name = "csv.export.base"
    _description = "Export CSV Base"
    _connector_model = ""
    _backend_model = ""
    _filename_template = "export_%Y%m%d_%H%M"

    def _default_filename(self):
        now = datetime.now()
        return now.strftime(self._filename_template)

    data = fields.Binary(string="CSV", readonly=True)
    filename = fields.Char(string="File Name", default=_default_filename)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def get_domain(self):
        raise NotImplementedError

    def get_headers(self):
        raise NotImplementedError

    def get_row(self, record):
        raise NotImplementedError

    def get_rows(self, recordset):
        return [self.get_row(record) for record in recordset]

    @api.multi
    def get_headers_rows_array(self):
        recordset = self.env[self._connector_model].search(self.get_domain())
        header = self.get_headers()
        rows = self.get_rows(recordset)
        return [header] + rows

    @api.multi
    def action_manual_export_base(self):
        self.ensure_one()
        data = self.get_headers_rows_array()
        file_data = StringIO()
        try:
            writer = CSVUnicodeWriter(file_data, delimiter="|")
            writer.writerows(data)
            file_value = file_data.getvalue()
            self.data = base64.encodestring(file_value)
        finally:
            file_data.close()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    @api.multi
    def action_send_to_backend_base(self):
        self.ensure_one()
        backends = self.env[self._backend_model].search(
            [("active", "=", True)]
        )
        data = base64.decodestring(self.data)
        backends.add(self.filename, data)
