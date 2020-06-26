# -*- coding: utf-8 -*-
# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Export Payment CSV",
    "version": "9.0.1.0.0",
    "depends": ["csv_export_base"],
    "author": "Coop IT Easy SCRLfs",
    "summary": "Export your payments as CSV flat files",
    "website": "https://www.coopiteasy.be",
    "license": "AGPL-3",
    "data": ["data/cron.xml", "views/export_csv_payment.xml"],
    "installable": True,
}
