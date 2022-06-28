# -*- coding: utf-8 -*-
import os
import time
import logging
from datetime import datetime
import itertools
from itertools import groupby

from odoo import api,fields,models
from odoo.exceptions import (
    Warning as UserError,
    ValidationError
)

def fix_date(fecha):
    d = '{0:%d/%m/%Y}'.format(fecha)
    return d




_DOCUMENTOS_EMISION = (
                        'ret_out_invoice', 

                        )
_DOCUMENTOS_RETENIBLES = (
                        'ret_in_invoice', 

                        )



class AccountRetentionLine(models.Model):
    _name = 'account.retention.line'
    _description = 'Líneas de retención'



    amount = fields.Float(string='Monto')
    base = fields.Float(string='Base')
    group_id = fields.Many2one('account.tax.group', string='Grupo de Impuesto')
    tax_id = fields.Many2one('account.tax', string='Impuesto')
    tax_repartition_line_id = fields.Many2one('account.tax.repartition.line')
    retention_id = fields.Many2one('account.retention', string='Retención')
    invoice_id = fields.Many2one('account.move', string='Factura')
    num_document = fields.Char(string='Numero documento')
    fiscal_year = fields.Char(string='Periodo Fiscal')
    code = fields.Char(string='Codigo', related="tax_id.description", readonly=True)
    name = fields.Char(string='Nombre', related="tax_id.name", readonly=True)
    sequence = fields.Integer('Secuencia')
    account_id = fields.Many2one('account.account', string="Cuenta")
    base_ret = fields.Float(string='Base', compute='compute_base_ret')
    
    @api.onchange('group_id')
    def onchange_group_id(self):
        self.tax_id=False
        self.base=False
        self.base_ret=False
        self.tax_repartition_line_id=False
        self.amount=False



    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for res in self:
            if res.tax_id:
                res.name=res.tax_id.name
                res.tax_repartition_line_id=res.tax_id.invoice_repartition_line_ids[1]

    @api.onchange('tax_id')
    def onchange_tax_base(self):
        for res in self:
            ret_taxes = []

            for line in res.invoice_id.invoice_line_ids:
                tax_detail = res.tax_id.compute_all(line.price_unit, line.currency_id, line.quantity, line.product_id, res.invoice_id.partner_id)['taxes']

                
                if res.tax_id.tax_group_id.code in ['ret_vat_b', 'ret_vat_srv', 'ret_ir','no_ret_ir']:
                    ret_taxes.append({
                        'fiscal_year': str(res.invoice_id.invoice_date.month).zfill(2)+'/'+str(res.invoice_id.invoice_date.year),
                        'group_id': res.tax_id.tax_group_id.id,
                        'tax_repartition_line_id': tax_detail[0]['tax_repartition_line_id'],
                        'amount': sum( [t['amount'] for t in tax_detail ]),
                        'base': sum( [t['base'] for t in tax_detail ]),
                        'tax_id': res.tax_id.id
                    })

            ret_taxes = sorted(ret_taxes, key = lambda x: x['tax_id'])
            ret_to_merge = groupby(ret_taxes, lambda x: x['tax_id'])
            ret_taxes = []
            for k,vv in ret_to_merge:
                v=list(vv)
                ret_taxes.append({
                            'fiscal_year': str(res.invoice_id.invoice_date.month).zfill(2)+'/'+str(res.invoice_id.invoice_date.year),
                            'group_id': v[0]['group_id'],
                            'tax_repartition_line_id': v[0]['tax_repartition_line_id'],
                            'amount': sum( [t['amount'] for t in v ]),
                            'base': sum( [t['base'] for t in v ]),
                            'tax_id': v[0]['tax_id']
                        })
            for retencion in ret_taxes:
                res.fiscal_year=retencion['fiscal_year']
                res.amount=retencion['amount']
                res.base=retencion['base']



    @api.depends('base','tax_repartition_line_id')
    def compute_base_ret(self):
        for res in self:
            res.base_ret = (
                res.base * res.tax_repartition_line_id.factor_percent /100
            ) if res.base and res.tax_repartition_line_id else 0.00



