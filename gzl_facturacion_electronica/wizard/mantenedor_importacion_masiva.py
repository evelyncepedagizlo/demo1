# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import date, datetime
import base64
import json
import xmltodict 
import dateutil.parser
from odoo.exceptions import ValidationError

class MantenedorImportacionMasiva(models.Model):
    _name = "mantenedor.importacion.masiva"

    name=fields.Char('Nombre')
    code=fields.Char('Codigo')
    active=fields.Boolean('Active',default=True)