# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    #signature = fields.Image(string='Firma', copy=False, attachment=True, max_width=624, max_height=354)
    contrato = fields.Many2one('contrato', string='Contrato')
    grupo = fields.Many2one('grupo.adjudicado', string='Grupo')
    grupo_contrato = fields.Char('Grupo - Contrato')
