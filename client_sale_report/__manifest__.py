# -*- coding: utf-8 -*-
{
    'name': "client_sale_report",

    'description': """
        Client sale report, add tree view in Account/Client/Cliente sale report
    """,

    'author': "Quanam",
    'website': "http://www.quanam.com",

    'category': 'Accounting/Accounting',
    'version': '0.1',
    'depends': ['account'],

    # always loaded
    'data': [
        'views/account_move_line_views.xml',
    ],
}
