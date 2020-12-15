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
            # buffer = StringIO()
            buffer = BytesIO()
            codecinfo = codecs.lookup("utf8")
            file_to_save = codecs.StreamReaderWriter(buffer, codecinfo.streamreader, codecinfo.streamwriter)

            not_result = True
            self._group_results = []
            ac_move_line_obj = self.env['account.move.line']
            # ac_move_line_ids = ac_move_line_obj.search([
            #     ('move_id.date','>=',datetime.strftime(_date, DATE_FORMAT)),
            #     ('move_id.date','<',datetime.strftime(_date-delta, DATE_FORMAT)),
            #     ('tax_code_id','in',[row_tax.id for row_tax in row.tax_ids if row_tax.line_beta])])

            # ac_move_line_ids = ac_move_line_obj.search([
            #     ('move_id.date', '>=', datetime.strftime(_date, DATE_FORMAT)),
            #     ('move_id.date', '<', datetime.strftime(_date - delta, DATE_FORMAT)),
            #     ('tax_ids', 'in', row.tax_ids.ids)])

            ac_move_line_ids = ac_move_line_obj.search([
                ('move_id.date', '>=', datetime.strftime(_date, DATE_FORMAT)),
                ('move_id.date', '<', datetime.strftime(_date - delta, DATE_FORMAT)),
                ('tax_ids', 'in', row.tax_ids.ids), ('partner_id','=',33185)])

            logging.info('len(ac_move_line_ids): %s', len(ac_move_line_ids))

            if ac_move_line_ids:

                def _do_action(self, ac_move_line, line_beta):
                    _found = False
                    rut = ac_move_line.partner_id.vat if ac_move_line.partner_id.vat else ""
                    if hasattr(ac_move_line.partner_id, 'fe_numero_doc'):
                        # todo asm ver que otros documentos
                        rut = ac_move_line.partner_id.fe_numero_doc.strip() if ac_move_line.partner_id.fe_numero_doc and ac_move_line.partner_id.fe_tipo_documento == "2" else ""
                    for _r in self._group_results:

                        logging.info('_r: %s', _r)
                        logging.info('ac_move_line.debit: %s', ac_move_line.debit)
                        logging.info('ac_move_line.credit: %s', ac_move_line.credit)
                        logging.info('ac_move_line.journal_id.type: %s', ac_move_line.journal_id.type)

                        if _r['vat'] == ac_move_line.company_id.vat and _r['rut'] == rut and _r['line_beta'] == line_beta:

                            if ac_move_line.debit:
                                if ac_move_line.journal_id.type == 'purchase':
                                    _r['amount'] += ac_move_line.debit
                                elif ac_move_line.journal_id.type == 'sale_refund':
                                    # if _r['amount'] < 0:
                                    #     _r['amount'] += (ac_move_line.debit * (-1))
                                    # else:
                                    #     _r['amount'] -= ac_move_line.debit
                                    if ac_move_line.debit < 0:
                                        _r['amount'] += (ac_move_line.debit * (-1))
                                    else:
                                        _r['amount'] -= ac_move_line.debit
                                else:
                                    _r['amount'] += ac_move_line.debit
                            elif ac_move_line.credit:
                                if ac_move_line.journal_id.type == 'sale':
                                    _r['amount'] += ac_move_line.credit
                                elif ac_move_line.journal_id.type == 'purchase_refund':
                                    # if _r['amount'] < 0:
                                    #     _r['amount'] += (ac_move_line.credit * (-1))
                                    # else:
                                    #     _r['amount'] -= ac_move_line.credit
                                    if ac_move_line.credit < 0:
                                        _r['amount'] += (ac_move_line.credit * (-1))
                                    else:
                                        _r['amount'] -= ac_move_line.credit
                                else:
                                    _r['amount'] += ac_move_line.credit
                                    # if _r['amount'] < 0:
                                    #     _r['amount'] = _r['amount'] + (ac_move_line.credit * (-1))
                                    # else:
                                    #     _r['amount'] -= ac_move_line.credit
                            _found = True
                            break
                    if not _found:
                        am = 0

                        logging.info('ac_move_line.debit: %s', ac_move_line.debit)
                        logging.info('ac_move_line.credit: %s', ac_move_line.credit)
                        logging.info('ac_move_line.journal_id.type: %s', ac_move_line.journal_id.type)

                        if ac_move_line.debit:
                            if ac_move_line.journal_id.type == 'purchase':
                                am = ac_move_line.debit
                            elif ac_move_line.journal_id.type == 'sale_refund':
                                am = -ac_move_line.debit
                            else:
                                am = ac_move_line.debit
                        elif ac_move_line.credit:
                            if ac_move_line.journal_id.type == 'sale':
                                am = ac_move_line.credit
                            elif ac_move_line.journal_id.type == 'purchase_refund':
                                am = -ac_move_line.credit
                            else:
                                am = ac_move_line.credit
                                # am = -ac_move_line.credit
                        if am:
                            self._group_results.append({
                                'amount': am,
                                'line_beta': line_beta,
                                'vat': ac_move_line.company_id.vat if ac_move_line.company_id.vat else "",
                                'rut': rut,
                                'year_month': row['year'] + row['month'],
                                'date_invoice': row['year'] + row['month'],
                                'form': "02181"  # It's a hardcode always?
                            })

                    logging.info('self._group_results: %s', self._group_results)


                for row_tax in row.tax_ids:
                    if row_tax.line_beta: #domain?
                        for ac_move_line in ac_move_line_ids:
                            # todo asm
                            # if ac_move_line.tax_code_id.id == row_tax.id:
                            logging.info('ac_move_line.tax_ids.ids: %s', ac_move_line.tax_ids.ids)
                            logging.info('row_tax.id: %s', row_tax.id)

                            if ac_move_line.tax_ids.ids == [row_tax.id]:
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
