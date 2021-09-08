# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    _sql_constraints = [
        (
            "partner_export_reference_unique",
            "UNIQUE (export_reference)",
            "The export reference must be unique!",
        ),
    ]

    def _default_export_reference(self):
        return self.env["ir.sequence"].next_by_code(
            "res.partner.export.reference"
        )

    export_reference = fields.Char(
        string="Export Reference",
        default=_default_export_reference,
        required=True,
        read_only=True,
        copy=False,
    )
