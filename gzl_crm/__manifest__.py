{
    "name" : "gzl_crm",
    "version" : "0.1",
    'depends' :['crm','sale','gzl_adjudicacion','gzl_account'
                ],
    "author" : "Yadira Quimis Gizlo",
    "description" : """
    Heredado de CRM
                    """,
    "website" : "http://www.gizlocorp.com",
    "category" : "Generic Modules",
   
    "data" : [   
                "data/data_accion_planificada.xml",
                "data/data_invoice.xml",

                
                "security/ir.model.access.csv",
                "views/crm_lead_view.xml", 
                "views/crm_lead_simplified_form.xml", 
                "views/crm_stage_view.xml", 
                "views/crm_team_view.xml", 
                "views/surcursal_view.xml", 


                "wizard/wizard_cuota_pago_amortizacion.xml",
                "wizard/report_crm_view.xml",   
                "wizard/proforma_view.xml",    
                "wizard/reporte_proforma.xml",
            ],
    
    'installable': True,
    'auto_install': False,
}



