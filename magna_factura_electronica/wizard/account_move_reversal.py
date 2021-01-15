# -*- coding: utf-8 -*-


from odoo import models, fields, api
import logging

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    # def reverse_moves(self):
    #     action = super(AccountMoveReversal, self).reverse_moves()
    #     logging.info('------------- action: %s', action)
    #
    #     if action:
    #
    #         if 'res_id' in action:
    #             logging.info('------------- action["res_id"]: %s', action['res_id'])
    #
    #             move = self.env['account.move'].browse(action['res_id'])
    #             if move.type in ('out_invoice', 'out_refund'):
    #                 logging.info('------------- move.type: %s', move.type)
    #
    #                 move.invoice_send_fe_proinfo()
    #         elif 'domain' in action:
    #             logging.info('------------- action["domain"]: %s', action['domain'][0][2])
    #
    #             for move in self.env['account.move'].browse(action['domain'][0][2]):
    #                 logging.info('------------- move.type: %s', move.type)
    #
    #                 if move.type in ('out_invoice', 'out_refund'):
    #                     move.invoice_send_fe_proinfo()
    #         else:
    #             return
    #     return action
