from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    partner_id_email_related = fields.Char(related='order_partner_id.email')
    date_order = fields.Datetime(related='order_id.date_order')
