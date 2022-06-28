# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.web.controllers.main import clean_action

class AccountAnalyticLine(models.AbstractModel):
    _inherit = 'account.analytic.line'

    debito = fields.Monetary(string='Debito', related='move_id.debit')
    credito = fields.Monetary(string='Crédito',related='move_id.credit')