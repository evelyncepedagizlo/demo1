# -*- coding: utf-8 -*-

import xml.etree.ElementTree as xee
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, except_orm


class PlantillasDinamicasInformes(models.Model):
    _name = 'plantillas.dinamicas.informes' 
    _description = 'Plantillas dinamicas para Informes'

    name = fields.Char( string='Nombre',required=True)
    identificador_clave = fields.Char( string='Identificador Clave')



    campos_ids = fields.One2many('campos.informe', 'informe_id', string='Identificadores para Informe')  

    #directorio = fields.Many2one('muk_dms.directory',string='directorio') 
    directorio = fields.Char(string='Directorio de Plantilla')  
    directorio_out = fields.Char(string='Directorio de Salida de Informe')  

class CamposInforme(models.Model):
    _name = "campos.informe"

    name = fields.Char('Nombre del Campo')
    identificar_docx = fields.Char('Identificador Documento Word')
    label = fields.Char('Label')
    informe_id = fields.Many2one('plantillas.dinamicas.informes','Informe')
    fila = fields.Integer('Fila de Documento Excel')
    columna = fields.Integer('Columna de Documento Excel')
    hoja_excel = fields.Integer('Hoja del  Excel')
    parent_id = fields.Many2one('campos.informe',  index=True)
    child_ids = fields.One2many('campos.informe', 'parent_id', string='Detalle')  






