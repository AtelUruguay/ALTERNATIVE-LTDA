# -*- coding: utf-8 -*-
from .base import SoapClientRequest
from .soap_request import SoapCotizacion

#Web service registry
SoapClientRequest.register('cotizacion', SoapCotizacion)
#Start Point
soap = SoapClientRequest()