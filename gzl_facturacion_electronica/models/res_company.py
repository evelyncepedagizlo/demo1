# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Rescompany(models.Model):
    _inherit = 'res.company'

    type_environment = fields.Selection([('1', 'Pruebas'), 
                                    ('2', 'Producción')],
                                    string='Tipo de Ambiente', default='1')
    numerical_code = fields.Char(string='Código Numérico')
    is_withholding_agent = fields.Boolean(string='Es Agente de Retención', default=False)
    num_special_contributor = fields.Char(string='Número de Contribuyente Especial', default="NAA")
    is_special_contributor = fields.Selection([('SI', 'SI'),
                                                ('NO', 'NO')
                                            ],string='Contribuyente Especial',required=True,default='NO')
    emission_code = fields.Selection([('1', 'Normal'),
                                        ('2', 'Indisponibilidad')
                                        ],string='Tipo de Emisión',required=True,default='1')
    resolution_number = fields.Char(string='Número de Resolución')