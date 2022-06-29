# -*- coding: utf-8 -*-
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import itertools
import logging
from itertools import groupby
import json


_logger = logging.getLogger(__name__)

_DOCUMENTOS_EMISION = (
                        'out_invoice', 
                        'liq_purchase', 
                        'out_refund',
                        'out_debit' 
                        )
_DOCUMENTOS_RETENIBLES = (
                        'out_invoice', 
                        'in_invoice', 
                        'out_refund', 
                        'in_refund', 
                        'out_debit',
                        'in_debit',
                        'liq_purchase'
                        )

class AccountMove(models.Model):
    _inherit = 'account.move'
    _order="id desc"
    
    _rec_name="nombre_mostrar"

    email_fe = fields.Char('Email Factura Electronica')

    email_fe2 = fields.Char(string='Email Factura Electronica')

    #contrato_id = fields.Many2one('contrato', string='Contrato')

    #contrato_estado_cuenta_ids = fields.Many2many('contrato.estado.cuenta', copy=False,string='Estado de Cuenta de Aportes',)
    
    #is_group_cobranza = fields.Boolean(string='Es Cobranza',compute="_compute_is_group_cobranza")


    # @api.onchange("partner_id")
    # def obtener_anticipos(self):
    #     for l in self:
    #         lista_ids=[]
    #         lista=[]
    #         if l.partner_id:
    #             linea_pago_ids=self.env['account.payment.line.account'].search([('partner_id','=',self.partner_id.id),('aplicar_anticipo','=',True)])
    #             for x in linea_pago_ids:
    #                 if x.payment_id.state=='posted':
    #                     lista.append({'linea_pago_id':x.id,
    #                           'payment_id':x.payment_id.id,
    #                           'credit':x.saldo_pendiente,
    #                           'anticipo_pendiente':False,
    #                           })
    #         for prueba in lista:
    #             id_registro=self.env['anticipos.pendientes'].create(prueba) 
    #             lista_ids.append(id_registro.id)
    #             self.update({'anticipos_ids':[(6,0,lista_ids)]}) 
         

    # @api.depends("partner_id")
    # def _compute_is_group_cobranza(self):
    #     self.is_group_cobranza = self.env['res.users'].has_group('gzl_facturacion_electronica.grupo_cobranza')

    # @api.onchange('contrato_estado_cuenta_ids')
    # def _onchange_contrato_estado_cuenta_ids(self):
    #     obj_product = self.env['product.template'].search([('default_code','=','CA1')])
    #     obj_account = self.env['account.account'].search([('code','=','4010101002')])
    #     obj_tax = self.env['account.tax'].search([('name','=','VENTAS DE ACTIVOS FIJOS GRAVADAS TARIFA 12%')])
    #     obj_account_debe = self.env['account.account'].search([('code','=','1010205001')])
    #     obj_account_haber = self.env['account.account'].search([('code','=','4010102002')])
    #     list_pagos_diferentes = {}
    #     valor = 0
    #     valor_debe = 0
    #     valor_haber = 0
    #     values = {
    #                 'product_id':obj_product.id,
    #                 'name': 'Cuota Administrativa. Pago de Cuota(s) de Contrato. Cuota Administrativa: ',
    #                 'account_id':obj_account.id,
    #                 'tax_ids': [(6,0,[obj_tax.id])],
    #                 'quantity': 0,
    #                 'price_unit':0,
    #             }
    #     cliente=self.partner_id.name
    #     if self.contrato_estado_cuenta_ids:
    #         obj_contrato_estado_cuenta = self.env['contrato.estado.cuenta'].search([('id','in',self.contrato_estado_cuenta_ids.ids)])
    #         i=0
    #         saldo_credito=0
    #         numero_cuotas=''
    #         for rec in obj_contrato_estado_cuenta:
    #             if i==0:
    #                 nombre=values.get('name')+str(rec.cuota_adm)+'.'+' IVA: '+str(rec.iva_adm)+' Cuota(s): '+rec.numero_cuota+','
    #             else:
    #                 nombre=values.get('name')+rec.numero_cuota+','
    #             i+=1
    #             values['quantity'] = values.get('quantity') + 1
    #             valor += rec.cuota_adm
    #             values['price_unit'] = valor/values.get('quantity')
    #             values['name'] =nombre
    #             list_pagos_diferentes.update({
    #                 str(rec.cuota_adm):values
    #             })
                    
    #         for rec in list_pagos_diferentes.values():
    #             if not self.invoice_line_ids:
    #                 self.invoice_line_ids = [(0,0,rec)] 
    #             else:
    #                 for ric in self.invoice_line_ids:
    #                     self.invoice_line_ids = [(1,ric.id,{
    #                         'name': rec.get('name'),
    #                         'quantity': rec.get('quantity'),
    #                         'price_unit': rec.get('price_unit'),
    #                     })]          
    #         self._move_autocomplete_invoice_lines_values()




    @api.onchange('invoice_payment_term_id','method_payment','contrato_estado_cuenta_ids','name','anticipos_ids')
    def obtener_infoadicional(self):
        numero_cuotas=","      
        saldo_credito=0
        longitud=0
        #longitud_total=len(self.contrato_estado_cuenta_ids)
        #for registros in self.contrato_estado_cuenta_ids:
        #    longitud+=1
        #    numero_cuotas=numero_cuotas+registros.numero_cuota+','
        #    saldo_credito+=registros.saldo
        lista_dic=[] 
        saldo=0

        valor_restar=0

        #for m in self.anticipos_ids:
        #    if m.anticipo_pendiente:
        #        valor_restar+=m.credit

        
        #for rec in self.contrato_estado_cuenta_ids:
        #    if valor_restar:
        #        if valor_restar<=rec.saldo_cuota_capital:
        #            for pag in self.anticipos_ids:
        #                if pag.anticipo_pendiente:
        #                    valor_restar=0
        #                    pass
        #        else:
        #            for pag in self.anticipos_ids:
        #                if pag.anticipo_pendiente:
        #                    valor_restar=valor_restar-rec.saldo_cuota_capital
                            
        #for ant in self.anticipos_ids:
        #    if ant.anticipo_pendiente:
                
        #        ant.valor_sobrante=valor_restar
                
        #        saldo+=ant.credit-valor_restar
        if self.invoice_payment_term_id:
            lista_dic.append({
                            'nombre': 'CRÉDITO',
                            'valor':str(round(saldo_credito-saldo,2))+' a '+self.invoice_payment_term_id.name})
        else:
            lista_dic.append({
                            'nombre': 'CRÉDITO',
                            'valor':str(round(saldo_credito-saldo,2))+' a '+str(self.invoice_date_due)})
        if self.method_payment:
            lista_dic.append({'nombre':'Desde','valor':str(self.invoice_date)}) 
            lista_dic.append({'nombre':'F/pago','valor':self.method_payment.name}) 


        if self.partner_id:
            lista_dic.append({'nombre':'Nota','valor':self.partner_id.name+self.name+'Cancela Cuotas'+numero_cuotas})
            if self.partner_id.email:
                lista_dic.append({'nombre':'Email','valor':self.partner_id.email})
        #if not self.campos_adicionales_facturacion:
        lista_ids=[]
        for prueba in lista_dic:
            id_registro=self.env['campos.adicionales.facturacion'].create(prueba) 
            lista_ids.append(id_registro.id)
            self.update({'campos_adicionales_facturacion':[(6,0,lista_ids)]}) 
        

    establecimiento = fields.Many2one('establecimiento')
    reversed_entry_nc_id = fields.Many2one(related='reversed_entry_id', store=True)
    ######## PAGE TRIBUTACION
    respuesta_sri = fields.Char('Respuesta SRI')
    clave_acceso_sri = fields.Char('Clave de Acceso')
    numero_autorizacion_sri = fields.Char('Número de Autorización SRI')
    fecha_autorizacion_sri = fields.Datetime('Fecha de Autorización')
    estado_autorizacion_sri = fields.Selection([('PPR', 'En procesamiento'), 
                                                ('AUT', 'Autorizado'),
                                                ('NAT', 'No Autorizado'),],
                                    string='Estado de Autorización del Sri')

    sustento_del_comprobante = fields.Many2one('ats.sustento.comprobante', string="Sustento del Comprobante")
    method_payment = fields.Many2one('account.epayment', string="Forma de Pago" )
    
    guia_ids = fields.Many2many('account.guia.remision', string='Guias de remision')
    auth_number = fields.Char('Autorización', copy=False)
    is_electronic = fields.Boolean('Es Electrónico?', compute="_get_electronic", default=False, store=True)
    is_manual_sequence = fields.Boolean('Es Secuencia Manual?', compute="_get_electronic", default=False, store=True)
    has_retention = fields.Boolean(compute='_check_retention',string="Tiene Retención en IR",store=True,readonly=True, default=False)
    reference = fields.Char('Num documento', copy=False, length=9)
    type = fields.Selection(selection_add=
        [
            ('liq_purchase', 'Liquidacion de Compra'),
            ('in_debit', 'Nota de debito (Emision)'),
            ('out_debit', 'Nota de debito (Recepcion)'),
        ])
    withholding_number = fields.Char('Num. Retención',readonly=True,states={'draft': [('readonly', False)]},copy=False)
    manual_referral_guide = fields.Char(string="Guía de Remisión Manual", copy=False, size=3, store=True)
    manual_establishment = fields.Char(string="Establecimiento Manual", copy=False, size=3,  store=True)
    manual_sequence = fields.Char(string="Secuencia Manual", size=9)
    
    type_environment = fields.Selection([('1', 'Pruebas'), 
                                    ('2', 'Producción')],
                                    string='Tipo de Ambiente')
    
    ### PAGE RETENCIONES
    retention_id = fields.Many2one('account.retention',string='Retención de Impuestos',store=True, readonly=True,copy=False)
    ret_name = fields.Char(related='retention_id.name')
    ret_manual = fields.Boolean('Numeración Manual',default=False)
    ret_manual_establishment = fields.Char(string="Establecimiento Manual", size=3, store=True, related='retention_id.manual_establishment')
    ret_manual_referral_guide = fields.Char(string="Guía de Remisión Manual", size=3, store=True, related='retention_id.manual_referral_guide')
    ret_manual_sequence = fields.Char(string="Secuencia Manual", size=9)
    ret_is_manual_sequence = fields.Boolean('Es Secuencia Manual?', compute="_get_electronic", default=False, store=True)
    ret_is_electronic = fields.Boolean('Es Electrónico?', compute="_get_electronic", default=False, store=True)
    ret_auth_number = fields.Char('Numero de autorizacion', related="ret_auth_id.authorization_number")
    ret_state = fields.Selection(
                            [
                                ('draft', 'Borrador'),
                                ('done', 'Validado'),
                                ('cancel', 'Anulado')
                            ],readonly=True,string='Estado',default='draft', related='retention_id.state')
    ret_auth_id = fields.Many2one('establecimiento','Autorizacion',readonly=True,related="journal_id.auth_retention_id")
    ret_tax_ids = fields.One2many('account.retention.line','invoice_id','Detalle de Impuestos', readonly=True, related='retention_id.tax_ids')
    ret_amount_total = fields.Monetary(compute='_compute_ret_total',string='Total',store=True,readonly=True)
    ret_clave_acceso_sri = fields.Char('Clave de Acceso', related='retention_id.clave_acceso_sri')
    ret_numero_autorizacion_sri = fields.Char('Número de Autorización SRI', related='retention_id.numero_autorizacion_sri')
    ret_fecha_autorizacion_sri = fields.Char('Fecha de Autorización', related='retention_id.fecha_autorizacion_sri')
    ret_estado_autorizacion_sri = fields.Selection([('PPR', 'En procesamiento'), 
                                                ('AUT', 'Autorizado'),
                                                ('NAT', 'NoAutorizad'),],
                                    string='Estado de Autorización del Sri', related='retention_id.estado_autorizacion_sri')

    


    tipo_referencia = fields.Char('Tipo de Referencia',compute='_obtener_tipo_referencia',store=True)
    #acunalema
    #acunalema
    view_amount_total = fields.Monetary(string='Total de la Factura',readonly=True,compute='_recompute_dynamic_lines_view',store=True)
    view_amount_tax_ret = fields.Monetary(string='Amount tax',readonly=True,compute='_compute_invoice_taxes_by_group_view',store=True)
    #@api.onchange('invoice_line_ids')
    #def _onchange_recompute_dynamic_lines_view(self):
    #    self._compute_invoice_taxes_by_group_view()
    #    self._recompute_dynamic_lines_view()

    #def get_cuotas_lines(self):
    #    if self.contrato_estado_cuenta_ids:
    #        cuotas = self.contrato_id.estado_de_cuenta_ids.search([('id','in',self.contrato_estado_cuenta_ids.ids)])
    #        if cuotas:
    #            return cuotas

    def get_total_and_subtotal_cuotas(self):
        cuotas = self.get_cuotas_lines()
        total = 0
        subtotal = 0
        iva = 0
        for rec in cuotas:
            iva += rec.iva_adm
            total += (rec.cuota_adm+rec.cuota_capital+rec.seguro+rec.rastreo+rec.otro+rec.iva_adm)
            subtotal = total - iva
        
        return {'subtotal':subtotal, 'total':total}


    def actualizar_retenciones(self):
        obj=self.env['account.move'].search([('type','in',['in_invoice','out_invoice'])])
        for l in obj:
            l._compute_invoice_taxes_by_group_view()
            l._recompute_dynamic_lines_view()
            
        
    
    
    @api.depends('amount_total')
    def _recompute_dynamic_lines_view(self):
        for l in self:
            l.view_amount_total = l.amount_total - l.view_amount_tax_ret               
    

    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group_view(self):
        ''' Helper to get the taxes grouped according their account.tax.group.
        This method is only used when printing the invoice.
        '''
        for move in self:
            lang_env = move.with_context(lang=move.partner_id.lang).env
            tax_lines = move.line_ids.filtered(lambda line: line.tax_line_id)
            tax_balance_multiplicator = -1 if move.is_inbound(True) else 1
            res = {}
            # There are as many tax line as there are repartition lines
            done_taxes = set()
            valor = 0.0
            for line in tax_lines:
                res.setdefault(line.tax_line_id.tax_group_id, {'base': 0.0, 'amount': 0.0})
                res[line.tax_line_id.tax_group_id]['amount'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
                tax_key_add_base = tuple(move._get_tax_key_for_group_add_base(line))
                if tax_key_add_base not in done_taxes:
                    if line.currency_id and line.company_currency_id and line.currency_id != line.company_currency_id:
                        amount = line.company_currency_id._convert(line.tax_base_amount, line.currency_id, line.company_id, line.date or fields.Date.today())
                    else:
                        amount = line.tax_base_amount
                    res[line.tax_line_id.tax_group_id]['base'] += amount
                    # The base should be added ONCE
                    done_taxes.add(tax_key_add_base)
                
            # At this point we only want to keep the taxes with a zero amount since they do not
            # generate a tax line.
            zero_taxes = set()
            for line in move.line_ids:
                for tax in line.tax_ids.flatten_taxes_hierarchy():
                    if tax.tax_group_id not in res or tax.id in zero_taxes:
                        res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
                        res[tax.tax_group_id]['base'] += tax_balance_multiplicator * (line.amount_currency if line.currency_id else line.balance)
                        zero_taxes.add(tax.id)

            res = sorted(res.items(), key=lambda l: l[0].sequence)
            move.amount_by_group = [(
                group.name, amounts['amount'],
                amounts['base'],
                formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id),
                formatLang(lang_env, amounts['base'], currency_obj=move.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]
            
            amounttot=0.0
            for group, amounts in res:
                print( "amount*"+str(amounts['amount'])+ " base "+str(amounts['base']))
                if group.name == 'Retención Impuesto a la Renta':
                    amounttot = amounts['amount']
                    #raise ValidationError(_( str(formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id))+" - "+str(group.name)+ " amount "+str(amounts['amount'])+ " base "+str(amounts['base'])))
            #raise ValidationError(_(str(cont)+" "+str(amounttot)+" "+str(valor)))
            move.view_amount_tax_ret =   amounttot
                    
                    #raise ValidationError(_( str(formatLang(lang_env, amounts['amount'], currency_obj=move.currency_id))+" - "+str(group.name)+ " amount "+str(amounts['amount'])+ " base "+str(amounts['base'])))
    @api.onchange('partner_id')
    def obtener_method_payment(self):
        self.method_payment=self.partner_id.method_payment
        self.email_fe=self.partner_id.email
        self.email_fe2=self.partner_id.email

    @api.depends('type')
    def _obtener_tipo_referencia(self):
        for s in self:
            if s.type:
                if s.type in  ['out_refund','out_debit','ret_out_invoice']:
                    s.tipo_referencia = 'out_invoice'
                elif s.type in ['in_refund','in_debit']:
                    s.tipo_referencia = 'in_invoice'

    dominio  = fields.Char(store=False, compute="_filtro_partner",readonly=True)

    @api.depends('type')
    def _filtro_partner(self):
        for l in self:
            if l.type=='liq_purchase':
                l.dominio=json.dumps( [('l10n_latam_identification_type_id.sigla','!=','R'),('active','=',True)] )
            else:
                l.dominio=json.dumps( [] )






    initial_balance = fields.Boolean('Balance Inicial', default=False)
    

    nombre_mostrar = fields.Char('Nombre a Mostrar',compute="actualizar_nombre_llamada",store=True)



    @api.depends('name', 'state')
    def actualizar_nombre_llamada(self):
        for move in self:
            if self._context.get('name_groupby'):
                name = '**%s**, %s' % (format_date(self.env, move.date), move._get_move_display_name())
                if move.ref:
                    name += '     (%s)' % move.ref
                if move.partner_id.name:
                    name += ' - %s' % move.partner_id.name
            else:
                if not( move.type=='in_invoice' or move.type=='out_invoice'):
                    name = move._get_move_display_name(show_ref=True)
                else:
                    if move.l10n_latam_document_number:
                        name = move.l10n_latam_document_number
                    else:
                        name = move._get_move_display_name(show_ref=True)
            
            move.nombre_mostrar=name

    @api.depends('name', 'state')
    def name_get(self):
        result = []
        for move in self:
            if self._context.get('name_groupby'):
                name = '**%s**, %s' % (format_date(self.env, move.date), move._get_move_display_name())
                if move.ref:
                    name += '     (%s)' % move.ref
                if move.partner_id.name:
                    name += ' - %s' % move.partner_id.name
            else:
                if not( move.type=='in_invoice' or move.type=='out_invoice'):
                    name = move._get_move_display_name(show_ref=True)
                else:
                    if move.l10n_latam_document_number:
                        name = move.l10n_latam_document_number
                    else:
                        name = move._get_move_display_name(show_ref=True)
            result.append((move.id, name))
        return result
            
  
    campos_adicionales_facturacion = fields.One2many('campos.adicionales.facturacion', inverse_name = 'move_id')

    campos_adicionales_facturacion_prove = fields.One2many('campos.adicionales.facturacion', inverse_name = 'move_id')



    #@api.onchange('auth_number','is_electronic')
    def onchange_auth_number(self):
        if self.auth_number:
            if not self.is_electronic and len(self.auth_number) != 10:
                raise UserError('La autorización ingresada no coincide con el formato del SRI de 10 digitos.')
            elif self.is_electronic and len(self.auth_number) not in (37,49) :
                raise UserError('La autorización ingresada no coincide con el formato del SRI de 37 ó 49 digitos.')
            
    @api.depends('ret_tax_ids.amount')
    def _compute_ret_total(self):
        for s in self:
            s.ret_amount_total = sum(tax.amount for tax in s.ret_tax_ids)
            
    @api.depends('invoice_line_ids.tax_ids')
    def _check_retention(self):
        self.has_retention = False
        TAXES = ['ret_vat_b', 'ret_vat_srv', 'ret_ir', 'no_ret_ir'] 
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.tax_group_id.code in TAXES:
                    self.has_retention = True
                    
    def post(self):
        for inv in self:
            if inv.type in _DOCUMENTOS_RETENIBLES:
                seq = self.env['ir.sequence']
                if inv.is_electronic==True and inv.type in _DOCUMENTOS_EMISION:
                    if self.establecimiento.sequence_id:
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
        if self.is_electronic:
            self.procesoComprobanteElectronico()
        
        return super().post()                

    @api.onchange('manual_sequence','manual_establishment','manual_referral_guide')
    @api.constrains('manual_sequence','manual_establishment','manual_referral_guide')
    def validar_secuencia(self):
        for inv in self:
            if inv.manual_sequence and inv.manual_establishment and inv.manual_referral_guide:
                if inv.is_electronic==False:
                    secuencia=inv.manual_establishment.zfill(3)+inv.manual_referral_guide.zfill(3)+str(inv.manual_sequence).zfill(9)

                    facturas_obj=[]
                    if inv.id:
                        facturas_obj=self.env['account.move'].search([('journal_id','=',inv.journal_id.id),
                                                                ('l10n_latam_document_number','=',secuencia),
                                                                ('l10n_latam_document_type_id','=',inv.l10n_latam_document_type_id.id),
                                                                ('partner_id','=',inv.partner_id.id),('id','!=',inv.id)])

                    else:
                        
                        facturas_obj=self.env['account.move'].search([('journal_id','=',inv.journal_id.id),
                                                                    ('l10n_latam_document_number','=',secuencia),
                                                                    ('l10n_latam_document_type_id','=',inv.l10n_latam_document_type_id.id),
                                                                    ('partner_id','=',inv.partner_id.id)])
                    if facturas_obj:
                        raise ValidationError("El numero de documento {0} ya ha sido asignado para este tipo de documentos y Proveedor/Cliente".format(secuencia))

    @api.constrains('l10n_latam_document_number')
    @api.onchange('l10n_latam_document_number')
    def validar_numero_documento(self):
        for inv in self:
            if inv.l10n_latam_document_number:
                if inv.id:
                    facturas_obj=self.env['account.move'].search([('journal_id','=',inv.journal_id.id),
                                                            ('l10n_latam_document_number','=',inv.l10n_latam_document_number),
                                                            ('l10n_latam_document_type_id','=',inv.l10n_latam_document_type_id.id),
                                                            ('partner_id','=',inv.partner_id.id),('id','!=',inv.id)])
                    if facturas_obj:
                        raise ValidationError("El numero de documento {0} ya ha sido asignado para este tipo de documentos y Proveedor/Cliente".format(inv.l10n_latam_document_number))


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

    @api.onchange('journal_id')
    @api.constrains('journal_id')
    def _onchange_journal(self):
        for l in self:
            if l.journal_id and l.type in _DOCUMENTOS_EMISION:
                if l.type == 'out_invoice':
                    l.establecimiento = l.journal_id.auth_out_invoice_id
                elif l.type == 'out_refund':
                    l.establecimiento = l.journal_id.auth_out_refund_id
                elif l.type == 'liq_purchase':
                    l.establecimiento = l.journal_id.auth_out_liq_purchase_id.id
                elif l.type == 'out_debit':
                    l.establecimiento = l.journal_id.auth_out_debit_id.id
                l.auth_number = not l.establecimiento.is_electronic and l.establecimiento.authorization_number
            return super(AccountMove, l)._onchange_journal()

    @api.constrains('establecimiento', 'type')
    @api.depends('establecimiento', 'type')
    def _get_electronic(self):
        for inv in self:
            if inv.type!='entry':
                if inv.establecimiento.is_manual_sequence:
                    inv.is_manual_sequence=True
                else:
                    inv.is_manual_sequence = False
                if inv.establecimiento.is_electronic:
                    inv.is_electronic = True
                else:
                    inv.is_electronic = False
                if inv.journal_id.auth_retention_id:
                    inv.ret_is_electronic = inv.journal_id.auth_retention_id.is_electronic
                    inv.ret_is_manual_sequence = inv.journal_id.auth_retention_id.is_manual_sequence

                
    def button_validate(self):
        return self.retention_id.button_validate()
        
    def print_retention(self):
        return self.retention_id.print_retention()
            
    def action_post(self):
        if self.type in _DOCUMENTOS_RETENIBLES:
            self.action_withholding_create()        
        self.post()
        if self.type in ['out_refund','in_refund'] :
            if self.reversed_entry_id.id:
                lines = self.reversed_entry_id.mapped('line_ids')
                for l in lines:
                    try:
                        self.js_assign_outstanding_line(l.id) 
                    except:
                        print('Error de asiento contable')    
        
        # if self.type == 'out_invoice':
        #     if self.contrato_estado_cuenta_ids:
        #         #obj_account_debe = self.env['account.account'].search([('code','=','1010205001')])
        #         obj_account_debe=self.partner_id.property_account_receivable_id
        #         cuota_capital_obj = self.env['rubros.contratos'].search([('name','=','cuota_capital')])
        #         seguro_obj = self.env['rubros.contratos'].search([('name','=','seguro')])
        #         otros_obj = self.env['rubros.contratos'].search([('name','=','otros')])
        #         rastreo_obj = self.env['rubros.contratos'].search([('name','=','rastreo')])
        #         #obj_account_haber = self.env['account.account'].search([('code','=','2020601001')])
        #         cuota_capital=0
        #         seguro=0
        #         otros=0
        #         rastreo=0
        #         obj_am = self.env['account.move']
        #         valor_credito=0

        #         if self.anticipos_ids:
        #             for m in self.anticipos_ids:
        #                 if m.anticipo_pendiente:
        #                     valor_credito+=m.credit

        #         valor_restar=valor_credito
        #         for rec in self.contrato_id.estado_de_cuenta_ids.search([('id','in',self.contrato_estado_cuenta_ids.ids)]):
        #             rec.factura_id = self.id
        #             if valor_restar:
        #                 if valor_restar<=rec.saldo_cuota_capital:
        #                     rec.saldo_cuota_capital=rec.saldo_cuota_capital-valor_restar
                            
        #                     for pag in self.anticipos_ids:
        #                         if pag.anticipo_pendiente:
        #                             pago_cuota_id=self.env['account.payment.cuotas'].create({'cuotas_id':rec.id,'pago_id':pag.payment_id.id,
        #                                                                                        'monto_pagado':pag.payment_id.amount,'valor_asociado':valor_restar})
        #                             valor_restar=0
        #                             pass
        #                 else:
                            
        #                     for pag in self.anticipos_ids:
        #                         if pag.anticipo_pendiente:

        #                             pago_cuota_id=self.env['account.payment.cuotas'].create({'cuotas_id':rec.id,'pago_id':pag.payment_id.id,
        #                                                                                             'monto_pagado':pag.payment_id.amount,'valor_asociado':rec.saldo_cuota_capital})
        #                             valor_restar=valor_restar-rec.saldo_cuota_capital

        #                     rec.saldo_cuota_capital=0
        #             cuota_capital += rec.saldo_cuota_capital
        #             seguro += rec.saldo_seguro
        #             otros += rec.saldo_otros
        #             rastreo +=rec.saldo_rastreo
        #         if cuota_capital>0:
        #             if not cuota_capital_obj:
        #                 raise ValidationError("Debe parametrizar la cuenta para los rubros de los contratos.")
        #             obj_am.create({
        #                 'date':self.invoice_date,
        #                 'journal_id':cuota_capital_obj.journal_id.id,
        #                 'company_id':self.company_id.id,
        #                 'type':'entry',
        #                 'ref':self.name,
        #                 'line_ids':[
        #                     (0,0,{
        #                     'account_id':obj_account_debe.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':0,
        #                     'debit':cuota_capital
        #                     }),
        #                     (0,0,{
        #                     'account_id':cuota_capital_obj.cuenta_id.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':cuota_capital,
        #                     'debit':0
        #                     })
        #                 ]
        #             }).action_post()
        #         obj_anticipo=self.env['anticipos.pendientes'].search([('factura_id','=',self.id),('anticipo_pendiente','=',False)])
        #         for ant in self.anticipos_ids:
        #             ant.linea_pago_id.saldo_pendiente=valor_restar
        #         #    ant.valor_sobrante=valor_restar
        #             if not ant.linea_pago_id.saldo_pendiente:
        #                 ant.linea_pago_id.aplicar_anticipo=False
        #         obj_anticipo.unlink()
        #         if seguro>0:
        #             if not seguro_obj:
        #                 raise ValidationError("Debe parametrizar la cuenta para los rubros de los contratos.")
        #             obj_am.create({
        #                 'date':self.invoice_date,
        #                 'journal_id':seguro_obj.journal_id.id,
        #                 'company_id':self.company_id.id,
        #                 'type':'entry',
        #                 'ref':self.name,
        #                 'line_ids':[
        #                     (0,0,{
        #                     'account_id':obj_account_debe.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':0,
        #                     'debit':seguro
        #                     }),
        #                     (0,0,{
        #                     'account_id':seguro_obj.cuenta_id.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':seguro,
        #                     'debit':0
        #                     })
        #                 ]
        #             }).action_post()
        #         if otros>0:
        #             if not otros_obj:
        #                 raise ValidationError("Debe parametrizar la cuenta para los rubros de los contratos.")
        #             obj_am.create({
        #                 'date':self.invoice_date,
        #                 'journal_id':otros_obj.journal_id.id,
        #                 'company_id':self.company_id.id,
        #                 'type':'entry',
        #                 'ref':self.name,
        #                 'line_ids':[
        #                     (0,0,{
        #                     'account_id':obj_account_debe.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':0,
        #                     'debit':otros
        #                     }),
        #                     (0,0,{
        #                     'account_id':otros_obj.cuenta_id.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':otros,
        #                     'debit':0
        #                     })
        #                 ]
        #             }).action_post()
        #         if rastreo>0:
        #             if not rastreo_obj:
        #                 raise ValidationError("Debe parametrizar la cuenta para los rubros de los contratos.")
        #             obj_am.create({
        #                 'date':self.invoice_date,
        #                 'journal_id':rastreo_obj.journal_id.id,
        #                 'company_id':self.company_id.id,
        #                 'type':'entry',
        #                 'ref':self.name,
        #                 'line_ids':[
        #                     (0,0,{
        #                     'account_id':obj_account_debe.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':0,
        #                     'debit':rastreo
        #                     }),
        #                     (0,0,{
        #                     'account_id':rastreo_obj.cuenta_id.id,
        #                     'partner_id':self.partner_id.id,
        #                     'credit':rastreo,
        #                     'debit':0
        #                     })
        #                 ]
        #             }).action_post()

    def action_withholding_create(self):
        TYPES_TO_VALIDATE = ['in_invoice', 'liq_purchase', 'in_debit']
        wd_number = False
        for inv in self:
            if not self.has_retention:
                continue
            # Autorizacion para Retenciones de la Empresa
            auth_ret = inv.journal_id.auth_retention_id
            if inv.type in ['in_invoice', 'liq_purchase', 'in_debit'] and not auth_ret:
                raise UserError(
                    u'No ha configurado la secuencia  de retenciones en el diario {0}'.format(inv.journal_id.name)
                )
            ret_taxes = []
            for line in self.invoice_line_ids:
                for tax in line.tax_ids:
                    tax_detail = tax.compute_all(line.price_unit, line.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
                    if tax.tax_group_id.code in ['ret_vat_b', 'ret_vat_srv', 'ret_ir','no_ret_ir']:
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
                withdrawing.email_fe=inv.email_fe2
                lines=[]
                for campo in inv.campos_adicionales_facturacion_prove:
                    dct_campo={'nombre':campo.nombre,'valor':campo.valor}
                    lines.append((0, 0, dct_campo))

                withdrawing.update({'campos_adicionales_facturacion': lines})



 


        return True
    
    
    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        ''' Compute the dynamic tax lines of the journal entry.

        :param lines_map: The line_ids dispatched by type containing:
            * base_lines: The lines having a tax_ids set.
            * tax_lines: The lines having a tax_line_id set.
            * terms_lines: The lines generated by the payment terms of the invoice.
            * rounding_lines: The cash rounding lines of the invoice.
        '''
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id
            if move.is_invoice(include_receipts=True):
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                if base_line.currency_id:
                    price_unit_foreign_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
                    price_unit_comp_curr = base_line.currency_id._convert(price_unit_foreign_curr,
                                                                          move.company_id.currency_id, move.company_id,
                                                                          move.date)
                else:
                    price_unit_foreign_curr = 0.0
                    price_unit_comp_curr = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            else:
                quantity = 1.0
                price_unit_foreign_curr = base_line.amount_currency
                price_unit_comp_curr = base_line.balance

            balance_taxes_res = base_line.tax_ids._origin.with_context({
                "tax_computation_context": {
                    "product_uom": base_line.product_uom_id
                }
            }).compute_all(
                price_unit_comp_curr,
                currency=base_line.company_currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=self.type in ('out_refund', 'in_refund'),
            )

            if base_line.currency_id:
                # Multi-currencies mode: Taxes are computed both in company's currency / foreign currency.
                amount_currency_taxes_res = base_line.tax_ids._origin.with_context({
                    "tax_computation_context": {
                        "product_uom": base_line.product_uom_id
                    }
                }).compute_all(
                    price_unit_foreign_curr,
                    currency=base_line.currency_id,
                    quantity=quantity,
                    product=base_line.product_id,
                    partner=base_line.partner_id,
                    is_refund=self.type in ('out_refund', 'in_refund'),
                )
                for b_tax_res, ac_tax_res in zip(balance_taxes_res['taxes'], amount_currency_taxes_res['taxes']):
                    tax = self.env['account.tax'].browse(b_tax_res['id'])
                    b_tax_res['amount_currency'] = ac_tax_res['amount']

                    # A tax having a fixed amount must be converted into the company currency when dealing with a
                    # foreign currency.
                    if tax.amount_type == 'fixed':
                        b_tax_res['amount'] = base_line.currency_id._convert(b_tax_res['amount'],
                                                                             move.company_id.currency_id,
                                                                             move.company_id, move.date)

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'balance': 0.0,
                    'amount_currency': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                line.tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            line.tag_ids = compute_all_vals['base_tags']

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(
                    tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                if self.type == 'out_invoice' and tax.tax_group_id.code in ('ret_ir', 'ret_vat_srv', 'ret_vat_b'):
                    continue

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'balance': 0.0,
                    'amount_currency': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['balance'] += tax_vals['amount']
                taxes_map_entry['amount_currency'] += tax_vals.get('amount_currency', 0.0)
                taxes_map_entry['tax_base_amount'] += tax_vals['base']
                taxes_map_entry['grouping_dict'] = grouping_dict
            line.tax_exigible = tax_exigible

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # Don't create tax lines with zero balance.
            # if self.currency_id.is_zero(taxes_map_entry['balance']) and self.currency_id.is_zero(taxes_map_entry['amount_currency']):
            #    taxes_map_entry['grouping_dict'] = False

            tax_line = taxes_map_entry['tax_line']
            tax_base_amount = -taxes_map_entry['tax_base_amount'] if self.is_inbound() else taxes_map_entry[
                'tax_base_amount']

            if not tax_line and not taxes_map_entry['grouping_dict']:
                continue
            elif tax_line and recompute_tax_base_amount:
                tax_line.tax_base_amount = tax_base_amount
            elif tax_line and not taxes_map_entry['grouping_dict']:
                # The tax line is no longer used, drop it.
                self.line_ids -= tax_line
            elif tax_line:
                if self.type == 'out_invoice' and tax_line.tax_group_id.code in ('ret_ir', 'ret_vat_srv', 'ret_vat_b'):
                    self.line_ids -= tax_line
                    taxes_map_entry['grouping_dict'] = False
                else:
                    tax_line.update({
                        'amount_currency': taxes_map_entry['amount_currency'],
                        'debit': taxes_map_entry['balance'] > 0.0 and taxes_map_entry['balance'] or 0.0,
                        'credit': taxes_map_entry['balance'] < 0.0 and -taxes_map_entry['balance'] or 0.0,
                        'tax_base_amount': tax_base_amount,
                    })

            else:
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                    'account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                tax_line = create_method({
                    'name': tax.name,
                    'move_id': self.id,
                    'partner_id': line.partner_id.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'quantity': 1.0,
                    'date_maturity': False,
                    'amount_currency': taxes_map_entry['amount_currency'],
                    'debit': taxes_map_entry['balance'] > 0.0 and taxes_map_entry['balance'] or 0.0,
                    'credit': taxes_map_entry['balance'] < 0.0 and -taxes_map_entry['balance'] or 0.0,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                tax_line._onchange_amount_currency()
                tax_line._onchange_balance()
    
    def _get_move_display_name(self, show_ref=False):
        ''' Helper to get the display name of an invoice depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
        :return:            A string representing the invoice.
        '''
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'liq_purchase': 'Liquidacion de compras',
                'sale_note': 'Nota de venta',
                'in_debit': 'Nota de Debito',
                'out_debit': 'Nota de Debito',
                'entry': _('Draft Entry'),
            }[self.type]
            if not self.name or self.name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.name
        return (draft_name or self.name) + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')
    
    def _reverse_moves(self, default_values_list=None, cancel=False):
        ''' Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.

        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in the method).
        :return:                    An account.move recordset, reverse of the current self.
        '''
        if not default_values_list:
            default_values_list = [{} for move in self]

        if cancel:
            lines = self.mapped('line_ids')
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()

        reverse_type_map = {
            'entry': 'entry',
            'out_invoice': 'out_refund',
            'out_refund': 'entry',
            'in_invoice': 'in_refund',
            'in_refund': 'entry',
            'out_receipt': 'entry',
            'in_receipt': 'entry',
            'in_debit' : 'entry',
            'out_debit': 'entry',
            'liq_purchase': 'in_refund',
            'sale_note': 'in_refund'
        }

        move_vals_list = []
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'type': reverse_type_map[move.type],
                'reversed_entry_id': move.id,
            })
            move_vals_list.append(move._reverse_move_vals(default_values, cancel=cancel))

        reverse_moves = self.env['account.move'].create(move_vals_list)
        for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False)):
            # Update amount_currency if the date has changed.
            if move.date != reverse_move.date:
                for line in reverse_move.line_ids:
                    if line.currency_id:
                        line._onchange_currency()
            reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)
        reverse_moves._check_balanced()

        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(move_reverse_cancel=cancel).post()
            for move, reverse_move in zip(self, reverse_moves):
                accounts = move.mapped('line_ids.account_id') \
                    .filtered(lambda account: account.reconcile or account.internal_type == 'liquidity')
                for account in accounts:
                    (move.line_ids + reverse_move.line_ids)\
                        .filtered(lambda line: line.account_id == account and line.balance)\
                        .reconcile()

        return reverse_moves






class CamposAdicionales(models.Model):
    _name = 'campos.adicionales.facturacion'
    _description = 'Campos Adicionales Tributacion'
    

    move_id = fields.Many2one('account.move', string = 'Factura')
    remision_id = fields.Many2one('account.guia.remision', string = 'Guia Remision')
    retention_id = fields.Many2one('account.retention', string = 'Retencion')
    nombre= fields.Char(string="Nombre")
    valor = fields.Char('Valor')

