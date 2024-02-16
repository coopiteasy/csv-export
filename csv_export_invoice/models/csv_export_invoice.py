# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError

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
    _filename_template = "INV_%Y%m%d_%H%M_%S%f.csv"

    def get_domain(self):
        domain = [("state", "!=", "draft"), ("state", "!=", "cancel")]
        if self.manual_date_selection:
            domain += [("date", ">=", self.start_date), ("date", "<", self.end_date)]
        else:
            domain.append(("export_to_sftp", "=", False))
        return domain

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        line = record
        invoice = line.invoice_id

        if invoice.company_id.invoice_reference_type == "structured":
            reference = invoice.reference
        else:
            reference = ""

        tax = line.invoice_line_tax_ids
        if len(tax) > 1:
            raise ValidationError(
                _("This module does not allow several taxes per invoice line")
            )

        tax_code = tax.export_code if tax else ""

        price_tax_signed = line.price_tax
        if invoice.type == "out_refund" or invoice.type == "in_refund":
            price_tax_signed = -line.price_tax

        product_name = line.product_id.with_context(lang="fr_BE").name

        row = (
            invoice.journal_id.code,
            invoice.number,
            invoice.date_invoice,
            invoice.date_due,
            invoice.partner_id.get_export_reference(),
            reference,
            invoice.origin,
            str(invoice.amount_total_signed),
            line.account_id.code,
            str(line.price_subtotal_signed),
            tax_code,
            str(price_tax_signed),
            product_name,
            invoice.department_id.bob_code,
            invoice.location_id.bob_code,
            invoice.project_id.bob_code,
            invoice.financing_id.bob_code,
            "",
            "",
        )

        row = tuple(self.replace_line_return(s) for s in row)

        return row

    def get_rows(self, recordset):
        invoices = recordset

        def export_order(invoice_line):
            journal_code = invoice_line.invoice_id.journal_id.code
            invoice_number = invoice_line.invoice_id.number
            if invoice_line.account_id:
                account_code = invoice_line.account_id.code
            else:
                account_code = ""
            return journal_code, invoice_number, account_code

        lines = invoices.mapped("invoice_line_ids").sorted(export_order)
        # remove notes and sections because not associated to an account
        # therefore it causes errors when importing with accounting software
        filtered_lines = lines.filtered(lambda l: not l.display_type)
        rows = [self.get_row(line) for line in filtered_lines]
        return rows
