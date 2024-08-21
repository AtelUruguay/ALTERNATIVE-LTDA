# -*- coding: utf-8 -*-
{
    'name': 'Sales Teams Custom',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Sales Teams Custom',
    'description': """
Modifica las líneas de sale.order para que sea de solo lectura el precio unitario si el usuario pertenece a los grupos:
sales_team.group_sale_salesman_all_leads ó 	sales_team.group_sale_salesman
===========================================================================
 """,
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['sales_team', 'sale'],
    'data': ['views/sale_order_views.xml',
             ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
