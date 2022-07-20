# -*- coding: utf-8 -*-
{
    'name': 'Account Cheque',
    'version': '13.0.0.1',
    'category': 'Accounting',
    'summary': 'Help of this app Manage complete of life cycle of Cheque Management',
    'description' :"""Account Cheque management
    Account Cheque Life Cycle Management Odoo
    write cheque management Odoo,
    cheque management system Odoo
    write cheque system on Odoo
    incoming cheque management Odoo
    outgoing cheque management Odoo
    life cycle of cheque system Odoo
    life cycle of cheque management system Odoo
    complete cycle of cheque Odoo
    cheque incoming cycle odoo
    cheque outgoing cycle odoo
    deposit cheque Odoo, cashed cheque, reconcile cheque, cheque write management, cheque submit, cheque submission
    register cheque, cheque register management
    Bounce cheque, cheque Bounce management
    reconcile cheque with payment,
    reconcile cheque with advance payment
    Account reconcilation with cheque management
    return cheque management
    cheque return management
    journal entry from the cheque management system
    write cheque with reconcile system
    Accounting write cheque management system
    Transfer cheque managament odoo

    Account check management
    Account check Life Cycle Management Odoo
    write check management Odoo,
    check management system Odoo
    write check system on Odoo
    incoming check management Odoo
    outgoing check management Odoo
    life cycle of check system Odoo
    life cycle of check management system Odoo
    complete cycle of check Odoo
    check incoming cycle odoo
    check outgoing cycle odoo
    deposit check Odoo, cashed check, reconcile check, check write management, check submit, check submission
    register check, check register management
    Bounce check, check Bounce management
    Account reconcilation with check management
    return check management
    check return management
    journal entry from the check management system
    write check with reconcile system
    Accounting write check manahement system
    Transfer cheque management odoo
    PDC cheque management
    PDC check management 
    post dated cheque management
    post dated check managament

    """,
    'depends': ['account','base','account_accountant','account_reports'],
    'data': [


            'views/menu_tesoreria_view.xml',
            'security/ir.model.access.csv',
            'report/account_cheque_report_view.xml',
            'report/account_cheque_report_template_view.xml',
            'views/account_cheque_view.xml',
            'views/res_config_settings.xml',
            'wizard/gzl_reporte_cheques_vencimiento_view.xml',
            

            
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: