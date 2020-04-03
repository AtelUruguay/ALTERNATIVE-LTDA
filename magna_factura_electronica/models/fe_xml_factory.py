import string
from xml.dom.minidom import Document, parse
import time
import base64
import logging
from math import fabs
# from suds.client import Client
# from suds.cache import NoCache
# from suds.plugin import MessagePlugin
# import ssl
# from functools import wraps
# from openerp import models, api
# from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

# Request
# <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:com="com.esignit.fe">
#    <soapenv:Header/>
#    <soapenv:Body>
#       <com:FEGeneraryFirmarDocumento.Execute>
#          <com:Inxmlentrada>?</com:Inxmlentrada>
#          <com:Tipocfe>?</com:Tipocfe>
#          <com:Fefacturaimportadaloteid>?</com:Fefacturaimportadaloteid>
#       </com:FEGeneraryFirmarDocumento.Execute>
#    </soapenv:Body>
# </soapenv:Envelope>

# <CFEEntrada xmlns="com.esignit.fe">
# 	<XMLEntradaNodoCFE>
# 		<FEIDDocTipoCFE>111</FEIDDocTipoCFE>
# 		<FEIDDocSerie>A</FEIDDocSerie>
# 		<FEIDDocNro>1</FEIDDocNro>
# 		<FEIDDocFchEmis>2016-04-18</FEIDDocFchEmis>
# 		<FEIDDocFmaPago>1</FEIDDocFmaPago>
# 		<FEIDDocFchVenc>2016-12-31</FEIDDocFchVenc>
# 		<FEEMIRUCEmisor>216224460012</FEEMIRUCEmisor>
# 		<FEEMIRznSoc>MENDIOROZ Y POSADA S.R.L.</FEEMIRznSoc>
# 		<FEEMINomComercial/>
# 		<FEEMICdgDGISucur>1</FEEMICdgDGISucur>
# 		<FEEMIDomFiscal/>
# 		<FEEMICiudad>MONTEVIDEO</FEEMICiudad>
# 		<FEEMIDepartamento>Montevideo</FEEMIDepartamento>
# 		<FERECTipoDocRecep>2</FERECTipoDocRecep>
# 		<FERECCodPaisRecep>UY</FERECCodPaisRecep>
# 		<FERECDocRecep>214844360018</FERECDocRecep>
# 		<FERECRznSocRecep>DGI</FERECRznSocRecep>
# 		<FERECDirRecep>FERNANDEZ CRESPO 1534</FERECDirRecep>
# 		<FERECCiudadRecep>MONTEVIDEO</FERECCiudadRecep>
# 		<FERECDeptoRecep/>
# 		<FETOTTpoMoneda>UYU</FETOTTpoMoneda>
# 		<FETOTMntNoGrv>0.00</FETOTMntNoGrv>
# 		<FETOTMntNetoIvaTasaMin>0.00</FETOTMntNetoIvaTasaMin>
# 		<FETOTMntNetoIVATasaBasica>20000.00</FETOTMntNetoIVATasaBasica>
# 		<FETOTIVATasaBasica>22.000</FETOTIVATasaBasica>
# 		<FETOTMntIVATasaMin>0.00</FETOTMntIVATasaMin>
# 		<FETOTMntIVATasaBasica>4400.00</FETOTMntIVATasaBasica>
# 		<FETOTMntTotal>24400.00</FETOTMntTotal>
# 		<FETOTCantLinDet>3</FETOTCantLinDet>
# 		<FETOTMontoNF>5000.00</FETOTMontoNF>
# 		<FETOTMntPagar>29400.00</FETOTMntPagar>
# 		<FEDetalles>
# 			<FEDetalle>
# 				<FEDETNroLinDet>1</FEDETNroLinDet>
# 				<FEDETIndFact>3</FEDETIndFact>
# 				<FEDETNomItem>aaa</FEDETNomItem>
# 				<FEDETCantidad>10.000</FEDETCantidad>
# 				<FEDETUniMed>kg</FEDETUniMed>
# 				<FEDETPrecioUnitario>1000.000000</FEDETPrecioUnitario>
# 				<FEDETMontoItem>10000.00</FEDETMontoItem>
# 			</FEDetalle>
# 			<FEDetalle>
# 				<FEDETNroLinDet>2</FEDETNroLinDet>
# 				<FEDETIndFact>3</FEDETIndFact>
# 				<FEDETNomItem>bbb</FEDETNomItem>
# 				<FEDETCantidad>5.000</FEDETCantidad>
# 				<FEDETUniMed>kg</FEDETUniMed>
# 				<FEDETPrecioUnitario>2000.000000</FEDETPrecioUnitario>
# 				<FEDETMontoItem>10000.00</FEDETMontoItem>
# 			</FEDetalle>
# 			<FEDetalle>
# 				<FEDETNroLinDet>3</FEDETNroLinDet>
# 				<FEDETIndFact>6</FEDETIndFact>
# 				<FEDETNomItem>ccc</FEDETNomItem>
# 				<FEDETCantidad>1.000</FEDETCantidad>
# 				<FEDETUniMed>N/A</FEDETUniMed>
# 				<FEDETPrecioUnitario>5000.000000</FEDETPrecioUnitario>
# 				<FEDETMontoItem>5000.00</FEDETMontoItem>
# 			</FEDetalle>
# 		</FEDetalles>
# 	</XMLEntradaNodoCFE>
# 	<XMLEntradaNodoAdicional>
# 		<TipoDocumentoId>111</TipoDocumentoId>
# 		<DocComCodigo>1</DocComCodigo>
# 		<DocComSerie>A</DocComSerie>
# 		<SucursalId>1</SucursalId>
# 		<Adenda/>
# 		<CAEDnro>1</CAEDnro>
# 		<CAEHnro>100</CAEHnro>
# 		<CAENA>20160001110</CAENA>
# 		<CAEFA>2016-01-01</CAEFA>
# 		<CAEFVD>2017-12-31</CAEFVD>
# 		<LoteId>0</LoteId>
# 		<CorreoReceptor/>
# 		<EsReceptor>false</EsReceptor>
# 	</XMLEntradaNodoAdicional>
# </CFEEntrada>


