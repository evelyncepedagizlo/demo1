# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TipoContratoAdjudicado(models.Model):
    
    _name = 'tipo.contrato.adjudicado'
    _description = 'Tipos de Contrato adjudicado'
  
    name=fields.Char('Nombre')
    descripcion=fields.Text('Descripcion')
    code=fields.Char('Código')
    numero_ganadores=fields.Integer('Número Ganadores')
    numero_suplentes=fields.Integer('Número Suplentes')
    active=fields.Boolean( default=True)
 