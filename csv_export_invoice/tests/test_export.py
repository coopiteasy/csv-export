# Copyright 2020 Coop IT Easy SC
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import datetime
import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestCSVExport(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        company = cls.env.ref("base.main_company")
        euro = cls.env.ref("base.EUR")
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

        cls.product = cls.env["product.product"].create(
            {
                "name": "Commune Présence",
            }
        )

        cls.invoice = cls.env["account.invoice"].create(
            {
                "company_id": company.id,
                "currency_id": euro.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Commune présence",
                            "price_unit": 450.0,
                            "quantity": 1.0,
                            "product_id": cls.product.id,
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

    def test_invoice_csv_export_exports_unicode_data(self):
        # coverage
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        cei = self.env["csv.export.invoice"].create(
            {"manual_date_selection": True, "start_date": today, "end_date": tomorrow}
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
        line_items = invoice_line.split("|")
        journal = line_items[0]
        reference = line_items[1]
        line_comment = line_items[12]

        self.assertEquals(expected_header, header)
        self.assertEquals(journal, self.invoice.journal_id.code)
        self.assertEquals(reference, self.invoice.number)
        self.assertEquals(line_comment, self.product.name)
        self.assertEquals(eol, "")

        # needs mocking
        # ice.action_send_to_backend_base()

    def test_invoice_csv_export_non_exporter(self):
        # coverage

        # setting all invoices as already exported
        # because we want to test only the export of the test invoice
        for invoice in self.env["account.invoice"].search([]):
            invoice.export_to_sftp = datetime.datetime.now()
        self.invoice.export_to_sftp = False

        cei = self.env["csv.export.invoice"].create({"manual_date_selection": False})
        cei.action_manual_export_base()

        csv_content = base64.decodebytes(cei.data).decode("utf-8")
        lines = csv_content.split("\n")
        # There should be three lines : header, one invoice line and EOF
        self.assertEquals(len(lines), 3)
