# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class InterfazMonedas(models.Model):
    _name = 'interfaz.monedas'
    _description = 'Interfaz de monedas'


    #Para esto es necesario configurar cada modena del sistema
    # @api.model
    # def _default_company(self):
    #     return self.env['res.company']._company_default_get('res.partner')

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, "%s - %s" % (record.currency_id.name, record.codigo_bcu)))
        return res

    codigo_bcu = fields.Char(u"Código moneda BCU", size=4, required=True, index=True, help=u"Se debe colocar el código de 4 digitos de la moneda que se muestra en el archivo oficial del BCU.")
    currency_id = fields.Many2one('res.currency', 'Moneda', required=True, ondelete="cascade")
    company_id = fields.Many2one('res.company', u'Compañía Moneda', required=True)

    _sql_constraints = [
        ('unique_inter_conf_data', 'unique(codigo_bcu, currency_id, company_id)', 'Ya existe un registro con los mismos datos.')
    ]