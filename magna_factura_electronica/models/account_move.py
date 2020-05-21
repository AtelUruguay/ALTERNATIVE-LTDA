# -*- coding: utf-8 -*-

import qrcode
import base64
from io import BytesIO
from odoo import api, fields, models
from . import fe_xml_factory
from odoo.exceptions import UserError
import logging


DOC_TYPE_DGI = [
    ('101', 'e-Ticket'),
    ('201', 'e-Ticket Contingencia'),
    ('102', 'Nota de Crédito de e-Ticket'),
    ('202', 'Nota de Crédito de e-Ticket Contingencia'),
    ('103', 'Nota de Débito de e-Ticket'),
    ('203', 'Nota de Débito de e-Ticket Contingencia'),
    ('111', 'e-Factura'),
    ('211', 'e-Factura Contingencia'),
    ('112', 'Nota de Crédito de e-Factura'),
    ('212', 'Nota de Crédito de e-Factura Contingencia'),
    ('113', 'Nota de Débito de e-Factura'),
    ('213', 'Nota de Débito de e-Factura Contingencia'),
    ('121', 'e-Factura Exportación'),
    ('221', 'e-Factura Exportación Contingencia'),
    ('122', 'Nota de Crédito de e-Factura Exportación'),
    ('222', 'Nota de Crédito de e-Factura Exportación Contingencia'),
    ('123', 'Nota de Débito de e-Factura Exportación'),
    ('223', 'Nota de Débito de e-Factura Exportación Contingencia'),
    ('124', 'e-Remito de Exportación'),
    ('224', 'e-Remito de Exportación Contingencia'),
    ('131', 'e-Ticket Venta por Cuenta Ajena'),
    ('231', 'e-Ticket Venta por Cuenta Ajena Contingencia'),
    ('132', 'Nota de Crédito de e-Ticket Venta por Cuenta Ajena'),
    ('232', 'Nota de Crédito de e-Ticket Venta por Cuenta Ajena Contingencia'),
    ('133', 'Nota de Débito de e-Ticket Venta por Cuenta Ajena'),
    ('233', 'Nota de Débito de e-Ticket Venta por Cuenta Ajena Contingencia'),
    ('141', 'e-Factura Venta por Cuenta Ajena'),
    ('241', 'e-Factura Venta por Cuenta Ajena Contingencia'),
    ('142', 'Nota de Crédito de e-Factura Venta por Cuenta Ajena'),
    ('242', 'Nota de Crédito de e-Factura Venta por Cuenta Ajena Contingencia'),
    ('143', 'Nota de Débito de e-Factura Venta por Cuenta Ajena'),
    ('243', 'Nota de Débito de e-Factura Venta por Cuenta Ajena Contingencia'),
    ('151', 'e-Boleta de entrada'),
    ('251', 'e-Boleta de entrada Contingencia'),
    ('152', 'Nota de Crédito de e-Boleta de entrada'),
    ('252', 'Nota de Crédito de e-Boleta de entrada'),
    ('153', 'Nota de Débito de e-Boleta de entrada'),
    ('253', 'Nota de Débito de e-Boleta de entrada'),
    ('181', 'e-Remito'),
    ('281', 'e-Remito Contingencia'),
    ('182', 'e-Resguardo'),
    ('282', 'e-Resguardo Contingencia')
]

