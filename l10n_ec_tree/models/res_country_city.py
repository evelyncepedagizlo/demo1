# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCountryCity(models.Model):
    
    _name = 'res.country.city'
    _description = 'Ciudades'
    _rec_name = 'nombre_ciudad'

    nombre_ciudad = fields.Char(string='Nombre Ciudad')
    codigo_ciudad = fields.Char(string='Código Ciudad')
    provincia_id = fields.Many2one('res.country.state', string='Provincia',  domain="[('country_id','=',ref('base.ec').id)]")