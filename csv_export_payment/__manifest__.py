# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Export Payment CSV",
    "version": "12.0.1.1.0",
    "depends": ["csv_export_base"],
    "author": "Coop IT Easy SC",
    "summary": "Export your payments as CSV flat files",
    "website": "https://coopiteasy.be",
    "license": "AGPL-3",
    "data": [
        "data/cron.xml",
        "views/account_payment.xml",
        "views/export_csv_payment.xml",
    ],
    "installable": True,
}
