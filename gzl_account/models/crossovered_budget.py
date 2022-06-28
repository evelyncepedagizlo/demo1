# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    utilidad_bruta = fields.Float(string='Utilidad Bruta', compute='compute_utilidad')
    utilidad_neta = fields.Float(string='Utilidad Neta', compute='compute_utilidad')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica")
    
    @api.depends('crossovered_budget_line.practical_amount', 'crossovered_budget_line.percentage' )
    def compute_utilidad(self):
        for l in self:
            gastos = 0
            costos = 0
            ingresos = 0
            for line in l.crossovered_budget_line:
                if line.tipo_presupuesto=='ingresos':
                    ingresos += line.practical_amount
                elif line.tipo_presupuesto=='costos':
                    costos += line.practical_amount
                else:
                    gastos += line.practical_amount
            l.utilidad_bruta = ingresos - costos
            l.utilidad_neta = l.utilidad_bruta - gastos

class CrossoveredBudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    tipo_presupuesto = fields.Selection([('ingresos', 'Ingresos'), 
                                        ('gastos', 'Gastos'),
                                        ('costos', 'Costos'),
                                        ('no_operacionales','No Operacionales')],
                                    string='Tipo de Presupuesto')
    difference = fields.Monetary(string="Diferencia", compute="compute_difference")

    @api.depends('practical_amount', 'planned_amount' )
    def compute_difference(self):
        for l in self:
            l.difference= l.practical_amount-l.planned_amount



class AccountBudgetPost(models.Model):
    _inherit = 'account.budget.post'

    tipo_presupuesto = fields.Selection([('ingresos', 'Ingresos'), 
                                        ('gastos', 'Gastos'),
                                        ('costos', 'Costos'),
                                        ('no_operacionales','No Operacionales')],
                                    string='Tipo de Presupuesto')