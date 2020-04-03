# -*- coding: utf-8 -*-

# import qrcode
# import pyqrcode
import base64
from io import BytesIO
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    fe_Contingencia = fields.Boolean('Es Contingencia')
    fe_SerieContingencia = fields.Char('Serie')
    fe_DocNroContingencia = fields.Char(u'Número')
    fe_Serie = fields.Char('Serie')
    fe_DocNro = fields.Char(u'Número')
    fe_FechaHoraFirma = fields.Char('Fecha/Hora de firma')
    fe_Estado = fields.Char('Estado')
    fe_URLParaVerificarQR = fields.Char('Código QR')
    fe_URLParaVerificarTexto = fields.Char('Verificación')
    fe_CAEDNro = fields.Integer('CAE Desde')
    fe_CAEHNro = fields.Integer('CAE Hasta')
    fe_CAENA = fields.Char('CAE Autorización')
    fe_CAEFA = fields.Char('CAE Fecha de autorización')
    fe_CAEFVD = fields.Char('CAE vencimiento')
    fe_qr_img = fields.Binary('Imagen QR', compute='_generate_qr_code')


    @api.depends('fe_URLParaVerificarQR')
    def _generate_qr_code(self):
        a=1
        # qr = qrcode.QRCode(
        #     version=1,
        #     error_correction=qrcode.constants.ERROR_CORRECT_L,
        #     box_size=10,
        #     border=4,
        # )
        # for rec in self:
        #     qr.add_data(rec.fe_URLParaVerificarQR)
        #     qr.make(fit=True)
        #     img = qr.make_image()
        #     temp = BytesIO()
        #     img.save(temp, format="PNG")
        #     qr_image = base64.b64encode(temp.getvalue())
        #     rec.fe_qr_img = qr_image


    #
    # def invoice_send_fe_data(self):
    #     for rec in self:
    #
    #         options = cfeFactory.cfeFactoryOptions()
    #         options._fechaComprobanteYYYYMMDD = rec.date_order.strftime('%Y%m%d')
    #         options._companiaId=rec.company_id.id
    #         options._tipoMonedaTransaccion=rec.currency_id.name
    #         if options._tipoMonedaTransaccion == 'UYU' and rec.currency_id.rate_silent > 0:
    #             #Si la compania esta en pesos, se convierte a pesos segun el cambio
    #             options._tipoCambio = round(1/rec.currency_id.rate_silent,3)
    #         else:
    #             #hardcode debo hacer triangulación de la moneda a pesos
    #             options._tipoCambio = round(28881/1000,3)
    #
    #         options._montoTotalAPagar = rec.amount_total
    #         options._emisorPartnerId = rec.company_id.partner_id
    #         options._montoSubtotal = rec.amount_total-rec.amount_tax
    #
    #     return True



    # def invoice_factura_electronica(self, cr, uid, id, context=None):
    #     pos_order = self.browse(cr, uid, id, context=context)
    #     dir_almacenamiento = pos_order.company_id.carpeta_almacenar
    #
    #     options = cfeFactory.cfeFactoryOptions()
    #     options._fechaComprobanteYYYYMMDD = pos_order.date_order.strftime('%Y%m%d')
    #     options._companiaId=pos_order.company_id.id
    #     options._tipoMonedaTransaccion=pos_order.currency_id.name
    #     if options._tipoMonedaTransaccion == 'UYU' and pos_order.currency_id.rate_silent > 0:
    #         #Si la compania esta en pesos, se convierte a pesos segun el cambio
    #         options._tipoCambio = round(1/pos_order.currency_id.rate_silent,3)
    #     else:
    #         #hardcode debo hacer triangulación de la moneda a pesos
    #         options._tipoCambio = round(28881/1000,3)
    #
    #     options._montoTotalAPagar = pos_order.amount_total
    #     options._emisorPartnerId = pos_order.company_id.partner_id
    #     options._montoSubtotal = pos_order.amount_total-pos_order.amount_tax
    #
    #     # ----------------------------- DATOS DEL EMISOR ------------------------------------------------#
    #     options._emisorRuc = pos_order.company_id.partner_id.city.numero_doc
    #     options._emisorCiudad= pos_order.company_id.partner_id.city
    #     #options._emisorPartnerId = se puede borrar?
    #     options._emisorCodigoCasaPrincipal = pos_order.company_id.codigo_casa_principal_sucursal
    #     options._emisorCorreo=pos_order.company_id.partner_id.correo_dgi
    #     options._emisorDepartamento = pos_order.company_id.partner_id.state_id.name
    #     options._emisorDomicilioFiscal = pos_order.company_id.partner_id.street
    #     options._emisorNombre = pos_order.company_id.partner_id.name
    #     options._emisorNombreCasaPrincipal=pos_order.company_id.codigo_casa_principal_sucursal
    #     options._emisorNombreComercial =  pos_order.company_id.partner_id.name[:150]
    #     options._emisorTelefono = pos_order.company_id.partner_id.phone
    #     options._formaPago=1
    #
    #     # ----------------------------- DATOS DEL RECEPTOR ------------------------------------------------#
    #     #if not pos_order.partner_id.numero_doc:
    #     #    raise osv.except_osv((u'Error: El cliente no tiene número de documento. Información requerida para la FE'),(u'Actualice los datos del Cliente y vuelva a intentar.'))
    #     #if not pos_order.partner_id.tipo_documento:
    #     #    raise osv.except_osv((u'Error: El cliente no tiene tipo de documento. Información requerida para la FE.'),(u'Actualice los datos del Cliente y vuelva a intentar.'))
    #     #if not pos_order.partner_id._check_tipo_documento():
    #     #    raise osv.except_osv((u'Error: El documento del cliente es inválido. Información requerida para la FE.'),(u'Actualice los datos del Cliente y vuelva a intentar.'))
    #
    #     options._receptorRazonSocial = pos_order.partner_id.name #invoice.partner_id.razon_social
    #     options._receptorDocumento = pos_order.partner_id.numero_doc
    #     options._receptorTipoDocumento = pos_order.partner_id.tipo_documento
    #     options._receptorCodigoPais = 'UY'
    #     if pos_order.partner_id.pais_documento.code:
    #         options._receptorCodigoPais = pos_order.partner_id.pais_documento.code
    #     options._receptorDireccion = pos_order.partner_id.direccion_f[:70]
    #     options._receptorCiudad = pos_order.partner_id.city
    #     options._receptorDepartamento = pos_order.partner_id.state_id.name
    #
    #     options._tipoMonedaTransaccion=pos_order.currency_id.name
    #     options._montoTotalNoGravado = 0
    #     options._montoNetoIVATasaBasica=0
    #     options._montoNetoIVATasaMinima=0
    #     options._montoNetoIVATasaOtra=0
    #     options._montoTotal=0
    #     options._montoTotalAPagar=0
    #
    #     for line in lines:
    #         line_aux = cfeFactory.cfeFactoryOptionsProductLineDetail()
    #         line_aux._tipoCod='INT1'
    #         line_aux._codigoItem= line.product_id.id
    #         if line_aux.product_id.taxes_id:
    #             line_aux._indicadorFacturacion = line_aux.product_id.taxes_id[0].codigo_dgi
    #             #if line_aux._indicadorFacturacion=='6' and line.price_unit<0: v_IndicadordeFacturacion='7'
    #         line_aux._nombreItem=line.product_id.name
    #         line_aux._descripcionAdicional=line.product_id.name
    #         line_aux._cantidad = line.qty
    #         line_aux._descuentoPorcentaje=line.discount
    #         line_aux._unidadMedidad = 'Unit'
    #         line_aux._precioUnitario=line.price_unit
    #         line_aux._montoRecargo=0
    #         line_aux._montoDescuento=line.price_subtotal_disc_incl
    #         options._lineasDetalle.append(line_aux)
    #
    #     options._numeroCAE='1'
    #     options._numeroInicialCAE=''
    #     options._numeroFinalCAE=''
    #     options._fechaVencimientoCAEYYYYMMDD='20151201'
    #
    #     xml_factory = cfeFactory.cfeFactory(options=options)
    #     XML = xml_factory.getXML()
    #
    #     logging.info(XML)
    #
    #     return XML