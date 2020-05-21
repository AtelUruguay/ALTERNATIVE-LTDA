# -*- coding: utf-8 -*-


from odoo import models, fields, api


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        action = super(AccountMoveReversal, self).reverse_moves()
        if action:
            if 'res_id' in action:
                move = self.env['account.move'].browse(action['res_id'])
                if move.type in ('out_invoice', 'out_refund'):
                    move.invoice_send_fe_proinfo()
            elif 'domain' in action:
                for move in self.env['account.move'].browse(action['domain'][0][2]):
                    if move.type in ('out_invoice', 'out_refund'):
                        move.invoice_send_fe_proinfo()
            else:
                return
        return action
