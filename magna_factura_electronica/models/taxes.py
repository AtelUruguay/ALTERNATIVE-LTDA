# -*- coding: utf-8 -*-

from odoo import api, fields, models


class account_tax(models.Model):
    _inherit = "account.tax"

    fe_indicador_facturacion = fields.Char('Código de impuesto de la DGI', size=2),


