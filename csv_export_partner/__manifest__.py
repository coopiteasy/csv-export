# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Export Partner CSV",
    "version": "12.0.1.0.0",
    "depends": ["csv_export_base"],
    "author": "Coop IT Easy SCRLfs",
    "summary": "Export your partners as CSV flat files",
    "website": "https://coopiteasy.be",
    "license": "AGPL-3",
    "data": [
        "data/cron.xml",
        "views/res_partner.xml",
        "views/export_csv_partner.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "post_init_hook": "set_default_export_reference",
}
