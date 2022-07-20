# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, tools,  _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime,timedelta,date

class AccountMove(models.Model):   
    _inherit = 'account.move'    
  
    @api.onchange("manual_establishment","manual_referral_guide")
    def obtener_diario_por_establecimiento(self,):
        diario_de_ventas=self.env['account.journal'].search([('type','=?',self.invoice_filter_type_domain),('auth_out_invoice_id.serie_establecimiento','=',self.manual_establishment),('auth_out_invoice_id.serie_emision','=',self.manual_referral_guide),('auth_out_invoice_id.active','=',True)],limit=1)
        if len(diario_de_ventas)>0:
            self.journal_id=diario_de_ventas.id
            self.auth_number=diario_de_ventas.auth_out_invoice_id.authorization_number


class AccountMoveLine(models.Model):   
    _inherit = 'account.move.line'    
  
    @api.constrains('account_id')
    def constrains_analytic_account_id(self):
        for l in self:
            if l.move_id.type=='entry' and l.account_id.analytic_account==True and not l.analytic_account_id:
                raise ValidationError('Seleccione una Cuenta analítica para la cta: '+l.account_id.code+' '+l.account_id.name.strip())

