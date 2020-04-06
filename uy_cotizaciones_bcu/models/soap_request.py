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
from .base import SoapClientBase

class SoapCotizacion(SoapClientBase):
    """ Web Service Cotizacion"""

    def _prepare_request(self, post_data):
        #Por el momento no se hace nada
        return post_data

    def request_execute(self, model, post_data):
        if not isinstance(post_data, (dict,)):
            raise Exception("Se espera un diccionario como valor de retorno. Se ha recibido el tipo: %s" % (type(post_data),))
        #url = 'https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcucotizaciones?wsdl'
        url = model.env['ir.config_parameter'].get_param('url_ws.bcu_cotizaciones')
        if not url:
            raise Exception(u'No se encuentra configurada la conexión con SICE.\n \
                Ir a: Configuración -> Parámetros -> Parámetros del sistema y cargar un registro \
                con clave url_ws.bcu_cotizaciones y valor la URL del servicio web.')
        self.ensure_connection(url=url, msg_attr = 'Servicio: Cotizaciones > Execute')
        _request = self._prepare_request(post_data)
        return self.client.service.Execute(_request)