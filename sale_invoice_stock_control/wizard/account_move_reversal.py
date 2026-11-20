from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    reserved_stock_move_ids = fields.Many2many(
        comodel_name='stock.move',
        string="Reserved Goods",
        compute='_compute_reserved_stock_move_ids',
        help="Goods reserved for the invoices being reversed, in pending deliveries.",
    )
    release_stock_reservation = fields.Selection(
        selection=[
            ('yes', "Yes, release the reservation"),
            ('no', "No, keep the reservation"),
        ],
        string="Release Stock Reservation",
        help="Only applies to credit notes (Reverse button). The reservation is "
             "released when the credit note is posted.",
    )

    @api.depends('move_ids')
    def _compute_reserved_stock_move_ids(self):
        for wizard in self:
            wizard.reserved_stock_move_ids = wizard.move_ids._get_stock_reserved_moves()

    def _prepare_default_reversal(self, move):
        values = super()._prepare_default_reversal(move)
        if move.move_type == 'out_invoice':
            values['release_stock_reservation'] = bool(
                self.env.context.get('release_stock_reservation'))
        return values

    def refund_moves(self):
        self.ensure_one()
        if self.reserved_stock_move_ids and not self.release_stock_reservation:
            raise UserError(_(
                "The invoices being reversed have goods reserved in pending deliveries. "
                "Please indicate whether the reservation must be released."
            ))
        return super(AccountMoveReversal, self.with_context(
            release_stock_reservation=self.release_stock_reservation == 'yes',
        )).refund_moves()
