from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    check_stock_before_invoice = fields.Boolean(
        string="Requires stock to invoice",
        default=False,
        help="If ticked, a sales order cannot be invoiced unless the whole pending "
             "quantity of this product can be reserved at the moment the invoice is "
             "created. Only meaningful on storable products.",
    )
