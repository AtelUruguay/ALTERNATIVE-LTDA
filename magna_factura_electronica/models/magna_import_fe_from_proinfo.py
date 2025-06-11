# -*- coding: utf-8 -*-
import logging

import base64
import csv
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

VALID_COLUMNS = ['FEEmpresaId', 'FEFDIDDocFchEmis', 'FEFDFETmstFirma', 'FEFDIDDocTipoCFE', 'FEFDIDDocSerie', 'FEFDIDDocNro', 'FEFacturaImpOrigDocComCodigo']

_logger = logging.getLogger(__name__)


class Magna_import_fe_from_proinfo(models.Model):
    _name = 'magna_import_fe_from_proinfo'
    _description = 'Importa datos de FE desde Proinfo'
    rec_name = 'filename'

    filename = fields.Char('Fichero', required=True)
    file_data = fields.Binary('Datos del fichero', required=True)
    move_ids = fields.Many2many('account.move', relation='magna_import_fe_from_proinfo_move_rel', string='Movimientos importados', required=False)
    move_ids_qty = fields.Integer(compute='_compute_move_ids_qty', string='Cantidad de movimientos importados', readonly=True)
    miss_move_ids = fields.Many2many('account.move', relation='magna_import_fe_from_proinfo_miss_move_rel', string='Movimientos no encontrados en el fichero', required=False)
    miss_move_ids_qty = fields.Integer(compute='_compute_miss_move_ids_qty', string='Cantidad de movimientos no encontrados en el fichero', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('imported', 'Importado'),
        ('error', 'Error')
    ], default='draft', string='Estado')
    
    @api.depends('move_ids')
    def _compute_move_ids_qty(self):
        for record in self:
            record.move_ids_qty = len(record.move_ids)

    @api.depends('miss_move_ids')
    def _compute_miss_move_ids_qty(self):
        for record in self:
            record.miss_move_ids_qty = len(record.miss_move_ids)
    
    
    def action_import_file(self):
        if not self.file_data:
            raise UserError(_("Por favor seleccione un fichero para importar."))
        
        pendant_moves_to_import = self.env['account.move'].search([
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_refund'),
                '|',('fe_URLParaVerificarQR', 'like', ',101,'),
                ('fe_URLParaVerificarQR', 'like', ',111,'),                
            ])
        
        if not pendant_moves_to_import:
            raise UserError(_("No existen facturas rectificativas pendientes de importar."))                

        try:                        

            file_content = base64.b64decode(self.file_data)
            csv_data = StringIO(file_content.decode('utf-8'))
            reader = csv.DictReader(csv_data, delimiter=",")                                                
            pendant_move_to_import_dict = {move.name: move for move in pendant_moves_to_import}                        
            _logger.info("Possible moves to import: %s", pendant_move_to_import_dict)
            csv_columns = reader.fieldnames
            if not set(VALID_COLUMNS).issubset(set(csv_columns)):
                raise ValidationError(_("El fichero no contiene las columnas requeridas: %s") % ', '.join(VALID_COLUMNS))            
            
            reader_filtered = [row for row in reader if row.get('FEFacturaImpOrigDocComCodigo') in pendant_move_to_import_dict.keys()]

            for row in reader_filtered:
                # Process each row as needed
                _logger.info("Processing row: %s", row)
                row_data = {
                    'fe_FechaHoraFirma': row.get('FEFDFETmstFirma'),
                    'fe_Serie': row.get('FEFDIDDocSerie'),
                    'fe_DocNro': row.get('FEFDIDDocNro'),                   
                }
                move_id = pendant_move_to_import_dict.get(row.get('FEFacturaImpOrigDocComCodigo'))
                if move_id:                                                                
                    move_id.write(row_data)
                    self.move_ids |= move_id
                else:
                    _logger.warning("No matching move found for row: %s", row)
                    
                
            self.state = 'imported'
            self.miss_move_ids = pendant_moves_to_import - self.move_ids

        except Exception as e:
            with self.env.cr.savepoint():
                self.state = 'error'
            raise UserError(_("An error occurred while importing the file: %s") % str(e))
        
        
    def action_reset(self):
        self.state = 'draft'
        self.move_ids = self.env['account.move']
        self.miss_move_ids = self.env['account.move']
        return True
    
    def action_view_miss_move_ids(self):
        return self.action_view_moves(miss_moves=True)


    def action_view_moves(self, miss_moves=False):                
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_refund_type')
        action['domain'] = [('id', 'in', self.move_ids.ids if not miss_moves else self.miss_move_ids.ids)]
        action['context'] = {'create': False, 'edit': False}
        return action

