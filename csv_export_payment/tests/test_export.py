# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime
import logging

# from odoo.exceptions import ValidationError
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestPaymentCSVExport(common.TransactionCase):
    def test_get_rows(self):
        ICE = self.env["csv.export.payment"]
        journal = self.env["account.journal"].search([], limit=1)
        payment_method = self.env["account.payment.method"].search([], limit=1)
        payment = self.env["account.payment"].create(
            {
                "journal_id": journal.id,
                "payment_method_id": payment_method.id,
                "payment_date": datetime.date.today(),
                "communication": "test payment",
                # "invoice_ids": [(4, inv_id, None)],
                "payment_type": "inbound",
                "amount": 200,
                "partner_id": self.ref("base.partner_demo"),
                "partner_type": "customer",
            }
        )
        rows = ICE.get_rows(payment)
        for row in rows:
            _logger.info(row)

    def test_invoice_csv_export(self):
        ice = self.env["csv.export.payment"].create(
            {"start_date": "2020-06-29", "end_date": "2020-06-30"}
        )
        ice.action_manual_export_base()
        # with self.assertRaises(ValidationError):
        #     ice.action_send_to_backend_base()
        # needs mocking
        # ice.action_send_to_backend_base()
