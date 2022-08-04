# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError

HEADERS = (
    "reference",
    "name",
    "company",
    "street_1",
    "street_2",
    "zip_code",
    "city",
    "lang",
    "mobile",
    "phone",
    "fax",
    "vat_category",
    "vat_number",
    "iban",
    "email",
    "payment_term",
)

_LANG_MAP = {"fr_BE": "FR", "nl_BE": "NL", "en_US": "EN"}

_FISCAL_POSITION_MAP = {
    False: "",
    u"Régime National": "",
    u"Régime Intra-Communautaire": "N",
    u"Régime Extra-Communautaire": "X",
}

_PAYMENT_TERM_MAP = {  # pylint: disable=duplicate-key
    False: "",  # noqa
    0: "0 JOUR",  # noqa
    7: "7 JOURS",
    10: "10 JOURS",
    14: "14 JOU",
    15: "15 JOURS",
    20: "20 JOURS",
    30: "30 JOURS",
    50: "50 JOURS",
    60: "60 JOURS",
}


class PartnerCSVExport(models.TransientModel):
    _name = "csv.export.partner"
    _inherit = "csv.export.base"
    _description = "Export Partner CSV"
    _connector_model = "res.partner"
    _filename_template = "CLI_%Y%m%d_%H%M_%S%f.csv"

    def get_recordset(self):
        # cf csv_export_invoice.py
        exported_invoices = self.env["account.invoice"].search(
            [
                ("state", "!=", "draft"),
                ("state", "!=", "cancel"),
                ("date", ">=", self.start_date),
                ("date", "<", self.end_date),
            ]
        )
        # cf csv_export_payment.py
        exported_payments = self.env["account.payment"].search(
            [
                ("journal_id.type", "=", "cash"),
                ("state", "!=", "draft"),
                ("payment_date", ">=", self.start_date),
                ("payment_date", "<", self.end_date),
            ]
        )

        invoice_partners = exported_invoices.mapped("partner_id")
        payment_partners = exported_payments.mapped("partner_id")
        return invoice_partners + payment_partners

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        partner = record

        # company partners do not have a firstname
        if partner.firstname:
            name = "{} {}".format(partner.lastname, partner.firstname)
        else:
            name = partner.lastname

        if partner.parent_id:
            company = partner.parent_id.name
        else:
            company = ""

        lang = _LANG_MAP.get(partner.lang, "")

        if partner.country_id and partner.zip:
            full_zip = "{}{}".format(partner.country_id.code, partner.zip)
        else:
            full_zip = ""

        bank_accounts = self.env["res.partner.bank"].search(
            [("partner_id", "=", partner.id)]
        )
        if bank_accounts:
            iban = bank_accounts[0].sanitized_acc_number
        else:
            iban = ""

        fiscal_position = partner.property_account_position_id
        if fiscal_position.name not in _FISCAL_POSITION_MAP:
            raise ValidationError(
                _("Fiscal position %s is not implemented.") % fiscal_position.name
            )
        fiscal_position_code = _FISCAL_POSITION_MAP.get(fiscal_position.name)

        if partner.property_payment_term_id:
            days = sorted(partner.property_payment_term_id.line_ids.mapped("days"))
            days = days[0] if days else False
            payment_term = _PAYMENT_TERM_MAP.get(days)

        else:
            payment_term = ""

        row = (
            partner.get_export_reference(),
            name,
            company,
            partner.street,
            partner.street2,
            full_zip,
            partner.city,
            lang,
            partner.mobile,
            partner.phone,
            "",  # dummy value for fax
            fiscal_position_code,
            partner.vat,
            iban,
            partner.email,
            payment_term,
        )

        row = tuple(self.replace_line_return(s) for s in row)

        return row
