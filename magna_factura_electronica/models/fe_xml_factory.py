# -*- coding: utf-8 -*-


from suds.client import Client
from suds.cache import NoCache
# from openerp.exceptions import ValidationError
from xml.dom.minidom import Document, parse
import logging
from odoo import api, fields, models

# logging.basicConfig(level=logging.INFO)
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)
# logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
# logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)



# -----------
# import logging
# logging.basicConfig(level=logging.INFO)
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# _logger = logging.getLogger('suds.transport').setLevel(logging.DEBUG)
# logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
# logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools
import os
from suds.wsse import UsernameToken, Security
from suds import Client, WebFault

key_ws_FE_GeneraryFirmarDocumento = "url_ws.fe.ws_generar_y_firmar_doc"
key_ws_FE_username = "url_ws.fe.username"
key_ws_FE_password = "url_ws.fe.password"
# -----------



debug = True

# try:
#     # Python 2: "unicode" is built-in
#     unicode
# except NameError:
#     unicode = str


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
    _adicionalEsReceptor = 'false'


    def __init__(self):
        pass


class cfeFactory():
    opt = cfeFactoryOptions()

    def __init__(self, options=None):
        self.opt = options

    def get_tipo_cfe(invoice_type, consumidor_final):
        if consumidor_final:  # eTicket
            if invoice_type == 'out_invoice':  # Factura de cliente
                return 101
            elif invoice_type == 'out_refund':  # NC de cliente
                return 102
        else:  # eFactura
            if invoice_type == 'out_invoice':  # Factura de cliente
                return 111
            elif invoice_type == 'out_refund':  # NC de cliente
                return 112
        return 0

    # def calc_tipo_comprobante(self, invoice):
    #     tipo_comprobante=''
    #     if invoice.fe_contingencia:
    #         if invoice.type == 'out_invoice':
    #             if invoice.partner_tipo_documento == 2:
    #                 tipo_comprobante = 211
    #                 if invoice.fe_nota_debito:
    #                     tipo_comprobante=213
    #             else:
    #                 tipo_comprobante = 201
    #                 if invoice.fe_nota_debito:
    #                     tipo_comprobante=203
    #
    #         if invoice.type == 'out_refund':
    #             if invoice.partner_tipo_documento == 2:
    #                 tipo_comprobante = 212
    #             else:
    #                 tipo_comprobante = 202
    #     else:
    #         if invoice.type == 'out_invoice':
    #             if invoice.partner_tipo_documento == 2:
    #                 tipo_comprobante = 111
    #                 if invoice.fe_nota_debito:
    #                     tipo_comprobante=113
    #             else:
    #                 tipo_comprobante = 101
    #                 if invoice.fe_nota_debito:
    #                     tipo_comprobante=103
    #
    #         if invoice.type == 'out_refund':
    #             if invoice.partner_tipo_documento == 2:
    #                 tipo_comprobante = 112
    #             else:
    #                 tipo_comprobante = 102
    #     logging.info('es de tipo')
    #     logging.info(tipo_comprobante)
    #     return tipo_comprobante

    #


    def getXML(self):
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
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEDnro', str(self.opt._adicionalCAEDnro))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEHnro', str(self.opt._adicionalCAEHnro))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAENA', str(self.opt._adicionalCAENA))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEFA', str(self.opt._adicionalCAEFA))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CAEFVD', str(self.opt._adicionalCAEFVD))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'LoteId', str(self.opt._adicionalLoteId))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'CorreoReceptor', str(self.opt._adicionalCorreoReceptor))
        self._set_fe_node_data(doc, XMLEntradaNodoAdicional, 'EsReceptor', str(self.opt._adicionalEsReceptor))

        XML = doc.toxml()
        # se quita el <?xml version="1.0" encoding="utf-8"?>
        XML = XML.split("?>")[1]

        # logging.info(XML)

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



    def conectar_ws_FE(self):
        """
        Establece la conexión con el WS y crea el objeto SOAP cliente
        de dicha conexión.
        """
        client = None
        # Obtener las URL necesaria de los parámetros del sistema
        try:
            # url_ws = tools.config[key_ws_FE_GeneraryFirmarDocumento]
            url_ws = "https://fe-test.proinfo.uy:443/servlet/afegeneraryfirmardocumento"
            if not url_ws:
                raise UserError(_(
                    'Error: No se encuentra configurada la ruta del WSDL para consumir el servicio: %s ' %
                    key_ws_FE_GeneraryFirmarDocumento))

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
                'Error No se encuentra configurada algun parametro: %s,'
                '%s o %s ' %
                (key_ws_FE_GeneraryFirmarDocumento, key_ws_FE_username,key_ws_FE_password)))

        # se usa archivo wsdl local al addon: FEGeneraryFirmarDocumento.wsdl'
        path_file = os.path.dirname(os.path.abspath(__file__))
        wsdl_ws = 'file://' + path_file + '/wsdls/FEGeneraryFirmarDocumento.wsdl'
        self.ws_FEGeneraryFirmarDocumento = None
        # Establecer las conexiones
        try:
            # self.ws_FEGeneraryFirmarDocumento = Client(wsdl_ws, location=url_ws, timeout=10)
            client = Client(wsdl_ws, location=url_ws, timeout=10)

            # security = Security()
            # token = UsernameToken(username_ws, pass_ws)
            # security.tokens.append(token)
            # self.ws_FEGeneraryFirmarDocumento.set_options(retxml=True)
            # self.ws_FEGeneraryFirmarDocumento.set_options(wsse=security)
            # _logger.info('self.ws_FEGeneraryFirmarDocumento: %s', self.ws_FEGeneraryFirmarDocumento)
        except Exception as e:
            raise UserError(
                _(u'Error TLK: No se pudo cargar WSDL:') + tools.ustr(e) + ':' + url_ws)

        return client

    def invocar_generar_y_firmar_doc(self, str_xml_cfe, tipo_CFE):
        """
        :return:
        """

        # Establecer la conexión
        # if not self.conectar_ws_FEGeneraryFirmarDocumento():
        client = self.conectar_ws_FE()
        if not client:
            logging.error(u"No se pudo establecer conexión WS")
            return False

        # Consumo de servicio
        try:
            respuesta_ws = client.service.Execute(Inxmlentrada=str_xml_cfe, Tipocfe=tipo_CFE, Fefacturaimportadaloteid=0)

            if respuesta_ws:
                logging.info('---------RESPUESTA: %s',respuesta_ws.Outxmlsalida)
                self.ws_procesar_respuesta(parse(respuesta_ws.Outxmlsalida))




                # print(respuesta_ws)
                # if respuesta_ws.Outxmlsalida:
                #     # print(respuesta_ws.Outxmlsalida)
                #
                #     xml_data = parse(respuesta_ws.Outxmlsalida).getElementsByTagName('FEXMLSalida')
                #     print(xml_data)
                #
                #     # parts = xml_data[0].getElementsByTagName('ITEM')
                #     # for p in parts:
                #
                #     # dom = parse(respuesta_ws.Outxmlsalida)
                #     # for node in dom.getElementsByTagName('FEXMLSalida'):
                #
                #
                # else:
                #     raise UserError('Error : ' + str(respuesta_ws))

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
        res = []
        vals = {}
        doc = parse(response_xml)
        lista_sobres = doc.getElementsByTagName("FEXMLSalida")
        for sobre in lista_sobres:
            logging.info('---------NODO: %s', sobre)
            # nodo_detalle = sobre.getElementsByTagName("Detalle")[0]
            # nodo_caratula = sobre.getElementsByTagName("Caratula")[0]
            # estado = nodo_detalle.getElementsByTagName("Estado")[0]
            # if estado.firstChild.data == 'AS':
            #     vals['aceptado'] = True
            #     nodo_paramconsulta = nodo_detalle.getElementsByTagName('ParamConsulta')[0]
            #     vals['idreceptor'] = nodo_caratula.getElementsByTagName('IDReceptor')[0].firstChild.data
            #     vals['token'] = nodo_paramconsulta.getElementsByTagName('Token')[0].firstChild.data
            # elif estado.firstChild.data == 'BS':
            #     nodo_motivo_detalle = nodo_detalle.getElementsByTagName("MotivosRechazo")[0]
            #     glosa = nodo_motivo_detalle.getElementsByTagName("Glosa")[0]
            #     detalle = nodo_motivo_detalle.getElementsByTagName("Detalle")[0]
            #     motivo = nodo_motivo_detalle.getElementsByTagName("Motivo")[0]
            #     vals['codigo'] = motivo.firstChild.data
            #     vals['descripcion'] = detalle.firstChild.data
            #     vals['glosa'] = glosa.firstChild.data
            #     vals['aceptado'] = False
            #     if vals['codigo'].strip() == 'S08':
            #         vals['idreceptor'] = nodo_caratula.getElementsByTagName('IDReceptor')[0].firstChild.data
            #         vals['token'] = ''  # nodo_paramconsulta.getElementsByTagName('Token')[0].firstChild.data
            #         vals['aceptado'] = True
            # res.append(vals)
        return True


