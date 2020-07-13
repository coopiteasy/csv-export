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

        tax_code = tax.export_code if tax else ""
        base_amount, tax_amount = self._get_line_amounts(line)
        total_amount = self._get_total_amount(invoice)

        row = (
            invoice.journal_id.code,
            invoice.number,
            invoice.date_invoice,
            invoice.date_due,
            invoice.partner_id.export_reference,
            reference,
            invoice.origin,
            str(total_amount),
            line.account_id.code,
            str(base_amount),
            tax_code,
            str(tax_amount),
            line.product_id.name,
            invoice.department_id.bob_code,
            invoice.location_id.bob_code,
            invoice.project_id.bob_code,
            invoice.financing_id.bob_code,
            "",
            "",
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

    def _get_line_amounts(self, line):
        """

        :param line_amount: float, including taxes
        :param tax: float, line tax amount
        :return: a tuple of total amount, base_amount and tax_amount.
          base_amount and tax_amount are rounded to two decimals.
          total_amount is the sum of rounded base_amount and tax_amount
          for lines in the invoice.
        """
        tax = line.invoice_line_tax_ids
        line_amount = round(line.price_subtotal, 2)
        if tax:
            tax_percentage = tax.amount
            tax_amount = round(line_amount * (tax_percentage / 100.0), 2)
            base_amount = line_amount - tax_amount
        else:
            tax_amount = 0.0
            base_amount = line_amount

        base_amount = base_amount or 0.
        tax_amount = tax_amount or 0.
        return base_amount, tax_amount

    def _get_total_amount(self, invoice):
        """
        We  go trough this function to make sure that
        Total invoice = sum(base line amount) + sum(tax line amount)
        for rounded amounts
        """
        return sum(
            sum(self._get_line_amounts(line))  # (base_amount, tax_amount)
            for line in invoice.invoice_line_ids
        )