class AccountMove(models.Model):
    _inherit = "account.move"

    fe_Contingencia = fields.Boolean('Es Contingencia', default=False)
    fe_SerieContingencia = fields.Char('Serie')
    fe_DocNroContingencia = fields.Char(u'Número')
    fe_Serie = fields.Char('Serie Factura')
    fe_DocNro = fields.Char(u'Número Factura')
    fe_FechaHoraFirma = fields.Char('Fecha/Hora de firma')
    fe_Hash = fields.Char('Hash')
    fe_Estado = fields.Char('Estado')
    fe_URLParaVerificarQR = fields.Char(u'Código QR')
    fe_URLParaVerificarTexto = fields.Char(u'Verificación')
    fe_CAEDNro = fields.Integer('CAE Desde')
    fe_CAEHNro = fields.Integer('CAE Hasta')
    fe_CAENA = fields.Char(u'CAE Autorización')
    fe_CAEFA = fields.Date(u'CAE Fecha de autorización')
    fe_CAEFVD = fields.Date('CAE Vencimiento')
    fe_qr_img = fields.Binary('Imagen QR', compute='_generate_qr_code', store=True, default=False)
    # doct_type = fields.Selection(DOC_TYPE_DGI, compute='_compute_doct_type', string='Tipo de factura DGI')
    forma_pago = fields.Selection([('1','Contado'),('2','Crédito')], compute='_compute_forma_pago', string='Forma de pago', default='1')


    @api.depends('fe_URLParaVerificarQR')
    def _generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        for rec in self:
            if rec.fe_URLParaVerificarQR:
                qr.add_data(rec.fe_URLParaVerificarQR)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.fe_qr_img = qr_image

    # @api.depends('type', 'partner_id')
    # def _compute_doct_type(self):
    #     for rec in self:
    #         val = False
    #         invoice_type = rec.type
    #         consumidor_final = rec.partner_id.fe_tipo_documento != '2'
    #         if consumidor_final:  # eTicket
    #             if invoice_type == 'out_invoice':  # Factura de cliente
    #                 val = '101'
    #             elif invoice_type == 'out_refund':  # NC de cliente
    #                 val = '102'
    #         else:  # eFactura
    #             if invoice_type == 'out_invoice':  # Factura de cliente
    #                 val = '111'
    #             elif invoice_type == 'out_refund':  # NC de cliente
    #                 val = '112'
    #         rec.doct_type = val


    @api.depends('invoice_payment_term_id','invoice_date_due')
    def _compute_forma_pago(self):
        for rec in self:
            # 1-Contado, 2-Credito
            today = fields.Date.context_today(self)
            payment_term_contado = self.env.ref('account.account_payment_term_immediate').id
            if rec.invoice_payment_term_id == payment_term_contado or rec.invoice_date_due == today:
                rec.forma_pago = '1'
            else:
                rec.forma_pago = '2'


    # se llama al action_post de super y antes de devolver el control, se envía la información de FE
    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.type in ('out_invoice', 'out_refund'):
            self.invoice_send_fe_proinfo()
        return res


    def invoice_send_fe_proinfo(self):
        fe_activa = self.env["ir.config_parameter"].sudo().get_param("magna_fe_activa")
        if fe_activa == 'True':
            for rec in self:
                tipo_cfe = self.get_tipo_cfe()
                in_xml_entrada = self.gen_Inxmlentrada(tipo_cfe)
                vals = fe_xml_factory.CfeFactory().invocar_generar_y_firmar_doc(in_xml_entrada, tipo_cfe)
                rec.write(vals)
        return True

    def get_tipo_cfe(self):
        for rec in self:
            invoice_type = rec.type
            consumidor_final = rec.partner_id.fe_tipo_documento != '2'
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

    def gen_Inxmlentrada(self, tipo_CFE):
        for rec in self:
            options = fe_xml_factory.cfeFactoryOptions()
            options._lineasDetalle = []

            options._tipoComprobante = tipo_CFE
            options._fechaComprobanteYYYYMMDD = rec.invoice_date.strftime('%Y-%m-%d')
            options._fechaVencimientoYYYYMMDD = rec.invoice_date_due.strftime('%Y-%m-%d')
            # indica si los montos de las líneas de detalles se expresan con impuestos incluidos
            options._indicadorMontoBruto = False
            options._esContingencia = rec.fe_Contingencia

            # 1-Contado, 2-Credito
            options._formaPago = rec.forma_pago

            # EMISOR
            options._emisorRuc = rec.company_id.vat
            options._emisorNombre = rec.company_id.name
            options._emisorDomicilioFiscal = rec.company_id.street
            options._emisorNombreComercial = rec.company_id.fe_nombre_fantasia
            options._emisorCodigoCasaPrincipal = rec.company_id.fe_codigo_principal_sucursal
            options._emisorCiudad = rec.company_id.city
            options._emisorDepartamento = rec.company_id.state_id and rec.company_id.state_id.name or False

            # RECEPTOR
            options._receptorTipoDocumento = rec.partner_id.fe_tipo_documento
            options._receptorCodigoPais = rec.partner_id.fe_pais_documento.code
            options._receptorDocumento = rec.partner_id.fe_numero_doc
            options._receptorRazonSocial = rec.partner_id.name
            options._receptorDireccion = rec.partner_id.street
            options._receptorCiudad = rec.partner_id.city
            options._receptorDepartamento = rec.partner_id.state_id and rec.partner_id.state_id.name or False

            # TOTALES
            options._tipoMonedaTransaccion = rec.currency_id.name
            options._tipoCambio = rec.currency_id.inverse_rate

            account_tax_obj = self.env['account.tax']
            account_tax_iva_minima_id = account_tax_obj.search([('company_id', '=', rec.company_id.id),
                                                                         ('fe_tax_codigo_dgi.code', '=', '2'),
                                                                         ('type_tax_use', '=', 'sale')], limit=1)
            account_tax_iva_basica_id = account_tax_obj.search([('company_id', '=', rec.company_id.id),
                                                                         ('fe_tax_codigo_dgi.code', '=', '3'),
                                                                         ('type_tax_use', '=', 'sale')], limit=1)
            if not account_tax_iva_minima_id:
                raise UserError(
                    'No existe configurado un impuesto con Código de DGI 2 (Iva tasa mínima)')
            if not account_tax_iva_basica_id:
                raise UserError(u'No existe configurado un impuesto con Código de DGI 3 (Iva tasa basica)')

            options._IVATasaMinima = account_tax_iva_minima_id[0].amount
            options._IVATasaBasica = account_tax_iva_basica_id[0].amount

            # ADICIONAL
            options._adicionalTipoDocumentoId = tipo_CFE
            options._adicionalDocComCodigo = rec.id
            options._adicionalSucursalId = rec.company_id.fe_codigo_principal_sucursal
            options._adicionalAdenda = ''
            options._adicionalCorreoReceptor = ''
            if rec.fe_Contingencia:
                options._serieComprobante = rec.fe_SerieContingencia
                options._numeroComprobante = rec.fe_DocNroContingencia
                options._adicionalCAEDnro = rec.fe_CAEDNro
                options._adicionalCAEHnro = rec.fe_CAEHNro
                options._adicionalCAENA = rec.fe_CAENA
                options._adicionalCAEFA = rec.fe_CAEFA.strftime('%Y-%m-%d')
                options._adicionalCAEFVD = rec.fe_CAEFVD.strftime('%Y-%m-%d')
            else:
                serie = self.env["ir.config_parameter"].sudo().get_param("magna_fe_serie")
                options._adicionalDocComSerie = serie

            # DETALLE
            monto_no_gravado = 0
            monto_neto_iva_tasa_basica = 0
            monto_neto_iva_tasa_minima = 0
            for line in rec.invoice_line_ids:
                line_aux = fe_xml_factory.cfeFactoryOptionsProductLineDetail()
                line_aux._cantidad = line.quantity
                line_aux._nombreItem = line.product_id.name
                line_aux._unidadMedidad = 'Unit'
                line_aux._precioUnitario = line.price_unit
                monto_descuento = line.quantity * line.price_unit * line.discount / 100
                monto_item = (line.quantity * line.price_unit) - monto_descuento
                line_aux._descuentoMonto = monto_descuento
                line_aux._montoItem = monto_item
                if line.tax_ids:
                    # if line.product_id.tax_ids[0].price_include:
                    #     options._indicadorMontoBruto = True

                    fe_tax_codigo_dgi_code = line.tax_ids[0].fe_tax_codigo_dgi.code # todo ojo,esta asumiendo que hay 1 solo impuesto por linea...
                    type_tax_use = line.tax_ids[0].type_tax_use
                    #todo si el indicador es true, ojo que tendria que "desarmar" los montos para esta linea...
                    line_aux._indicadorFacturacion = fe_tax_codigo_dgi_code

                    if fe_tax_codigo_dgi_code == '1' and type_tax_use == 'sale':
                        monto_no_gravado += monto_item
                    if fe_tax_codigo_dgi_code == '2' and type_tax_use == 'sale':
                        monto_neto_iva_tasa_minima += monto_item
                    if fe_tax_codigo_dgi_code == '3' and type_tax_use == 'sale':
                        monto_neto_iva_tasa_basica += monto_item
                else:
                    monto_no_gravado += monto_item
                    line_aux._indicadorFacturacion = self.env.ref('magna_factura_electronica.fe_ind_fact_dgi_1').code

                options._lineasDetalle.append(line_aux)

            monto_iva_tasa_minima = monto_neto_iva_tasa_minima * account_tax_iva_minima_id[0].amount /100
            monto_iva_tasa_basica = monto_neto_iva_tasa_basica * account_tax_iva_basica_id[0].amount / 100
            options._montoTotalNoGravado = monto_no_gravado
            options._montoNetoIVATasaMinima = monto_neto_iva_tasa_minima
            options._montoIVATasaMinima = monto_iva_tasa_minima
            options._montoNetoIVATasaBasica = monto_neto_iva_tasa_basica
            options._montoIVATasaBasica = monto_iva_tasa_basica

            # options._montoTotal = abs(rec.amount_total - monto_no_facturable)
            options._montoTotal = monto_no_gravado + monto_neto_iva_tasa_minima + monto_neto_iva_tasa_basica + monto_iva_tasa_minima + monto_iva_tasa_basica
            options._montoTotalAPagar = rec.amount_total

            xml_factory = fe_xml_factory.CfeFactory(options=options)
            XML = xml_factory.get_data_XML()

            return XML



    def report_get_DgiParam(self):
        resolucion_dgi = self.env["ir.config_parameter"].sudo().get_param("magna_fe_resolucion_DGI")
        return resolucion_dgi

    def report_get_document_type(self):
        value = dict(self.env['res.partner']._fields['fe_tipo_documento'].selection).get(self.partner_id.fe_tipo_documento)
        return value


    def report_get_doct_type(self):
        tipo_cfe = self.get_tipo_cfe()
        value = dict(DOC_TYPE_DGI).get(str(tipo_cfe))
        return value


