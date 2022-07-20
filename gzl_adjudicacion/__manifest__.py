{
    "name" : "gzl_adjudicacion",
    'category': 'Adjudicaciones',
    "version" : "0.1",
    'depends' :['base','mail','portal','base_setup','l10n_ec_tree','report_xlsx',],
    "author" : "Yadira Quimis Gizlo",
    "description" : """
    product
                    """,
    "website" : "http://www.gizlocorp.com",
    "category" : "Generic Modules",
   
    "data" : [   
                    'data/data_grupo_adjudicacion.xml',
                    'data/data_tipo_contrato.xml',
                    'data/data_secuencia.xml',
                    'data/data_calificacion_cliente_parametros.xml',
                    'data/data_configuracion_adicional.xml',
                    'data/data_numero_meses.xml' ,   
                    'data/data_roles.xml',
                    'data/ir_cron.xml',
                    'data/data_mail_template.xml',


                    'security/ir.model.access.csv',

                    'views/menu_view.xml',
                    'views/socio_view.xml',
                    'views/tipo_contrato_view.xml',
                    'views/concesionario_view.xml',
                    'views/grupo_adjudicado_view.xml',
                    'views/entrega_vehiculo_view.xml',
                    'views/asamblea_view.xml',
                    'views/contrato_view.xml',
                    'views/res_config_settings_views.xml',
                    'views/configuracion_adicional.xml',
                    'views/calificador_view.xml',
                    'views/stylesheet_view.xml',
                    'views/numero_meses_view.xml',
                    'views/adjudicaciones_team_view.xml',
                    'views/items_patrimonio.xml',
                    'views/paginas_de_control.xml',
                    'views/calificaciones_clientes_view.xml',
                    'views/puntos_bienes.xml',
                    'views/transacciones_grupos_view.xml',
                    'views/devolucion_view.xml',
                    'views/contrato_informe_view.xml',
                    'views/contrato_view_adendum.xml', 

                    
                    'wizard/wizard_pago_contrato_view.xml',
                    'wizard/wizard_adelantar_pago_view.xml',
                    'wizard/wizard_actualizar_rubro_view.xml',
                    'wizard/wizard_contrato_adendum_view.xml',
                    'wizard/wizard_cesion_derecho_view.xml',
                    'wizard/wizard_report_devolucion_monto.xml',
                    'wizard/wizard_actualizar_contrato_view.xml',
                    
                    ],
    
    'installable': True,
    'auto_install': False,
}



