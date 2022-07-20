# -*- coding: utf-8 -*-
{
    'name': 'Impresion de Cheques para Ecuador',
    'version': '13.0.0.1.0',
    'category': 'Accounting',
    'complexity': 'normal',
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/report_check_pacifico.xml',
        'views/reports.xml',
        'views/account_view.xml',
        'views/report_template_matriz.xml',
        'views/reports_matriz.xml',
        'views/report_payment_receipt_templates.xml',
    ],
    'depends': [
        'base',
        'account_accountant',
        'account_check_printing',
        'account_batch_payment',
        'bi_account_cheque',
        'account',
    ],

    'installable': True,
    'auto_install': False,

}
