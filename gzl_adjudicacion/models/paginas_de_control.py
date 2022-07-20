# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
import datetime
from odoo.exceptions import UserError, ValidationError


class PaginasDeControl(models.Model):
    _name = 'paginas.de.control'
    _description = 'Revisión de paginas de control'
    _rec_name= 'nombre'
    
    nombre = fields.Char('Nombre',  required=True)
    descripcion=fields.Char('Descripcion',  required=True)
    