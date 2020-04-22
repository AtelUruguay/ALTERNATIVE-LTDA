# -*- coding: utf-8 -*-
{
    'name' : 'Magna - Factura electrónica',
    'version' : '0.1',
    'summary': 'Realiza el envío de los datos de factura al proveedor de factura electrónica',
    'description': """
    """,
    'category': 'Localizacion',
    'author': 'Quanam',
    'website': 'https://www.quanam.com',
    'depends' : ['base', 'account'],
    'data': [
        # 'data/fe_data.xml',
        'views/account_move_views.xml',
        'views/partner_view.xml',
        'views/company_view.xml',
        'views/taxes_view.xml'
    ],
    'demo': [],
    # 'qweb': [
    #     "static/src/xml/account_reconciliation.xml",
    # ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
