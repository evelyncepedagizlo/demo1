# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.web.controllers.main import clean_action

class AccountAnalyticAccount(models.AbstractModel):
    _inherit = 'account.analytic.account'

    business_area_id = fields.Many2one('business.area', string='Área/Unidad')
    axis_id = fields.Many2one('axis', string='Eje')
    project_id = fields.Many2one('parent.project', string='Proyecto Padre')


class BusinessArea(models.Model):
    _name = 'parent.project'
    _rec_name = 'name'

    name = fields.Char('Proyecto Padre')
    active = fields.Boolean('Activo', default=True)


class BusinessArea(models.Model):
    _name = 'business.area'
    _rec_name = 'name'

    sequence = fields.Integer(string="Secuencia",default=1000)
    name = fields.Char('Área de Negocio')
    active = fields.Boolean('Activo', default=True)


class Axis(models.Model):
    _name = 'axis'
    _rec_name = 'name'

    name = fields.Char('Eje')
    active = fields.Boolean('Activo', default=True)

class HierarchyAnalyticalAccounts(models.Model):
    _name = 'hierarchy.analytical.accounts'
    
    business_area_id = fields.Many2one('business.area', string='Área/Unidad')
    axis_id = fields.Many2one('axis', string='Eje')
    project_id = fields.Many2one('parent.project', string='Proyecto Padre')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica')
    description = fields.Char(string='Descripción')

    @api.onchange('analytic_account_id')
    def onchange_analytic_account_id(self):
        analytic = self.env['account.analytic.account'].search([('id','=',self.analytic_account_id.id)])
        analytic.update({
            'business_area_id':self.business_area_id.id,
            'axis_id':self.axis_id.id,
            'project_id':self.project_id.id,
             })
