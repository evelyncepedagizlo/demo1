# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class Stage(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _inherit = "crm.stage"


    rol = fields.Selection([('comercial', 'Comercial'), 
                                      ('delegado', 'Delegado'),('postventa','Post-Venta')
                                    ],string='Rol', default='comercial') 

    

    modificacion_solo_equipo = fields.Boolean( string='Solo puede Editar el equipo asignado' )

    colocar_venta_como_ganada = fields.Boolean( string='En este estado se puede colocar la venta como ganada' )

    restringir_movimiento = fields.Boolean( string='Restringir movimiento de Estado de Oportunidad' )

    stage_anterior_id = fields.Many2one('crm.stage', string='Estado Anterior' )
    stage_siguiente_id = fields.Many2one('crm.stage', string='Estado Siguiente' )


    solicitar_adjunto_documento = fields.Boolean( string='Solicitar Adjunto de Documentos' )

    correos = fields.Text( string='')


    crear_reunion_en_calendar = fields.Boolean( string='Crear Reunión con Cliente para llamada de Calidad' )



    notificar_delegado = fields.Boolean( string='Notificar Delegado' )
    notificar_postvneta = fields.Boolean( string='Notificar Postventa' )
    notificar_facturacion = fields.Boolean( string='Notificar Facturacion' )
    crear_factura = fields.Boolean( string='Crear Factura' )
    notificar_nomina = fields.Boolean( string='Notificar Nómina' )
    generar_cotizacion = fields.Boolean( string='Generar Cotización' )
    etapa_inicial = fields.Boolean( string='Etapa Inicial' )
    crear_contrato = fields.Boolean( string='Crear Contrato' )