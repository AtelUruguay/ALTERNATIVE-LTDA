# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    partner_id_email_related = fields.Char(related='partner_id.email')
    move_id_invoice_origin_related = fields.Char(related='move_id.invoice_origin')