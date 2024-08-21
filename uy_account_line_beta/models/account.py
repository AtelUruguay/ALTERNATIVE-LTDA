# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, api
from odoo import exceptions
from odoo import _

class account_tax(models.Model):
    _name = 'account.tax'
    _inherit = 'account.tax'

    line_beta = fields.Char('Line Beta', size=3)

    @api.constrains('line_beta')
    def _check_line_beta(self):
        for rec in self:
            if rec.line_beta:
                try:
                    int(rec.line_beta)
                except:
                    raise exceptions.ValidationError(_("The field 'Line Beta' must be a number of 3 digits"))

