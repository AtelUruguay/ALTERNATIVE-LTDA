{
    'name': "Stock Control Before Invoicing",
    'summary': "Block invoicing a sales order without stock, and reserve the goods when invoicing",
    'description': """
Stock Control Before Invoicing
==============================

Prevents invoicing a sales order when there is not enough stock to cover the
lines that require it, and reserves the goods at that exact moment.

The check runs when the invoice is created from the sales order, both from the
*Create Invoice* button and from the invoicing wizard. Only lines whose product
is flagged with *Requires stock to invoice* are evaluated, and each line is
required in full: a partial reservation blocks the invoice.

Users in the *Can invoice without stock* group may invoice anyway by filling in
a justification, which is logged in the order chatter.

Down payment invoices are not affected: the advance payment wizard builds them
without going through the sales order invoicing method.

Implemented by inheritance of ``sale.order`` and ``product.template``; no
standard model, view or flow is modified.
""",
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'author': "Quanam",
    'website': "https://www.quanam.com",
    'license': 'LGPL-3',
    'depends': [
        'sale_stock',
    ],
    'data': [
        'security/sale_invoice_stock_control_security.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
