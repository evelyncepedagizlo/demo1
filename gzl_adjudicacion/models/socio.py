# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, tools,  _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime,timedelta,date
import re


class Partner(models.Model):   
    _inherit = 'res.partner'    
  



    tipo=fields.Char(string='Tipo')
    monto = fields.Float(string='Monto')
    id_cliente = fields.Char(string='ID Cliente')
    direccion = fields.Text(string='Dirección')
    tipo_contrato = fields.Many2one("tipo.contrato.adjudicado", String="Tipo de Contrato")
    codigo_cliente = fields.Char(string='Código Cliente')
    fecha_nacimiento  = fields.Date(string='Fecha de nacimiento')
    estado_civil = fields.Selection(selection=[
                    ('soltero', 'Soltero/a'),
                    ('union_libre', 'Unión libre'),
                    ('casado', 'Casado/a'),
                    ('divorciado', 'Divorciado/a'),
                    ('viudo', 'Viudo/a')                    
                    ], string='Estado Civil', default='soltero')
    num_cargas_familiares = fields.Integer(string='Cargas Familiares')