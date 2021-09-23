# Copyright 2021 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    export_to_sftp = fields.Datetime(
        string="Exported to SFTP",
        copy=False,
    )