# -------------------------------------------------------------------------------------------------------------------------

# class WebServiceFE(models.TransientModel):
#     _name = 'web.service.FE'
#
#     def conectar_ws_FEGeneraryFirmarDocumento(self):
#         """
#         Establece la conexión con el WS y crea el objeto SOAP cliente
#         de dicha conexión.
#         """
#
#         # Obtener las URL necesaria de los parámetros del sistema
#         try:
#             # url_ws = tools.config[key_ws_FE_GeneraryFirmarDocumento]
#             url_ws = "https://fe-test.proinfo.uy:443/servlet/afegeneraryfirmardocumento"
#             if not url_ws:
#                 raise UserError(_(
#                     'Error: No se encuentra configurada la ruta del WSDL para consumir el servicio: %s ' %
#                     key_ws_FE_GeneraryFirmarDocumento))
#
#             # username_ws = tools.config[key_ws_FE_username]
#             # if not username_ws:
#             #     raise UserError(_(
#             #         'Error TLK: No se encuentra configurado el Usuario para consumir el servicio: %s ' %
#             #         key_ws_FE_username))
#             #
#             # pass_ws = tools.config[key_ws_FE_password]
#             # if not pass_ws:
#             #     raise UserError(_(
#             #         'Error TLK: No se encuentra configurada la contraseña para consumir el servicio: %s ' %
#             #         key_ws_FE_password))
#         except Exception:
#             raise UserError(_(
#                 'Error No se encuentra configurada algun parametro: %s,'
#                 '%s o %s ' %
#                 (key_ws_FE_GeneraryFirmarDocumento, key_ws_FE_username,key_ws_FE_password)))
#
#         # se usa archivo wsdl local al addon: FEGeneraryFirmarDocumento.wsdl'
#         path_file = os.path.dirname(os.path.abspath(__file__))
#         wsdl_ws = 'file://' + path_file + '/wsdls/FEGeneraryFirmarDocumento.wsdl'
#         self.ws_FEGeneraryFirmarDocumento = None
#         # Establecer las conexiones
#         try:
#             self.ws_FEGeneraryFirmarDocumento = Client(wsdl_ws, location=url_ws, timeout=10)
#
#             # security = Security()
#             # token = UsernameToken(username_ws, pass_ws)
#             # security.tokens.append(token)
#             # self.ws_FEGeneraryFirmarDocumento.set_options(retxml=True)
#             # self.ws_FEGeneraryFirmarDocumento.set_options(wsse=security)
#             # logging.info('self.ws_FEGeneraryFirmarDocumento: %s', self.ws_FEGeneraryFirmarDocumento)
#         except Exception as e:
#             raise UserError(
#                 _(u'Error TLK: No se pudo cargar WSDL:') + tools.ustr(e) + ':' + url_ws)
#
#         return True
#
#
#     # @api.model
#     def invocar_generar_y_firmar_doc(self, str_xml_cfe, tipo_CFE):
#         """
#         :return:
#         """
#
#         # Establecer la conexión
#         if not self.conectar_ws_FEGeneraryFirmarDocumento():
#             logging.error(u"No se pudo establecer conexión WS")
#             return False
#
#         # Consumo de servicio
#         try:
#             respuesta_ws = self.ws_FEGeneraryFirmarDocumento.service.Execute(Inxmlentrada=str_xml_cfe,
#                     Tipocfe=tipo_CFE, Fefacturaimportadaloteid=0)
#
#             if respuesta_ws:
#                 if respuesta_ws.Outxmlsalida:
#                     print(respuesta_ws.Outxmlsalida)
#                 else:
#                     raise UserError('Error : ' + str(respuesta_ws))
#
#         except UserError:
#             raise
#
#         except WebFault as e:
#             logging.error(_("No se pudo obtener los datos de WS:" + str(e)))
#             raise UserError('Error: No se pudo Procesar el request')
#
#         except Exception as e:
#             logging.error(_("No se pudo obtener los datos de WS:" + tools.ustr(e)))
#             raise UserError('Error: No se pudo Procesar el request, exception grave')
#
#         return True

