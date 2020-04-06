# -*- coding: utf-8 -*-
{
    "name": "Cotizaciones Banco Central del Uruguay",
    "version": "2.0",
    "description": """
Permite establecer las cotizaciones que se quieren actualizar desde el BCU.

Configurar las monedas en Contabilidad -> Cotizaciones -> Monedas Interfaz

Para actualizar manualmente ir a Contabilidad -> Cotizaciones -> Actualizar Cotizaciones
    """,
    "author": "GDev-Team",
    "category": "Tools",
    "depends": ['base'],
    "data":['cotizacion_view.xml',
            'cotizacion_cron_job.xml',
            'data/config_param.xml'],
    "active": False,
    "installable": True,
    'auto_install': False,
    'application': True
}