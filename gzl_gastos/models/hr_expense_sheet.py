# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica')
    expense_sheet_line_id = fields.One2many('hr.expense.sheet.line', 'expense_sheet_id')
    expense_sheet_line_active_id = fields.One2many('hr.expense.sheet.line.active', 'expense_sheet_id')
    total_expense = fields.Monetary(string="Total Gastos")

    @api.constrains('name')
    def all_pay(self):
        pagos = self.env['account.payment'].search([('is_expense', '=', True),('state','=','posted')])
        lines = self.env['hr.expense.sheet.line']
        for l in pagos:
            if l.journal_id.type=='bank':
                bank=l.journal_id.bank_id.name
            else:
                bank=''
            lines.create({
                'name_employee':l.third_name,
                'name_responsable_project':'',
                'concept':l.communication,
                'bank':bank,
                'date':l.payment_date,
                'amount':l.amount,
                'expense_sheet_id':self.id,
            })
            
    @api.constrains('expense_sheet_line_id')
    def one_active(self):
        line = self.env['hr.expense.sheet.line'].search([('expense_sheet_id','=',self.id),('is_active','=',True)])
        if len(line)>1:
            raise ValidationError('Solo puede activar un registro')
        else:
            line_active = self.env['hr.expense.sheet.line.active'].search([('expense_sheet_id', '=', self.id)],limit =1)
            if line_active:
                line_active.update({
                                    'name_employee':line.name_employee,
                                    'name_responsable_project':'',
                                    'concept':line.concept,
                                    'bank':line.bank,
                                    'date':line.date,
                                    'amount':line.amount,
                                    #'expense_sheet_id':self.id,
                                    })
            else:
                self.env['hr.expense.sheet.line.active'].create({
                                                                'name_employee':line.name_employee,
                                                                'name_responsable_project':'',
                                                                'concept':line.concept,
                                                                'bank':line.bank,
                                                                'date':line.date,
                                                                'amount':line.amount,
                                                                'expense_sheet_id':self.id,
                                                                })
            self.total_expense = line.amount-self.total_amount
    
class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    analytic_account_id = fields.Many2one('account.analytic.account',related='sheet_id.analytic_account_id',readonly=True)

class HrExpenseSheetLine(models.Model):
    _name = 'hr.expense.sheet.line'

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)
    name_employee = fields.Char(string='Nombre del Empleado')
    name_responsable_project = fields.Char(string='Responsable del Proyecto')
    concept = fields.Char(string="Concepto")
    bank = fields.Char(string="Banco")
    date = fields.Date(string="Fecha")
    amount = fields.Monetary(string="Monto", store=True, currency_field='currency_id')
    expense_sheet_id = fields.Many2one('hr.expense.sheet', string="Informe de Gasto")
    is_active = fields.Boolean(string='Activo', default=False)


class HrExpenseSheetLineActive(models.Model):
    _name = 'hr.expense.sheet.line.active'

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)
    name_employee = fields.Char(string='Nombre del Empleado')
    name_responsable_project = fields.Char(string='Responsable del Proyecto')
    concept = fields.Char(string="Concepto")
    bank = fields.Char(string="Banco")
    date = fields.Date(string="Fecha")
    amount = fields.Monetary(string="Monto", store=True, currency_field='currency_id')
    expense_sheet_id = fields.Many2one('hr.expense.sheet', string="Informe de Gasto")
