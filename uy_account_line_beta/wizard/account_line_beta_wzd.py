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
from odoo import fields, models
from datetime import datetime, date
from odoo.tools import ustr, DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from dateutil.relativedelta import relativedelta
# from cStringIO import StringIO
from io import StringIO, BytesIO
import base64
import codecs
import logging

class account_line_beta_wzd(models.TransientModel):
    _name = 'account.line.beta.wzd'
    _rec_name = 'month'

    def get_account_tax_id(self, tax_line):
        invoice = tax_line.invoice_id
        for line in invoice.invoice_line:
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, invoice.partner_id)['taxes']
            for tax in taxes:
                if invoice.type in ('out_invoice','in_invoice'):
                    if tax['base_code_id'] == tax_line.base_code_id.id and tax['tax_code_id'] == tax_line.tax_code_id.id:
                        return tax['id']
                else:
                    if tax['ref_base_code_id'] == tax_line.base_code_id.id and tax['ref_tax_code_id'] == tax_line.tax_code_id.id:
                        return tax['id']
        return False

    def add_to_file(self, result_item, file_output):
        data = []
        data.append(result_item['vat'].zfill(12))               # Company VAT
        data.append(result_item['form'])                        # Form hardcode
        data.append(result_item['year_month'])                  # Wizard yearmonth
        data.append(result_item['rut'].zfill(12))               # Partner VAT
        data.append(result_item['date_invoice'])                # Invoice yearmonth
        data.append(result_item['line_beta'])                   # Line beta
        data.append(ustr(result_item['amount']))                # Tax Line Amount
        file_output.write(";".join(data) + ";\n")


    def action_next(self):
        # self.ensure_one()
        for row in self:
            logging.info('row.tax_ids: %s', row.tax_ids)

            delta = relativedelta(months=-1, day=1)
            _date = datetime.strptime("01-%s-%s"%(row['month'], row['year']), "%d-%m-%Y").date()
            buffer = BytesIO()
            codecinfo = codecs.lookup("utf8")
            file_to_save = codecs.StreamReaderWriter(buffer, codecinfo.streamreader, codecinfo.streamwriter)
            not_result = True
            self._group_results = []
            ac_move_line_obj = self.env['account.move.line']

            # todo chequear que sea solo rut o cedula las compras? un proveedor no es siempre con rut? en qué caso es la ci?
            # todo que hago con iva compras base? eso no es un tipo de impuesto, cómo lo mapeo????
            exentos_tax_ids = row.tax_ids.filtered(lambda x: x.type_tax_use == 'purchase' and x.tax_group_id.name == 'EXENTOS')
            gravados_tax_ids = list(set(row.tax_ids.ids) - set(exentos_tax_ids.ids))

            ac_move_line_gravados_ids = ac_move_line_obj.search([
                '&',('move_id.date', '>=', datetime.strftime(_date, DATE_FORMAT)),
                '&',('move_id.date', '<', datetime.strftime(_date - delta, DATE_FORMAT)),
                '&',('move_id.state', '=', 'posted'),
                '&',('tax_line_id', 'in', gravados_tax_ids),
                '|',('move_id.type', 'in', ['in_invoice', 'in_refund']),
                '&',('move_id.type', 'in', ['out_invoice','out_refund']),('partner_id.fe_tipo_documento','=', "2"),
                ])

            logging.info('gravados ac_move_line_ids.ids: %s', ac_move_line_gravados_ids.ids)
            logging.info('exentos_tax_ids: %s', exentos_tax_ids)

            # agregar los compras excentos
            # ir a buscar las lineas del mismo asiento que corresponde al valor base (tax_ids == row_tax.id)
            ac_move_line_exentos_ids = ac_move_line_obj.search([
                ('move_id.date', '>=', datetime.strftime(_date, DATE_FORMAT)),
                ('move_id.date', '<', datetime.strftime(_date - delta, DATE_FORMAT)),
                ('move_id.state', '=', 'posted'),
                ('tax_ids', 'in', exentos_tax_ids.ids),
                ('move_id.type', 'in', ['in_invoice', 'in_refund'])
            ])
            logging.info('exentos ac_move_line_ids.ids: %s', ac_move_line_exentos_ids.ids)


            ac_move_line_ids = ac_move_line_gravados_ids + ac_move_line_exentos_ids

            logging.info('todos ac_move_line_ids.ids: %s', ac_move_line_ids.ids)

            if ac_move_line_ids:

                def _do_action(self, ac_move_line, line_beta):
                    _found = False
                    rut = ac_move_line.partner_id.fe_numero_doc.strip() if ac_move_line.partner_id.fe_numero_doc else ""

                    for _r in self._group_results:
                        if _r['vat'] == ac_move_line.company_id.vat and _r['rut'] == rut and _r['line_beta'] == line_beta:
                            if ac_move_line.move_id.type in ['out_invoice']:
                                _r['amount'] += ac_move_line.credit
                            elif ac_move_line.move_id.type in ['out_refund']:
                                _r['amount'] -= ac_move_line.debit
                            elif ac_move_line.move_id.type in ['in_invoice']:
                                _r['amount'] += ac_move_line.debit
                            elif ac_move_line.move_id.type in ['in_refund']:
                                _r['amount'] -= ac_move_line.credit
                            _found = True
                            break
                    if not _found:
                        am = 0
                        if ac_move_line.move_id.type in ['out_invoice']:
                            am = ac_move_line.credit
                        elif ac_move_line.move_id.type in ['out_refund']:
                            am = ac_move_line.debit * (-1)
                        elif ac_move_line.move_id.type in ['in_invoice']:
                            am = ac_move_line.debit
                        elif ac_move_line.move_id.type in ['in_refund']:
                            am = ac_move_line.credit * (-1)
                        if am:
                            self._group_results.append({
                                'amount': round(am, 2),
                                'line_beta': line_beta,
                                'vat': ac_move_line.company_id.vat if ac_move_line.company_id.vat else "",
                                'rut': rut,
                                'year_month': row['year'] + row['month'],
                                'date_invoice': row['year'] + row['month'],
                                'form': "02181"  # It's a hardcode always?
                            })

                    logging.info('self._group_results: %s', self._group_results)


                for row_tax in row.tax_ids:
                    logging.info('row_tax.line_beta: %s', row_tax.line_beta)
                    if row_tax.line_beta: #domain?

                        logging.info('row_tax.id: %s', row_tax.id)
                        for ac_move_line in ac_move_line_ids:


                            logging.info('ac_move_line.tax_line_id.id: %s', ac_move_line.tax_line_id.id)
                            logging.info('ac_move_line.tax_ids.ids: %s', ac_move_line.tax_ids.ids)

                            if ac_move_line.tax_line_id.id == row_tax.id or ac_move_line.tax_ids.ids in [row_tax.id]:
                                _do_action(self, ac_move_line, row_tax.line_beta)

                if self._group_results:
                    file_to_save.write(";".join([ustr('RUT compañía'), 'Form', ustr('Año'), 'RUT cliente', 'Fecha', ustr('Código'), 'Monto'])+";\n")
                    for _r in self._group_results:
                        self.add_to_file(_r, file_to_save)
            _value = file_to_save.getvalue()
            if _value:
                not_result = False

            row.write({'state':'exported' if not not_result else 'init',
                        'file_name': 'linea_beta_' + row['year'] + row['month'] +'.'+row['file_format'] if not not_result else False,
                        'file': base64.encodebytes(_value) if not not_result else False,
                        'not_result': not_result
                    })
            file_to_save.close()

            return {'type':'ir.actions.act_window',
                    'name': u'Factura Línea Beta',
                    'res_model': 'account.line.beta.wzd',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id': row.id
                }


    def action_back(self):
        for rec in self:
            rec.write({'state':'init',
                    'file_name': False,
                    'file': False,
                    'not_result': False
                })
            return {'type':'ir.actions.act_window',
                'name': u'Factura Línea Beta',
                'res_model': 'account.line.beta.wzd',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_id': rec.id
                    }

    def _get_years(self):
        current_year = date.today().year
        select = [(ustr(year),ustr(year)) for year in range(current_year-10, current_year+1)]
        select.reverse()
        return select


    month = fields.Selection([('01', 'January'),
                            ('02', 'February'),
                            ('03', 'March'),
                            ('04', 'April'),
                            ('05', 'May'),
                            ('06', 'June'),
                            ('07', 'July'),
                            ('08', 'August'),
                            ('09', 'September'),
                            ('10', 'October'),
                            ('11', 'November'),
                            ('12', 'December')], string='Month', required=True, readonly=True, states={'init': [('readonly', False)]}, default=ustr(date.today().month) if date.today().month >= 10 else '0'+ustr(date.today().month))
    year = fields.Selection(_get_years, string='Year', required=True, readonly=True, states={'init': [('readonly', False)]}, default=ustr(date.today().year))
    file_format = fields.Selection([('txt','File (.txt)'),('csv','File (.csv)')], 'File format', required=True, readonly=True, states={'init': [('readonly', False)]}, default='txt')
    # 'tax_ids': fields.many2many('account.tax.code', 'account_line_beta_tax_code_wzd_rel', 'wzd_id', 'tax_code_id',
    #                             string='Account Taxes', domain=[('line_beta', '!=', False)], required=True,
    #                             readonly=True, states={'init': [('readonly', False)]}),
    tax_ids = fields.Many2many('account.tax', 'account_line_beta_tax_code_wzd_rel', 'wzd_id', 'tax_id', string='Account Taxes', domain=[('line_beta','!=',False)], required=True, readonly=True, states={'init': [('readonly', False)]})
    file_name = fields.Char('File name', size=128)
    file = fields.Binary('File')
    state = fields.Selection([('init','Init'),('exported','Exported')],'State', default='init')
    not_result = fields.Boolean('Not result')
    show_all = fields.Boolean('Show all')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