class AccountRetention(models.Model):

    @api.model
    def _default_currency(self):
        company = self.env['res.company']._company_default_get('account.move')  # noqa
        return company.currency_id

    def _default_type(self):
        context = self._context
        return context.get('type', 'out_invoice')

    def _get_in_type(self):
        context = self._context
        return context.get('in_type', 'ret_out_invoice')


    @api.model
    def _get_default_invoice_date(self):
        return fields.Date.today()


    STATES_VALUE = {'draft': [('readonly', False)]}

    _name = 'account.retention'
    _description = 'Retención'
    _order="id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    name = fields.Char('Número',size=64,readonly=True,copy=False, states=STATES_VALUE,)
    internal_number = fields.Char('Número Interno',size=64,readonly=True,copy=False)
    manual = fields.Boolean('Numeración Manual',readonly=True,default=True, states=STATES_VALUE,)
    auth_id = fields.Many2one('establecimiento','Autorizacion',readonly=True,states=STATES_VALUE)
    auth_number = fields.Char('Numero de autorización')
    type = fields.Selection(related='invoice_id.type',string='TipoComprobante',readonly=True,store=True,default=_default_type)
    in_type = fields.Selection(
        [
            ('ret_in_invoice', u'Retención a Proveedor'),
            ('ret_out_invoice', u'Retención de Cliente'),
            ('ret_in_refund', u'Retención Nota de Credito Proveedor'),
            ('ret_out_refund', u'Retención Nota de Credito Cliente'),
            ('ret_liq_purchase', u'Retención de Liquidación en Compras'),
            ('ret_in_debit', u'Retención de Nota de Debito Proveedor'),
            ('ret_out_debit', u'Retención Nota de Debito Cliente'),
        ],string='Tipo',readonly=True,default=_get_in_type)
    date = fields.Date('Fecha Emision',readonly=True,states={'draft': [('readonly', False)]}, required=True,default=_get_default_invoice_date)
    tax_ids = fields.One2many('account.retention.line','retention_id','Detalle de Impuestos', readonly=True,states=STATES_VALUE,copy=False)
    invoice_id = fields.Many2one('account.move',string='Factura',required=False,readonly=True,states=STATES_VALUE,domain=[('state', '=', 'open')],copy=False)
    partner_id = fields.Many2one('res.partner',string='Empresa',required=True,readonly=True,states=STATES_VALUE )
    move_ret_id = fields.Many2one('account.move',string='Asiento Retención',readonly=True,copy=False)
    state = fields.Selection(
                            [
                                ('draft', 'Borrador'),
                                ('done', 'Validado'),
                                ('cancel', 'Anulado')
                            ],readonly=True,string='Estado',default='draft',track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency',required=True,readonly=True,states={'draft': [('readonly', False)]},default=_default_currency)
    amount_total = fields.Monetary(compute='_compute_total',string='Total',store=True,readonly=True)
    to_cancel = fields.Boolean(string='Para anulación',readonly=True,states=STATES_VALUE)
    company_id = fields.Many2one('res.company','Company',required=True,change_default=True,readonly=True, states={'draft': [('readonly', False)]},default=lambda self: self.env['res.company']._company_default_get('account.move'))
    sri_sent = fields.Boolean('Enviado', default=False)
    
    manual_establishment = fields.Char(string="Establecimiento Manual", size=3, store=True, states=STATES_VALUE)
    manual_referral_guide = fields.Char(string="Guía de Remisión Manual", size=3, store=True, states=STATES_VALUE)
    manual_sequence = fields.Char(string="Secuencia Manual", size=9, states=STATES_VALUE)
    is_manual_sequence = fields.Boolean('Es Secuencia Manual?', compute="_get_electronic", states=STATES_VALUE)
    is_electronic = fields.Boolean('Es Electrónico?', compute="_get_electronic", states=STATES_VALUE)

    clave_acceso_sri = fields.Char('Clave de Acceso')
    numero_autorizacion_sri = fields.Char('Número de Autorización SRI')
    fecha_autorizacion_sri = fields.Char('Fecha de Autorización')
    estado_autorizacion_sri = fields.Selection([('PPR', 'En procesamiento'), 
                                                ('AUT', 'Autorizado'),
                                                ('NAT', 'NoAutorizad'),],
                                    string='Estado de Autorización del Sri')

    l10n_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Document Type', readonly=False, auto_join=True, index=True,
        states={'posted': [('readonly', True)]}, compute='_compute_l10n_latam_document_type', store=True)


    l10n_latam_document_number = fields.Char(string='Document Number', readonly=True, states={'draft': [('readonly', False)]})

    campos_adicionales_facturacion = fields.One2many('campos.adicionales.facturacion', inverse_name = 'retention_id')

    email_fe = fields.Char('Email Factura Electronica')


    _sql_constraints = [
        (
            'unique_number_type',
            'unique(name,type,partner_id)',
            u'El número de retención es único.'
        )
    ]
    




    @api.onchange('partner_id')
    def actualizar_email_factura(self):
        self.email_fe=self.partner_id.email







    @api.depends('in_type')
    def _compute_l10n_latam_document_type(self):
        dctCodDoc={
            'ret_out_invoice':self.env.ref('l10n_ec_tree.ec_03'),
            'ret_in_invoice':self.env.ref('l10n_ec_tree.ec_11'),
            'ret_in_refund':self.env.ref('l10n_ec_tree.ec_11'),
            'ret_in_debit':self.env.ref('l10n_ec_tree.ec_11'),
            'ret_out_refund':self.env.ref('l10n_ec_tree.ec_03'),

            }  
        for rec in self:
            rec.l10n_latam_document_type_id = dctCodDoc[rec.in_type].id

      
    def post(self):
        for inv in self:
            seq = self.env['ir.sequence']
            if inv.is_electronic==True and inv.type in _DOCUMENTOS_EMISION:
                    inv.l10n_latam_document_number = inv.establecimiento.serie_establecimiento+inv.establecimiento.serie_emision+str(seq.next_by_code(inv.establecimiento.sequence_id.code))                 
                    today_date = date.today() 
                    fecha_emision = today_date.strftime("%d%m%Y") 
                    clave_acceso_48 = fecha_emision+ \
                                        str((inv.l10n_latam_document_type_id.code).strip())+ \
                                        str((inv.partner_id.vat).strip())+ \
                                        str(inv.company_id.type_environment.strip())+ \
                                        str(inv.l10n_latam_document_number).strip()+ \
                                        str(inv.company_id.numerical_code).strip()+ \
                                        str(inv.company_id.emission_code).strip()
                    digito_verificador = inv.GenerarClaveAcceso(clave_acceso_48)
                    inv.clave_acceso_sri = clave_acceso_48+str(digito_verificador)
                    #inv.numero_autorizacion_sri = clave_acceso_48+str(digito_verificador) 
            else:
                if inv.establecimiento.sequence_id:
                    inv.l10n_latam_document_number = inv.establecimiento.serie_establecimiento+inv.establecimiento.serie_emision+str(seq.next_by_code(inv.establecimiento.sequence_id.code))     
                else:
                    if inv.manual_establishment and inv.manual_referral_guide and inv.manual_sequence:
                        inv.l10n_latam_document_number = inv.manual_establishment.zfill(3)+inv.manual_referral_guide.zfill(3)+str(inv.manual_sequence).zfill(9)


        return super().post()

    def GenerarClaveAcceso(self,clave_acceso_48):
        factores = itertools.cycle((2,3,4,5,6,7))
        suma = 0
        for digito, factor in zip(reversed(clave_acceso_48), factores):
            digito = int(digito)
            suma += digito*factor
        control = 11 - suma%11
        if control == 10:
            return 1
        elif control == 11:
            return 0
        else:
            return control













    @api.depends('auth_id', 'type')
    def _get_electronic(self):
        for ret in self:
            if ret.auth_id.is_manual_sequence:
                ret.is_manual_sequence=True
            else:
                ret.is_manual_sequence = False
            if ret.auth_id.is_electronic:
                ret.is_electronic=True
            else:
                ret.is_electronic = False
    
    @api.onchange('auth_id')
    def _get_is_manual(self):
        if self.auth_id.is_manual_sequence==True:
            self.manual_establishment=self.auth_id.serie_establecimiento
            self.manual_referral_guide=self.auth_id.serie_emision
    
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.depends('tax_ids.amount')
    def _compute_total(self):
        for s in self:
            s.amount_total = sum(tax.amount for tax in s.tax_ids)
    
    def button_validate(self):
        for ret in self:
            if not ret.tax_ids:
                raise UserError('No ha aplicado impuestos.')
            self.action_validate(self.name)
            if ret.manual:
                ret.invoice_id.write({'retention_id': ret.id})
            if self.in_type in ['ret_out_invoice']:
                self.create_move()


        
    
    def action_validate(self, number=None):
        """
        @number: Número para usar en el documento
        """
        self.action_number(number)
        if self.in_type in ['ret_in_invoice']:
            self.procesoComprobanteElectronico()
    
        return self.write({'state': 'done'})
    
    def action_number(self, number):
        for wd in self:
            if wd.to_cancel:
                raise UserError('El documento fue marcado para anular.')
            sequence = wd.auth_id.sequence_id
            if self.type == 'in_invoice':
                if wd.auth_id.is_manual_sequence==True:
                    number = (wd.manual_sequence or wd.invoice_id.ret_manual_sequence).zfill(9)
                else:
                    number = sequence.next_by_id()
                if wd.invoice_id.ret_manual_establishment and wd.invoice_id.ret_manual_referral_guide:
                    wd.write({'name': '%s%s%09s'%(wd.invoice_id.ret_manual_establishment, wd.invoice_id.ret_manual_referral_guide, number)})
                else:
                    wd.write({'name': '%s%s%09s'%(wd.auth_id.serie_establecimiento, wd.auth_id.serie_emision, number)})



            elif self.type == 'out_invoice':
                wd.write({'name': '%s%s%09s'%(wd.manual_establishment.zfill(3), wd.manual_referral_guide.zfill(3), wd.manual_sequence.zfill(9))})
                
        return True

    def create_move(self):
        """
        Generacion de asiento contable para aplicar como
        pago a factura relacionada
        """
        for ret in self:
            inv = ret.invoice_id
            move_data = {
                'name':inv.name,
                'journal_id': inv.journal_id.id,
                'ref': 'Ret. '+inv.name,
                'date': ret.date
            }
            total_counter = 0
            lines = []
            
            for line in ret.tax_ids:
                if line.tax_repartition_line_id.account_id:
                    if line.tax_repartition_line_id:
                        lines.append((0, 0, {
                            'partner_id': ret.partner_id.id,
                            'account_id': line.tax_repartition_line_id.account_id.id,
                            'name': ret.name,
                            'debit': abs(line.amount),
                            'credit': 0.00
                        }))

                total_counter += abs(line.amount)
            rec_account = inv.partner_id.property_account_receivable_id.id
            pay_account = inv.partner_id.property_account_payable_id.id
            lines.append((0, 0, {
                'partner_id': ret.partner_id.id,
                'account_id': ret.in_type == 'ret_in_invoice' and pay_account or rec_account,
                'name': ret.name,
                'debit': 0.00,
                'credit': total_counter
            }))
            move_data.update({'line_ids': lines})
            move = self.env['account.move'].create(move_data)




            acctype = self.type == 'in_invoice' and 'payable' or 'receivable'
            inv_lines = inv.line_ids
            acc2rec = inv_lines.filtered(lambda l: l.account_id.internal_type == acctype)  
            acc2rec += move.line_ids.filtered(lambda l: l.account_id.internal_type == acctype)  
            acc2rec.auto_reconcile_lines()
            ret.write({'move_ret_id': move.id})
            move.post()
        return True
    
    def action_cancel(self):
        """
        Método para cambiar de estado a cancelado el documento
        """
        for ret in self:
            if ret.move_ret_id:
                ret.move_ret_id._reverse_moves()
                continue
            
            ret.invoice_id.write({
                'retention_id': None
            })
            self.env.cr.commit()
            ret.invoice_id.button_draft()

            data = {'state': 'cancel'}
            self.write({'state': 'cancel'})
        return True
    
    def action_draft(self):
        self.write({'state': 'draft'})
        return True
    
    def print_retention(self):
        """
        Método para imprimir reporte de retencion
        """
        return self.env.ref('gzl_facturacion_electronica.report_account_retention').report_action(self)