# -*- coding: utf-8 -*-
from xml.dom.minidom import Document, parse
import time
import base64
import logging



debug=True

def loguear(text):
    if debug:
        logging.info(text)


class cfeFactoryOptionsProductLineDetail():
    _cantidad = 0
    _nombreItem = ''
    _unidadMedidad = 0
    _precioUnitario = 0
    _montoItem = 0
    _indicadorFacturacion = 0

class cfeFactoryOptions():

    _fechaVencimientoYYYYMMDD=''
    _fechaComprobanteYYYYMMDD = ''
    _esContingencia = False

    _tipoComprobante = 0
    _serieComprobante = 0
    _numeroComprobante = 0

    _emisorRuc = ''
    _emisorNombre = ''
    _emisorDomicilioFiscal = ''
    _emisorNombreComercial = ''
    _emisorCodigoCasaPrincipal = ''
    _emisorCiudad = ''
    _emisorDepartamento = ''

    _receptorTipoDocumento=''
    _receptorCodigoPais=''
    _receptorDocumento=''
    _receptorRazonSocial=''
    _receptorDireccion=''
    _receptorCiudad=''
    _receptorDepartamento=''

    _formaPago = 0
    _tipoMonedaTransaccion = ''
    # _montoTotalImpuestoPercibido = 0
    _montoTotalNoGravado = 0
    _montoTotalAPagar = 0
    # _montoSubtotal = 0
    # _montoTotalExportacionAsimiladas=0
    # _montoTotalImpuestoPercibido=0
    # _montoTotalIVASuspenso=0
    _montoNetoIVATasaMinima=0
    _montoNetoIVATasaBasica=0
    # _montoNetoIVATasaOtra=0
    _IVATasaMinima=0
    _IVATasaBasica=0
    # _montoIVATasaMinima=0
    _montoIVATasaBasica=0
    # _montoIVATasaOtra=0
    _montoTotal=0

    _lineasDetalle = [] #invoice.invoice_line

    _adicionalTipoDocumentoId = 0
    _adicionalDocComCodigo = ''
    _adicionalDocComSerie = ''
    _adicionalSucursalId = 0
    _adicionalAdenda = ''
    _adicionalCAEDnro = 0
    _adicionalCAEHnro = 0
    _adicionalCAENA = ''
    _adicionalCAEFA = ''
    _adicionalCAEFVD = ''
    _adicionalLoteId = 0
    _adicionalCorreoReceptor = ''
    _adicionalEsReceptor = ''


    def __init__(self):
        pass

