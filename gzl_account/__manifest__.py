# -*- coding: utf-8 -*-
{
    'name': 'gzl_account',
    'version': '1.0',
    'description': 'Modificaciones en Contabilidad',
    'depends': ['account','account_reports'], #project
    'data': [
        #'security/ir.model.access.csv',
        
        'views/num_cuenta_bancaria_view.xml',
        'views/res_partner_bank_view.xml',
        'views/account_payment_view.xml',
        'views/crossovered_budget_view.xml',
        'views/account_account_view.xml',
        #'views/account_analytic_account_view.xml',
        'views/account_asset_view.xml',
        'wizard/account_budget_wizard_view.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
