# -*- coding: utf-8 -*-
{
    'name': 'gzl_gastos',
    'version': '1.0',
    'description': 'Modificaciones en el Módulo de Gastos',
    'depends': ['hr_expense','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_sheet_view.xml',
        'views/account_payment_view.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
