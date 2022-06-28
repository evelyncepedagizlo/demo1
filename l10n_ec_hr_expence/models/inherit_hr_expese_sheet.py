# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountAuthorisation(models.Model):
    _inherit = 'hr.expense.sheet'

    refund_type= fields.Selection([
        ('refund_client', _('Refun client invoice')),
        ('refund_supplier', _('Refun supplier invoice')),
        ('refund_employee', _('Refun employee')),
        ('cash_box', _('Cahs box')),
    ], string=_('Refun type'), compute='_compute_refund_type')
    journal_type= fields.Selection([
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
    ], compute='_compute_refund_type')
    expense_user_id = fields.Many2one(comodel_name='res.users', default=lambda self: self.env.uid)

    document_number = fields.Many2one('account.move', string='Document number', readonly=True)
    auth_inv_id = fields.Many2one(
        'establecimiento',
        string='Establecimiento',
        readonly=True,
        states={'approve': [('readonly', False)]},
        help='Autorizacion para documento',
        copy=False
    )

    def _compute_refund_type(self):
        for record in self:
            if record.expense_line_ids:
                record.refund_type = record.expense_line_ids[0].refund_type
                record.journal_type = self._get_journal_type(self.refund_type)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        for record  in self:
            if record.journal_id and record.refund_type:
                if record.refund_type in ('refund_employee', 'cash_box'):
                    record.auth_inv_id = record.journal_id.auth_out_liq_purchase_id
                elif record.refund_type == 'refund_client':
                    record.auth_inv_id = record.journal_id.auth_out_invoice_id
                elif record.refund_type == 'refund_supplier':
                    record.auth_inv_id = False

    def _get_journal_type(self, journal_type):
        return{
            'refund_employee': 'purchase',
            'cash_box': 'purchase',
            'refund_client': 'sale',
            'refund_supplier': 'purchase',
        }.get(journal_type)

    def _get_type_move(self, refund_type):
        return{
            'refund_client':'out_invoice',
            'refund_supplier':'in_invoice',
            'refund_employee':'liq_purchase',
            'cash_box':'liq_purchase',
        }.get(refund_type)

    def _hook_get_invoice_lines(self, line, expense):
        return line

    def _get_invoice_lines(self):
        lines = []
        for expense in self.expense_line_ids:
            line = {
                'product_id': expense.product_id.id,
                'name': expense.product_id.description,
                'account_id': expense.account_id.id,
                'quantity': expense.quantity,
                'price_unit': expense.unit_amount,
                'tax_ids': expense.tax_ids.ids,
            }
            line = self._hook_get_invoice_lines(line, expense)
            lines.append((0, 0, line))
        return lines

    def _open_invoce_by_id(self, move_id):
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_invoice_tree')
        return {
            "name": _("Account move"),
            'domain': str([('id', '=', move_id.id)]),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'views': [(form_view and form_view.id or False, 'form'),
                        (tree_view and tree_view.id or False, 'tree')],
            'type': 'ir.actions.act_window',
            'res_id': move_id.id,
            'target': 'current',
            'nodestroy': True
        }
    
    def _hook_move_data(self, move_data):
        return move_data

    def action_generate_invoice(self):
        self.ensure_one()
        refund_type = ""
        if self.expense_line_ids:
            refund_type = self.expense_line_ids[0].refund_type
            if not refund_type:
                raise ValidationError(_("Las líneas de pagos deben tener tipo de reembolso para generar la Factura."))
            for line in self.expense_line_ids:
                if line.refund_type != refund_type:
                    raise ValidationError(_("Gastos con Tipo de reembolso diferentes. Los gastos " +
                                            "seleccionados deben ser del mismo tipo para crear una " +
                                            "factura. Verificar gastos registrados."))
        partner_shipping = self.expense_line_ids[0].partner_shipping_id.id
        refund_type = self._get_type_move(refund_type)
        if refund_type in ('in_invoice', 'liq_purchase') and not (self.journal_id or self.auth_inv_id):
            raise ValidationError(_("The daily and establishment fields must be filled"))
        if not self.accounting_date:
            raise ValidationError(_("You must fill the date field in order to generate the invoice"))
        account_move = self.env['account.move']
        move_data = {
            'type': refund_type,
            'ref': "Informe de gasto "+ self.name,
            'partner_shipping_id': partner_shipping,
            'date': self.accounting_date,
            'journal_id': self.journal_id.id,
            'establecimiento': self.auth_inv_id.id,
            'invoice_line_ids': self._get_invoice_lines(),
        }
        move_data = self._hook_move_data(move_data)
        move_id = account_move.create(move_data)
        self.document_number = move_id
        self.state = 'post'
        return self._open_invoce_by_id(move_id)
