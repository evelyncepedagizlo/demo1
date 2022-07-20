# -*- coding: utf-8 -*-
 

import time
from datetime import datetime, date

from odoo import api, fields, models
from odoo.exceptions import (
    ValidationError,
    Warning as UserError
)

class TipoProveedorReembolso(models.Model):
    _name = 'tipo.proveedor.reembolso'
    _description = 'Tipo de Proveedor de Reembolso'

   

    name = fields.Char('Nombre')
    code = fields.Char('Código')
    active = fields.Boolean('Active',default=True)
