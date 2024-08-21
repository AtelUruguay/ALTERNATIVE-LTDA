# -*- coding: utf-8 -*-
{
    "name": "Cotizaciones Banco Central del Uruguay",
    "version": "17.0.1.0.0",
    "description": """
    Permite establecer las cotizaciones que se quieren actualizar desde el BCU.

    Configurar las monedas en Contabilidad -> Cotizaciones -> Monedas Interfaz

    Para actualizar manualmente ir a Contabilidad -> Cotizaciones -> Actualizar Cotizaciones
        """,
    'author': 'Quanam',
    'website': 'http://www.quanam.com',
    'category': 'Tools',
    'license': 'AGPL-3',
    'depends': ['base', 'account'],
    'data': [
        # Data
        'data/ir_config_param_data.xml',
        'data/ir_cron_cotizacion_data.xml',
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/interfaz_monedas_views.xml',
        'views/res_company_views.xml',
        # Wizard
        'wizard/cotizacion_wizard_views.xml',
        # Menus
        'views/uy_cotizaciones_bcu_menus.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True
}
