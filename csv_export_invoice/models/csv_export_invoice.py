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
        base_amount, tax_amount = self._get_line_amounts(line)
        total_amount = self._get_total_amount(invoice)

        product_name = line.product_id.with_context(lang="fr_BE").name

        if invoice.type == u"out_refund":
            origin = self.env["account.invoice"].search(
                [
                    ("number", "=", invoice.origin),
                    ("journal_id", "=", invoice.journal_id.id),
                ]
            )
            if origin:
                total_amount = -total_amount
                base_amount = -base_amount
                tax_amount = -tax_amount

        row = (
            invoice.journal_id.code,
            invoice.number,
            invoice.date_invoice,
            invoice.date_due,
            invoice.partner_id.get_export_reference(),
            reference,
            invoice.origin,
            str(total_amount),
            line.account_id.code,
            str(base_amount),
            tax_code,
            str(tax_amount),
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

    def _get_line_amounts(self, line):
        """

        :param line_amount: float, including taxes
        :param tax: float, line tax amount
        :return: a tuple of total amount, base_amount and tax_amount.
          base_amount and tax_amount are rounded to two decimals.
          total_amount is the sum of rounded base_amount and tax_amount
          for lines in the invoice.
        """
        taxes = line.invoice_line_tax_ids
        tax_amounts = taxes.compute_all(
            line.price_unit,
            line.invoice_id.currency_id,
            line.quantity,
            product=line.product_id,
            partner=line.invoice_id.partner_id,
        )
        total_included = tax_amounts.get("total_included", 0.0)
        total_excluded = tax_amounts.get("total_excluded", 0.0)
        tax_amount = total_included - total_excluded
        return total_excluded, tax_amount

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
