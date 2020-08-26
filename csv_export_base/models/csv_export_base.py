# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import logging
from datetime import date, datetime, timedelta

import openerp
from openerp import _, api, fields, models
from openerp.exceptions import ValidationError

from .csv_writer import CSVUnicodeWriter

_logger = logging.getLogger(__name__)

try:
    from cStringIO import StringIO
except ImportError as err:
    _logger.debug(err)


class BaseCSVExport(models.AbstractModel):
    _name = "csv.export.base"
    _description = "Export CSV Base"
    _connector_model = ""
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

    def replace_line_return(self, s):
        if type(s) is str or type(s) is unicode:  # noqa
            return s.replace("\n", " ").strip()
        else:
            return s

    @api.multi
    def get_headers_rows_array(self):
        recordset = self.env[self._connector_model].search(self.get_domain())
        _logger.info("fetching data for %s export" % self._connector_model)
        header = self.get_headers()
        rows = self.get_rows(recordset)
        return [header] + rows

    @api.multi
    def action_manual_export_base(self):
        """Generate CSV"""
        self.ensure_one()
        data = self.get_headers_rows_array()
        file_data = StringIO()
        try:
            _logger.info(
                "writing {} lines to {}".format(len(data), self.filename)
            )
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
        """Send CSV to SFTP server"""
        self.ensure_one()
        exports = self.env["backend.sftp.export"].search(
            [
                ("active", "=", True),
                ("backend_id.active", "=", True),
                ("model_id.model", "=", self._name),
            ]
        )
        if not exports:
            raise ValidationError(
                _("No sftp server configured for this export.")
            )

        for export in exports:
            data = base64.decodestring(self.data)
            try:
                export.add(self.filename, data)
                self._log_export(export.path, success=True)
            except Exception as e:
                _logger.error(e)
                self._log_export(export.path, success=False)
                raise e

    @api.multi
    def _log_export(self, path, success):
        # use a cursor to make sure log is written to database in case an
        # exception and rollback occurs
        with api.Environment.manage():
            with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                for export in self:
                    env["csv.export.history"].sudo().create(
                        {
                            "date": fields.Datetime.now(),
                            "path": path,
                            "model": self._name,
                            "filename": export.filename,
                            "start_date": export.start_date,
                            "end_date": export.end_date,
                            "success": success,
                        }
                    )

    @api.model
    def cron_daily_export(self):
        model = self._model._name
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        cep = self.env[model].create(
            {
                "start_date": fields.Date.to_string(start_date),
                "end_date": fields.Date.to_string(end_date),
            }
        )
        cep.action_manual_export_base()
        cep.action_send_to_backend_base()
