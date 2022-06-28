from odoo import models, fields, api

class PeriodsDebtsDue(models.Model):
    _name = 'periods.debts.due'
    _description = 'Periodos para el reporte de deuda por vencer'

    name = fields.Char(required=True)
    day_from = fields.Integer(required=True)
    day_to = fields.Integer(required=True)
    active = fields.Boolean()
