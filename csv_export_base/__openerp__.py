# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Export CSV Base",
    "version": "9.0.1.0.0",
    "depends": ["account", "sftp_backend"],
    "author": "Coop IT Easy SCRLfs",
    "summary": "Base to create module to export csv files.",
    "website": "https://www.coopiteasy.be",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/csv_export_history.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {"python": ["cStringIO"]},
    "installable": True,
}
