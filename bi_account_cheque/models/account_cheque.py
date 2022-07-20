# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import date, datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class AccountCheque(models.Model):
    _name = "account.cheque"
    _order = 'id desc'
    _description = 'Cheques'
    _rec_name= 'sequence'

    sequence = fields.Char(string='Secuencia', readonly=True ,copy=True, index=True)
    name = fields.Char(string="Name",required="0")
    bank_account_id = fields.Many2one('account.account','Bank Account')
    cheque_number = fields.Char(string="Cheque Number",required=True)
    amount = fields.Float(string="Amount",required=True)
    cheque_date = fields.Date(string="Cheque Date",default=datetime.now().date())
    cheque_given_date = fields.Date(string="Fecha de entrega Cheque")
    cheque_receive_date = fields.Date(string="Cheque Receive Date")
    cheque_return_date = fields.Date(string="Cheque Return Date")
    payee_user_id = fields.Many2one('res.partner',string="Empresa")
    credit_account_id = fields.Many2one('account.account',string="Credit Account")
    debit_account_id = fields.Many2one('account.account',sring="Debit Account")
    comment = fields.Text(string="Comentario")
    attchment_ids = fields.One2many('ir.attachment','account_cheque_id',string="Adjuntos")
    status = fields.Selection([('draft','Borrador'),
                                ('registered','Registrado'),
                                #('bounced','Rebotado'),
                                #('return','Devuelto'),
                                ('cashed','Hecho'),
                                ('cancel','Cancelado')],string="Status",default="draft",copy=False, index=True, track_visibility='onchange')
    
    status1 = fields.Selection([('draft','Borrador'),
                                ('registered','Registrado'),
                                #('bounced','Rebotado'),
                                #('return','Devuelto'),
                                #('deposited','Depositado'),
                                ('cashed','Hecho'),
                                ('cancel','Cancelado')],string="Status",default="draft",copy=False, index=True, track_visibility='onchange')
    
    journal_id = fields.Many2one('account.journal',string="Journal",required=True)
    company_id = fields.Many2one('res.company',string="Company",required=True)
    journal_items_count =  fields.Integer(compute='_active_journal_items',string="Elementos") 
    # invoice_ids = fields.One2many('account.invoice','account_cheque_id',string="Invoices",compute="_count_account_invoice")
    attachment_count  =  fields.Integer('Attachments', compute='_get_attachment_count')
    '''journal_type = fields.Selection([('purchase_refund', 'Refund Purchase'), ('purchase', 'Create Supplier Invoice')], 'Journal Type', readonly=True, default=_get_journal_type)'''
    third_party_name = fields.Char('A nombre de Tercero')
    payment_id = fields.Many2one('account.payment',string="Pago")

    @api.onchange("payee_user_id")
    def actualizar_nombre_tercero(self):
        if self.payee_user_id.id:
            self.third_party_name=self.payee_user_id.name
        else:
            self.third_party_name=False

    
    
    
    
    def print_checks(self):
        """ Check that the recordset is valid, set the payments state to sent and call print_checks() """
        # Since this method can be called via a client_action_multi, we need to make sure the received records are what we expect
        self = self.filtered(lambda r: r.payment_id.payment_method_id.code == 'check_printing' and r.payment_id.state != 'reconciled')

        if len(self) == 0:
            raise UserError(_("Payments to print as a checks must have 'Check' selected as payment method and "
                              "not have already been reconciled"))
        if any(payment.journal_id != self[0].payment_id.journal_id for payment in self):
            raise UserError(_("In order to print multiple checks at once, they must belong to the same bank journal."))

        # if not self[0].payment_id.journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first pre-printed check
            # so payments are attributed the number of the check the'll be printed on.
            # last_printed_check = self.payment_id.search([
            #     ('journal_id', '=', self[0].payment_id.journal_id.id),
            #     ('check_number', '!=', 0)], order="check_number desc", limit=1)
            # next_check_number = last_printed_check and last_printed_check.check_number + 1 or 1
        return {
            'name': _('Print Pre-numbered Checks Payroll'),
            'type': 'ir.actions.act_window',
            'res_model': 'print.prenumbered.checks',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'payment_ids': self.payment_id.id,
                'default_next_check_number': self[0].cheque_number,
            }}
        # else:
        #     self.filtered(lambda r: r.payment_id.state == 'draft').post()
        #     return self.do_print_checks()
    
    @api.model 
    def default_get(self, flds): 
        result = super(AccountCheque, self).default_get(flds)
        res = self.env['res.config.settings'].sudo(1).search([], limit=1, order="id desc")
        result['credit_account_id'] = res.out_credit_account_id.id
        result['debit_account_id'] = res.out_debit_account_id.id
        result['journal_id'] = res.specific_journal_id.id 
        return result 
        
    def open_payment_matching_screen(self):
        # Open reconciliation view for customers/suppliers
        move_line_id = False
        if self.payee_user_id:
            account_move_line_ids = self.env['account.move.line'].search([('partner_id','=',self.payee_user_id.id)])
            for move_line in account_move_line_ids:
                if move_line.account_id.reconcile:
                    move_line_id = move_line.id
                    break;
            action_context = {'company_ids': [self.company_id.id], 'partner_ids': [self.payee_user_id.id]}
            if account_move_line_ids:
                action_context.update({'move_line_id': move_line_id})
            return {
                'type': 'ir.actions.client',
                'tag': 'manual_reconciliation_view',
                'context': action_context,
            }
        
    # @api.multi
    # def _count_account_invoice(self):
    #     invoice_list = []
    #     for invoice in self.payee_user_id.invoice_ids:
    #         invoice_list.append(invoice.id)
    #         self.invoice_ids = [(6, 0, invoice_list)]
    #     return
        
    def _active_journal_items(self):
        list_of_move_line = []
        for journal_items in self:
            journal_item_ids = self.env['account.move'].search([('account_cheque_id','=',journal_items.id)])
        for move in journal_item_ids:
            for line in move.line_ids:
                list_of_move_line.append(line.id)
        item_count = len(list_of_move_line)
        journal_items.journal_items_count = item_count
        return
        
    def action_view_jornal_items(self):
        self.ensure_one()
        list_of_move_line = []
        for journal_items in self:
            journal_item_ids = self.env['account.move'].search([('account_cheque_id','=',journal_items.id)])
        for move in journal_item_ids:
            for line in move.line_ids:
                list_of_move_line.append(line.id)
        return {
            'name': 'Elementos del Diario',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'domain': [('id', '=', list_of_move_line)],
        }
        
    def _get_attachment_count(self):
        for cheque in self:
            attachment_ids = self.env['ir.attachment'].search([('account_cheque_id','=',cheque.id)])
            cheque.attachment_count = len(attachment_ids)
        
    def attachment_on_account_cheque(self):
        self.ensure_one()
        return {
            'name': 'Attachment.Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'domain': [('account_cheque_id', '=', self.id)],
        }
        
    @api.model
    def create(self, vals):
        journal = self.env['account.journal'].browse(vals['journal_id'])
        sequence = journal.sequence_id
        vals['sequence'] = sequence.with_context(ir_sequence_date=datetime.today().date().strftime("%Y-%m-%d")).next_by_id()
        result = super(AccountCheque, self).create(vals)
        return result
        
    def set_to_submit(self):
        account_move_obj = self.env['account.move']
        for s in self:
            move_lines = []
            vals = {
                    'name' : s.name,
                    'date' : s.cheque_given_date,
                    'journal_id' : s.journal_id.id,
                    'company_id' : s.company_id.id,
                    'state' : 'draft',
                    'ref' : s.sequence + '- ' + s.cheque_number + '- ' + 'Registered',
                    'account_cheque_id' : s.id
            }
            account_move = account_move_obj.create(vals)
            debit_vals = {
                    'partner_id' : s.payee_user_id.id or False,
                    'account_id' : s.debit_account_id.id, 
                    'debit' : s.amount,
                    'date_maturity' : datetime.now().date(),
                    'move_id' : account_move.id,
                    'company_id' : s.company_id.id,
            }
            move_lines.append((0, 0, debit_vals))
            credit_vals = {
                    'partner_id' : s.payee_user_id.id or False,
                    'account_id' : s.credit_account_id.id, 
                    'credit' : s.amount,
                    'date_maturity' : datetime.now().date(),
                    'move_id' : account_move.id,
                    'company_id' : s.company_id.id,
                }
            move_lines.append((0, 0, credit_vals))
            account_move.write({'line_ids' : move_lines})
            s.status = 'registered'
            # return account_move



    # def set_to_bounced(self):
    #     account_move_obj = self.env['account.move']
    #     for s in self:
    #         move_lines = []
    #         vals = {
    #                     'name' : s.name,
    #                     'date' : s.cheque_given_date,
    #                     'journal_id' : s.journal_id.id,
    #                     'company_id' : s.company_id.id,
    #                     'state' : 'draft',
    #                     'ref' : s.sequence + '- ' + s.cheque_number + '- ' + 'Bounced',
    #                     'account_cheque_id' : s.id
    #         }
    #         account_move = account_move_obj.create(vals)
    #         debit_vals = {
    #                     'partner_id' : s.payee_user_id.id or False,
    #                     'account_id' : s.payee_user_id.property_account_payable_id.id or s.third_account_id.id, 
    #                     'debit' : s.amount,
    #                     'date_maturity' : datetime.now().date(),
    #                     'move_id' : account_move.id,
    #                     'amount_currency':0,
    #                     'company_id' : s.company_id.id,
    #                     'payment_id': s.payment_id.id,
    #         }
    #         move_lines.append((0, 0, debit_vals))
    #         credit_vals = {
    #                     'partner_id' : s.payee_user_id.id or False,
    #                     'account_id' : s.debit_account_id.id, 
    #                     'credit' : s.amount,
    #                     'date_maturity' : datetime.now().date(),
    #                     'move_id' : account_move.id,
    #                     'amount_currency':0,
    #                     'company_id' : s.company_id.id,
    #                     'payment_id': s.payment_id.id,
    #         }
    #         move_lines.append((0, 0, credit_vals))
    #         account_move.write({'line_ids' : move_lines})
    #         account_move.post()
    #         s.status = 'bounced'
            # return account_move      

    # def set_to_return(self):
    #     return_check = self.env['ir.default'].sudo().get("res.config.settings",'return_check_id',False,self.env.company.id)
    #     # deposite_account_id = self.env['ir.default'].sudo().get("res.config.settings",'deposite_account_id',False,self.env.company.id)
    #     if not return_check :
    #         raise UserError("Configure la Cuenta de Cheques Devueltos en Configuraciones")
    #     self.payment_id.state = 'draft'
    #     account_move_obj = self.env['account.move']
    #     move_lines = []
    #     list_of_move_line = [] 
    #     for journal_items in self:
    #         journal_item_ids = self.env['account.move'].search([('account_cheque_id','=',journal_items.id)])
        
    #     matching_dict = []
    #     for move in journal_item_ids:
    #         for line in move.line_ids:
    #             if line.full_reconcile_id:
    #                 matching_dict.append(line)
    #                 #line.remove_move_reconcile()
                                    
    #     if len(matching_dict) != 0:
    #         rec_id = matching_dict[0].full_reconcile_id.id
    #         a = self.env['account.move.line'].search([('full_reconcile_id','=',rec_id)])
            
    #         for move_line in a:
    #             move_line.remove_move_reconcile()
        
        
    #     vals = {
    #                 'name' : self.name,
    #                 'date' : self.cheque_given_date,
    #                 'journal_id' : self.journal_id.id,
    #                 'company_id' : self.company_id.id,
    #                 'state' : 'draft',
    #                 'ref' : self.sequence + '- ' + self.cheque_number + ' ' + 'Devuelto',
    #                 'account_cheque_id' : self.id
    #     }
    #     account_move = account_move_obj.create(vals)
    #     debit_vals = {
    #                 'partner_id' : self.payee_user_id.id or False,
    #                 'account_id' : self.bank_account_id.id, 
    #                 'debit' : self.amount,
    #                 'date_maturity' : datetime.now().date(),
    #                 'move_id' : account_move.id,
    #                 'amount_currency':0,
    #                 'company_id' : self.company_id.id,
    #                 'payment_id': self.payment_id.id,
    #     }
    #     move_lines.append((0, 0, debit_vals))
    #     credit_vals = {
    #                 'partner_id' : self.payee_user_id.id or False,
    #                 'account_id' : self.debit_account_id.id, 
    #                 'credit' : self.amount,
    #                 'date_maturity' : datetime.now().date(),
    #                 'move_id' : account_move.id,
    #                 'amount_currency':0,
    #                 'company_id' : self.company_id.id,
    #                 'payment_id': self.payment_id.id,
    #     }
    #     move_lines.append((0, 0, credit_vals))
    #     account_move.write({'line_ids' : move_lines})
    #     account_move.post()
    #     self.status = 'return'
    #     self.cheque_return_date = datetime.now().date()
    #     self.payment_id.state = 'posted'
    #     return account_move           

    # def set_to_reset(self):
    #     account_move_obj = self.env['account.move']
    #     move_lines = []
    #     for journal_items in self:
    #         journal_item_ids = self.env['account.move'].search([('account_cheque_id','=',journal_items.id)])
    #     journal_item_ids.unlink()
    #     vals = {
    #                 'name' : self.name,
    #                 'date' : self.cheque_given_date,
    #                 'journal_id' : self.journal_id.id,
    #                 'company_id' : self.company_id.id,
    #                 'state' : 'draft',
    #                 'ref' : self.sequence + '- ' + self.cheque_number + '- ' + 'Registered',
    #                 'account_cheque_id' : self.id
    #     }
    #     account_move = account_move_obj.create(vals)
    #     debit_vals = {
    #                 'partner_id' : self.payee_user_id.id or False,
    #                 'account_id' : self.credit_account_id.id, 
    #                 'debit' : self.amount,
    #                 'date_maturity' : datetime.now().date(),
    #                 'move_id' : account_move.id,
    #                 'amount_currency':0,
    #                 'company_id' : self.company_id.id,
    #                 'payment_id': s.payment_id.id,
    #     }
    #     move_lines.append((0, 0, debit_vals))
    #     credit_vals = {
    #                 'partner_id' : self.payee_user_id.id or False,
    #                 'account_id' : self.debit_account_id.id, 
    #                 'credit' : self.amount,
    #                 'date_maturity' : datetime.now().date(),
    #                 'move_id' : account_move.id,
    #                 'amount_currency':0,
    #                 'payment_id': s.payment_id.id,
    #                 'company_id' : self.company_id.id,
    #     }
    #     move_lines.append((0, 0, credit_vals))
    #     account_move.write({'line_ids' : move_lines})
    #     account_move.post()
    #     self.status = 'registered'
    #     self.cheque_return_date = datetime.now().date()
    #     return account_move                      

    def set_to_cancel(self): 
        account_move_obj = self.env['account.move']
        move_lines = []
        self.payment_id.state = 'reconciled'
        vals = {
                'name' : self.name,
                'date' : self.cheque_receive_date,
                'journal_id' : self.journal_id.id,
                'company_id' : self.company_id.id,
                'state' : 'draft',
                'ref' : self.sequence + '- ' + self.cheque_number + ' ' + 'Cancelado',
                'account_cheque_id' : self.id
            }
        account_move = account_move_obj.create(vals)
        debit_vals = {
                    'partner_id' : self.payee_user_id.id or False,
                    'account_id' : self.credit_account_id.id,
                    'debit' : self.amount,
                    'date_maturity' : datetime.now().date(),
                    'move_id' : account_move.id,
                    'amount_currency':0,
                    'payment_id': self.payment_id.id,
                    'company_id' : self.company_id.id,
        }
        move_lines.append((0, 0, debit_vals))
        credit_vals = {
                    'partner_id' : self.payee_user_id.id or False,
                    'account_id' : self.debit_account_id.id, 
                    'credit' : self.amount,
                    'date_maturity' : datetime.now().date(),
                    'move_id' : account_move.id,
                    'amount_currency':0,
                    'payment_id': self.payment_id.id,
                    'company_id' : self.company_id.id,
        }
        move_lines.append((0, 0, credit_vals))
        account_move.write({'line_ids' : move_lines})
        account_move.post()
        self.status = 'cancel'

    # -------------------------------------------------------------------------
    # CONSTRAINS METHODS
    # -------------------------------------------------------------------------

        
    @api.constrains('cheque_number','journal_id')
    def verificar_numero_cheque_por_banco(self):

        cheques=self.env['account.cheque'].search([('journal_id.bank_id.id','=',self.journal_id.bank_id.id),('cheque_number','=',self.cheque_number),('id','!=',self.id)],limit=1)
        
        if len(cheques)>0:
            raise ValidationError(_("El Número de Cheque {0} ya se encuentra ingresado en la siguiente secuencia {1} en el {2}").format(self.cheque_number,cheques.sequence,self.journal_id.bank_id.name))


    def cheque_wizard_action(self):
        viewid = self.env.ref('bi_account_cheque.cheque_wizard_wizard_view').id
        return {   
            'name':'Validar Cheque',
            'view_type':'form',
            'views' : [(viewid,'form')],
            'res_model':'cheque.wizard',
            'type':'ir.actions.act_window',
            'target':'new',
            }


