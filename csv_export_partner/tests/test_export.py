# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestPartnerCSVExport(common.TransactionCase):
    # code coverage
    def test_get_rows(self):
        partner = self.env.ref("base.partner_demo")
        rows = self.env["csv.export.partner"].get_rows(partner)
        for row in rows:
            _logger.info(row)

    def test_partner_csv_export(self):
        ice = self.env["csv.export.partner"].create(
            {
                "manual_date_selection": True,
                "start_date": "2020-06-29",
                "end_date": "2020-06-30",
            }
        )
        ice.action_manual_export_base()
        # needs mocking
        # ice.action_send_to_backend_base()

    def test_cron(self):
        export_model = self.env["ir.model"].search(
            [("model", "=", "csv.export.partner")]
        )
        backend = self.env["backend.sftp"].create(
            {
                "name": "test backend",
                "username": "test name",
                "host": "test.org",
                "port": 2222,
                "auth_method": "agent",
            }
        )
        self.env["backend.sftp.export"].create(
            {
                "backend_id": backend.id,
                "model_id": export_model.id,
                "path": "path/to/dir",
            }
        )
        # needs moking
        # self.env["csv.export.partner"].cron_daily_export()
