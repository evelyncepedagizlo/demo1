# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tipo_inventario = fields.Many2one('tipo.inventario', string='Tipo de Inventario')
    bodega = fields.Many2one('stock.warehouse', string='Bodega')