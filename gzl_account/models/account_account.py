# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountAccount(models.Model):
    _inherit = "account.account"

    user_type_id = fields.Many2one('account.account.type', string='Type', required=False)
    nivel = fields.Integer(string='Nivel')
    naturaleza = fields.Selection([('deudor', 'Deudor'), 
                                    ('acreedor', 'Acreedor')],
                                    string='Naturaleza')
    agregado = fields.Selection([('genero', 'GENERO'), 
                                ('grupo', 'GRUPO'),
                                ('rubro', 'RUBRO'), 
                                ('cuenta', 'CUENTA'),
                                ('auxiliar', 'AUXILIAR'),
                                ],string='Agregado')
    analytic_account = fields.Boolean(string='Es obligatorio la cta analítica?', default=False)

    tipo_cuenta = fields.Selection([('T', 'Total'), 
                                ('D', 'Detalle')
                                ],string='Tipo de cuenta')
    
    tipo_estado = fields.Selection([('1', 'ESTADO DE SITUACIÓN FINANCIERA'), 
                                    ('2', 'ESTADO DE RESULTADO INTEGRAL'),
                                    ('3', 'ESTADO DE FLUJOS DE EFECTIVO'), 
                                    ('4', 'ESTADO DE CAMBIOS EN EL PATRIMONIO')
                                    ],string='Tipo de Estado')
    
    signo = fields.Selection([('P', 'Positivo'), 
                              ('N', 'Negativo'),
                              ('D', 'Doble'),
                            ],string='Signo')