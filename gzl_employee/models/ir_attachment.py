# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'ir.attachment'

    foundation_documents = fields.Boolean(string='Son documentos de fundación?', default=False)
