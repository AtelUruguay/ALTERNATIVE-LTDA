# -*- coding: utf-8 -*-
{
    'name' : 'Magna - Factura electrónica',
    'version': '17.0.1.1.0',
    'summary': 'Realiza el envío de los datos de factura al proveedor de factura electrónica',
    'description': """
    """,
    'category': 'Localizacion',
    'author': 'Quanam',
    'website': 'https://www.quanam.com',
    'depends' : ['base','account','base_currency_inverse_rate','web'],
    "data": [
        "data/fe_data.xml",
        "data/fe_mail_template_data.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/company_view.xml",
        "views/magna_import_fe_from_proinfo_views.xml",
        "views/partner_view.xml",
        "views/taxes_view.xml",
        "wizards/magna_import_fe_wizard.xml",
        "report/magna_fe_invoice_report_tmpl.xml",
        "report/magna_fe_invoice_report.xml"
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
