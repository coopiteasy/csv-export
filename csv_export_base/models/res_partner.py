# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    _sql_constraints = [
        (
            "partner_export_reference_unique",
            "UNIQUE (_export_reference)",
            "The export reference must be unique!",
        ),
    ]

    def _next_export_reference(self):
        return self.env["ir.sequence"].next_by_code("res.partner.export.reference")

    @api.multi
    def get_export_reference(self):
        self.ensure_one()
        if self._export_reference:
            return self._export_reference
        else:
            export_reference = self._next_export_reference()
            self._export_reference = export_reference
            return export_reference

    _export_reference = fields.Char(
        string="Export Reference",
        read_only=True,
        copy=False,
    )
