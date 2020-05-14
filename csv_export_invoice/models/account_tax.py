# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    export_code = fields.Char(string="Export Code", required=False)
