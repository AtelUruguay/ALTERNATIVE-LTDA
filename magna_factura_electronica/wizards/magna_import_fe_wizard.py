# -*- coding: utf-8 -*-
import logging
import base64
import csv
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

VALID_COLUMNS = ['FEEmpresaId', 'FEFDIDDocFchEmis', 'FEFDFETmstFirma', 'FEFDIDDocTipoCFE', 'FEFDIDDocSerie', 'FEFDIDDocNro', 'FEFacturaImpOrigDocComCodigo']


class MagnaImportFEWizard(models.TransientModel):
    _name = 'magna_import_fe_wizard'
    _description = 'Magna_import_fe_wizard'

    import_file = fields.Binary(string='File to import', attachment=False)
    import_file_name = fields.Char(string='File Name', required=False)
    move_ids = fields.Many2many('account.move', string='Moves success imported', required=False)
    

    def button_import_file(self):
        if not self.import_file:
            raise UserError(_("Por favor seleccione un fichero para importar."))
        
        pendant_moves_to_import = self.env['account.move'].search_read([
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_refund'),
                '|',('fe_URLParaVerificarQR', 'like', ',101,'),
                ('fe_URLParaVerificarQR', 'like', ',111,'),                
            ],['name', 'id'],)
        if not pendant_moves_to_import:
            raise UserError(_("No existen facturas rectificativas pendientes de importar."))

        try:                        

            file_content = base64.b64decode(self.import_file)
            csv_data = StringIO(file_content.decode('utf-8'))
            reader = csv.DictReader(csv_data, delimiter=",")                                                
            
            pendant_move_to_import_dict = {move['name']: move for move in pendant_moves_to_import}                        
            
            _logger.info("Possible moves to import: %s", pendant_move_to_import_dict)
            csv_columns = reader.fieldnames
            if set(VALID_COLUMNS).issubset(set(csv_columns)):
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
                        # Process the move_id as needed
                        move_record = self.env['account.move'].browse(move_id['id'])
                        move_record.write(row_data)
                        self.move_ids |= move_record
                    else:
                        _logger.warning("No matching move found for row: %s", row)
                        
                return self.action_view_moves()
                

        except Exception as e:
            raise UserError(_("An error occurred while importing the file: %s") % str(e))
        
        
    def action_view_moves(self):
        if not self.move_ids:
            raise UserError(_("No se han importado movimientos."))

        action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_move_out_refund_type')
        action['domain'] = [('id', 'in', self.move_ids.ids)]
        action['context'] = {'create': False, 'edit': False}
        return action
