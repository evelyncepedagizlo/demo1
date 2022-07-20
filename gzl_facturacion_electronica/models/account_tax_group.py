# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    code = fields.Char(string='Código')
