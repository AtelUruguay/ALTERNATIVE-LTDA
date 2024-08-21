# -*- coding: utf-8 -*-
from odoo import models, fields, api


class InterfazMonedas(models.Model):
    _name = 'interfaz.monedas'
    _description = "Interfaz Monedas"

    codigo_bcu = fields.Char(u"Código moneda BCU", size=4, required=True, select=True,
                             help=u"Se debe colocar el código de 4 digitos de la moneda que se muestra en el archivo oficial del BCU.")
    currency_id = fields.Many2one('res.currency', 'Moneda', required=True, ondelete="cascade")
    company_id = fields.Many2one('res.company', u'Compañía Moneda', required=True)

    _sql_constraints = [
        ('unique_inter_conf_data', 'unique(codigo_bcu, currency_id, company_id)',
         'Ya existe un registro con los mismos datos.')
    ]

    @api.depends('currency_id.name', 'codigo_bcu')
    def _compute_display_name(self):
        for record in self:
            if record.currency_id.name and record.codigo_bcu:
                record.display_name = (record.id, "%s - %s" % (record.currency_id.name, record.codigo_bcu))
            else:
                super()._compute_display_name()
