# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import _, models
from openerp.exceptions import ValidationError

# HEADERS = (  # todo request same header column names and order
#     "date",
#     "customer_reference",
#     "payment_journal",
#     "invoice",
#     "invoice_journal",
#     "reference",
#     "amount",
#     "communication",
# )

HEADERS = (
    # DateFin	CustomerRef	JouFin	DocFin	MtPaye	JouFact	NumFact	MtFact	CommStruc
    "date",
    "customer_reference",
    "payment_journal",
    "invoice",
    "invoice_journal",
    "reference",
    "amount",
    "communication",
)


class PartnerCSVImport(models.TransientModel):
    _name = "csv.import.payment"
    _description = "Import Payment CSV"
    _connector_model = "account.payment"
    _filename_template = "CASH_%Y%m%d_%H%M.csv"
    # _filename_template = "CASH_%Y%m%d_%H%M.csv" # todo request same file name template

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
            raise ValidationError(
                _("The csv export can't handle multiple invoice per payment")
            )
        invoice = payment.invoice_ids

        row = (
            payment.name,
            payment.journal_id.code,
            payment.payment_date,
            payment.partner_id.name,
            payment.partner_id.export_reference,
            invoice.number,
            invoice.journal_id.code,
            str(payment.amount),
        )

        row = tuple(self.replace_line_return(s) for s in row)

        return row
