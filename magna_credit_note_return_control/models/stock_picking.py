from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    credit_note_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='return_picking_id',
        string="Credit Notes",
        readonly=True,
        help="Credit notes issued for the goods returned through this receipt.",
    )
    credit_note_count = fields.Integer(
        string="Credit Notes Count",
        compute='_compute_credit_note_count',
    )

    @api.depends('credit_note_ids')
    def _compute_credit_note_count(self):
        for picking in self:
            picking.credit_note_count = len(picking.credit_note_ids)

    def _get_posted_credit_notes(self, exclude=None):
        """Posted credit notes backed by these receipts.

        :param exclude: account.move to leave out, typically the one being checked
        :return: account.move recordset
        """
        credit_notes = self.credit_note_ids.filtered(lambda move: move.state == 'posted')
        return credit_notes - exclude if exclude else credit_notes

    def action_view_credit_notes(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_move_out_refund_type')
        action['context'] = {'create': False}
        if len(self.credit_note_ids) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = self.credit_note_ids.id
        else:
            action['domain'] = [('id', 'in', self.credit_note_ids.ids)]
        return action
