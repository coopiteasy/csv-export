# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import logging
import re
from collections import namedtuple
from datetime import datetime, date, timedelta

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
_logger = logging.getLogger(__name__)

try:
    from cStringIO import StringIO
except ImportError as err:
    _logger.debug(err)

# HEADERS = (  # todo request same header column names and order
#     "reference",
#     "payment_journal",
#     "date",
#     "customer_name",
#     "customer_reference",
#     "invoice",
#     "invoice_journal",
#     "amount",
# )

HEADERS = (
    "date",  # DateFin
    "customer_reference",  # CustomerRef
    "payment_journal",  # JouFin
    "reference",  # DocFin
    "amount",  # MtPaye
    "invoice_journal",  # JouFact
    "invoice",  # NumFact
    "MtFact",
    "communication",  # CommStruc
)

PaymentLine = namedtuple("PaymentLine", HEADERS)


class PaymentCSVImport(models.TransientModel):
    _name = "csv.import.payment"
    _description = "Import Payment CSV"
    _connector_model = "account.payment"
    _filename_template = "BOBPAI%Y%m%d....\.CSV"

    def _default_start_date(self):
        yesterday = date.today() - timedelta(days=1)
        return fields.Date.to_string(yesterday)

    def _default_end_date(self):
        return fields.Date.today()

    import_mode = fields.Selection(
        string="Import Mode",
        selection=[("csv_file", "CSV File"), ("sftp", "SFTP Server")],
        default="csv_file",
        required=True,
    )
    start_date = fields.Date(
        string="Start Date",
        default=_default_start_date,
    )
    end_date = fields.Date(
        string="End Date",
        default=_default_end_date,
    )
    data = fields.Binary(string="CSV")

    def _fetch_file_from_sftp(self):
        io_conf = self.env["backend.sftp.export"].search(
            [
                ("active", "=", True),
                ("backend_id.active", "=", True),
                ("model_id.model", "=", self._name),
            ]
        )
        if not io_conf:
            raise ValidationError(
                _("No sftp server configured for this export.")
            )
        if len(io_conf) > 1:
            raise ValidationError(
                _("Imports only support 1 configuration per model")
            )

        directory_files = io_conf.list(io_conf.path)
        fetch_day = fields.Date.from_string(self.start_date)
        fetch_pattern = fetch_day.strftime(self._filename_template)
        file_names = [fn for fn in directory_files if re.match(fetch_pattern, fn)]
        if file_names:
            _logger.info("fetching file %s from sftp backend" % file_names)
            return io_conf.get(file_names.pop())
        else:
            _logger.warn("no file %s on sftp backend" % file_names)
            raise ValueError(_("No files for day %s" % self.start_date))

    def _prepare_payment_data(self, csv_content):
        """
        csv content:
        - lines separator: \n
        - column separator: ;
        :param csv_lines: a bytelist (str) representing csv content
        :returns a tuple (payment_data, errors)
            - payment data is a dictionary of writable values to be passed
                to account.payment object
            - errors is a recordset of csv.import.error
        """
        csv_content = csv_content.replace("\r\n", "\n")
        csv_lines = csv_content.splitlines()

        errors = self.env["csv.import.error"]
        partner_obj = self.env["res.partner"]
        journal_obj = self.env["account.journal"]

        payment_method = self.env["account.payment.method"].search(
            [
                ("code", "=", "manual"),
                ("payment_type", "=", "inbound"),
            ]
        )  # todo check this

        payments_data = []

        for line_no, row in enumerate(csv_lines[1:], start=1):  # pop headers
            payment_line = PaymentLine(*tuple(row.split("|")))

            partner = partner_obj.search(
                [("export_reference", "=", payment_line.customer_reference)]
            )
            if not partner:
                errors += errors.create(
                    {
                        "line_no": line_no,
                        "line_content": row,
                        "error_message": _(
                            "No partner found for export reference %s"
                            % payment_line.customer_reference
                        ),
                    }
                )
                continue

            journal = journal_obj.search(
                [("code", "=", payment_line.payment_journal)]
            )
            if not journal:
                errors += errors.create(
                    {
                        "line_no": line_no,
                        "line_content": row,
                        "error_message": _(
                            "No journal for code %s"
                            % payment_line.payment_journal
                        ),
                    }
                )
                continue

            try:
                payment_date = datetime.strptime(payment_line.date, "%Y%m%d")
            except ValueError as e:
                errors += errors.create(
                    {
                        "line_no": line_no,
                        "line_content": row,
                        "error_message": _(
                            "Could not parse date %s. %s"
                            % (payment_line.date, e.message)
                        ),
                    }
                )
                continue
            try:
                amount = float(payment_line.amount)
            except ValueError as e:
                errors += errors.create(
                    {
                        "line_no": line_no,
                        "line_content": row,
                        "error_message": _(
                            "Could not parse amount %s. %s"
                            % (payment_line.amount, e.message)
                        ),
                    }
                )
                continue
            payments_data.append(
                {
                    "payment_method_id": payment_method.id,
                    "payment_type": "inbound",
                    "partner_id": partner.id,
                    "partner_type": "customer",
                    "journal_id": journal.id,
                    "payment_date": fields.Date.to_string(payment_date),
                    "amount": amount,
                    "communication": payment_line.communication,
                    # "payment_reference": payment_line.communication,
                }
            )

        return payments_data, errors

    @api.multi
    def action_import_payment_data(self):
        self.ensure_one()
        _logger.info("Loading csv file")
        payment_obj = self.env["account.payment"]

        if self.import_mode == "csv_file":
            csv_content = base64.b64decode(self.data)
        elif self.import_mode == "sftp":
            csv_content = self._fetch_file_from_sftp()
        else:
            raise NotImplementedError(
                "Unsupported import mode %s" % self.import_mode
            )

        payment_data, errors = self._prepare_payment_data(csv_content)

        if errors:
            return {
                "type": "ir.actions.act_window",
                "name": _("Errors on CSV Import"),
                "res_model": "csv.import.error",
                "domain": [("id", "in", errors.ids)],
                "view_type": "form",
                "view_mode": "tree,form",
                "context": self.env.context,
                "target": "current",
            }

        payments = [
            payment_obj.create(payment_dict) for payment_dict in payment_data
        ]
        _logger.info("Created %s payments from csv" % len(payments))
        return {
            "type": "ir.actions.act_window",
            "name": _("Imported Payments"),
            "res_model": "account.payment",
            "domain": [("id", "in", [p.id for p in payments])],
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.env.context,
            "target": "current",
        }
