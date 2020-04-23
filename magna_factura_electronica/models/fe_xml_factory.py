# -*- coding: utf-8 -*-


from xml.dom.minidom import Document, parseString
import logging
from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools
import os
from suds.wsse import UsernameToken, Security
from suds import Client, WebFault

# logging.basicConfig(level=logging.INFO)
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)
# logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
# logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)


debug = True

# try:
#     # Python 2: "unicode" is built-in
#     unicode
# except NameError:
#     unicode = str


def loguear(text):
    if debug:
        logging.info(text)


key_ws_FE_url = "magna_ws_fe.url"
key_ws_FE_username = "magna_ws_fe.username"
key_ws_FE_password = "magna_ws_fe.password"


class cfeFactoryOptionsProductLineDetail():
    _cantidad = 0
    _nombreItem = ''
    _unidadMedidad = ''
    _precioUnitario = 0
    _montoItem = 0
    _indicadorFacturacion = 0

class cfeFactoryOptions():
    _fechaVencimientoYYYYMMDD=''
    _fechaComprobanteYYYYMMDD = ''
    _esContingencia = False
    _tipoComprobante = 0
    _serieComprobante = 'A'
    _numeroComprobante = 1
    _indicadorMontBruto = False

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
    _montoTotal=0
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
    _montoIVATasaMinima=0
    _montoIVATasaBasica=0
    # _montoIVATasaOtra=0


    _lineasDetalle = []

    _adicionalTipoDocumentoId = 0
    _adicionalDocComCodigo = ''
    _adicionalDocComSerie = ''
    _adicionalSucursalId = 0
    _adicionalAdenda = ''
    _adicionalCAEDnro = 0
    _adicionalCAEHnro = 0
    _adicionalCAENA = 0
    _adicionalCAEFA = ''
    _adicionalCAEFVD = ''
    _adicionalLoteId = 0
    _adicionalCorreoReceptor = ''
    _adicionalEsReceptor = 'false'

    def __init__(self):
        pass


