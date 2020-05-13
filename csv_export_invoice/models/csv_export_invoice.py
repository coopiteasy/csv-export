# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import _, models
from openerp.exceptions import ValidationError

HEADERS = (
    "Journal",
    "Document",
    "Datefact",
    "DateEch",
    "RefCli",
    "CommStruc",
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
            reference,
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
