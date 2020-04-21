# -*- coding: utf-8 -*-

import qrcode
import base64
from io import BytesIO
from odoo import api, fields, models
from . import fe_xml_factory
import logging


# # -----------
# import logging
# # logging.basicConfig(level=logging.INFO)
# # logging.getLogger('suds.client').setLevel(logging.DEBUG)
# _logger = logging.getLogger('suds.transport').setLevel(logging.DEBUG)
# # logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
# # logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)
#
# from odoo.exceptions import UserError
# from odoo import api, fields, models, _, tools
# import os
# from suds.wsse import UsernameToken, Security
# from suds import Client, WebFault
#
# key_ws_FE_GeneraryFirmarDocumento = "url_ws.fe.ws_generar_y_firmar_doc"
# key_ws_FE_username = "url_ws.fe.username"
# key_ws_FE_password = "url_ws.fe.password"
# # -----------




class AccountMove(models.Model):
    _inherit = "account.move"

    fe_Contingencia = fields.Boolean('Es Contingencia')
    fe_SerieContingencia = fields.Char('Serie')
    fe_DocNroContingencia = fields.Char(u'Número')
    fe_Serie = fields.Char('Serie Factura')
    fe_DocNro = fields.Char(u'Número Factura')
    fe_FechaHoraFirma = fields.Char('Fecha/Hora de firma')
    fe_Estado = fields.Char('Estado')
    fe_URLParaVerificarQR = fields.Char(u'Código QR', default="https://www.efactura.dgi.gub.uy/consultaQR/cfe?213738620011,111,A,3,29400.00,20200408,9roxpijcw7sgAkZsoJzWr%2Br0xhE=")
    fe_URLParaVerificarTexto = fields.Char(u'Verificación')
    fe_CAEDNro = fields.Integer('CAE Desde')
    fe_CAEHNro = fields.Integer('CAE Hasta')
    fe_CAENA = fields.Char(u'CAE Autorización')
    fe_CAEFA = fields.Char(u'CAE Fecha de autorización')
    fe_CAEFVD = fields.Char('CAE vencimiento')
    fe_qr_img = fields.Binary('Imagen QR', compute='_generate_qr_code', store=False)

    @api.depends('fe_URLParaVerificarQR')
    def _generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        for rec in self:
            qr.add_data(rec.fe_URLParaVerificarQR)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            rec.fe_qr_img = qr_image


    # se llama al action_post de super y antes de devolver el control, se envía la información de FE
    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.invoice_send_fe_proinfo()
        return res

    def invoice_send_fe_proinfo(self):
        for rec in self:
            tipo_CFE = fe_xml_factory.cfeFactory.get_tipo_cfe(rec.type, consumidor_final=not rec.partner_id.vat)
            in_xml_entrada = rec.gen_Inxmlentrada()

            fe_xml_factory.cfeFactory().invocar_generar_y_firmar_doc(str_xml_cfe=in_xml_entrada, tipo_CFE=tipo_CFE)




        return True


    def gen_Inxmlentrada(self):
        for rec in self:
            options = fe_xml_factory.cfeFactoryOptions()
            options._lineasDetalle = []

            # todo ver tema tipo de cfe
            options._tipoComprobante = fe_xml_factory.cfeFactory.get_tipo_cfe(rec.type, rec.partner_id.fe_consumidor_final)
            # options._serieComprobante = rec. #todo
            # options._numeroComprobante = rec. #todo
            options._fechaComprobanteYYYYMMDD = rec.invoice_date.strftime('%Y%m%d')

            options._indicadorMontBruto = True #todo

            options._formaPago = 1 #1-Contado, 2-Credito
            options._fechaVencimientoYYYYMMDD = rec.invoice_date_due.strftime('%Y%m%d')

            # EMISOR todo ver si los datos salen de aca o de los campos nuevos que puse
            options._emisorRuc = rec.company_id.partner_id.vat
            options._emisorNombre = rec.company_id.partner_id.name #razon social
            options._emisorDomicilioFiscal = rec.company_id.partner_id.street
            options._emisorNombreComercial = rec.company_id.name
            options._emisorCodigoCasaPrincipal = rec.company_id.fe_codigo_principal_sucursal
            options._emisorCiudad = rec.company_id.partner_id.city
            options._emisorDepartamento = rec.company_id.partner_id.state_id.name

            # RECEPTOR todo ver si los datos salen de aca o de los campos nuevos que puse
            options._receptorTipoDocumento = rec.partner_id.fe_tipo_documento
            if rec.partner_id.fe_pais_documento.code:
                options._receptorCodigoPais = rec.partner_id.fe_pais_documento.code
            options._receptorDocumento = rec.partner_id.vat
            options._receptorRazonSocial = rec.partner_id.fe_razon_social
            options._receptorDireccion = rec.partner_id.fe_addr_facturacion
            options._receptorCiudad = rec.partner_id.city
            options._receptorDepartamento = rec.partner_id.state_id.name

            # TOTALES
            options._tipoMonedaTransaccion = rec.currency_id.name

            group_taxes = rec.amount_by_group
            logging.info(group_taxes)
            # [
            #  ('Impuestos', 17.38, 79.0, '$ 17.38', '$ 79.00', 2, 1),
            #  ('Tax 15%', 3525.0, 23500.0, '$ 3,525.00', '$ 23,500.00', 2, 2)
            #  ]

            account_tax_obj = self.env['account.tax']
            # account_tax_iva_exento_id = account_tax_obj.search([('company_id', '=', rec.company_id.id),
            #                                                              ('fe_tax_codigo_dgi', '=', '1'),
            #                                                              ('type_tax_use', '=', 'sale')], limit=1)[0]
            account_tax_iva_minima_id = account_tax_obj.search([('company_id', '=', rec.company_id.id),
                                                                         ('fe_tax_codigo_dgi', '=', '2'),
                                                                         ('type_tax_use', '=', 'sale')], limit=1)[0]
            account_tax_iva_basica_id = account_tax_obj.search([('company_id', '=', rec.company_id.id),
                                                                         ('fe_tax_codigo_dgi', '=', '3'),
                                                                         ('type_tax_use', '=', 'sale')], limit=1)[0]

            options._IVATasaMinima = account_tax_iva_minima_id.amount
            options._IVATasaBasica = account_tax_iva_basica_id.amount

            # ADICIONAL
            options._adicionalTipoDocumentoId = 0
            options._adicionalDocComCodigo = ''
            options._adicionalDocComSerie = ''
            options._adicionalSucursalId = 0
            options._adicionalAdenda = ''
            options._adicionalCAEDnro = 0
            options._adicionalCAEHnro = 0
            options._adicionalCAENA = ''
            options._adicionalCAEFA = ''
            options._adicionalCAEFVD = ''
            options._adicionalLoteId = 0
            options._adicionalCorreoReceptor = ''
            options._adicionalEsReceptor = 'false'


            # DETALLE
            monto_no_gravado = 0
            monto_neto_iva_tasa_basica = 0
            monto_neto_iva_tasa_minima = 0
            monto_no_facturable = 0
            monto_iva_basica = 0
            monto_iva_minima = 0

            for line in rec.invoice_line_ids:
                line_aux = fe_xml_factory.cfeFactoryOptionsProductLineDetail()
                line_aux._cantidad = line.quantity
                line_aux._nombreItem = line.product_id.name
                line_aux._unidadMedidad = 'Unit'
                line_aux._precioUnitario = line.price_unit
                line_aux._montoItem = line.quantity * line.price_unit

                impuesto = line.price_total - line.price_subtotal #todo revisar si esta bien
                if line.tax_ids:
                    line_aux._indicadorFacturacion = line.tax_ids[0].fe_tax_codigo_dgi
                    # if line.product_id.tax_ids[0].price_include:
                    #     options._montoBruto = True
                    if line.tax_ids[0].fe_tax_codigo_dgi == '1' and line.tax_ids[0].type_tax_use == 'sale':
                        monto_no_gravado += line.price_subtotal
                    if line.tax_ids[0].fe_tax_codigo_dgi == '2' and line.tax_ids[0].type_tax_use == 'sale':
                        monto_neto_iva_tasa_minima += line.price_subtotal
                        monto_iva_minima += impuesto
                    if line.tax_ids[0].fe_tax_codigo_dgi == '3' and line.tax_ids[0].type_tax_use == 'sale':
                        monto_neto_iva_tasa_basica += line.price_subtotal
                        monto_iva_basica += impuesto
                else:
                    monto_no_gravado += line.price_subtotal

                options._lineasDetalle.append(line_aux)

            options._montoTotalNoGravado = monto_no_gravado
            options._montoNetoIVATasaMinima = monto_neto_iva_tasa_minima
            options._montoIVATasaMinima = monto_iva_minima
            options._montoNetoIVATasaBasica = monto_neto_iva_tasa_basica
            options._montoIVATasaBasica = monto_iva_basica

            options._montoTotal = abs(rec.amount_total - monto_no_facturable)
            options._montoTotalAPagar = rec.amount_total

            xml_factory = fe_xml_factory.cfeFactory(options=options)
            XML = xml_factory.getXML()

            return XML







