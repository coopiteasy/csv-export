# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import models, _
from openerp.exceptions import ValidationError

HEADERS = (
    "reference",
    "payment_journal",
    "date",
    "customer_name",
    "customer_reference",
    "invoice",
    "invoice_journal",
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
            ("journal_id.type", "=", "cash"),
            ("state", "!=", "draft"),
            ("payment_date", ">=", self.start_date),
            ("payment_date", "<", self.end_date),
        ]

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        payment = record

        if len(payment.invoice_ids) > 1:
            raise ValidationError(_(
                "The csv export can't handle multiple invoice per payment"
            ))
        invoice = payment.invoice_ids

        rows = (
            payment.name,
            payment.journal_id.code,
            payment.payment_date,
            payment.partner_id.name,
            payment.partner_id.export_reference,
            invoice.number,
            invoice.journal_id.code,
            payment.amount,
        )
        return rows
