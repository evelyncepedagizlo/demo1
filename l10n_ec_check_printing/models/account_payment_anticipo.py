# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentAnticipo(models.Model):
    _name = 'account.payment.anticipo'
    _description = 'Lista de Pagos del Anticipo'
    _rec_name = 'payment_id'

    payment_id = fields.Many2one(
        'account.payment', 'Advance payment',
        required=True, ondelete='cascade')
    invoice_id = fields.Many2one(
        'account.move', string='Factura', required=True)
    amount_residual = fields.Float( string='Saldo')

    amount = fields.Float(
        'Pago', required=True)

    move_id = fields.Many2one(
        'account.move', 'Journal entry', readonly=True)

    aplica_anticipo = fields.Boolean(
        'Aplica Anticipo')



class AccountPaymentAnticipoValor(models.Model):
    _name = 'account.payment.anticipo.valor'
    _description = 'Lista de Pagos del Anticipo'
    _rec_name = 'payment_id'

    payment_id = fields.Many2one(
        'account.payment', 'Advance payment',
        required=True, ondelete='cascade')

    aplicacion_anticipo = fields.Float( string='Saldo')

    fechaAplicacion = fields.Date( string='Fecha de Aplicacion')

