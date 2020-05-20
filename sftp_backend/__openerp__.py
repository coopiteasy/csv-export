# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SFTP Backend",
    "version": "9.0.1.0.0",
    "depends": ["base"],
    "author": "Coop IT Easy SCRLfs",
    "summary": "SFTP backend utils.",
    "website": "http://www.coopiteasy.be",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/backend_sftp.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {"python": ["paramiko"]},
    "installable": True,
}
