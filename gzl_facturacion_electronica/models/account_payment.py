# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    contrato_estado_cuenta_payment_ids = fields.One2many('contrato.estado.cuenta.payment', 'payment_pagos_id')
    deuda_total=fields.Float("Deuda Total")
    valor_deuda=fields.Float("Valor a Pagar",compute='_saldo_pagar', store=True)
    saldo_pago=fields.Float("Saldo", compute='_saldo_pagar', store=True)
    total_asignado=fields.Float("Total asignado", compute="total_asignar")
    contrato_id = fields.Many2one('contrato', string='Contrato')
    valor_deuda_admin=fields.Float("Cuota Administrativa a Pagar",compute='_saldo_pagar', store=True)

    saldo_cuota_capital = fields.Float(string='Saldo Cuota Capital')
    saldo_seguro = fields.Float(string='Saldo_seguro')
    saldo_rastreo = fields.Float(string='Saldo Rastreo')
    saldo_otros = fields.Float(string='Saldo Otros')
    abono_contrato = fields.Boolean(string='Contrato')
    credito_contrato=fields.Boolean(string='Credito')

    tipo_valor = fields.Selection([
        ('enviar_credito', 'Enviar a Credito'),
        ('crear_acticipo', 'Crear Anticipo')
    ], string='Tipo')

    contrato_valor = fields.Monetary('Contrato')
    credito = fields.Monetary('Credito')

    #@api.onchange('abono_contrato')
    #def asignar_contrato(self):
        #self.crear_asientos()

    #@api.onchange('credito_contrato')
    #def asignar_credito(self):
     #   self.crear_asientos()


    def crear_detalles(self):
        for l in self:
            if l.amount==0 or not l.amount:
                raise ValidationError("Debe Asignar un monto a Pagar")
        
        self._onchange_tipo_valor()
        viewid = self.env.ref('gzl_facturacion_electronica.pago_cuota_form2').id
        return {   
            'name':'Detalle de Cuotas',
            'view_type':'form',
            'views' : [(viewid,'form')],
            'res_model':'account.payment',
            'res_id':self.id,
            'type':'ir.actions.act_window',
            'target':'new',
            }

    def cerrar_ventana(self):
        return {
        'type':'ir.actions.act_window_close'
        }

    @api.onchange('amount')
    def _onchange_amount(self):
        self.saldo_pago=self.amount

    @api.onchange('contrato_id')
    def _onchange_tipo_valor(self):    
        lista_cuotas=[]
        if self.contrato_id:
            if self.contrato_estado_cuenta_payment_ids:
                for l in self.contrato_estado_cuenta_payment_ids:
                    if l.contrato_id==self.contrato_id:
                        pass
                    else:
                        self.update({'contrato_estado_cuenta_payment_ids':[(6,0,[])]}) 
            for cuota in self.contrato_id.estado_de_cuenta_ids:
                if not cuota.factura_id and cuota.estado_pago=='pendiente':
                    lista_cuotas.append(cuota.id)

        obj_estado_cuenta_ids = self.env['contrato.estado.cuenta'].search([('id','in',lista_cuotas)])
        cuotas = {
            'numero_cuota':'',
            'fecha':'',
            'cuota_capital':'',
            'seguro':'',
            'rastreo':'',
            'otro':'',
            'programado':'',
            'saldo':'',
            'cuota_capital_pagar':'',
            'seguro_pagar':'',
            'rastreo_pagar':'',
            'otro_pagar':'',
            'entrada_pagar':'',
            'monto_pagar':'',
            'contrato_id':'',
        }
        if not self.contrato_estado_cuenta_payment_ids:
            if obj_estado_cuenta_ids:
                for ric in obj_estado_cuenta_ids:
                    # list_ids_cuotas.append(ric)
                    if ric.saldo!=0:
                        saldo=ric.saldo_cuota_capital+ric.saldo_seguro+ric.saldo_rastreo+ric.saldo_otros+ric.saldo_programado
                        cuotas.update({
                            'numero_cuota':ric.numero_cuota,
                            'fecha':ric.fecha,
                            'cuota_capital':ric.saldo_cuota_capital,
                            'seguro':ric.saldo_seguro,
                            'rastreo':ric.saldo_rastreo,
                            'otro':ric.saldo_otros,
                            'programado':ric.programado,
                            'saldo':saldo,
                            'contrato_id':ric.contrato_id.id,
                            # 'cuota_capital_pagar':ric.cuota_capital_pagar,
                            # 'seguro_pagar':'',
                            # 'rastreo_pagar':'',
                            # 'otro_pagar':'',
                            # 'monto_pagar':'',
                        }) 
                        self.contrato_estado_cuenta_payment_ids = [(0,0,cuotas)]

    @api.depends('contrato_estado_cuenta_payment_ids')
    def total_asignado(self):
        for l in self:
            for x in l.contrato_estado_cuenta_payment_ids:
                l.total_asignado+=x.monto_pagar

    @api.onchange('tipo_valor','amount','credito_contrato','credito')
    @api.depends('tipo_valor','amount','credito_contrato','credito')
    def _saldo_pagar(self):
        for l in self:
            valor_asignado=0
            contrato_valor=0
            credito_contrato=0
            for x in l.payment_line_ids:
                if x.pagar:
                    valor_asignado+=x.amount
            if l.abono_contrato:
                for y in l.contrato_estado_cuenta_payment_ids:
                    if y.monto_pagar:
                        contrato_valor+=y.monto_pagar
            if l.credito_contrato:
                credito_contrato=l.amount-valor_asignado-contrato_valor
            l.contrato_valor=contrato_valor
            l.credito=credito_contrato
            l.valor_deuda=valor_asignado
            l.saldo_pago=l.amount-valor_asignado-contrato_valor-credito_contrato
            if round(valor_asignado+contrato_valor+credito_contrato,2)==round(l.amount,2):
                l.saldo_pago=0

                


            #l.valor_deuda=l.amount
            #l.saldo_pago=0
            #if l.tipo_valor=='enviar_credito':
            #    valor_asignado=0
            #    for x in l.contrato_estado_cuenta_payment_ids:
            #        if x.monto_pagar:
            #            valor_asignado+=x.monto_pagar

            #    if round(valor_asignado,2) > round(l.amount,2):
            #        raise ValidationError("Los valores a pagar exceden los ${0} especificados.".format(l.amount))
            #    l.valor_deuda=valor_asignado
            #    if round(valor_asignado,2)==round(l.amount,2):
            #        l.saldo_pago=0
            #    else:
            #        l.saldo_pago=l.amount-l.valor_deuda
            #elif l.tipo_valor=='crear_acticipo':
            #        valor_asignado=0
            #        valor_facturas=0
            #        for x in l.payment_line_ids:
            #            if x.pagar:
            #                valor_asignado+=(x.actual_amount+x.monto_pendiente_pago)
            #        l.valor_deuda=valor_asignado
            #        l.saldo_pago=l.amount-l.valor_deuda
            #elif not l.tipo_valor:
            #    valor_asignado=0

            #    for x in l.payment_line_ids:
            #        if x.pagar:
            #            valor_asignado+=x.amount
            #    l.valor_deuda=valor_asignado
            #    l.saldo_pago=l.amount-valor_asignado