#
#
# import os
# class WsConnection(models.TransientModel):
#     _name = 'fe.ws_connection'
#     _description = u'Conexión del ws'
#
#     @api.model
#     def get_client_conn(self):
#         """
#         Establece la conexión con el WS y crea el objeto SOAP cliente de dicha conexión.
#         """
#         # Obtener la URL de parámetros del sistema
#         fe_url_ws = self.env['ir.config_parameter'].get_param('magna_fe_url_ws', '')
#         if not fe_url_ws or fe_url_ws == '0':
#             logging.info('Servicio Web FE: No se pudo conectar con el servicio.')
#             return False, 'Error!\n %s' % (
#             'No se encuentra configurada la ruta del WSDL para consumir los servicios del proveedor de FE',)
#         # Establecer la conexión
#         try:
#             # client = Client(fe_url_ws, cache=NoCache(), retxml=True)
#
#             path_file = os.path.dirname(os.path.abspath(__file__))
#             wsdl_ws = 'file://' + path_file + '/wsdls/FEGeneraryFirmarDocumento.wsdl'
#             url_ws = "https://fe-test.proinfo.uy:443/servlet/afegeneraryfirmardocumento"
#
#             client = Client(wsdl_ws, location=url_ws, timeout=10)
#
#
#             logging.info('-----------CLIENT %s', client)
#             return True, client
#         except Exception as e:
#             return False, 'Error!\n %s' % ('Ha ocurrido un error en la comunicación web con el proveedor de FE',)
#

