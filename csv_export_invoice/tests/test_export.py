# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import datetime
import logging

from odoo.fields import Date
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestCSVExport(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        company = cls.env.ref("base.main_company")
        euro = cls.env.ref("base.EUR")
        product = cls.env.ref("product.product_product_3")
        uom = cls.env.ref("uom.product_uom_unit")
        partner = cls.env.ref("base.res_partner_12")

        revenue_acc = cls.env["account.account"].search(
            [
                ("company_id", "=", company.id),
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                ),
            ],
            limit=1,
        )

        cls.invoice = cls.env["account.invoice"].create(
            {
                "company_id": company.id,
                "currency_id": euro.id,
                # "account_id": account_rcv.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Computer SC234",
                            "price_unit": 450.0,
                            "quantity": 1.0,
                            "product_id": product.id,
                            "uom_id": uom.id,
                            "account_id": revenue_acc.id,
                        },
                    )
                ],
                "partner_id": partner.id,
            }
        )
        cls.invoice.action_invoice_open()

    def test_get_rows(self):
        # coverage
        cei_obj = self.env["csv.export.invoice"]
        invoice = self.invoice
        rows = cei_obj.get_rows(invoice)
        for row in rows:
            _logger.info(row)

    def test_invoice_csv_export(self):
        # coverage
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        cei = self.env["csv.export.invoice"].create(
            {"start_date": today, "end_date": tomorrow}
        )
        cei.action_manual_export_base()
        csv_content = base64.decodebytes(cei.data).decode("utf-8")
        header, invoice_line, eol = csv_content.split("\n")
        expected_header = (
            "journal|reference|date_invoice|date_due|partner_reference"
            "|structured_communication|comment|total_amount|account"
            "|base_amount|vat_code|vat_amount|line_comment"
            "|ana1|ana2|ana3|ana4|ana5|ana6\r"
        )
        expected_invoice_line_start = "{code}|{reference}|{date_invoice}".format(
            code=self.invoice.journal_id.code,
            reference=self.invoice.number,
            date_invoice=Date.to_string(self.invoice.date_invoice),
        )
        self.assertEquals(expected_header, header)
        self.assertTrue(invoice_line.startswith(expected_invoice_line_start))
        self.assertEquals(eol, "")
        # needs mocking
        # ice.action_send_to_backend_base()
