from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCreditNoteReturnControl(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data['company']
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.storable_product = cls.env['product.product'].create({
            'name': "Returnable Product",
            'type': 'product',
        })
        cls.supervisor = cls.env['res.users'].create({
            'name': "Credit Note Supervisor",
            'login': 'cn_supervisor',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'groups_id': [Command.set([
                cls.env.ref('base.group_user').id,
                cls.env.ref('account.group_account_invoice').id,
                cls.env.ref('stock.group_stock_user').id,
                cls.env.ref(
                    'magna_credit_note_return_control.'
                    'group_credit_note_return_exception').id,
            ])],
        })

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @classmethod
    def _create_return_picking(cls, partner, validate=True):
        """Create an incoming transfer bringing goods back from `partner`."""
        picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.warehouse.in_type_id.id,
            'partner_id': partner.id,
            'location_id': cls.customer_location.id,
            'location_dest_id': cls.warehouse.lot_stock_id.id,
            'move_ids': [Command.create({
                'name': cls.storable_product.name,
                'product_id': cls.storable_product.id,
                'product_uom_qty': 1.0,
                'product_uom': cls.storable_product.uom_id.id,
                'location_id': cls.customer_location.id,
                'location_dest_id': cls.warehouse.lot_stock_id.id,
            })],
        })
        picking.action_confirm()
        if validate:
            picking.move_ids.write({'quantity': 1.0, 'picked': True})
            picking.button_validate()
        return picking

    def _create_credit_note(self, reason=None, picking=None, partner=None):
        credit_note = self.init_invoice(
            'out_refund',
            partner=partner or self.partner_a,
            products=self.storable_product,
            company=self.company,
        )
        credit_note.write({
            'credit_note_reason': reason,
            'return_picking_id': picking.id if picking else False,
        })
        return credit_note

    # ------------------------------------------------------------------
    # REASON
    # ------------------------------------------------------------------

    def test_reason_is_required_to_post(self):
        credit_note = self._create_credit_note()
        with self.assertRaisesRegex(ValidationError, "reason is missing"):
            credit_note.action_post()

    def test_reason_other_than_goods_return_needs_no_receipt(self):
        credit_note = self._create_credit_note(reason='price_adjustment')
        credit_note.action_post()
        self.assertEqual(credit_note.state, 'posted')
        self.assertFalse(credit_note.return_picking_id)

    def test_reason_is_cleared_on_non_credit_notes(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.partner_a,
            products=self.storable_product, company=self.company)
        self.assertFalse(invoice.credit_note_reason)

    def test_receipt_is_cleared_when_reason_changes(self):
        picking = self._create_return_picking(self.partner_a)
        credit_note = self._create_credit_note(reason='goods_return', picking=picking)
        self.assertEqual(credit_note.return_picking_id, picking)
        credit_note.credit_note_reason = 'invoicing_error'
        self.assertFalse(credit_note.return_picking_id)

    # ------------------------------------------------------------------
    # GOODS RETURN CONTROL
    # ------------------------------------------------------------------

    def test_goods_return_without_receipt_is_blocked(self):
        credit_note = self._create_credit_note(reason='goods_return')
        with self.assertRaisesRegex(ValidationError, "No return receipt"):
            credit_note.action_post()
        self.assertEqual(credit_note.state, 'draft')

    def test_goods_return_with_valid_receipt_is_posted(self):
        picking = self._create_return_picking(self.partner_a)
        credit_note = self._create_credit_note(reason='goods_return', picking=picking)
        credit_note.action_post()
        self.assertEqual(credit_note.state, 'posted')
        self.assertEqual(picking.credit_note_ids, credit_note)
        self.assertEqual(picking.credit_note_count, 1)

    def test_goods_return_with_draft_receipt_is_blocked(self):
        picking = self._create_return_picking(self.partner_a, validate=False)
        credit_note = self._create_credit_note(reason='goods_return', picking=picking)
        with self.assertRaisesRegex(ValidationError, "not done yet"):
            credit_note.action_post()

    def test_receipt_of_another_customer_is_rejected(self):
        picking = self._create_return_picking(self.partner_b)
        with self.assertRaisesRegex(ValidationError, "does not belong to"):
            self._create_credit_note(reason='goods_return', picking=picking)

    def test_receipt_cannot_back_two_posted_credit_notes(self):
        picking = self._create_return_picking(self.partner_a)
        first = self._create_credit_note(reason='goods_return', picking=picking)
        first.action_post()

        second = self._create_credit_note(reason='goods_return', picking=picking)
        with self.assertRaisesRegex(ValidationError, "already backs"):
            second.action_post()

    def test_delivery_cannot_back_a_credit_note(self):
        delivery = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'partner_id': self.partner_a.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.customer_location.id,
        })
        with self.assertRaisesRegex(ValidationError, "is not a receipt"):
            self._create_credit_note(reason='goods_return', picking=delivery)

    # ------------------------------------------------------------------
    # AVAILABLE RECEIPTS
    # ------------------------------------------------------------------

    def test_available_receipts_exclude_other_customers_and_used_receipts(self):
        own_picking = self._create_return_picking(self.partner_a)
        other_picking = self._create_return_picking(self.partner_b)
        credit_note = self._create_credit_note()

        self.assertIn(own_picking, credit_note.available_return_picking_ids)
        self.assertNotIn(other_picking, credit_note.available_return_picking_ids)

        used = self._create_credit_note(reason='goods_return', picking=own_picking)
        used.action_post()

        other_credit_note = self._create_credit_note()
        self.assertNotIn(own_picking, other_credit_note.available_return_picking_ids)
        # The receipt stays selectable on the credit note that already uses it.
        self.assertIn(own_picking, used.available_return_picking_ids)

    # ------------------------------------------------------------------
    # EXCEPTION
    # ------------------------------------------------------------------

    def test_supervisor_bypasses_control_and_leaves_an_audit_trail(self):
        credit_note = self._create_credit_note(reason='goods_return')
        credit_note = credit_note.with_user(self.supervisor)
        credit_note.return_control_exception_reason = "Goods in transit, agreed with the customer."

        message_count = len(credit_note.message_ids)
        credit_note.action_post()

        self.assertEqual(credit_note.state, 'posted')
        self.assertEqual(len(credit_note.message_ids), message_count + 1)
        self.assertIn("Return control bypassed", credit_note.message_ids[0].body)
        self.assertIn("No return receipt", credit_note.message_ids[0].body)

    def test_exception_without_justification_still_blocks(self):
        credit_note = self._create_credit_note(reason='goods_return')
        with self.assertRaisesRegex(ValidationError, "No return receipt"):
            credit_note.with_user(self.supervisor).action_post()

    # ------------------------------------------------------------------
    # REVERSAL WIZARD
    # ------------------------------------------------------------------

    def test_reversal_wizard_carries_the_control_fields_over(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.partner_a, post=True,
            products=self.storable_product, company=self.company)
        picking = self._create_return_picking(self.partner_a)

        wizard = self.env['account.move.reversal'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({
            'move_ids': [Command.set(invoice.ids)],
            'journal_id': invoice.journal_id.id,
            'credit_note_reason': 'goods_return',
            'return_picking_id': picking.id,
        })
        self.assertIn(picking, wizard.available_return_picking_ids)

        wizard.reverse_moves()
        credit_note = invoice.reversal_move_id
        self.assertEqual(credit_note.credit_note_reason, 'goods_return')
        self.assertEqual(credit_note.return_picking_id, picking)

        credit_note.action_post()
        self.assertEqual(credit_note.state, 'posted')

    # ------------------------------------------------------------------
    # SMART BUTTON
    # ------------------------------------------------------------------

    def test_action_view_credit_notes(self):
        picking = self._create_return_picking(self.partner_a)
        credit_note = self._create_credit_note(reason='goods_return', picking=picking)
        credit_note.action_post()

        action = picking.action_view_credit_notes()
        self.assertEqual(action['res_id'], credit_note.id)
        self.assertEqual(action['res_model'], 'account.move')
