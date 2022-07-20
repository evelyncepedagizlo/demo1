# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError
from . import amount_to_text_es
from datetime import datetime, timedelta

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
    'out_debit': 'customer',
    }

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    check_report_id = fields.Many2one(
        'ir.actions.report',
        'Formato de Cheque'
    )



            
class AccountMove (models.Model):
    _inherit = 'account.move.line'

    
    def _reconcile_lines(self, debit_moves, credit_moves, field):
        """ This function loops on the 2 recordsets given as parameter as long as it
            can find a debit and a credit to reconcile together. It returns the recordset of the
            account move lines that were not reconciled during the process.
        """
        if not self.env.context.get('multi_payment'):
            return super(AccountMove, self)._reconcile_lines(debit_moves, credit_moves, field)
        to_create = []
        cash_basis = debit_moves and debit_moves[0].account_id.internal_type in ('receivable', 'payable') or False
        cash_basis_percentage_before_rec = {}
        dc_vals ={}
       # raise ValidationError(str(credit_moves))
        
        contador_invoice=len(credit_moves.mapped('move_id'))
        facturas_credit= credit_moves.mapped('move_id.id')
        lista_ids_creditos=[]
        for factura in facturas_credit:
            creditos= credit_moves.filtered(lambda l: l.move_id.id==factura)
            if len(creditos)>0:
                lista_ids_creditos.append(creditos[0].id)
        
        
        credit_moves=self.env['account.move.line'].browse(lista_ids_creditos)
        
        while (debit_moves and credit_moves):
            debit_move = debit_moves[0]
            credit_move = credit_moves[0]
            company_currency = debit_move.company_id.currency_id
            balance = (credit_move + debit_move)
            payment_line_id = balance.mapped('payment_id.payment_line_ids').filtered(lambda x: x.invoice_id.id in balance.move_id.ids and x.amount>0)
           # raise ValidationError(payment_line_id)
            if len(payment_line_id)>1:
                payment_line_id=payment_line_id[0]
                
                
            temp_amount_residual = payment_line_id.amount
            temp_amount_residual_currency = payment_line_id.amount
            dc_vals[(debit_move.id, credit_move.id)] = (debit_move, credit_move, temp_amount_residual_currency)
            amount_reconcile = payment_line_id.amount
            if payment_line_id.invoice_id == debit_move.move_id:
                debit_move.amount_residual -= temp_amount_residual
                debit_move.amount_residual_currency -= temp_amount_residual_currency
                debit_moves -= debit_move
            if payment_line_id.invoice_id == credit_move.move_id:
                credit_move.amount_residual += temp_amount_residual
                credit_move.amount_residual_currency += temp_amount_residual_currency
                credit_moves -= credit_move
            currency = False
            amount_reconcile_currency = 0
            if field == 'amount_residual_currency':
                currency = credit_move.currency_id.id
                amount_reconcile_currency = temp_amount_residual_currency
                amount_reconcile = temp_amount_residual
            elif bool(debit_move.currency_id) != bool(credit_move.currency_id):
                currency = debit_move.currency_id or credit_move.currency_id
                currency_date = debit_move.currency_id and credit_move.date or debit_move.date
                amount_reconcile_currency = company_currency._convert(amount_reconcile, currency, debit_move.company_id, currency_date)
                currency = currency.id
            if cash_basis:
                tmp_set = debit_move | credit_move
                cash_basis_percentage_before_rec.update(tmp_set._get_matched_percentage())
            if not self.company_id.currency_id.is_zero(amount_reconcile) \
                    or not self.company_id.currency_id.is_zero(amount_reconcile_currency):
                to_create.append({
                    'debit_move_id': debit_move.id,
                    'credit_move_id': credit_move.id,
                    'amount': amount_reconcile,
                    'amount_currency': amount_reconcile_currency,
                    'currency_id': currency,
                })
        cash_basis_subjected = []
        part_rec = self.env['account.partial.reconcile']
        for partial_rec_dict in to_create:
            debit_move, credit_move, amount_residual_currency = dc_vals[partial_rec_dict['debit_move_id'], partial_rec_dict['credit_move_id']]
            if not amount_residual_currency and debit_move.currency_id and credit_move.currency_id:
                part_rec.create(partial_rec_dict)
            else:
                cash_basis_subjected.append(partial_rec_dict)
        for after_rec_dict in cash_basis_subjected:
            new_rec = part_rec.create(after_rec_dict)
            if cash_basis and not (
                    new_rec.debit_move_id.move_id == new_rec.credit_move_id.move_id.reversed_entry_id
                    or
                    new_rec.credit_move_id.move_id == new_rec.debit_move_id.move_id.reversed_entry_id
            ):
                new_rec.create_tax_cash_basis_entry(cash_basis_percentage_before_rec)
        return debit_moves+credit_moves

    def remove_move_reconcile(self):
        """ Undo a reconciliation """
        move_id = self.env.context.get('move_id')
        if not move_id:
            return super().remove_move_reconcile()
        (
            self.mapped('matched_debit_ids').filtered(
                lambda x: x.debit_move_id.move_id.id == move_id
            ) +
            self.mapped('matched_credit_ids').filtered(
                lambda x: x.credit_move_id.move_id.id == move_id
            )
        ).unlink()


class AccountCheque(models.Model):
    _inherit = "account.cheque"
 
    payee_user_id = fields.Many2one('res.partner',string="Payee", required=False)
