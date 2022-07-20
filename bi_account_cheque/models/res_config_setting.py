# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from ast import literal_eval

        
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    out_credit_account_id = fields.Many2one('account.account',string="Credit Account",company_dependent=True)
    out_debit_account_id = fields.Many2one('account.account',string="Debit Account",company_dependent=True)
    
    deposite_account_id = fields.Many2one('account.account',string="Deposite Account",company_dependent=True)
    specific_journal_id = fields.Many2one('account.journal',string="Specific Journal",company_dependent=True)

    return_check_id = fields.Many2one('account.account',string="Return Check Account",company_dependent=True)
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.default'].sudo()
        out_credit_account_id = ICPSudo.get("res.config.settings",'out_credit_account_id',False,self.env.company.id)
        out_debit_account_id = ICPSudo.get("res.config.settings",'out_debit_account_id',False,self.env.company.id)
        deposite_account_id = ICPSudo.get("res.config.settings",'deposite_account_id',False,self.env.company.id)
        specific_journal_id = ICPSudo.get("res.config.settings",'specific_journal_id',False,self.env.company.id)
        return_check_id = ICPSudo.get("res.config.settings",'return_check_id',False,self.env.company.id)
        
        res.update(
            out_credit_account_id=out_credit_account_id,
            out_debit_account_id=out_debit_account_id,
            deposite_account_id=deposite_account_id,
            specific_journal_id=specific_journal_id,
            return_check_id=return_check_id,
            )
        return res


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.default'].sudo()
        ICPSudo.set("res.config.settings",'out_credit_account_id',self.out_credit_account_id.id,False,self.env.company.id)
        ICPSudo.set("res.config.settings",'out_debit_account_id',self.out_debit_account_id.id,False,self.env.company.id)
        ICPSudo.set("res.config.settings",'deposite_account_id',self.deposite_account_id.id,False,self.env.company.id)
        ICPSudo.set("res.config.settings",'specific_journal_id',self.specific_journal_id.id,False,self.env.company.id)
        ICPSudo.set("res.config.settings",'return_check_id',self.return_check_id.id,False,self.env.company.id)