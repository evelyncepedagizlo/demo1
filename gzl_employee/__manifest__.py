# -*- coding: utf-8 -*-
{
    'name': 'gzl_employee',
    'version': '1.0',
    'description': 'Modificaciones en Empleados',
    'depends': ['hr','hr_payroll','l10n_ec_hr_payroll'],
    'data': [
            'security/ir.model.access.csv',

            'data/data_groups.xml',
            'data/data_age.xml',
            'data/ir_cron.xml',

            'views/hr_employee_view.xml',
            'views/hr_payslip_view.xml',
            'views/ir_attachment_view.xml',
            'views/res_bank_view.xml',
            'views/comision_view.xml',
            'views/comision_bitacora_view.xml',
            
            'wizard/report_thirteenth_salary_view.xml',
            'wizard/report_fourteenth_salary_view.xml',
            'wizard/report_payment_file_view.xml',
            'wizard/report_vacations_view.xml',
            'wizard/report_comisiones_view.xml',
            'wizard/res_company_views.xml',
            'wizard/report_comisionistas_view.xml'
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
