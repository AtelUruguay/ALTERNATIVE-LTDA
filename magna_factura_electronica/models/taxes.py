# -*- coding: utf-8 -*-

from odoo import api, fields, models


class account_tax(models.Model):
    _inherit = "account.tax"

    fe_tax_codigo_dgi = fields.Many2one('fe_indicador_facturacion_dgi', string=u'Código de impuesto de la DGI', required=True)





class IndicadorFacturacionDgi(models.Model):
    _name = "fe_indicador_facturacion_dgi"

    code = fields.Char(u'Código', required=True, size=2)
    name = fields.Char('Nombre', required=True)