class CfeFactory():
    opt = cfeFactoryOptions()

    def __init__(self, options=None):
        self.opt = options


    def get_data_XML(self):
        doc = Document()

        CFEEntrada = doc.createElement("CFEEntrada")
        CFEEntrada.setAttribute("xmlns", 'com.esignit.fe')
        doc.appendChild(CFEEntrada)
        XMLEntradaNodoCFE = doc.createElement("XMLEntradaNodoCFE")
        CFEEntrada.appendChild(XMLEntradaNodoCFE)

        # IDENTIFICADOR
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocTipoCFE', str(self.opt._tipoComprobante))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocSerie', str(self.opt._serieComprobante))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocNro', str(self.opt._numeroComprobante))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocFchEmis', str(self.opt._fechaComprobanteYYYYMMDD))
        if self.opt._indicadorMontBruto:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocMntBruto', '1')
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocFmaPago', str(self.opt._formaPago))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEIDDocFchVenc', str(self.opt._fechaVencimientoYYYYMMDD))

        # EMISOR
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIRUCEmisor', str(self.opt._emisorRuc))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIRznSoc', str(self.opt._emisorNombre))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMINomComercial', str(self.opt._emisorNombreComercial))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMICdgDGISucur', str(self.opt._emisorCodigoCasaPrincipal))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIDomFiscal', str(self.opt._emisorDomicilioFiscal))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMICiudad', str(self.opt._emisorCiudad))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FEEMIDepartamento', str(self.opt._emisorDepartamento))

        # RECEPTOR
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECTipoDocRecep', str(self.opt._receptorTipoDocumento))
        cod_pais_receptor = self.opt._receptorCodigoPais
        if cod_pais_receptor:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECCodPaisRecep', cod_pais_receptor)
        if self.opt._receptorDocumento:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECDocRecep', self.opt._receptorDocumento)
        if self.opt._receptorRazonSocial:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECRznSocRecep', str(self.opt._receptorRazonSocial))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECDirRecep', str(self.opt._receptorDireccion))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECCiudadRecep', str(self.opt._receptorCiudad))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FERECDeptoRecep', str(self.opt._receptorDepartamento))

        # TOTALES DE ENCABEZADO
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTTpoMoneda', str(self.opt._tipoMonedaTransaccion))
        if self.opt._montoTotalNoGravado: #Tiene valor sólo si es exento de iva o no tiene impuestos (monto total de lineas que no tienen impuestos o exentos de iva)
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNoGrv', "{0:.2f}".format(self.opt._montoTotalNoGravado).replace(".", ".").replace('-',''))
        else:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNoGrv', '0.00')
        if self.opt._montoNetoIVATasaMinima:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNetoIvaTasaMin', "{0:.2f}".format(self.opt._montoNetoIVATasaMinima).replace(".", "."))
        if self.opt._montoNetoIVATasaBasica:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntNetoIVATasaBasica', "{0:.2f}".format(self.opt._montoNetoIVATasaBasica).replace(".", "."))
        if self.opt._IVATasaMinima:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTIVATasaMin', "{0:.3f}".format(self.opt._IVATasaMinima).replace(".", "."))
        if self.opt._IVATasaBasica:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTIVATasaBasica', "{0:.3f}".format(self.opt._IVATasaBasica).replace(".", "."))
        if self.opt._montoIVATasaMinima:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntIVATasaMin', "{0:.2f}".format(self.opt._montoIVATasaMinima).replace(".", "."))
        if self.opt._montoIVATasaBasica:
            self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntIVATasaBasica', "{0:.2f}".format(self.opt._montoIVATasaBasica).replace(".", "."))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntTotal',  "{0:.2f}".format(self.opt._montoTotal).replace(".", ".").replace('-',''))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTCantLinDet', str(len(self.opt._lineasDetalle)))
        self._set_fe_node_data(doc, XMLEntradaNodoCFE, 'FETOTMntPagar',  "{0:.2f}".format(self.opt._montoTotalAPagar).replace(".", ".").replace('-',''))

        # DETALLE
        ZonaDetalle = doc.createElement("FEDetalles")
        XMLEntradaNodoCFE.appendChild(ZonaDetalle)
        nroSecuencial = 0
        for linea in self.opt._lineasDetalle:
            if linea._precioUnitario < 0 or linea._cantidad < 0:
                continue
            nroSecuencial += 1
            SubZonaItem = doc.createElement("FEDetalle")
            ZonaDetalle.appendChild(SubZonaItem)
            self._set_fe_node_data(doc, SubZonaItem, 'FEDETNroLinDet', str(nroSecuencial))
            self._set_fe_node_data(doc, SubZonaItem, 'FEDETIndFact', linea._indicadorFacturacion)
            self._set_fe_node_data(doc, SubZonaItem, 'FEDETNomItem', linea._nombreItem)
            self._set_fe_node_data(doc, SubZonaItem, 'FEDETCantidad', str(linea._cantidad))
            if linea._unidadMedidad:
                self._set_fe_node_data(doc, SubZonaItem, 'FEDETUniMed', linea._unidadMedidad)
            self._set_fe_node_data(doc, SubZonaItem, 'FEDETPrecioUnitario', "{0:.6f}".format(linea._precioUnitario).replace(".", "."))
            self._set_fe_node_data(doc, SubZonaItem, 'FEDETMontoItem', "{0:.2f}".format(linea._montoItem).replace(".", "."))

        # NODO ADICIONAL
        XMLEntradaNodoAdicional = doc.createElement("XMLEntradaNodoAdicional")
        CFEEntrada.appendChild(XMLEntradaNodoAdicional)
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'TipoDocumentoId', str(self.opt._adicionalTipoDocumentoId))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'DocComCodigo', str(self.opt._adicionalDocComCodigo))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'DocComSerie', str(self.opt._adicionalDocComSerie))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'SucursalId', str(self.opt._adicionalSucursalId))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'Adenda', str(self.opt._adicionalAdenda))
        if self.opt._esContingencia:
            self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEDnro', str(self.opt._adicionalCAEDnro))
            self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEHnro', str(self.opt._adicionalCAEHnro))
            self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAENA', str(self.opt._adicionalCAENA))
            self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEFA', str(self.opt._adicionalCAEFA))
            self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEFVD', str(self.opt._adicionalCAEFVD))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'LoteId', str(self.opt._adicionalLoteId))
        if self.opt._adicionalCorreoReceptor:
            self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CorreoReceptor', str(self.opt._adicionalCorreoReceptor))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'EsReceptor', str(self.opt._adicionalEsReceptor))

        XML = doc.toprettyxml()
        # se quita el <?xml version="1.0" encoding="utf-8"?>
        XML = XML.split("?>")[1]

        logging.info('Inxmlentrada --> %s', XML)

        return XML

    @api.model
    def _set_fe_node_data(self, documento, area, elemento, dato):
        if not dato:
            dato = ''
        logging.info(dato)
        Campo = documento.createElement(elemento)
        area.appendChild(Campo)
        # asm todo poner el unicode?
        # ptext = documento.createTextNode(unicode(dato))
        ptext = documento.createTextNode(dato)
        Campo.appendChild(ptext)
        return True



    def conectar_ws_FEGeneraryFirmarDocumento(self):
        """
        Establece la conexión con el WS y crea el objeto SOAP cliente
        de dicha conexión.
        """
        # Obtener las URL necesaria de los parámetros del sistema
        try:
            url_ws = tools.config[key_ws_FE_url]
            # url_ws = "https://fe-test.proinfo.uy:443/servlet/afegeneraryfirmardocumento"
            if not url_ws:
                raise UserError(_(
                    'Error: No se encuentra configurada la ruta del WSDL para consumir el servicio: %s ' %
                    key_ws_FE_url))

            # username_ws = tools.config[key_ws_FE_username]
            # if not username_ws:
            #     raise UserError(_(
            #         'Error TLK: No se encuentra configurado el Usuario para consumir el servicio: %s ' %
            #         key_ws_FE_username))
            #
            # pass_ws = tools.config[key_ws_FE_password]
            # if not pass_ws:
            #     raise UserError(_(
            #         'Error TLK: No se encuentra configurada la contraseña para consumir el servicio: %s ' %
            #         key_ws_FE_password))
        except Exception:
            raise UserError(_(
                'Error No se encuentra configurado algun parametro: %s, %s o %s ' %
                (key_ws_FE_url, key_ws_FE_username,key_ws_FE_password)))

        # se usa archivo wsdl local al addon: FEGeneraryFirmarDocumento.wsdl'
        path_file = os.path.dirname(os.path.abspath(__file__))
        wsdl_ws = 'file://' + path_file + '/wsdls/FEGeneraryFirmarDocumento.wsdl'

        # Establecer las conexiones
        try:
            client = Client(wsdl_ws, location=url_ws, timeout=10)
            # security = Security()
            # token = UsernameToken(username_ws, pass_ws)
            # security.tokens.append(token)
            # self.ws_FEGeneraryFirmarDocumento.set_options(retxml=True)
            # self.ws_FEGeneraryFirmarDocumento.set_options(wsse=security)
            # _logger.info('self.ws_FEGeneraryFirmarDocumento: %s', self.ws_FEGeneraryFirmarDocumento)
            return client
        except Exception as e:
            raise UserError(
                _(u'Error TLK: No se pudo cargar WSDL:') + tools.ustr(e) + ':' + url_ws)

    def invocar_generar_y_firmar_doc(self, str_xml_cfe, tipo_CFE):
        """
        :return:
        """
        # Establecer la conexión
        client = self.conectar_ws_FEGeneraryFirmarDocumento()
        if not client:
            logging.error(u"No se pudo establecer conexión WS")
            return False

        # Consumo de servicio
        try:
            respuesta_ws = client.service.Execute(Inxmlentrada=str_xml_cfe, Tipocfe=tipo_CFE, Fefacturaimportadaloteid=0)
            if respuesta_ws:
                if respuesta_ws.Outxmlsalida:
                    logging.info('RESPUESTA: %s',respuesta_ws.Outxmlsalida)
                    return self.ws_procesar_respuesta(respuesta_ws.Outxmlsalida)
                else:
                    raise UserError('Error : ' + str(respuesta_ws))

        except UserError:
            raise

        except WebFault as e:
            logging.error(_("No se pudo obtener los datos de WS:" + str(e)))
            raise UserError('Error: No se pudo Procesar el request')

        except Exception as e:
            logging.error(_("No se pudo obtener los datos de WS:" + tools.ustr(e)))
            raise UserError('Error: No se pudo Procesar el request, exception grave')

        return True



    def ws_procesar_respuesta(self, response_xml):
        vals = {}
        doc = parseString(response_xml)
        nodos = doc.getElementsByTagName("FEXMLSalida")
        for nodo in nodos:
            estado = nodo.getElementsByTagName("Estado")[0].firstChild.data
            if estado == 'AS':
                vals['fe_Serie'] = nodo.getElementsByTagName("Serie")[0].firstChild.data
                vals['fe_DocNro'] = nodo.getElementsByTagName("DocNro")[0].firstChild.data
                vals['fe_FechaHoraFirma'] = nodo.getElementsByTagName("FechaHoraFirma")[0].firstChild.data
                vals['fe_Estado'] = estado
                vals['fe_URLParaVerificarQR'] = nodo.getElementsByTagName("URLParaVerificarQR")[0].firstChild.data
                vals['fe_URLParaVerificarTexto'] = nodo.getElementsByTagName("URLParaVerificarTexto")[0].firstChild.data
                vals['fe_CAEDNro'] = nodo.getElementsByTagName("FechaHoraFirma")[0].firstChild.data
                vals['fe_CAEHNro'] = nodo.getElementsByTagName("CAEHNro")[0].firstChild.data
                vals['fe_CAENA'] = nodo.getElementsByTagName("CAENA")[0].firstChild.data
                vals['fe_CAEFA'] = nodo.getElementsByTagName("CAEFA")[0].firstChild.data
                vals['fe_CAEFVD'] = nodo.getElementsByTagName("CAEFVD")[0].firstChild.data
                vals['fe_Hash'] = nodo.getElementsByTagName("Hash")[0].firstChild.data
            elif estado == 'BS':
                error_msg = nodo.getElementsByTagName("MensajeError")[0].firstChild.data
                raise UserError(u'Ha habido un error en el envío de la factura al proveedor de FE: ' + error_msg)

        return vals

