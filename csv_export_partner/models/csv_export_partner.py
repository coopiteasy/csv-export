# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import _, models
from openerp.exceptions import ValidationError

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
    u"Régime National": "A",
    u"Régime Intra-Communautaire": "N",
    u"Régime Extra-Communautaire": "X",
}


class PartnerCSVExport(models.TransientModel):
    _name = "csv.export.partner"
    _inherit = "csv.export.base"
    _description = "Export Partner CSV"
    _connector_model = "res.partner"
    _filename_template = "CLI_%Y%m%d_%H%M.csv"

    def get_domain(self):
        return [
            ("write_date", ">=", self.start_date),
            ("write_date", "<", self.end_date),
        ]

    def get_headers(self):
        return HEADERS

    def get_row(self, record):
        partner = record

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
                _("Fiscal position %s is not implemented.")
                % fiscal_position.name
            )
        fiscal_position_code = _FISCAL_POSITION_MAP.get(fiscal_position.name)

        if partner.property_payment_term_id:
            days = sorted(
                partner.property_payment_term_id.line_ids.mapped("days")
            )
            payment_term = days[0] if days else ""
        else:
            payment_term = ""

        row = (
            partner.id,
            partner.name,
            company,
            partner.street,
            partner.street2,
            full_zip,
            partner.city,
            lang,
            partner.mobile,
            partner.phone,
            partner.fax,
            fiscal_position_code,
            partner.vat,
            iban,
            partner.email,
            payment_term,
        )
        return row
