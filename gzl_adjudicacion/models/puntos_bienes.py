# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError



class PuntosBienes(models.Model):
    _name = 'puntos.bienes'
    _description = 'Bienes'
    _rec_name= 'nombre'
    
    #items bienes
    nombre = fields.Char('Nombre',  required=True)
    valorPuntos = fields.Integer('Ptos.',  required=True)
    poseeBien = fields.Char()
