from odoo import models, fields, api

class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'
    
    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        """ Prepare the pdf report for the invoice passed as parameter.
        :param invoice:         An account.move record.
        :param invoice_data:    The collected data for the invoice so far.
        """
        if invoice.invoice_pdf_report_id:   
            return
        
        if invoice_data.get('mail_template_id') and invoice_data['mail_template_id'].report_template_ids:
            report_ref = invoice_data['mail_template_id'].report_template_ids[0]
            
            
        else:
            report_ref = 'account.account_invoices'
        
        content, _report_format = self.env['ir.actions.report'].with_company(invoice.company_id)._render(report_ref, invoice.ids)

        invoice_data['pdf_attachment_values'] = {
            'raw': content,
            'name': invoice._get_invoice_report_filename(),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
            'res_field': 'invoice_pdf_report_file', # Binary field
        }

   