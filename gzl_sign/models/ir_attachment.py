# -*- coding: utf-8 -*-
from odoo import fields, models

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    tipo_plantilla = fields.Selection(selection=[
            ('adjudicacion', 'Adjudicacion'),
            ('otros', 'Otros')
            ], string="Tipo Plantilla")
    
