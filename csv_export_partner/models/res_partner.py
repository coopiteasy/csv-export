# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    export_to_sftp = fields.Datetime(
        string="Exported to SFTP",
        default=False,
    )
