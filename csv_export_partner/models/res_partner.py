# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _default_export_reference(self):
        return self.env["ir.sequence"].next_by_code(
            "res.partner.export.reference"
        )

    export_reference = fields.Char(
        string="Export Reference",
        default=_default_export_reference,
        read_only=True,
        copy=False,
    )
