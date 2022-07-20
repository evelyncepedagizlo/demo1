# -*- coding: utf-8 -*-
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import logging

######################################### NOTA DE CREDITO #########################################
class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'
    
    manual_establishment = fields.Char(string="Establecimiento Manual", copy=False, size=3,  store=True)
    manual_referral_guide = fields.Char(string="Guía de Remisión Manual", copy=False, size=3, store=True)
    manual_sequence = fields.Char(string="Secuencia Manual", size=9)
    
    def _prepare_default_reversal(self, move):
        return {
            'ref': _('Reversal of: %s, %s') % (move.name, self.reason) if self.reason else _('Reversal of: %s') % (move.name),
            'date': self.date or move.date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
            'invoice_payment_term_id': None,
            'auto_post': True if self.date > fields.Date.context_today(self) else False,
            'invoice_user_id': move.invoice_user_id.id,
            'manual_establishment':self.manual_establishment,
            'manual_referral_guide':self.manual_referral_guide,
            'manual_sequence':self.manual_sequence,
            'clave_acceso_sri':False,
            'numero_autorizacion_sri':False
        }
    
    @api.onchange('date','reason','ref','invoice_date')
    def onchange_number_document(self):
        sequence=self.env['ir.sequence']
        seq=self.move_id.journal_id.auth_out_refund_id
        if seq:
            self.manual_establishment = seq.serie_establecimiento
            self.manual_referral_guide = seq.serie_emision
            if seq.is_electronic:
                self.manual_sequence = str(sequence.next_by_code(seq.sequence_id.code))   
                
                
                
                
######################################### NOTA DE DEBITO #########################################
class AccountMove(models.Model):
    _inherit = "account.move"
    
    debit_origin_id = fields.Many2one('account.move', 'Factura Origen', readonly=True, copy=False)
    debit_origin_nd_id = fields.Many2one(related="debit_origin_id", store=True)
    debit_note_ids = fields.One2many('account.move', 'debit_origin_id', 'Debit Notes',
                                     help="The debit notes created for this invoice")
    debit_note_count = fields.Integer('Number of Debit Notes', compute='_compute_debit_count')

    @api.depends('debit_note_ids')
    def _compute_debit_count(self):
        debit_data = self.env['account.move'].read_group([('debit_origin_id', 'in', self.ids)],
                                                        ['debit_origin_id'], ['debit_origin_id'])
        data_map = {datum['debit_origin_id'][0]: datum['debit_origin_id_count'] for datum in debit_data}
        for inv in self:
            inv.debit_note_count = data_map.get(inv.id, 0.0)

    def action_view_debit_notes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nota de Débito',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('debit_origin_id', '=', self.id)],
        }
    
class AccountDebitNote(models.TransientModel):
    """
    Add Debit Note wizard: when you want to correct an invoice with a positive amount.
    Opposite of a Credit Note, but different from a regular invoice as you need the link to the original invoice.
    In some cases, also used to cancel Credit Notes
    """
    _name = 'account.debit.note'
    _description = 'Add Debit Note wizard'

    move_ids = fields.Many2many('account.move', 'account_move_debit_move', 'debit_id', 'move_id',
                                domain=[('state', '=', 'posted')])
    date = fields.Date(string='Fecha Nota de Débito', default=fields.Date.context_today, required=True)
    reason = fields.Char(string='Motivo')
    journal_id = fields.Many2one('account.journal', string='Utilizar Diario Específico')
    copy_lines = fields.Boolean("Copiar Lineas",help="En caso de que necesite hacer correcciones para cada línea, puede ser útil copiarlas.", default=True)
    # computed fields
    move_type = fields.Char(compute="_compute_from_moves")
    journal_type = fields.Char(compute="_compute_from_moves")
    manual_establishment = fields.Char(string="Establecimiento Manual", copy=False, size=3,  store=True)
    manual_referral_guide = fields.Char(string="Guía de Remisión Manual", copy=False, size=3, store=True)
    manual_sequence = fields.Char(string="Secuencia Manual", size=9)
    
    @api.onchange('date','reason','move_type','journal_id','move_ids')
    def onchange_number_document(self):
        sequence=self.env['ir.sequence']
        seq=self.move_ids.journal_id.auth_out_debit_id
        if seq:
            self.manual_establishment = seq.serie_establecimiento
            self.manual_referral_guide = seq.serie_emision
            if seq.is_electronic:
                self.manual_sequence = str(sequence.next_by_code(seq.sequence_id.code)) 

    @api.model
    def default_get(self, fields):
        res = super(AccountDebitNote, self).default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
        if any(move.state != "posted" for move in move_ids):
            raise UserError(_('Solo puede debitar facturas publicadas.'))
        res['move_ids'] = [(6, 0, move_ids.ids)]
        return res

    @api.depends('move_ids')
    def _compute_from_moves(self):
        for record in self:
            move_ids = record.move_ids
            record.move_type = move_ids[0].type if len(move_ids) == 1 or not any(m.type != move_ids[0].type for m in move_ids) else False
            record.journal_type = record.move_type in ['in_refund', 'in_invoice'] and 'purchase' or 'sale'

    def _prepare_default_values(self, move):
        if move.type == 'in_invoice':
            type = 'in_debit'
        if move.type == 'out_invoice':
            type =  'out_debit'
        default_values = {
                'ref': '%s, %s' % (move.name, self.reason) if self.reason else move.name,
                'date': self.date or move.date,
                'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
                'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
                'invoice_payment_term_id': None,
                'debit_origin_id': move.id,
                'type': type,
                'manual_establishment':self.manual_establishment,
                'manual_referral_guide':self.manual_referral_guide,
                'manual_sequence':self.manual_sequence,
                'clave_acceso_sri':False,
                'numero_autorizacion_sri':False
            }
        #if not self.copy_lines or move.type in [('in_refund', 'out_refund')]:
        #    default_values['line_ids'] = [(5, 0, 0)]
        return default_values

    def create_debit(self):
        self.ensure_one()
        new_moves = self.env['account.move']
        for move in self.move_ids.with_context(include_business_fields=True): #copy sale/purchase links
            default_values = self._prepare_default_values(move)
            new_move = move.with_context(internal_type='debit_note').copy(default=default_values) # Context key is used for l10n_latam_invoice_document for ar/cl/pe
            move_msg = _(
                "Esta nota de débito se creó a partir de:") + " <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>" % (
                       move.id, move.name)
            new_move.message_post(body=move_msg)
            new_moves |= new_move

        action = {
            'name': 'Nota de Débito',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            }
        if len(new_moves) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': new_moves.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', new_moves.ids)],
            })
        return action