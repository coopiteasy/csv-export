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

    import_mode = fields.Selection(
        string="Import Mode",
        selection=[("csv_file", "CSV File"), ("sftp", "SFTP Server")],
        default="csv_file",
        required=True,
    )
    data = fields.Binary(string="CSV")
    backend = fields.Many2one(
        comodel_name="backend.sftp.export",
        string="Backend",
        compute="_compute_backend",
    )

    @api.multi
    def _compute_backend(self):
        for csv_export in self:
            backend = self.env["backend.sftp.export"].search(
                [
                    ("active", "=", True),
                    ("backend_id.active", "=", True),
                    ("model_id.model", "=", csv_export._name),
                ]
            )
            if not backend:
                raise ValidationError(
                    _("No sftp server configured for this export.")
                )
            if len(backend) > 1:
                raise ValidationError(
                    _("Imports only support 1 configuration per model")
                )
            csv_export.backend = backend

    @api.multi
    def action_import_payment_data(self):
        self.ensure_one()
        _logger.info("Loading csv file")

        if self.import_mode == "csv_file":
            return self._import_csv_file()
        elif self.import_mode == "sftp":
            return self._import_sftp_files()
        else:
            raise NotImplementedError(
                "Unsupported import mode %s" % self.import_mode
            )

    @api.multi
    def _import_csv_file(self):
        csv_content = base64.b64decode(self.data)
        payment_data, errors = self._prepare_payment_data(csv_content)
        if errors:
            return self._redirect_to_errors(errors)
        else:
            payments = self._create_payments(payment_data)
            return self._redirect_to_payments(payments)

    @api.multi
    def _import_sftp_files(self):
        file_names = self.backend.list(self.backend.path)
        errors = self.env["csv.import.error"]
        payments = self.env["account.payment"]
        for file_name in file_names:
            _logger.info("fetching file %s from sftp backend" % file_name)
            csv_content = self.backend.get(file_name)
            payment_data, errors = self._prepare_payment_data(
                csv_content, file_name=file_name
            )
            if errors:
                errors += errors
            else:
                payments += self._create_payments(payment_data)

        if errors:
            return self._redirect_to_errors(errors)
        if not payments:
            raise ValidationError(_("No payments to import."))
        else:
            self._archive_sftp_files(file_names)
            return self._redirect_to_payments(payments)

    def _redirect_to_errors(self, errors):
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

    def _redirect_to_payments(self, payments):
        return {
            "type": "ir.actions.act_window",
            "name": _("Imported Payments"),
            "res_model": "account.payment",
            "domain": [("id", "in", payments.ids)],
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.env.context,
            "target": "current",
        }

    def _prepare_payment_data(self, csv_content, file_name="Uploaded file"):
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
                        "file_name": file_name,
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
                        "file_name": file_name,
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
                        "file_name": file_name,
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
                        "file_name": file_name,
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

    def _create_payments(self, payment_data):
        payments = self.env["account.payment"]
        for payment_dict in payment_data:
            payments += self.env["account.payment"].create(payment_dict)
        _logger.info("Created %s payments from csv" % len(payments))
        return payments

    def _archive_sftp_files(self, file_names):
        for file_name in file_names:
            data = self.backend.get(file_name)
            archive_dir = self.backend.path + "-processed"
            self.backend.add(file_name, data, directory=archive_dir)
            _logger.info("moved %s to %s" % (file_name, archive_dir))
            self.backend.delete(file_name)
