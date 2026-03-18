# -*- coding: utf-8 -*-
{
    'name': 'No Product Create from Documents',
    'summary': 'Blocks product creation from sales, purchases and invoices line forms.',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['sale', 'purchase', 'account'],
    'data': [
        'views/restrict_product_creation_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
