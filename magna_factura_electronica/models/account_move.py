# -*- coding: utf-8 -*-

# import qrcode
# import pyqrcode
import base64
from io import BytesIO
from odoo import api, fields, models
from . import fe_xml_factory
import logging
from xml.dom.minidom import Document, parse


class AccountMove(models.Model):
    _inherit = "account.move"

    fe_Contingencia = fields.Boolean('Es Contingencia')
    fe_SerieContingencia = fields.Char('Serie')
    fe_DocNroContingencia = fields.Char(u'Número')
    fe_Serie = fields.Char('Serie Factura')
    fe_DocNro = fields.Char(u'Número Factura')
    fe_FechaHoraFirma = fields.Char('Fecha/Hora de firma')
    fe_Estado = fields.Char('Estado')
    fe_URLParaVerificarQR = fields.Char(u'Código QR')
    fe_URLParaVerificarTexto = fields.Char(u'Verificación')
    fe_CAEDNro = fields.Integer('CAE Desde')
    fe_CAEHNro = fields.Integer('CAE Hasta')
    fe_CAENA = fields.Char(u'CAE Autorización')
    fe_CAEFA = fields.Char(u'CAE Fecha de autorización')
    fe_CAEFVD = fields.Char('CAE vencimiento')
    # fe_qr_img = fields.Binary('Imagen QR', compute='_generate_qr_code')


    # @api.depends('fe_URLParaVerificarQR')
    # def _generate_qr_code(self):
    #     a=1
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=10,
    #         border=4,
    #     )
    #     for rec in self:
    #         qr.add_data(rec.fe_URLParaVerificarQR)
    #         qr.make(fit=True)
    #         img = qr.make_image()
    #         temp = BytesIO()
    #         img.save(temp, format="PNG")
    #         qr_image = base64.b64encode(temp.getvalue())
    #         rec.fe_qr_img = qr_image


    #
    # def action_paid(self, cr, uid, ids, context=None):
    #     res = super(pos_order, self).action_paid(cr, uid, ids, context=context)
    #     if res:  # If function returns True then order is paid and picking is done
    #         for order_id in ids:
    #             self.invoice_ensobrar(cr, uid, order_id, context=context)
    #     return res
    #


    def invoice_send_fe_proinfo(self):
        for rec in self:
            # todo arreglar esto
            tipoCFE = 111
            str_xml_cfe = rec.invoice_factura_electronica()
            logging.info(str_xml_cfe)

            str_xml_sobre = fe_xml_factory.cfeFactory().invoice_ensobrar(str_xml_cfe=str_xml_cfe, tipoCFE=tipoCFE)

            # client = fe_xml_factory.cfeFactory._get_client_conn()
            # res = client.service.Execute(str_xml_sobre)
            # logging.info(res)
        return True


    def invoice_factura_electronica(self):
        for rec in self:
            options = fe_xml_factory.cfeFactoryOptions()
            options._lineasDetalle = []

            options._fechaComprobanteYYYYMMDD = rec.invoice_date.strftime('%Y%m%d')
            options._tipoMonedaTransaccion=rec.currency_id.name
            options._fechaVencimientoYYYYMMDD = rec.invoice_date.strftime('%Y%m%d')
            options._montoTotalAPagar = rec.amount_total
            # options._tipoComprobante = rec.
            # options._serieComprobante = rec.
            # options._numeroComprobante = rec.

            # options._emisorRuc = rec.company_id.partner_id.city.numero_doc
            options._emisorNombre = rec.company_id.partner_id.name
            options._emisorDomicilioFiscal = rec.company_id.partner_id.street
            options._emisorNombreComercial = rec.company_id.partner_id.name[:150]

            # todo arreglar
            # options._emisorCodigoCasaPrincipal = rec.company_id.codigo_casa_principal_sucursal
            options._emisorCodigoCasaPrincipal= 1

            options._emisorCiudad = rec.company_id.partner_id.city
            options._emisorDepartamento = rec.company_id.partner_id.state_id.name
            # todo arreglar
            # options._receptorTipoDocumento = rec.partner_id.tipo_documento
            options._receptorTipoDocumento = 'RUT'


            options._receptorCodigoPais = 'UY'
            # todo arreglar
            # if rec.partner_id.pais_documento.code:
            #     options._receptorCodigoPais = rec.partner_id.pais_documento.code
            # options._receptorDocumento = rec.partner_id.numero_doc
            options._receptorRazonSocial = rec.partner_id.name #invoice.partner_id.razon_social
            # options._receptorDireccion = rec.partner_id.direccion_f[:70]
            options._receptorCiudad = rec.partner_id.city
            options._receptorDepartamento = rec.partner_id.state_id.name

            options._formaPago = 1
            options._montoTotalNoGravado = 0
            options._montoNetoIVATasaMinima=0
            options._montoNetoIVATasaBasica=0
            options._IVATasaMinima=0
            options._IVATasaBasica=0
            options._montoIVATasaBasica = 0
            options._montoTotal = 0

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

            for line in rec.invoice_line_ids:
                line_aux = fe_xml_factory.cfeFactoryOptionsProductLineDetail()
                line_aux._cantidad = line.quantity
                line_aux._nombreItem = line.product_id.name
                line_aux._unidadMedidad = 'Unit'
                line_aux._precioUnitario = line.price_unit
                line_aux._montoItem = line.price_unit
                # if line.product_id.taxes_id:
                #     line_aux._indicadorFacturacion = line.product_id.taxes_id[0].codigo_dgi
                options._lineasDetalle.append(line_aux)

            xml_factory = fe_xml_factory.cfeFactory(options=options)
            XML = xml_factory.getXML()

            logging.info(XML)

        return XML

