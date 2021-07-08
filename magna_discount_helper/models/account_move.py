# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class AccountMove(models.Model):
    _inherit = "account.move"

    my_discount = fields.Float(string='Descuento a aplicar')

    @api.onchange('my_discount')
    def onchange_my_discount(self):
        for rec in self:
            if rec.my_discount > 0:
                for line in rec.invoice_line_ids:
                    line.discount = rec.my_discount
                    # line._onchange_price_subtotal()
            return {'value': {'my_discount': 0}}
