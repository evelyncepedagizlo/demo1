# -*- coding: utf-8 -*-
#############################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo import api, models, registry, SUPERUSER_ID
from . import funciones

class InventarioServicios(models.Model):
    _name = "inventario.servicio"

    name = fields.Char('Nombre')
    ip_address = fields.Char('Dirección IP')
    link = fields.Char('Link')


    description = fields.Html(string='Description')
    active=fields.Boolean('Activo',default=True)
    identificador_servicio = fields.Char('Clave')
    header = fields.Char('Header')
    data = fields.Char('Data')
    idCliente = fields.Char('ID Cliente')
    clientSecret = fields.Char('Client Secret')
    oauth = fields.Boolean('OAUT Token')
    idtoken = fields.Many2one('inventario.servicio',string='Servicio Token')

    @api.constrains('ip_address')
    def validaciones_ip(self):
        if self.ip_address:
            funciones.validate_ip(self.ip_address)