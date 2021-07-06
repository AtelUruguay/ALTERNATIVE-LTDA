# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    my_discount = fields.Float(string='Descuento a aplicar')

    @api.onchange('my_discount')
    def onchange_my_discount(self):
        for line in self.order_line:
            line.discount = self.my_discount
        return {'value': {'my_discount': 0}}


