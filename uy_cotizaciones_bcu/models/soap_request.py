# -*- coding: utf-8 -*-
from .base import SoapClientBase


class SoapCotizacion(SoapClientBase):
    """ Web Service Cotizacion"""

    def _prepare_request(self, post_data):
        # Por el momento no se hace nada
        return post_data

    def request_execute(self, model, post_data):
        if not isinstance(post_data, (dict,)):
            raise Exception(
                "Se espera un diccionario como valor de retorno. Se ha recibido el tipo: %s" % (type(post_data),))
        # url = 'https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcucotizaciones?wsdl'
        url = model.env['ir.config_parameter'].get_param('url_ws.bcu_cotizaciones')
        if not url:
            raise Exception(u'No se encuentra configurada la conexión con SICE.\n \
                Ir a: Configuración -> Parámetros -> Parámetros del sistema y cargar un registro \
                con clave url_ws.bcu_cotizaciones y valor la URL del servicio web.')
        self.ensure_connection(url=url, msg_attr='Servicio: Cotizaciones > Execute')
        _request = self._prepare_request(post_data)
        return self.client.service.Execute(_request)
