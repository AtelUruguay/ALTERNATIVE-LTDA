from odoo import api, fields, models
from odoo.addons.account.models.account_move import TYPE_REVERSE_MAP

from ..models.account_move import CREDIT_NOTE_REASON_SELECTION


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    credit_note_reason = fields.Selection(
        selection=CREDIT_NOTE_REASON_SELECTION,
        string="Credit Note Reason",
        help="Reason carried over to the credit notes created by this wizard.",
    )
    return_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string="Return Receipt",
        check_company=True,
        help="Validated receipt proving that the customer returned the goods.",
    )
    available_return_picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string="Available Return Receipts",
        compute='_compute_available_return_picking_ids',
    )

    @api.depends('move_ids', 'company_id')
    def _compute_available_return_picking_ids(self):
        for wizard in self:
            partner = wizard.move_ids.commercial_partner_id
            if len(partner) == 1:
                wizard.available_return_picking_ids = self.env['account.move']._get_available_return_pickings(
                    partner, wizard.company_id,
                )
            else:
                wizard.available_return_picking_ids = False

    def _prepare_default_reversal(self, move):
        values = super()._prepare_default_reversal(move)
        if TYPE_REVERSE_MAP.get(move.move_type) == 'out_refund':
            values.update({
                'credit_note_reason': self.credit_note_reason,
                'return_picking_id': self.return_picking_id.id,
            })
        return values
