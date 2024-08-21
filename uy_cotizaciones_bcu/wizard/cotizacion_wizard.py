# -*- coding: utf-8 -*-
import logging
from datetime import timedelta, datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from ..models.soap import soap
from ..models.base import Dic2Object


_logger = logging.getLogger(__name__)


class cotizaciones_wizard(models.TransientModel):
    _name = 'cotizaciones.wizard'
    _description = 'Wizard de cotizaciones'

    # columns
    fecha_desde = fields.Date('Fecha desde', required=True)
    fecha_hasta = fields.Date('Fecha hasta', required=True)

    @api.constrains('fecha_desde', 'fecha_hasta')
    def _check_dates(self):
        for row in self:
            if row.fecha_desde > row.fecha_hasta:
                raise ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin")
            if row.fecha_hasta > fields.Date.today():
                raise ValidationError("La fecha de fin no puede ser mayor que la actual")

    @api.model
    def date_range(self, start_date, end_date):
        for n in range(int((fields.Date.from_string(end_date) - fields.Date.from_string(start_date)).days + 1)):
            yield fields.Date.from_string(start_date) + timedelta(days=n)

    @api.model
    def _execute(self, response, start_date, end_date):
        cur_rate_obj = self.env['res.currency.rate']
        int_conf_rows = self.env['interfaz.monedas'].search([('company_id', '=', self.env.user.company_id.id)])
        if response:
            _soap_result = {}
            for data1 in response.datoscotizaciones:
                data2 = data1[1]
                for data in data2:
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
                    # Moneda Code
                    code = int(inter.codigo_bcu)
                    if code in _soap_result:
                        if cursor_date_find_str in _soap_result[code]:
                            _d = _soap_result[code][cursor_date_find_str]
                            # Rate
                            rate = _d.TCC
                            if inter.company_id.currency_id.symbol == 'USD':
                                rate = _d.ArbAct
                            # rate = round(1.0000 / rate, 6)

                            cur_rate_rows = cur_rate_obj.search(
                                [('currency_id', '=', inter.currency_id.id), ('name', '=', cursor_date_str)])
                            if cur_rate_rows:
                                for cur_rate in cur_rate_rows:
                                    # cur_rate.write({'rate': rate})
                                    cur_rate.write({'inverse_company_rate': rate})
                            else:
                                cur_rate_obj.create({
                                    # 'rate': rate,
                                    'inverse_company_rate': rate,
                                    'currency_id': inter.currency_id.id,
                                    'name': cursor_date_str
                                })
                        else:
                            if code not in _date_not_found:
                                _date_not_found[code] = {}
                            _date_not_found[code][cursor_date_find_str] = Dic2Object({
                                'cursor_date_find_str': cursor_date_find_str,
                                'cursor_date_str': cursor_date_str,
                                'currency_id': inter.currency_id.id,
                            })
            # UPDATE LOST (feriados, fin de semana, fuera del rango menor)
            if _date_not_found:
                for code, value in _date_not_found.items():
                    for _d in value.values():
                        cur_rate_row_prev = cur_rate_obj.search(
                            [('currency_id', '=', _d.currency_id), ('name', '<', _d.cursor_date_str)],
                            order='name DESC', limit=1)
                        cur_rate_not_rows = cur_rate_obj.search(
                            [('currency_id', '=', _d.currency_id), ('name', '=', _d.cursor_date_str)])
                        if cur_rate_row_prev:
                            if cur_rate_not_rows:
                                for cur_rate in cur_rate_not_rows:
                                    # cur_rate.write({'rate': cur_rate_row_prev.rate})
                                    cur_rate.write({'inverse_company_rate': cur_rate_row_prev.inverse_company_rate})
                            else:
                                cur_rate_obj.create({
                                    # 'rate': cur_rate_row_prev.rate,
                                    'inverse_company_rate': cur_rate_row_prev.inverse_company_rate,
                                    'currency_id': _d.currency_id,
                                    'name': _d.cursor_date_str
                                })
        else:
            # Se valida porque puede que no cumpla para ningún día del rango seleccionado
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
                    cur_rate_row_prev = cur_rate_obj.search(
                        [('currency_id', '=', inter.currency_id.id), ('name', '<', cursor_date_str)], order='name DESC',
                        limit=1)
                    cur_rate_not_rows = cur_rate_obj.search(
                        [('currency_id', '=', inter.currency_id.id), ('name', '=', cursor_date_str)])
                    if cur_rate_row_prev:
                        if not cur_rate_not_rows:
                            cur_rate_obj.create({
                                # 'rate': cur_rate_row_prev.rate,
                                'inverse_company_rate': cur_rate_row_prev.inverse_company_rate,
                                'currency_id': inter.currency_id.id,
                                'name': cursor_date_str
                            })
        return True

    def cotizacion_response(self, response):
        # Se reponen 1 día que se quitó porque el objetivo era obtener los resultados de 1 día antes siempre
        return self._execute(response, (
                fields.Date.from_string(self.env.context['start_date']) + timedelta(days=1)).strftime(
            DEFAULT_SERVER_DATE_FORMAT),
                             self.env.context['end_date'])

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
            'start_date': (self.fecha_desde + timedelta(days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
            'end_date': self.fecha_hasta.strftime(DEFAULT_SERVER_DATE_FORMAT)
        })._send_date_range()
        return True

    @soap.cotizacion(request="execute", response="cotizacion_response", trigger_error=True, new_api=True)
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
        int_conf_rows = self.env['interfaz.monedas'].search([('company_id', '=', self.env.user.company_id.id)])
        # Esto lo hace sin importar el UTC
        self.env.cr.execute("SELECT to_char(now(), 'YYYY-MM-DD')")
        end_date = self.env.cr.fetchone()[0]
        # ASM Ini
        end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).date()
        # ASM Fin
        start_date = end_date
        for inter in int_conf_rows:
            # start_date = end_date
            rate = cur_rate_obj.search([('currency_id', '=', inter.currency_id.id), ('name', '<', start_date)],
                                       order='name DESC', limit=1)
            if rate:
                start_date = rate.name
            self.with_context({
                # 'items': [inter.codigo_bcu,],
                'start_date': (start_date + timedelta(days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT),
                'end_date': end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            })._cron_send_date_range()
        return True
