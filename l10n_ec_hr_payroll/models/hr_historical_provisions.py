# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import ValidationError


class HrHistoricalProvisions(models.Model):
    _name = 'hr.historical.provisions'

    def _calcule_period(self):
        year = date.today().year - 2
        result = []
        for line in range(3):
            result.append((year,year))
            year += 1
        return result

    period = fields.Selection(selection="_calcule_period", string=_('Period'), store=True)
    employee_id = fields.Many2one('hr.employee', string=_('Employee'))
    working_days = fields.Float(string=_('Working days'))
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    previus_value = fields.Monetary(string=_('Value (Previus Period)'))
    actual_value = fields.Monetary(string=_('Value (Current period)'))
    total = fields.Monetary(string=_('Total'), compute="_compute_total")
    active = fields.Boolean(string=_('Active'))
    provision = fields.Selection([
        ('ProvDec13', 'Décimo Tercero'),
        ('ProvDec14', 'Décimo Cuarto'),
    ], string=_('Provision'))

    @api.depends('previus_value', 'actual_value')
    def _compute_total(self):
        for record in self:
            record.total = record.previus_value + record.actual_value


