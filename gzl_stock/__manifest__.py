# -*- coding: utf-8 -*-
{
    'name': 'gzl_stock',
    'version': '1.0',
    'description': 'Modificaciones en Inventario',
    'depends': ['stock','stock_account'],
    'data': [
        'data/data_tipo_inventario.xml',

        'security/ir.model.access.csv',
        
        'views/tipo_inventario_view.xml',
        'views/product_template_view.xml',
        'views/stock_valuation_layer_view.xml',
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
