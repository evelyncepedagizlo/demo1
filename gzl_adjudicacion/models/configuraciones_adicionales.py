# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ConfiguracionAdicional(models.Model):
    _name = 'configuracion.adicional.template'
    

    name = fields.Char(string='Nombre' )
    requisitosPoliticasCredito = fields.Text(string='Informacion Cobranzas' )
