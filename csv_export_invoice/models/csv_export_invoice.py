# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from datetime import datetime

from cStringIO import StringIO
from openerp import _, api, fields, models
from openerp.exceptions import ValidationError

from .csv_writer import CSVUnicodeWriter

HEADERS = (
    "Journal",
    "Document",
    "Datefact",
    "DateEch",
    "RefCli",
    # "CommStruc",
    "Remarque",
    "MtTTC",
    "CompteGen",
    "MtBase",
    "CodeTva",
    "MtTva",
    "RemarqueLigne",
    "ANA1",
    "ANA2",
    "ANA3",
    "ANA4",
    "ANA5",
    "ANA6",
)


class InvoiceCSVExport(models.TransientModel):
    _name = "csv.export.invoice"
    _description = "Export Invoice CSV"
    _connector_model = "account.invoice"

    def _default_filename(self):
        now = datetime.now()
        filename = "FACT_%s.csv" % now.strftime("%Y%m%d_%H%M")
        return filename.replace("-", "_")

    data = fields.Binary(string="CSV", readonly=True)
    filename = fields.Char(string="File Name", default=_default_filename)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def get_domain(self):
        return [("date", ">=", self.start_date), ("date", "<", self.end_date)]

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        line = record
        invoice = line.invoice_id

        tax = line.invoice_line_tax_ids
        if len(tax) > 1:
            raise ValidationError(
                _("This module does not allow several taxes per invoice line")
            )
        elif tax:
            tax_code = tax.name  # todo map code
            tax_amount = line.price_subtotal * (21.0 / 100)
            base_amount = line.price_subtotal - tax_amount
        else:
            tax_code = ""
            tax_amount = 0.0
            base_amount = line.price_subtotal

        if line.account_analytic_id and line.account_analytic_id.code:
            analytic_code = line.account_analytic_id.code
        else:
            analytic_code = ""

        row = (
            invoice.journal_id.code,
            invoice.number,  # todo change sequence
            invoice.date_invoice,
            invoice.date_due,
            invoice.partner_id.name,
            # CommStruc
            invoice.origin,
            line.price_subtotal,
            line.account_id.code,
            base_amount,
            tax_code,
            tax_amount,
            line.product_id.name,
            analytic_code,
        )
        return row

    def get_rows(self, recordset):
        invoices = recordset
        lines = invoices.mapped("invoice_line_ids").sorted(
            lambda l: (
                l.invoice_id.journal_id.code,
                l.invoice_id.number,
                l.account_id.code,
            )
        )
        rows = [self.get_row(line) for line in lines]
        return rows

    @api.multi
    def get_data(self):
        recordset = self.env[self._connector_model].search(self.get_domain())
        header = self.get_headers()
        rows = self.get_rows(recordset)
        data = [header] + rows
        return data

    @api.multi
    def action_manual_export_invoice(self):
        self.ensure_one()
        data = self.get_data()
        # file_data = open("test_file.csv", "w")
        file_data = StringIO()
        try:
            writer = CSVUnicodeWriter(file_data, delimiter="|")
            writer.writerows(data)
            file_value = file_data.getvalue()
            # print(file_value)
            self.data = base64.encodestring(file_value)
        finally:
            file_data.close()
        return {
            "type": "ir.actions.act_window",
            "res_model": "csv.export.invoice",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
