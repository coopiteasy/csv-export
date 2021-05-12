# Copyright 2021 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models


class CSVImportError(models.TransientModel):
    _name = "csv.import.error"
    _description = "Logs csv import error"

    file_name = fields.Char(
        string="File Name",
    )
    line_no = fields.Integer(
        string="Line Number",
    )
    line_content = fields.Char(
        string="Line Content",
    )
    error_message = fields.Char(string="Error Message")
