# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = 'crm.team'
    _description = 'Sales Team'


    correos = fields.Char( string='Correos' )
    miembros = fields.Many2many('res.users', string='Miembros del Equipo' )
    surcursal_id = fields.Many2one('surcursal', string='Surcursal')

    rol = fields.Selection([('comercial', 'Comercial'), 
                                      ('delegado', 'Delegado'),('postventa','Post-Venta')
                                    ],string='Rol', default='comercial') 

    
    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_team_id(self, user_id=None, domain=None):
        if not user_id:
            user_id = self.env.uid
        team_id = self.env['crm.team'].search([
            '|', ('user_id', '=', user_id), ('miembros', '=', user_id),
            '|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not team_id and 'default_team_id' in self.env.context:
            team_id = self.env['crm.team'].browse(self.env.context.get('default_team_id'))
        if not team_id:
            team_domain = domain or []
            default_team_id = self.env['crm.team'].search(team_domain, limit=1)
            return default_team_id or self.env['crm.team']
        return team_id



    @api.onchange("miembros")
    def actualizar_correos_team(self,):
        correos=self.miembros.mapped('email')
        correoCadena=""
        for correo in correos:
            if correo:
                correoCadena=correoCadena+correo+','
        correoCadena=correoCadena.strip(',')
        self.correos=correoCadena



    @api.model
    def create(self, values):
        team = super(CrmTeam, self.with_context(mail_create_nosubscribe=True)).create(values)
        if values.get('miembros'):
            team._add_members_to_favorites()
        return team

    def write(self, values):
        res = super(CrmTeam, self).write(values)
        if values.get('miembros'):
            self._add_members_to_favorites()
        return res

    def unlink(self):
        default_teams = [
            self.env.ref('sales_team.salesteam_website_sales'),
            self.env.ref('sales_team.pos_sales_team'),
            self.env.ref('sales_team.ebay_sales_team')
        ]
        for team in self:
            if team in default_teams:
                raise UserError(_('Cannot delete default team "%s"' % (team.name)))
        return super(CrmTeam,self).unlink()

    def _add_members_to_favorites(self):
        for team in self:
            team.favorite_user_ids = [(4, member.id) for member in team.miembros]
