# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reportes',
    'version': '1.0',
    'category': 'Reportes',
    'summary': 'Reportes Adjudicaciones',
    'description': """
===========================================================================
 """,
    'website': 'https://odoo.com/',
    'depends': [
                'gzl_account','bi_account_cheque',
                ],
    'update_xml': [],
    'data': [
            'data/data_grupo.xml',
            
            'security/ir.model.access.csv',

            'views/menu_view.xml',
			'views/fields_view.xml',
            'wizard/informe_credito_cobranza_view.xml',
            'wizard/reporte_estado_de_cuenta_view.xml',
            'wizard/contrato_reserva_view.xml',
            'report/reporte_estado_de_cuenta_template.xml',
            'report/reporte_estado_de_cuenta.xml',
            'wizard/contrato_adendum_wizard_view.xml',
            'wizard/carta_finalizacion_wizard.xml',
            'wizard/pagare_wizard.xml',
            'wizard/reporte_grupos.xml',



            ],
    'installable': True,
    'auto_install': False,


}

