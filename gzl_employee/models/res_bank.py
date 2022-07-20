# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import *

class ResBank(models.Model):
    _inherit = 'res.bank'

    code = fields.Char(string='Código')
    is_bank_gy = fields.Boolean(default=False, string='Es banco Guayaquil?')