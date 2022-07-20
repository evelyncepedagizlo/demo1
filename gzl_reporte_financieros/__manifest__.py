# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Reportes Financieros',
    'version': '1.0',
    'category': 'Reportes',
    'summary': 'Reportes ',
    'description': """
===========================================================================
 """,
    'website': 'https://odoo.com/',
    'depends': [
                'gzl_account','bi_account_cheque',
                ],
    'data': [
            'data/data_periods_debts_due.xml',
        
            'security/ir.model.access.csv',

            'wizard/gzl_reporte_subproyectos_por_mes_view.xml',
            'wizard/report_of_debts_due_views.xml',
            'wizard/gzl_reporte_proveedores_clientes_view.xml',
            'wizard/gzl_reporte_anticipo_view.xml',
            'wizard/gzl_reporte_impuesto_view.xml',
            'wizard/gzl_reporte_ventas_view.xml',
            'wizard/gzl_reporte_compras_view.xml',
            'wizard/gzl_reporte_estado_cuenta_view.xml',
            'wizard/gzl_reporte_analisis_cartera_view.xml',
            'wizard/gzl_reporte_estado_cuenta_bancario_view.xml',
            'wizard/importar_csv_view.xml',
            'report/reporte_conciliacion_bancaria_template.xml',
            'report/reporte_conciliacion_bancaria.xml',
            'report/reporte_anticipo_template.xml',
            'report/reporte_anticipo.xml',
            'report/reporte_estado_cuenta_template.xml',
            'report/reporte_estado_cuenta.xml',
            'report/reporte_estado_cuenta_bancario_template.xml',
            'report/reporte_estado_cuenta_bancario.xml',
            'report/reporte_saldo_empresas_template.xml',
            'report/reporte_saldo_empresas.xml',



             ],
    'installable': True,
    'auto_install': False,
}

