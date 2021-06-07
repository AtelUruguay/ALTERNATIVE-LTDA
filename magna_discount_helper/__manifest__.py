# -*- coding: utf-8 -*-
{
    'name' : 'Magna - Funcionalidad de carga de descuentos',
    'version' : '0.1',
    'summary': 'Facilita la asignación de descuentos en las líneas de pedido de venta y factura',
    'description': """
    """,
    'category': 'Localizacion',
    'author': 'Quanam',
    'website': 'https://www.quanam.com',
    'depends' : ['base','account','sale'],
    'data': [
        'views/account_move_views.xml',
        'views/sale_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
