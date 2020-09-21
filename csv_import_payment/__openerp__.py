# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Import Payment CSV",
    "version": "9.0.1.0.0",
    "depends": ["csv_export_base", "sftp_backend"],
    "author": "Coop IT Easy SCRLfs",
    "summary": "Import payments as CSV flat files from BOB",
    "website": "https://www.coopiteasy.be",
    "license": "AGPL-3",
    "data": ["data/cron.xml", "views/import_csv_payment.xml"],
    "installable": True,
}