class ChequeWizard(models.TransientModel):
    _name = 'cheque.wizard'
    _description = 'Wizard para cheques'

    @api.model 
    def default_get(self, flds): 
        result = super(ChequeWizard, self).default_get(flds)
        account_cheque_id = self.env['account.cheque'].browse(self._context.get('active_id'))
        result['is_outgoing'] = True
        result['chequed_date']=account_cheque_id.cheque_date
        result['bank_account_id']=account_cheque_id.bank_account_id.id

        return result
        
    def create_cheque_entry(self):
        account_cheque = self.env['account.cheque'].browse(self._context.get('active_ids'))
        account_move_obj = self.env['account.move']
        move_lines = []
        
        vals = {
                    'name' : account_cheque.name,
                    'date' : self.chequed_date,
                    'journal_id' : account_cheque.journal_id.id,
                    'company_id' : account_cheque.company_id.id,
                    'state' : 'draft',
                    'ref' : account_cheque.sequence + '- ' + account_cheque.cheque_number + '- ' + 'Cashed',
                    'account_cheque_id' : account_cheque.id
        }
        account_move = account_move_obj.create(vals)
        debit_vals = {
                    'partner_id' : account_cheque.payee_user_id.id or False,
                    'account_id' : account_cheque.debit_account_id.id, 
                    'debit' : account_cheque.amount,
                    'date_maturity' : datetime.now().date(),
                    'move_id' : account_move.id,
                    'amount_currency':0,
                    'company_id' : account_cheque.company_id.id,
        }
        move_lines.append((0, 0, debit_vals))
        credit_vals = {
                    'partner_id' : account_cheque.payee_user_id.id or False,
                    'account_id' : self.bank_account_id.id, 
                    'credit' : account_cheque.amount,
                    'date_maturity' : datetime.now().date(),
                    'move_id' : account_move.id,
                    'amount_currency':0,
                    'company_id' : account_cheque.company_id.id,
        }
        move_lines.append((0, 0, credit_vals))
        account_move.write({'line_ids' : move_lines})
        account_cheque.status = 'cashed'
        return account_move


    chequed_date = fields.Date(string="Cheque Date")
    bank_account_id = fields.Many2one('account.account',string="Bank Account")
    is_outgoing = fields.Boolean(string="Is Outgoing",default=False)
    

