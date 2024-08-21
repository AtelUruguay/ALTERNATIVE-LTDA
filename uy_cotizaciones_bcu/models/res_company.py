# -*- coding: utf-8 -*-
from odoo import models, fields

class res_company(models.Model):
    _inherit = 'res.company'

    date_bcu = fields.Selection([
            ('1', 'Restar 1 dia'),
            ('2', 'Fecha actual'), ], 'Fecha BCU', default='2', help=u"Restar 1 dia: resta un día a la cotización del BCU")