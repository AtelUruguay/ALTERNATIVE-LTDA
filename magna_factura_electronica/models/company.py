# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    fe_codigo_principal_sucursal = fields.Char(u'Código Casa Principal/Sucursal', size=4)


