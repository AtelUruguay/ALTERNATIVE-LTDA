# -*- coding: utf-8 -*-
#@author: Liber Matos
#@version: 1.0
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
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
from .soap import soap
from .base import Dic2Object
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging

class cotizaciones_wizard(models.TransientModel):
    _name = 'cotizaciones.wizard'
    _description = 'Wizard de cotizaciones'

    #columns
    fecha_desde = fields.Date('Fecha desde', required=True)
    fecha_hasta = fields.Date('Fecha hasta', required=True)

    @api.constrains('fecha_desde','fecha_hasta')
    def _check_dates(self):
        for row in self:
            if row.fecha_desde > row.fecha_hasta:
                raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")
            if row.fecha_hasta > fields.Date.today():
                raise ValidationError("La fecha de fin no puede ser mayor que la actual")

    @api.model
    def date_range(self, start_date, end_date):
        for n in range(int((end_date - start_date).days+1)):
            yield start_date + timedelta(days=n)

    @api.model
    def _execute(self, response, start_date, end_date):
        # if response.respuestastatus.status != 1:
        #     raise ValidationError(u"Ha ocurrido un error\n Código: %s \n Descripción: %s" % (response.respuestastatus.codigoerror, response.respuestastatus.mensaje))
        # if not response.datoscotizaciones[0]:
        #     raise ValidationError(u"No se obtuvo respuesta, vuelva a intentarlo más tarde")
        cur_rate_obj = self.env['res.currency.rate']
        int_conf_rows = self.env['interfaz.monedas'].search([('company_id','=',self.env.user.company_id.id)])
        time_diff = ' 03:00:00'

        if response:
            logging.info('RESPONSE: %s', response)
            #Demo
            # Fecha = 2017-05-03
            # Moneda = 9900
            # Nombre = "UNIDAD REAJUSTAB"
            # CodigoISO = "U.R."
            # Emisor = "URUGUAY"
            # TCC = 988.03
            # TCV = 988.03
            # ArbAct = 35.29561
            # FormaArbitrar = 0
            _soap_result= {}
            for data in response.datoscotizaciones[0]:
                if data.Moneda not in _soap_result:
                    _soap_result[data.Moneda] = {}
                _soap_result[data.Moneda][data.Fecha.strftime(DEFAULT_SERVER_DATE_FORMAT)] = Dic2Object({
                    'Fecha': data.Fecha,
                    'Moneda': data.Moneda,
                    'Nombre': data.Nombre,
                    'CodigoISO': data.CodigoISO,
                    'Emisor': data.Emisor,
                    'TCC': data.TCC,
                    'TCV': data.TCV,
                    'ArbAct': data.ArbAct,
                    'FormaArbitrar': data.FormaArbitrar
                })
            _date_not_found = {}
            logging.info('_soap_result: %s', _soap_result)
            for cursor_date in self.date_range(start_date, end_date):
                logging.info('cursor_date: %s', cursor_date)
                for inter in int_conf_rows:
                    cursor_date_iter = cursor_date

                    logging.info('inter.company_id.date_bcu: %s',inter.company_id.date_bcu)
                    if inter.company_id.date_bcu == '1':
                        cursor_date_iter = cursor_date + timedelta(days=-1)
                        cursor_date_find = cursor_date_iter
                    else:
                        cursor_date_find = cursor_date_iter + timedelta(days=-1)

                    cursor_date_str = cursor_date_iter.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    cursor_date_find_str = cursor_date_find.strftime(DEFAULT_SERVER_DATE_FORMAT)

                    logging.info('cursor_date_iter: %s', cursor_date_iter)
                    logging.info('cursor_date_str: %s', cursor_date_str)
                    logging.info('cursor_date_find_str: %s', cursor_date_find_str)
                    #Moneda Code
                    code = int(inter.codigo_bcu)
                    if code in _soap_result:
                        if cursor_date_find_str in _soap_result[code]:
                            _d = _soap_result[code][cursor_date_find_str]
                            #Rate
                            rate = _d.TCC
                            if inter.company_id.currency_id.symbol == 'USD':
                                rate = _d.ArbAct
                            # rate = round(1.0000 / rate, 6)

                            date_rate_str = cursor_date_str + time_diff
                            cur_rate_rows = cur_rate_obj.search([('currency_id','=',inter.currency_id.id),('name','=',date_rate_str)])
                            if cur_rate_rows:
                                for cur_rate in cur_rate_rows:
                                    cur_rate.write({'rate': rate})
                            else:
                                cur_rate_obj.create({
                                        # 'rate': rate,
                                        'inverse_rate': rate,
                                        'currency_id': inter.currency_id.id,
                                        'name': date_rate_str
                                })
                        else:
                            if code not in _date_not_found:
                                _date_not_found[code] = {}
                            _date_not_found[code][cursor_date_find_str] = Dic2Object({
                                'cursor_date_find_str': cursor_date_find_str,
                                'cursor_date_str': cursor_date_str,
                                'currency_id': inter.currency_id.id,
                            })
            #UPDATE LOST (feriados, fin de semana, fuera del rango menor)
            if _date_not_found:
                for code, value in _date_not_found.items():
                    for _d in value.values():

                        date_rate_str = _d.cursor_date_str + time_diff
                        cur_rate_row_prev = cur_rate_obj.search([('currency_id','=',_d.currency_id),('name','<',_d.cursor_date_str)], order='name DESC', limit=1)
                        cur_rate_not_rows = cur_rate_obj.search([('currency_id','=',_d.currency_id),('name','=',date_rate_str)])
                        if cur_rate_row_prev:
                            if cur_rate_not_rows:
                                for cur_rate in cur_rate_not_rows:
                                    cur_rate.write({'rate': cur_rate_row_prev.rate})
                            else:
                                cur_rate_obj.create({
                                        # 'rate': cur_rate_row_prev.rate,
                                        'inverse_rate': cur_rate_row_prev.rate,
                                        'currency_id': _d.currency_id,
                                        'name': date_rate_str
                                })
        else:
            #Se valida porque puede que no cumpla para ningún día del rango seleccionado
            for cursor_date in self.date_range(start_date, end_date):
                for inter in int_conf_rows:
                    cursor_date_iter = cursor_date
                    if inter.company_id.date_bcu == '1':
                        cursor_date_iter = cursor_date + timedelta(days=-1)
                        cursor_date_find = cursor_date_iter
                    else:
                        cursor_date_find = cursor_date_iter + timedelta(days=-1)
                    cursor_date_str = cursor_date_iter.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    cursor_date_find_str = cursor_date_find.strftime(DEFAULT_SERVER_DATE_FORMAT)

                    date_rate_str = cursor_date_str + time_diff
                    cur_rate_row_prev = cur_rate_obj.search([('currency_id','=',inter.currency_id.id),('name','<',cursor_date_str)], order='name DESC', limit=1)
                    cur_rate_not_rows = cur_rate_obj.search([('currency_id','=',inter.currency_id.id),('name','=',date_rate_str)])
                    if cur_rate_row_prev:
                        if not cur_rate_not_rows:
                            cur_rate_obj.create({
                                    # 'rate': cur_rate_row_prev.rate,
                                    'inverse_rate': cur_rate_row_prev.rate,
                                    'currency_id': inter.currency_id.id,
                                    'name': date_rate_str
                            })
                        #Esto se suspende porque puede introducir errores de datos al sistema.
                        #Solo se crea no se actualiza...
                        # if cur_rate_not_rows:
                        #     for cur_rate in cur_rate_not_rows:
                        #         cur_rate.write({'rate': cur_rate_row_prev.rate})
                        # else:
                        #     cur_rate_obj.create({
                        #             'rate': cur_rate_row_prev.rate,
                        #             'currency_id': inter.currency_id.id,
                        #             'name': cursor_date_str
                        #     })
        return True

    def cotizacion_response(self, response):
        #Se reponen 1 día que se quitó porque el objetivo era obtener los resultados de 1 día antes siempre
        return self._execute(response, self.env.context['start_date'] + timedelta(days=1), self.env.context['end_date'])

    @soap.cotizacion(request="execute", response="cotizacion_response", trigger_error=False, new_api=True)
    def _send_date_range(self):
        self.ensure_one()
        items = [item.codigo_bcu for item in self.env['interfaz.monedas'].search([])]
        if not items:
            raise ValidationError("No existen configurada ninguna Moneda Interfaz")
        return {
                    'Moneda': {'item': items},
                    'FechaDesde': self.env.context['start_date'],
                    'FechaHasta': self.env.context['end_date'],
                    'Grupo': 0
        }

    def action_update(self):
        self.ensure_one()
        self.with_context({
            'start_date': self.fecha_desde + timedelta(days=-1),
            'end_date': self.fecha_hasta})._send_date_range()
        return True

    @soap.cotizacion(request="execute", response="cotizacion_response", trigger_error=False, new_api=True)
    def _cron_send_date_range(self):
        # items = self.env.context['items']
        items = [item.codigo_bcu for item in self.env['interfaz.monedas'].search([])]
        if not items:
            return {}
        return {
                    # 'Moneda': {'item': self.env.context['items']},
                    'Moneda': {'item': items},
                    'FechaDesde': self.env.context['start_date'],
                    'FechaHasta': self.env.context['end_date'],
                    'Grupo': 0
        }

    @api.model
    def cron_action_update(self):
        # items = [item.codigo_bcu for item in self.env['interfaz.monedas'].search([])]
        cur_rate_obj = self.env['res.currency.rate']
        int_conf_rows = self.env['interfaz.monedas'].search([('company_id','=',self.env.user.company_id.id)])
        #Esto lo hace sin importar el UTC
        self.env.cr.execute("SELECT to_char(now(), 'YYYY-MM-DD')")
        end_date = self.env.cr.fetchone()[0]
        # ASM Ini
        end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).date()
        # ASM Fin
        start_date = end_date
        logging.info('start_date: %s',start_date)
        for inter in int_conf_rows:
            # start_date = end_date
            rate = cur_rate_obj.search([('currency_id','=',inter.currency_id.id),('name','<',start_date)], order='name DESC', limit=1)
            if rate:
                logging.info('rate.name: %s', rate.name)
                start_date = rate.name
                # start_date = start_date.split(' ')[0]
            self.with_context({
                # 'items': [inter.codigo_bcu,],
                'start_date': start_date + timedelta(days=-1),
                'end_date': end_date
            })._cron_send_date_range()
        return True