# -------------------------------------------------------------------------------------------------------------------------
#
#
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
#             # _logger.info('self.ws_FEGeneraryFirmarDocumento: %s', self.ws_FEGeneraryFirmarDocumento)
#         except Exception as e:
#             raise UserError(
#                 _(u'Error TLK: No se pudo cargar WSDL:') + tools.ustr(e) + ':' + url_ws)
#
#         return True
#
#
#     @api.model
#     def invocar_generar_y_firmar_doc(self):
#         """
#
#         :return:
#         """
#
#         # Establecer la conexión
#         if not self.conectar_ws_FEGeneraryFirmarDocumento():
#             _logger.error(u"No se pudo establecer conexión WS")
#             return False
#
#         # Consumo de novedades
#         try:
#
#             Inxmlentrada = '''&lt;CFEEntrada xmlns=&quot;com.esignit.fe&quot;&gt;
# 	&lt;XMLEntradaNodoCFE&gt;
# 		&lt;FEIDDocTipoCFE&gt;111&lt;/FEIDDocTipoCFE&gt;
# 		&lt;FEIDDocSerie&gt;A&lt;/FEIDDocSerie&gt;
# 		&lt;FEIDDocNro&gt;1&lt;/FEIDDocNro&gt;
# 		&lt;FEIDDocFchEmis&gt;2020-04-18&lt;/FEIDDocFchEmis&gt;
# 		&lt;FEIDDocFmaPago&gt;1&lt;/FEIDDocFmaPago&gt;
# 		&lt;FEIDDocFchVenc&gt;2020-12-31&lt;/FEIDDocFchVenc&gt;
# 		&lt;FEEMIRUCEmisor&gt;213738620011&lt;/FEEMIRUCEmisor&gt;
# 		&lt;FEEMIRznSoc&gt;ALTERNATIVE LTDA&lt;/FEEMIRznSoc&gt;
# 		&lt;FEEMINomComercial/&gt;
# 		&lt;FEEMICdgDGISucur&gt;1&lt;/FEEMICdgDGISucur&gt;
# 		&lt;FEEMIDomFiscal/&gt;
# 		&lt;FEEMICiudad&gt;MONTEVIDEO&lt;/FEEMICiudad&gt;
# 		&lt;FEEMIDepartamento&gt;Montevideo&lt;/FEEMIDepartamento&gt;
# 		&lt;FERECTipoDocRecep&gt;2&lt;/FERECTipoDocRecep&gt;
# 		&lt;FERECCodPaisRecep&gt;UY&lt;/FERECCodPaisRecep&gt;
# 		&lt;FERECDocRecep&gt;214844360018&lt;/FERECDocRecep&gt;
# 		&lt;FERECRznSocRecep&gt;DGI&lt;/FERECRznSocRecep&gt;
# 		&lt;FERECDirRecep&gt;FERNANDEZ CRESPO 1534&lt;/FERECDirRecep&gt;
# 		&lt;FERECCiudadRecep&gt;MONTEVIDEO&lt;/FERECCiudadRecep&gt;
# 		&lt;FERECDeptoRecep/&gt;
# 		&lt;FETOTTpoMoneda&gt;UYU&lt;/FETOTTpoMoneda&gt;
# 		&lt;FETOTMntNoGrv&gt;0.00&lt;/FETOTMntNoGrv&gt;
# 		&lt;FETOTMntNetoIvaTasaMin&gt;0.00&lt;/FETOTMntNetoIvaTasaMin&gt;
# 		&lt;FETOTMntNetoIVATasaBasica&gt;20000.00&lt;/FETOTMntNetoIVATasaBasica&gt;
# 		&lt;FETOTIVATasaBasica&gt;22.000&lt;/FETOTIVATasaBasica&gt;
# 		&lt;FETOTMntIVATasaMin&gt;0.00&lt;/FETOTMntIVATasaMin&gt;
# 		&lt;FETOTMntIVATasaBasica&gt;4400.00&lt;/FETOTMntIVATasaBasica&gt;
# 		&lt;FETOTMntTotal&gt;24400.00&lt;/FETOTMntTotal&gt;
# 		&lt;FETOTCantLinDet&gt;3&lt;/FETOTCantLinDet&gt;
# 		&lt;FETOTMontoNF&gt;5000.00&lt;/FETOTMontoNF&gt;
# 		&lt;FETOTMntPagar&gt;29400.00&lt;/FETOTMntPagar&gt;
# 		&lt;FEDetalles&gt;
# 			&lt;FEDetalle&gt;
# 				&lt;FEDETNroLinDet&gt;1&lt;/FEDETNroLinDet&gt;
# 				&lt;FEDETIndFact&gt;3&lt;/FEDETIndFact&gt;
# 				&lt;FEDETNomItem&gt;aaa&lt;/FEDETNomItem&gt;
# 				&lt;FEDETCantidad&gt;10.000&lt;/FEDETCantidad&gt;
# 				&lt;FEDETUniMed&gt;kg&lt;/FEDETUniMed&gt;
# 				&lt;FEDETPrecioUnitario&gt;1000.000000&lt;/FEDETPrecioUnitario&gt;
# 				&lt;FEDETMontoItem&gt;10000.00&lt;/FEDETMontoItem&gt;
# 			&lt;/FEDetalle&gt;
# 			&lt;FEDetalle&gt;
# 				&lt;FEDETNroLinDet&gt;2&lt;/FEDETNroLinDet&gt;
# 				&lt;FEDETIndFact&gt;3&lt;/FEDETIndFact&gt;
# 				&lt;FEDETNomItem&gt;bbb&lt;/FEDETNomItem&gt;
# 				&lt;FEDETCantidad&gt;5.000&lt;/FEDETCantidad&gt;
# 				&lt;FEDETUniMed&gt;kg&lt;/FEDETUniMed&gt;
# 				&lt;FEDETPrecioUnitario&gt;2000.000000&lt;/FEDETPrecioUnitario&gt;
# 				&lt;FEDETMontoItem&gt;10000.00&lt;/FEDETMontoItem&gt;
# 			&lt;/FEDetalle&gt;
# 			&lt;FEDetalle&gt;
# 				&lt;FEDETNroLinDet&gt;3&lt;/FEDETNroLinDet&gt;
# 				&lt;FEDETIndFact&gt;6&lt;/FEDETIndFact&gt;
# 				&lt;FEDETNomItem&gt;ccc&lt;/FEDETNomItem&gt;
# 				&lt;FEDETCantidad&gt;1.000&lt;/FEDETCantidad&gt;
# 				&lt;FEDETUniMed&gt;N/A&lt;/FEDETUniMed&gt;
# 				&lt;FEDETPrecioUnitario&gt;5000.000000&lt;/FEDETPrecioUnitario&gt;
# 				&lt;FEDETMontoItem&gt;5000.00&lt;/FEDETMontoItem&gt;
# 			&lt;/FEDetalle&gt;
# 		&lt;/FEDetalles&gt;
# 	&lt;/XMLEntradaNodoCFE&gt;
# 	&lt;XMLEntradaNodoAdicional&gt;
# 		&lt;TipoDocumentoId&gt;111&lt;/TipoDocumentoId&gt;
# 		&lt;DocComCodigo&gt;1&lt;/DocComCodigo&gt;
# 		&lt;DocComSerie&gt;A&lt;/DocComSerie&gt;
# 		&lt;SucursalId&gt;1&lt;/SucursalId&gt;
# 		&lt;Adenda/&gt;
# 		&lt;CAEDnro&gt;1&lt;/CAEDnro&gt;
# 		&lt;CAEHnro&gt;100&lt;/CAEHnro&gt;
# 		&lt;CAENA&gt;20160001110&lt;/CAENA&gt;
# 		&lt;CAEFA&gt;2016-01-01&lt;/CAEFA&gt;
# 		&lt;CAEFVD&gt;2017-12-31&lt;/CAEFVD&gt;
# 		&lt;LoteId&gt;0&lt;/LoteId&gt;
# 		&lt;CorreoReceptor/&gt;
# 		&lt;EsReceptor&gt;false&lt;/EsReceptor&gt;
# 	&lt;/XMLEntradaNodoAdicional&gt;
# &lt;/CFEEntrada&gt;'''
#             respuesta_ws = self.ws_FEGeneraryFirmarDocumento.service.Execute(Inxmlentrada=Inxmlentrada,
#                     Tipocfe='111', Fefacturaimportadaloteid=12)  # noqa
#
#             if respuesta_ws:
#                 if respuesta_ws.Outxmlsalida:
#                     print(respuesta_ws.Outxmlsalida)
#                 else:
#                     raise UserError(
#                         'Error : ' + str(respuesta_ws))
#
#         except UserError:
#             raise
#
#         except WebFault as e:
#             _logger.error(_("No se pudo obtener los datos de WS:" + str(e)))
#             raise UserError(
#                 'Error: No se pudo Procesar el request')
#
#         except Exception as e:
#             _logger.error(
#                 _("No se pudo obtener los datos de WS:" + tools.ustr(e)))
#             raise UserError(
#                 'Error: No se pudo Procesar el request, exception grave')
#
#         return True