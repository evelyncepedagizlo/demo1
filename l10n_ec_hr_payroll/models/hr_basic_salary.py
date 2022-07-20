# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from collections import defaultdict
from odoo import api, fields, models
from odoo.tools import date_utils
from odoo.osv import expression
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _name = 'hr.basic.salary'

    period = fields.Char(string='', size=4)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    basic_salary_old = fields.Monetary(string='')
    basic_salary_new = fields.Monetary(string='')
    change_percent = fields.Float(string='', compute='compute_change_percent')
    active = fields.Boolean(default=False)
    
    @api.onchange('basic_salary_old', 'basic_salary_new')
    @api.depends('basic_salary_old', 'basic_salary_new')
    def compute_change_percent(self):
        for line in self:
            if line.basic_salary_old and line.basic_salary_new:
                line.change_percent = ((line.basic_salary_new / line.basic_salary_old)-1) *100
            else: 
                line.change_percent = 0.0
    
    @api.onchange('active')
    def _onchange_active(self):
        ids=[]
        env = self.env['hr.basic.salary'].search([('active','=',True)], order="write_date desc").ids
        for rec in env:
            ids.append(rec)
        if len(ids) > 1:
            ids.pop(-1)
        for record in self.search([('id','in', tuple(ids))]):
            record.active = False