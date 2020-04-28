# -*- coding: utf-8 -*-

from odoo import api, fields, models


DOCUMENT_TYPE_SELECTION = [
    ('2', 'RUT (Uruguay)'),
    ('3', 'C.I. (Uruguay)'),
    ('4', 'Otros'),
    ('5', 'Pasaporte (Todos los Países)'),
    ('6', 'DNI (Documento de Identidad de Argentina, Brasil, Chile o Paraguay)')
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fe_consumidor_final = fields.Boolean('Consumidor final FE', default=True)
    fe_tipo_documento = fields.Selection(DOCUMENT_TYPE_SELECTION, 'Tipo de Documento', default='3')
    fe_pais_documento = fields.Many2one('res.country',u'País del Documento')
    fe_numero_doc = fields.Char(u'Número de Documento', size=32)


    @api.onchange('is_company')
    def onchange_type(self):
        if self.is_company:
            self.fe_consumidor_final = False



    # Funcion que chequea el digito verificador de la cedula
    # def chkdig(self,ci):
    #     #toma el numero de CI menos en numero que está despues del guión
    #     #hace todos los calculos y devuelve el valor que debe tener el numero despues del guión
    #     ci= int(ci)
    #     a1=int(ci*0.000001)
    #     a2=int(ci*0.00001)-(a1*10)
    #     a3=int(ci*0.0001)-(a1*100+a2*10)
    #     a4=int(ci*0.001)-(a1*1000+a2*100+a3*10)
    #     a5=int(ci*0.01)-(a1*10000+a2*1000+a3*100+a4*10)
    #     a6=int(ci*0.1)-(a1*100000+a2*10000+a3*1000+a4*100+a5*10)
    #     a7=int(ci*1)-(a1*1000000+a2*100000+a3*10000+a4*1000+a5*100+a6*10)
    #     b1= (a1*2) % 10
    #     b2= (a2*9) % 10
    #     b3= (a3*8) % 10
    #     b4= (a4*7) % 10
    #     b5= (a5*6) % 10
    #     b6= (a6*3) % 10
    #     b7= (a7*4) % 10
    #     t1=b1+b2+b3+b4+b5+b6+b7
    #     t2= t1 % 10
    #     chd1=abs(t2-10)
    #     chd1= chd1 % 10
    #     return chd1


    # funcion que chequea que el rut sea correcto
    # def check_rut(self,rut):
    #
    #     multiplicadores = [4,3,2,9,8,7,6,5,4,3,2]
    #     resultado=[]
    #     suma = 0
    #     for digit in list(rut):
    #         for multi in multiplicadores:
    #             resultado.append(int(digit)*multi)
    #             multiplicadores.remove(multi)
    #             break
    #     for digito in resultado:
    #         suma += digito
    #     resto = suma % 11
    #     check_digit= 11 - resto
    #     if check_digit < 10:
    #         return check_digit
    #     if check_digit == 11:
    #         return 0
    #     if check_digit==10:
    #         return '-1'

    # funcion que valida si el documento o la cedula son correctas dependiendo del tipo de documento, utilizando las funciones de arriba
    # def _check_tipo_documento(self, cr, uid, ids, context=None):
    #     for record in self.browse(cr, uid,ids, context=context):
    #         tipo_documento = record.tipo_documento
    #         numero = record.numero_doc
    #         if numero:
    #             numero = numero.strip()
    #             if not numero.isdigit() and tipo_documento in (2,3):
    #                 raise osv.except_osv(('Warning!'), ('El número de documento del cliente contiene caracteres que no son digitos para el tipo de documento ingresado'))
    #         if (tipo_documento) and (numero):
    #             if tipo_documento==3:
    #                 if len(str(numero))!= 8:
    #                     raise osv.except_osv(('Warning!'), ('La C.I. ingresada no es correcta'))
    #                 #el algoritmo toma todos los numeros menos el ultimo, por eso se le hace el casteo y 'acortamiento' del numero
    #                 ultimo_digito = self.chkdig(int(str(numero)[:7]))
    #                 if ultimo_digito!= int(str(numero)[-1:]):
    #                     raise osv.except_osv(('Warning!'), ('La C.I. ingresada no es correcta'))
    #             if tipo_documento==2:
    #                 if len((numero))>= 11:
    #                     if int(numero[:2]) not in range(1,22):
    #                         raise osv.except_osv(('Warning!'),('El RUT ingresado no es valido.'))
    #                     if numero[2:8]=='000000':
    #                         raise osv.except_osv(('Warning!'),('El RUT ingresado no es valido.'))
    #                     if numero[8:10]!='00':
    #                         raise osv.except_osv(('Warning!'),('El RUT ingresado no es valido.'))
    #                     last_digit = self.check_rut(numero[:11])
    #                     if len(str(numero))== 12:
    #                         if last_digit!=int(str(numero)[-1]):
    #                             raise osv.except_osv(('Warning!'),('El RUT ingresado no es valido.'))
    #                     if len(str(numero))== 11 and last_digit != '-1':
    #                         raise osv.except_osv(('Warning!'),('El RUT ingresado no es valido.'))
    #                 else:
    #                     raise osv.except_osv(('Warning!'),('El RUT ingresado no es valido.'))
    #         return True

    # funcion que valida si los datos para DGI están correctamente cargados
    # cuando se indica que no es consumidor Final.
    # def _check_consumidor_final(self, cr, uid, ids, context=None):
    #     for record in self.browse(cr, uid,ids, context=context):
    #         consumidor_final = record.consumidor_final
    #         tipo_documento = record.tipo_documento
    #         numero = record.numero_doc
    #         pais_documento = record.pais_documento
    #
    #         if not consumidor_final:
    #             if not tipo_documento or not numero.strip() or not \
    #                     pais_documento:
    #                 raise osv.except_osv(('Error!'), (
    #                     'Debe especificar Tipo, País y Número de Documento '
    #                     'cuando no es Consumidor Final FE.'))
    #     return True
    #
    # _constraints = [(_check_tipo_documento," El documento ingresado es "
    #                                        "inválido para el tipo de documento seleccionado.",['numero_doc','tipo_documento']),
    #                 (_check_consumidor_final,"Debe especificar Tipo, País y "
    #                                          "Número de Documento cuando no "
    #                                          "es Consumidor Final FE.",
    #                  ['consumidor_final','pais_documento', 'numero_doc',
    #                   'tipo_documento'])]

#
# class account_invoice(osv.Model):
#     _inherit = 'account.invoice'
#     _columns = {
#          'partner_tipo_documento': fields.related('partner_id', 'tipo_documento', type='selection', selection=DOCUMENT_TYPE_SELECTION, readonly=True, string='Tipo de Documento'),
#     }
#
