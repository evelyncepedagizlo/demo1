# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import *

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    direccion = fields.Char('Dirección')
    correo = fields.Char('Correo electrónico')
    res_bank_id = fields.Many2one('res.bank', string='Banco')
    account_type = fields.Selection(selection=[
            ('A', 'Ahorros'),
            ('C', 'Corriente'),
            ('M', 'Cuenta Amiga')], string='Tipo de Cuenta')
    number_bank = fields.Char('Número de Cta')
    children_id = fields.One2many('hr.employee.children','employee_id', string='Id hijos')
    observation = fields.Text(string='Observaciones')

    def has_13months(self, date_init, contract=False):
        days = sum([(c.date_end - c.date_start).days for c in self.contract_ids if c.state == 'close'])
        days = 0 if not days else days[0]
        if not contract:
            raise ValidationError("%s debe tener un contracto activo." %(self.name))
        days += (date_init - contract.date_start).days
        if days >= 395:
            return days
        elif days < 395 and days > 365:
            return days - 365
        return 0


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'


    direccion = fields.Char('Dirección')
    correo = fields.Char('Correo electrónico')
    res_bank_id = fields.Many2one('res.bank', string='Banco')
    account_type = fields.Selection(selection=[
            ('A', 'Ahorros'),
            ('C', 'Corriente'),
            ('M', 'Cuenta Amiga')], string='Tipo de Cuenta')
    number_bank = fields.Char('Número de Cta')
    children_id = fields.One2many('hr.employee.children','employee_id', string='Id hijos')
    observation = fields.Text(string='Observaciones')













class HrEmployeeChildren(models.Model):
    _name = 'hr.employee.children'
    
    employee_id = fields.Many2one('hr.employee', string='Id empleado')
    name = fields.Char(string='Nombre')
    date_birth = fields.Date(string='Fecha de nacimiento')
    age = fields.Char(string='Edad')
    gender = fields.Selection(selection=[
            ('femenino', 'Femenino'),
            ('masculino', 'Masculino')], string='Género', required=True)
    
    def planned_action_age(self):
        res = self.env['hr.employee.children'].search([('date_birth','!=',False)])
        for l in res:
            if l.date_birth:
                now = date.today()
                #month = str(now.month - l.date_birth.month)
                #m=''
                #if month=='1':
                #    m='mes'
                #else:
                #    m='meses'
                l.age = str(now.year - l.date_birth.year) +' años ' 
