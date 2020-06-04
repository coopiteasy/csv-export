# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Export Invoice CSV",
    "version": "9.0.1.0.0",
    "depends": ["account", "csv_export_base", "l10n_be_invoice_bba"],
    "author": "Coop IT Easy SCRLfs",
    "summary": "Export your invoices as CSV flat files",
    "website": "https://www.coopiteasy.be",
    "license": "AGPL-3",
    "data": [
        "views/account_tax.xml",
        "views/export_csv_invoice.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
