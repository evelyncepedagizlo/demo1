# -*- coding: utf-8 -*-
{
    'name': "l10n_ec_hr_expence",

    'summary': """
        Arreglos del modulo gastos para la localización en empresas sin branch""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://opa-consulting.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_expense','gzl_facturacion_electronica'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/inherit_hr_expense.xml',
        'views/inherit_hr_expense_sheet.xml'
    ],
}
