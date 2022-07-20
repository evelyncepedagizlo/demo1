# -*- coding: utf-8 -*-
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import itertools
import logging
from itertools import groupby
import json

class WizardImportDocuments(models.TransientModel):
    _name = "wizard.agregar.retencion"
    _description = 'Agregar retención a monto de factura'
    
    STATES_VALUE = {'draft': [('readonly', False)]}

    group_id = fields.Many2one('account.tax.group', string='Grupo de Impuesto')
    tax_id = fields.Many2many('account.tax', string='Impuesto')
    

    invoice_id= fields.Many2one('account.move', string='Factura')
    auth_number = fields.Char('Numero de autorización')

   
    manual_establishment = fields.Char(string="Establecimiento Manual", size=3, store=True, states=STATES_VALUE)
    manual_referral_guide = fields.Char(string="Guía de Remisión Manual", size=3, store=True, states=STATES_VALUE)
    manual_sequence = fields.Char(string="Secuencia Manual", size=9, states=STATES_VALUE)



    def crear_retenciones(self, ):    
        self.invoice_id.retenciones_cliente=self.tax_id
        self.invoice_id.action_withholding_create_modify()








class AccountMove(models.Model):
    _inherit = 'account.move'


    retenciones_cliente = fields.Many2many('account.tax', string='Guias de remision')



    def agregar_retencion(self):
        context={'default_invoice_id':self.id}

        action = self.env.ref('gzl_facturacion_electronica.action_crear_retencion').read()[0]
        action['context']=context

        return action





    def action_withholding_create_modify(self):
        TYPES_TO_VALIDATE = ['in_invoice', 'liq_purchase', 'in_debit']
        wd_number = False
        for inv in self:
            #raise ValidationError(inv.has_retention)

           # if not inv.has_retention:
            #    continue
            # Autorizacion para Retenciones de la Empresa
            auth_ret = inv.journal_id.auth_retention_id
            if inv.type in ['in_invoice', 'liq_purchase', 'in_debit'] and not auth_ret:
                raise UserError(
                    u'No ha configurado la secuencia  de retenciones en el diario {0}'.format(inv.journal_id.name)
                )
            ret_taxes = []

           # raise ValidationError('llega aqui')

            for line in inv.invoice_line_ids:
                for tax in inv.retenciones_cliente:
                    tax_detail = tax.compute_all(line.price_unit, line.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']

                    
                    if tax.tax_group_id.code in ['ret_vat_b', 'ret_vat_srv', 'ret_ir']:
                        ret_taxes.append({
                            'fiscal_year': str(inv.invoice_date.month).zfill(2)+'/'+str(inv.invoice_date.year),
                            'group_id': tax.tax_group_id.id,
                            'tax_repartition_line_id': tax_detail[0]['tax_repartition_line_id'],
                            'amount': sum( [t['amount'] for t in tax_detail ]),
                            'base': sum( [t['base'] for t in tax_detail ]),
                            'tax_id': tax.id
                        })

            ret_taxes = sorted(ret_taxes, key = lambda x: x['tax_id'])
            ret_to_merge = groupby(ret_taxes, lambda x: x['tax_id'])
            ret_taxes = []
            for k,vv in ret_to_merge:
                v=list(vv)
                ret_taxes.append({
                            'fiscal_year': str(inv.invoice_date.month).zfill(2)+'/'+str(inv.invoice_date.year),
                            'group_id': v[0]['group_id'],
                            'tax_repartition_line_id': v[0]['tax_repartition_line_id'],
                            'amount': sum( [t['amount'] for t in v ]),
                            'base': sum( [t['base'] for t in v ]),
                            'tax_id': v[0]['tax_id']
                        })
            
            ret_taxes_orm = self.env['account.retention.line'].create(ret_taxes)
            if inv.retention_id:
                inv.retention_id.tax_ids = [(5,0,0)]
                ret_taxes_orm.write({
                    'retention_id': inv.retention_id.id,
                    'num_document': inv.l10n_latam_document_number
                })
                #inv.retention_id.action_validate(wd_number)
                return True
            today = date.today()
            ret_date = inv.invoice_date
            #if today>ret_date:
            #    ret_date = today
            withdrawing_data = {
                'partner_id': inv.partner_id.id,
                'name': wd_number,
                'invoice_id': inv.id,
                'auth_id': auth_ret.id,
                'type': inv.type,
                'in_type': 'ret_%s' % inv.type,
                'date': ret_date,
                
            }

            if len(ret_taxes) > 0:
                withdrawing = self.env['account.retention'].create(withdrawing_data)  # noqa

                ret_taxes_orm.write({'retention_id': withdrawing.id, 'num_document': inv.reference})  # noqa

                if inv.type in TYPES_TO_VALIDATE and withdrawing.is_manual_sequence!=True:
                    withdrawing.action_validate(wd_number)

                inv.write({'retention_id': withdrawing.id})
        return True
    