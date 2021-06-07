# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class AccountMove(models.Model):
    _inherit = "account.move"

    my_discount = fields.Float(string='Descuento a aplicar')

    def button_apply_discount(self):
        for rec in self:
            for line in rec.invoice_line_ids:
                line.discount = rec.my_discount


