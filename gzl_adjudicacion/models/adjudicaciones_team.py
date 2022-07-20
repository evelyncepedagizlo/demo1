# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class AdjudicacionTeam(models.Model):
    _name = 'adjudicaciones.team'
    _description = 'Adjudicaciones Roles'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    correo = fields.Char(string="Correo")

    name = fields.Char('Rol Adjudicaciones', required=True, translate=True)
    code=fields.Char('Código',  required=True)
    descripcion=fields.Text('Descripcion',  required=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the Sales Team without removing it.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one(
        "res.currency", related='company_id.currency_id',
        string="Currency", readonly=True)
    user_id = fields.Many2one('res.users', string='Responsable', check_company=True)
    member_ids = fields.Many2many('res.users', string='Miembros del Equipo' )


    correos = fields.Char( string='Correos' )

    @api.onchange("member_ids")
    def actualizar_correos_team(self,):
        correos=self.member_ids.mapped('email')
        correoCadena=""
        for correo in correos:
            if correo:
                correoCadena=correoCadena+correo+','
        correoCadena=correoCadena.strip(',')
        self.correos=correoCadena

