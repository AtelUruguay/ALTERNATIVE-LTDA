# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class AccountMove(models.Model):
    _inherit = "account.move"

    my_discount = fields.Float(string='Descuento a aplicar')

    @api.onchange('my_discount')
    def onchange_my_discount(self):
        for line in self.invoice_line_ids:
            line.discount = self.my_discount
        return {'value': {'my_discount': 0}}
