# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection_add=[
        ('anticipo', 'Anticipo')
    ])

    @api.model
    def _prepare_liquidity_account(self, name, company, currency_id, type):
        '''
        This function prepares the value to use for the creation of the default debit and credit accounts of a
        liquidity journal (created through the wizard of generating COA from templates for example).

        :param name: name of the bank account
        :param company: company for which the wizard is running
        :param currency_id: ID of the currency in which is the bank account
        :param type: either 'cash' or 'bank'
        :return: mapping of field names and values
        :rtype: dict
        '''
        digits = 6
        #acc = self.env['account.account'].search([('company_id', '=', company.id)], limit=1)
        #if acc:
        #    digits = len(acc.code)
        # Seek the next available number for the account code
        #if type == 'bank':
        #    account_code_prefix = company.bank_account_code_prefix or ''
        #else:
        #    account_code_prefix = company.cash_account_code_prefix or company.bank_account_code_prefix or ''

        #liquidity_type = self.env.ref('account.data_account_type_liquidity')
        #return {
        #        'name': name,
        #        'currency_id': currency_id or False,
        #        'code': self.env['account.account']._search_new_account_code(company, digits, account_code_prefix),
        #        'user_type_id': liquidity_type and liquidity_type.id or False,
        #        'company_id': company.id,
        #}
   
    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.env.company.id)
        if vals.get('type') in ('bank', 'cash'):
            # For convenience, the name can be inferred from account number
            if not vals.get('name') and 'bank_acc_number' in vals:
                vals['name'] = vals['bank_acc_number']

            # If no code provided, loop to find next available journal code
            if not vals.get('code'):
                vals['code'] = self.get_next_bank_cash_default_code(vals['type'], company_id)
                if not vals['code']:
                    raise UserError(_("Cannot generate an unused journal code. Please fill the 'Shortcode' field."))


            # Create a default debit/credit account if not given
            # default_account = vals.get('default_debit_account_id') or vals.get('default_credit_account_id')
            company = self.env['res.company'].browse(company_id)
            # if not default_account:
            #     account_vals = self._prepare_liquidity_account(vals.get('name'), company, vals.get('currency_id'), vals.get('type'))
            #     default_account = self.env['account.account'].create(account_vals)
            #     vals['default_debit_account_id'] = default_account.id
            #     vals['default_credit_account_id'] = default_account.id
            if vals['type'] == 'cash':
                if not vals.get('profit_account_id'):
                    vals['profit_account_id'] = company.default_cash_difference_income_account_id.id
                if not vals.get('loss_account_id'):
                    vals['loss_account_id'] = company.default_cash_difference_expense_account_id.id

        if 'refund_sequence' not in vals:
            vals['refund_sequence'] = vals['type'] in ('sale', 'purchase')

        # We just need to create the relevant sequences according to the chosen options
        if not vals.get('sequence_id'):
            vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})
        if vals.get('type') in ('sale', 'purchase') and vals.get('refund_sequence') and not vals.get('refund_sequence_id'):
            vals.update({'refund_sequence_id': self.sudo()._create_sequence(vals, refund=True).id})
        journal = super(AccountJournal, self.with_context(mail_create_nolog=True)).create(vals)
        if 'alias_name' in vals:
            journal._update_mail_alias(vals)

        # Create the bank_account_id if necessary
        if journal.type == 'bank' and not journal.bank_account_id and vals.get('bank_acc_number'):
            journal.set_bank_account(vals.get('bank_acc_number'), vals.get('bank_id'))

        return journal