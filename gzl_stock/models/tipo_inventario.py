# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class TipoInventario(models.Model):
    _name = 'tipo.inventario'
    _rec_name = 'nombre'
    _order = 'nombre'

    nombre = fields.Char(string='Tipo de Inventario', required=True)
    activo = fields.Boolean(string="Activo", default=True)