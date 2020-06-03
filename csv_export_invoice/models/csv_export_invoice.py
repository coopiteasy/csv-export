# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import _, models
from openerp.exceptions import ValidationError

HEADERS = (
    "journal",
    "reference",
    "date_invoice",
    "date_due",
    "partner_reference",
    "structured_communication",
    "comment",
    "total_amount",
    "account",
    "base_amount",
    "vat_code",
    "vat_amount",
    "line_comment",
    "ana1",
    "ana2",
    "ana3",
    "ana4",
    "ana5",
    "ana6",
)


class InvoiceCSVExport(models.TransientModel):
    _name = "csv.export.invoice"
    _inherit = "csv.export.base"
    _description = "Export Invoice CSV"
    _connector_model = "account.invoice"
    _filename_template = "INV_%Y%m%d_%H%M.csv"

    def get_domain(self):
        return [
            ("state", "!=", "draft"),
            ("state", "!=", "cancel"),
            ("date", ">=", self.start_date),
            ("date", "<", self.end_date),
        ]

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        line = record
        invoice = line.invoice_id

        if invoice.reference_type == "bba":
            reference = invoice.reference
        else:
            reference = ""

        tax = line.invoice_line_tax_ids
        if len(tax) > 1:
            raise ValidationError(
                _("This module does not allow several taxes per invoice line")
            )

        tax_code = tax.name if tax else ""  # todo get tax code
        total_amount, base_amount, tax_amount = self._get_amounts(line.price_subtotal, tax)

        # todo analytic accounts
        if line.account_analytic_id and line.account_analytic_id.code:
            analytic_code = line.account_analytic_id.code
        else:
            analytic_code = ""

        row = (
            invoice.journal_id.code,
            invoice.number,
            invoice.date_invoice,
            invoice.date_due,
            invoice.partner_id.export_reference,
            reference,
            invoice.origin,
            total_amount,
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

    def _get_amounts(self, total_amount, tax):

        total_amount = round(total_amount, 2)
        if tax:
            tax_percentage = tax.amount
            tax_amount = round(total_amount * (tax_percentage / 100))
            base_amount = total_amount - tax_amount
        else:
            tax_amount = 0.0
            base_amount = total_amount

        return total_amount, base_amount, tax_amount
