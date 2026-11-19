from odoo import Command
from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestSaleInvoiceStockControl(TestSaleCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data['company']
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        # The control only makes sense with manual reservation: with reservation
        # at confirmation the stock is already committed before invoicing.
        cls.warehouse.out_type_id.reservation_method = 'manual'

        cls.controlled_product = cls.env['product.product'].create({
            'name': "Controlled Product",
            'type': 'product',
            'invoice_policy': 'order',
            'check_stock_before_invoice': True,
        })
        cls.free_product = cls.env['product.product'].create({
            'name': "Uncontrolled Product",
            'type': 'product',
            'invoice_policy': 'order',
            'check_stock_before_invoice': False,
        })
        cls.authorised_user = cls.env['res.users'].create({
            'name': "Sales Supervisor",
            'login': 'stock_control_supervisor',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'groups_id': [Command.set([
                cls.env.ref('sales_team.group_sale_salesman').id,
                cls.env.ref('account.group_account_invoice').id,
                cls.env.ref('stock.group_stock_user').id,
                cls.env.ref(
                    'sale_invoice_stock_control.'
                    'group_invoice_without_stock').id,
            ])],
        })

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @classmethod
    def _set_stock(cls, product, quantity):
        cls.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'inventory_quantity': quantity,
        }).action_apply_inventory()

    def _confirmed_order(self, product=None, quantity=5.0):
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'warehouse_id': self.warehouse.id,
            'order_line': [Command.create({
                'product_id': (product or self.controlled_product).id,
                'product_uom_qty': quantity,
            })],
        })
        order.action_confirm()
        return order

    # ------------------------------------------------------------------
    # CONTROL
    # ------------------------------------------------------------------

    def test_invoicing_without_stock_is_blocked(self):
        order = self._confirmed_order()
        with self.assertRaisesRegex(UserError, "not enough stock"):
            order._create_invoices()
        self.assertFalse(order.invoice_ids)

    def test_invoicing_with_full_stock_succeeds(self):
        self._set_stock(self.controlled_product, 5.0)
        order = self._confirmed_order()
        invoice = order._create_invoices()
        self.assertTrue(invoice)
        self.assertEqual(sum(order.picking_ids.move_ids.mapped('quantity')), 5.0)

    def test_partial_stock_blocks_the_whole_line(self):
        self._set_stock(self.controlled_product, 3.0)
        order = self._confirmed_order(quantity=5.0)
        with self.assertRaisesRegex(UserError, "2.0 missing|not enough stock"):
            order._create_invoices()

    def test_reservation_happens_only_when_invoicing(self):
        self._set_stock(self.controlled_product, 5.0)
        order = self._confirmed_order()
        # Manual reservation: confirming the order must not reserve anything.
        self.assertEqual(sum(order.picking_ids.move_ids.mapped('quantity')), 0.0)
        order._create_invoices()
        self.assertEqual(sum(order.picking_ids.move_ids.mapped('quantity')), 5.0)

    def test_unflagged_product_is_not_controlled(self):
        order = self._confirmed_order(product=self.free_product)
        invoice = order._create_invoices()
        self.assertTrue(invoice)

    def test_service_product_is_not_controlled(self):
        service = self.env['product.product'].create({
            'name': "A Service",
            'type': 'service',
            'invoice_policy': 'order',
            'check_stock_before_invoice': True,
        })
        order = self._confirmed_order(product=service)
        self.assertTrue(order._create_invoices())

    # ------------------------------------------------------------------
    # RESERVATION ROLLBACK
    # ------------------------------------------------------------------

    def test_blocked_invoice_releases_what_it_reserved(self):
        self._set_stock(self.controlled_product, 3.0)
        order = self._confirmed_order(quantity=5.0)
        with self.assertRaises(UserError):
            order._create_invoices()
        # The partial reservation this check created must not survive.
        self.assertEqual(sum(order.picking_ids.move_ids.mapped('quantity')), 0.0)

    def test_a_manual_reservation_is_never_taken_back(self):
        self._set_stock(self.controlled_product, 3.0)
        order = self._confirmed_order(quantity=5.0)
        # The warehouse reserved by hand before anybody tried to invoice.
        order.picking_ids.action_assign()
        reserved_by_warehouse = sum(order.picking_ids.move_ids.mapped('quantity'))
        self.assertEqual(reserved_by_warehouse, 3.0)

        with self.assertRaises(UserError):
            order._create_invoices()
        self.assertEqual(
            sum(order.picking_ids.move_ids.mapped('quantity')),
            reserved_by_warehouse,
            "the reservation made by the warehouse must be left untouched",
        )

    # ------------------------------------------------------------------
    # EXCEPTION
    # ------------------------------------------------------------------

    def test_authorised_user_without_justification_is_still_blocked(self):
        order = self._confirmed_order()
        with self.assertRaisesRegex(UserError, "Stock Control Exception"):
            order.with_user(self.authorised_user)._create_invoices()

    def test_unauthorised_user_is_asked_for_an_authorisation(self):
        order = self._confirmed_order()
        with self.assertRaisesRegex(UserError, "ask for an authorisation"):
            order._create_invoices()

    def test_authorised_user_bypasses_and_leaves_an_audit_trail(self):
        order = self._confirmed_order()
        order = order.with_user(self.authorised_user)
        order.stock_control_override_reason = "Urgent delivery agreed with the customer."

        message_count = len(order.message_ids)
        invoice = order._create_invoices()

        self.assertTrue(invoice)
        self.assertEqual(len(order.message_ids), message_count + 1)
        self.assertIn("Stock control bypassed", order.message_ids[0].body)
        self.assertIn("Urgent delivery", order.message_ids[0].body)

    def test_exception_field_is_hidden_without_the_group(self):
        fields = self.env['sale.order'].with_user(
            self.company_data['default_user_salesman']).fields_get(['stock_control_override_reason'])
        self.assertFalse(fields)

    # ------------------------------------------------------------------
    # DOWN PAYMENTS
    # ------------------------------------------------------------------

    def test_down_payment_is_not_blocked(self):
        order = self._confirmed_order()
        wizard = self.env['sale.advance.payment.inv'].with_context(
            active_model='sale.order', active_ids=order.ids, active_id=order.id,
        ).create({
            'advance_payment_method': 'percentage',
            'amount': 20.0,
        })
        wizard.create_invoices()
        self.assertTrue(order.invoice_ids, "a down payment must not hit the control")

    # ------------------------------------------------------------------
    # CREDIT NOTE: RELEASE OF THE RESERVATION
    # ------------------------------------------------------------------

    def _posted_invoice(self, quantity=5.0):
        self._set_stock(self.controlled_product, quantity)
        order = self._confirmed_order(quantity=quantity)
        invoice = order._create_invoices()
        invoice.action_post()
        return order, invoice

    def _reversal_wizard(self, invoice, **values):
        return self.env['account.move.reversal'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({'journal_id': invoice.journal_id.id, **values})

    def _post_credit_note(self, credit_note):
        # Keep the test independent from other modules that require a reason
        # on customer credit notes (e.g. magna_credit_note_return_control).
        if 'credit_note_reason' in credit_note._fields:
            credit_note.credit_note_reason = 'invoicing_error'
        credit_note.action_post()

    def _reserved(self, order):
        return sum(order.picking_ids.move_ids.mapped('quantity'))

    def test_wizard_shows_the_reserved_goods(self):
        order, invoice = self._posted_invoice()
        wizard = self._reversal_wizard(invoice)
        self.assertEqual(wizard.reserved_stock_move_ids, order.picking_ids.move_ids)

    def test_credit_note_requires_an_answer_when_goods_are_reserved(self):
        _order, invoice = self._posted_invoice()
        wizard = self._reversal_wizard(invoice)
        with self.assertRaisesRegex(UserError, "reservation must be released"):
            wizard.refund_moves()

    def test_credit_note_releases_the_reservation_when_posted(self):
        order, invoice = self._posted_invoice()
        wizard = self._reversal_wizard(invoice, release_stock_reservation='yes')
        wizard.refund_moves()
        credit_note = wizard.new_move_ids
        self.assertTrue(credit_note.release_stock_reservation)
        # Nothing happens while the credit note is a draft.
        self.assertEqual(self._reserved(order), 5.0)

        self._post_credit_note(credit_note)
        self.assertEqual(self._reserved(order), 0.0)
        self.assertIn("Stock reservation released", order.message_ids[0].body)

    def test_credit_note_keeps_the_reservation_when_asked(self):
        order, invoice = self._posted_invoice()
        wizard = self._reversal_wizard(invoice, release_stock_reservation='no')
        wizard.refund_moves()
        self._post_credit_note(wizard.new_move_ids)
        self.assertEqual(self._reserved(order), 5.0)

    def test_partial_credit_note_releases_only_the_credited_quantity(self):
        order, invoice = self._posted_invoice()
        wizard = self._reversal_wizard(invoice, release_stock_reservation='yes')
        wizard.refund_moves()
        credit_note = wizard.new_move_ids
        credit_note.invoice_line_ids.quantity = 2.0
        self._post_credit_note(credit_note)
        self.assertEqual(self._reserved(order), 3.0)

    def test_reverse_and_create_invoice_keeps_the_reservation(self):
        order, invoice = self._posted_invoice()
        wizard = self._reversal_wizard(invoice)
        wizard.modify_moves()
        self.assertEqual(self._reserved(order), 5.0)
