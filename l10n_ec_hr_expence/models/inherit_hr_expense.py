# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAuthorisation(models.Model):
    _inherit = 'hr.expense'

    refund_type= fields.Selection([
        ('refund_client', _('Refun client invoice')),
        ('refund_supplier', _('Refun supplier invoice')),
        ('refund_employee', _('Refun employee')),
        ('cash_box', _('Cahs box')),
    ], string=_('Refun type'))
    document_type = fields.Selection([
        ('client_invoice', _('Client Invoice')),
        ('supplier_invoice', _('Supplier Invoice')),
    ], string='Document type')
    supplier_id = fields.Many2one('res.partner', string=_('Supplier'))
    partner_shipping_id = fields.Many2one('res.partner', string=_("Delivery Address"))
    ref  = fields.Char(string='Reference')
    sustento_id = fields.Many2one('ats.sustento.comprobante', string=_('Sustento del Comprobante'))
    document_number = fields.Char(string='Nro. Documento', copy=False)
    auth_number = fields.Char('Autorización', copy=False)
    document_date = fields.Date(string='Document date')

    @api.onchange('supplier_id')
    def onchange_supplier_id(self):
        self.partner_shipping_id = False
        if self.supplier_id:
            addr = self.supplier_id.address_get(['delivery'])
            self.partner_shipping_id = addr and addr.get('delivery')
            child_ids = [child_id.id for child_id in self.supplier_id.child_ids if child_id]
            if child_ids:
                child_ids.append(self.supplier_id.id)
                return  {'domain':{'partner_shipping_id':[('id', 'in', child_ids)]}}
            return {'domain':{'partner_shipping_id':[('id', '=', self.supplier_id.id)]}}

    @api.constrains('document_number')
    def check_document_number(self):
        if self.document_number:
            if len(self.document_number) > 15:
                raise UserError(
                    u'El número de documento debe tener 15 números o menos'
                )

    @api.constrains('auth_number')
    def check_auth_number(self):
        """
        Metodo que verifica la longitud de la autorizacion
        10: documento fisico
        49: factura electronica modo offline
        """
        if self.auth_number and len(self.auth_number) not in [10, 49]:
            raise UserError(
                u'La autorización debe tener 10 o 49 dígitos según el documento.'
            )

    def action_submit_expenses(self):
        sheet = self._create_sheet_from_expenses()
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'res_id': sheet.id,
        }

    def _create_sheet_from_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))
        if any(expense.refund_type != self.mapped('refund_type')[0] for expense in self):
            raise ValidationError(_("Gastos con Tipo de reembolso diferentes. Los gastos " +
                                            "seleccionados deben ser del mismo tipo para crear un " +
                                            "informe. Verificar gastos registros."))
        if any(not expense.product_id for expense in self):
            raise UserError(_("You can not create report without product."))
        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        sheet = self.env['hr.expense.sheet'].create({
            'company_id': self.company_id.id,
            'employee_id': self[0].employee_id.id,
            'name': todo[0].name if len(todo) == 1 else '',
            'refund_type': self[0].refund_type,
            'expense_line_ids': [(6, 0, todo.ids)]
        })
        # sheet._onchange_employee_id()
        return sheet