class AccountMoveLine(models.Model):
    _inherit='account.move'

    account_cheque_id  =  fields.Many2one('account.cheque', 'Journal Item')

class ReportWizard(models.TransientModel):
    _name = "report.wizard"
    _description ='Reporte'

    from_date = fields.Date('Fecha Desde', required = True)
    to_date = fields.Date('Fecha Hasta',required = True)

    
    def submit(self):
        inc_temp = []
        out_temp = []
        temp = [] 
        

        out_account_cheque_ids = self.env['account.cheque'].search([(str('cheque_date'),'>=',self.from_date),(str('cheque_date'),'<=',self.to_date)])
            
        if not out_account_cheque_ids:
            raise UserError(_('There Is No Any Cheque Details.'))
        else:
            for out in out_account_cheque_ids:
                temp.append(out.id)
                               
        data = temp
        in_data = inc_temp
        out_data = out_temp
        datas = {
            'ids': self._ids,
            'model': 'account.cheque',
            'form': data,
            'from_date':self.from_date,
            'to_date':self.to_date
        }
        return self.env.ref('bi_account_cheque.account_cheque_report_id').report_action(self,data=datas)

class IrAttachment(models.Model):
    _inherit='ir.attachment'

    account_cheque_id  =  fields.Many2one('account.cheque', 'Attchments')
