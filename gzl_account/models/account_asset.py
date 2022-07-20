# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountAsset(models.Model):
    _inherit = "account.asset"

    serie1 = fields.Char( string='Serie 1')
    serie2 = fields.Char( string='Serie 2')
    modelo = fields.Char( string='Modelo')
    color = fields.Char( string='Color')
    otros = fields.Char( string='Otros Datos')
    image_1920 = fields.Binary("Imagen")
