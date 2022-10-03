# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError

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
    _filename_template = "CASH_%Y%m%d_%H%M_%S%f.csv"

    def get_domain(self):
        # est-ce que les paiments peuvent rester en draft plusieurs jours?
        #  => non, les paiements ne passent pas par l'état brouillon.
        domain = [("state", "!=", "draft"), ("state", "!=", "cancel")]
        if self.manual_date_selection:
            domain += [("date", ">=", self.start_date), ("date", "<", self.end_date)]
        else:
            domain.append(("export_to_sftp", "=", False))
        return domain

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        payment = record

        if len(payment.invoice_ids) > 1:
            raise ValidationError(
                _("The csv export can't handle multiple invoice per payment")
            )
        invoice = payment.invoice_ids

        if payment.partner_type == "customer":
            if payment.payment_type == "inbound":
                amount = payment.amount
            if payment.payment_type == "outbound":
                amount = -payment.amount
        if payment.partner_type == "supplier":
            if payment.payment_type == "inbound":
                amount = -payment.amount
            if payment.payment_type == "outbound":
                amount = payment.amount

        row = (
            payment.name,
            payment.journal_id.code,
            payment.payment_date,
            payment.partner_id.name,
            payment.partner_id.get_export_reference(),
            invoice.number,
            invoice.journal_id.code,
            str(amount),
        )

        row = tuple(self.replace_line_return(s) for s in row)

        return row
