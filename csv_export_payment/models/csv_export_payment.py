# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import models

HEADERS = (
    "reference",
    "journal",
    "date",
    "customer_reference",
    "invoice",
    "amount",
)


class PartnerCSVExport(models.TransientModel):
    _name = "csv.export.payment"
    _inherit = "csv.export.base"
    _description = "Export Payment CSV"
    _connector_model = "account.payment"
    _filename_template = "CASH_%Y%m%d_%H%M.csv"

    def get_domain(self):
        return [
            ("journal_id.code", "=", "CSH1"),
            ("state", "!=", "draft"),
            ("payment_date", ">=", self.start_date),
            ("payment_date", "<", self.end_date),
        ]

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        payment = record

        invoices = ",".join(payment.invoice_ids.mapped("number"))

        rows = (
            payment.name,
            payment.journal_id.code,
            payment.payment_date,
            payment.partner_id.name,
            invoices,
            payment.amount,
        )
        return rows
