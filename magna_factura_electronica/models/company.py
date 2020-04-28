# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # fe_nombre_fantasia = fields.Char(u'Nombre fantasia', size=50)
    fe_codigo_principal_sucursal = fields.Char(u'Código Casa Principal/Sucursal', size=4)


