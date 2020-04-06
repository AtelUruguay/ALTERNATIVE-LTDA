# -*- coding: utf-8 -*-
{
    "name": "Cotizaciones Banco Central del Uruguay",
    "version": "0.1",
    'summary': 'Interfaz con BCU para obtener cotizaciones de las monedas. Ajustado para Odoo v13.',
    "description": """
Permite establecer las cotizaciones que se quieren actualizar desde el BCU.

Configurar las monedas en Contabilidad -> Cotizaciones -> Monedas Interfaz

Para actualizar manualmente ir a Contabilidad -> Cotizaciones -> Actualizar Cotizaciones
    """,
    "author": "Quanam",
    'website': 'https://www.quanam.com',
    "category": "Localización",

    "depends": ['base', 'account'],

    "data":[
        'security/ir.model.access.csv',
        'views/cotizacion_view.xml',
        'data/cotizacion_cron_job.xml',
        'data/config_param.xml'
    ],

    "active": False,
    "installable": True,
    'auto_install': False,
    'application': True
}