class cfeFactory():
    opt=cfeFactoryOptions()

    def __init__(self, options=None):
        self.opt = options

    def getXML(self):
        doc = Document()

        CFEEntrada = doc.createElement("<CFEEntrada>")
        CFEEntrada.setAttribute("xmlns", 'com.esignit.fe')
        doc.appendChild(CFEEntrada)
        XMLEntradaNodoCFE = doc.createElement("<XMLEntradaNodoCFE>")
        CFEEntrada.appendChild(XMLEntradaNodoCFE)

        # *** 1.1 - INICIO IDENTIFICADOR DEL COMPROBANTE ***
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocTipoCFE', str(self.opt._tipoComprobante))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocSerie', str(self.opt._serieComprobante))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocNro', str(self.opt._numeroComprobante))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocFchEmis', str(self.opt._fechaComprobanteYYYYMMDD))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocFmaPago', str(self.opt._formaPago))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocFchVenc', str(self.opt._fechaVencimientoYYYYMMDD))

        # EMISOR
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIRUCEmisor', str(self.opt._emisorRuc))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIRznSoc', str(self.opt._emisorNombre))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMINomComercial', str(self.opt._emisorNombreComercial))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMICdgDGISucur', str(self.opt._emisorCodigoCasaPrincipal))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIDomFiscal', str(self.opt._emisorDomicilioFiscal))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMICiudad', str(self.opt._emisorCiudad))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIDepartamento', str(self.opt._emisorDepartamento))

        # RECEPTOR
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECTipoDocRecep', str(self.opt._receptorTipoDocumento))
        cod_pais_receptor = self.opt._receptorCodigoPais
        if cod_pais_receptor:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECCodPaisRecep', cod_pais_receptor)
        if self.opt._receptorDocumento:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECDocRecep', self.opt._receptorDocumento)

        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECRznSocRecep', str(self.opt._receptorRazonSocial))

        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECDirRecep', str(self.opt._receptorDireccion))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECCiudadRecep', str(self.opt._receptorCiudad))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECDeptoRecep', str(self.opt._receptorDepartamento))


        # TOTALES DE ENCABEZADO
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTTpoMoneda', str(self.opt._tipoMonedaTransaccion))
        if self.opt._montoTotalNoGravado: #Tiene valor sólo si es exento de iva o no tiene impuestos (monto total de lineas que no tienen impuestos o exentos de iva)
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNoGrv', "{0:.2f}".format(self.opt._montoTotalNoGravado).replace(".", ".").replace('-',''))
        else:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNoGrv', '0.00')
        if self.opt._montoNetoIVATasaMinima:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNetoIvaTasaMin', "{0:.2f}".format(self.opt._montoNetoIVATasaMinima).replace(".", "."))
        if self.opt._montoNetoIVATasaBasica:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNetoIVATasaBasica', "{0:.2f}".format(self.opt._montoNetoIVATasaBasica).replace(".", "."))
        if self.opt._IVATasaBasica:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTIVATasaBasica', "{0:.3f}".format(self.opt._IVATasaBasica).replace(".", "."))
        if self.opt._IVATasaMinima:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntIVATasaMin', "{0:.3f}".format(self.opt._IVATasaMinima).replace(".", "."))
        if self.opt._montoIVATasaBasica:
            self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntIVATasaBasica', "{0:.2f}".format(self.opt._montoIVATasaBasica).replace(".", "."))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntTotal',  "{0:.2f}".format(self.opt._montoTotal).replace(".", ".").replace('-',''))
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTCantLinDet', str(len(self.opt._lineasDetalle)))
        # todo poner el campo correcto
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMontoNF',  "{0:.2f}".format(self.opt._montoTotal).replace(".", ".").replace('-',''))
        
        self.set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntPagar', "{0:.2f}".format(self.opt._montoTotalAPagar).replace(".", "."))
        # FIN ENCABEZADO


        # INICIO DETALLE
        ZonaDetalle = doc.createElement("FEDetalles")
        XMLEntradaNodoCFE.appendChild(ZonaDetalle)
        nroSecuencial = 0
        for linea in self.opt._lineasDetalle:
            if linea._precioUnitario < 0 or linea._cantidad < 0:
                continue
            nroSecuencial += 1
            SubZonaItem = doc.createElement("FEDetalle")
            ZonaDetalle.appendChild(SubZonaItem)
            self.set_fe_node_data(doc, SubZonaItem, 'FEDETNroLinDet', str(nroSecuencial))
            self.set_fe_node_data(doc, SubZonaItem, 'FEDETIndFact', linea._indicadorFacturacion)
            self.set_fe_node_data(doc, SubZonaItem, 'FEDETNomItem', linea._nombreItem)
            self.set_fe_node_data(doc, SubZonaItem, 'FEDETCantidad', linea._cantidad)
            if linea._unidadMedidad:
                self.set_fe_node_data(doc, SubZonaItem, 'FEDETUniMed', linea._unidadMedidad)
            self.set_fe_node_data(doc, SubZonaItem, 'FEDETPrecioUnitario', "{0:.6f}".format(linea._precioUnitario).replace(".", "."))
            self.set_fe_node_data(doc, SubZonaItem, 'FEDETMontoItem', "{0:.2f}".format(linea._montoItem).replace(".", "."))
        # FIN DETALLE


        # INICIO NODO ADICIONAL
        XMLEntradaNodoAdicional = doc.createElement("<XMLEntradaNodoAdicional>")
        CFEEntrada.appendChild(XMLEntradaNodoAdicional)
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'TipoDocumentoId', str(self.opt._adicionalTipoDocumentoId))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'DocComCodigo', str(self.opt._adicionalDocComCodigo))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'DocComSerie', str(self.opt._adicionalDocComSerie))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'SucursalId', str(self.opt._adicionalSucursalId))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'Adenda', str(self.opt._adicionalAdenda))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEDnro', str(self.opt._adicionalCAEDnro))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEHnro', str(self.opt._adicionalCAEHnro))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAENA', str(self.opt._adicionalCAENA))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEFA', str(self.opt._adicionalCAEFA))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEFVD', str(self.opt._adicionalCAEFVD))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'LoteId', str(self.opt._adicionalLoteId))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CorreoReceptor', str(self.opt._adicionalCorreoReceptor))
        self.set_fe_node_data(doc, XMLEntradaNodoAdicional, 'EsReceptor', str(self.opt._adicionalEsReceptor))
        # FIN NODO ADICIONAL---------------------------------------#
        
        return doc.toxml(encoding="utf-8")


    def set_fe_node_data(self, documento, area, elemento, dato):
        if not dato:
            dato = ''
        logging.info(dato)
        Campo = documento.createElement(elemento)
        area.appendChild(Campo)
        # todo poner el unicode
        # ptext = documento.createTextNode(unicode(dato))
        ptext = documento.createTextNode(dato)
        Campo.appendChild(ptext)
        return True


    # @api.model
    # def _get_client_conn(self, retornaXML=False):
    #     """
    #     Establece la conexión con el WS y crea el objeto SOAP cliente de dicha conexión.
    #     """
    #     # Obtener la URL de parámetros del sistema
    #     fe_url_ws = self.env['ir.config_parameter'].get_param('magna_fe_url_ws', '')
    #     if not fe_url_ws or fe_url_ws == '0':
    #         _logger.info('Servicio Web FE: No se pudo conectar con el servicio.')
    #         return False, 'Error!\n %s' % (
    #         'No se encuentra configurada la ruta del WSDL para consumir los servicios del proveedor de FE',)
    #     # Establecer la conexión
    #     try:
    #         return True, Client(fe_url_ws, cache=NoCache(), retxml=retornaXML)
    #     except Exception as e:
    #         return False, 'Error!\n %s' % ('Ha ocurrido un error en la comunicación web con el proveedor de FE',)
    #

