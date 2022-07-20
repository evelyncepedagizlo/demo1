{
    "name" : "gzl_sign",
    "version" : "0.1",
    'depends' :['sign','base','crm'
                ],
    "author" : "Yadira Quimis Gizlo",
    "description" : """
    Heredado de SIGN
                    """,
    "website" : "http://www.gizlocorp.com",
    "category" : "Generic Modules",
   
    "data" : [   
                #'data/data_contrato_licitacion.xml',

                #'views/res_partner_view.xml',
                #'views/ir_attachment_view.xml',

                'wizard/peticion_firma_view.xml',
                   
            ],
    
    'installable': True,
    'auto_install': False,
}