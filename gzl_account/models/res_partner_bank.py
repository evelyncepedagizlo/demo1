# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    codigo_swift = fields.Char(string='Código Swift')
    account_type = fields.Selection(selection=[
            ('Ahorros', 'Ahorros'),
            ('Corriente', 'Corriente')], string='Tipo de Cuenta')


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # @api.constrains('vat')
    # def create_id_extern(self):
    #     if self.vat and not self.parent_id:
    #         if self.customer_rank!=0:
    #             self.env['ir.model.data'].create({
    #               #'module':'',
    #               'name':'CLIENTE_'+self.vat.strip(),
    #               'model':'res.partner',
    #               'res_id':self.id,
    #           })
    #         else:
    #             self.env['ir.model.data'].create({
    #                 #'module':'',
    #                 'name':'PROVEEDOR_'+self.vat.strip(),
    #                 'model':'res.partner',
    #                 'res_id':self.id,
    #             })
                
class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    
    order_of = fields.Char(string='Orden de')