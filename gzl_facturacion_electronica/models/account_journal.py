# -*- coding: utf-8 -*-
 

import time
from datetime import datetime, date
from odoo import api, fields, models

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    auth_out_invoice_id = fields.Many2one('establecimiento','Secuencia Facturas')
    auth_out_refund_id = fields.Many2one('establecimiento','Secuencia Notas de Crédito')
    auth_retention_id = fields.Many2one('establecimiento','Secuencia Retenciones')
    auth_out_debit_id = fields.Many2one('establecimiento','Secuencia Notas de debito')
    auth_out_liq_purchase_id = fields.Many2one('establecimiento','Secuencia Liquidacion de compras')
    format_transfer_id = fields.Selection([
                                        ('banco_pichincha','Banco Pichincha'),
                                        ('banco_austro','Bando del Austro'),
                                        ('banco_internacional','Banco Internacional'),
                                        ('banco_pacifico','Banco del Pacifico')
                                        ],string='Formato de Transferencia Bancaria')
