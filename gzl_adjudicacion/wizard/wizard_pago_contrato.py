# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError

#import numpy_financial as npf


class WizardPagoCuotaAmortizacion(models.TransientModel):
    _name = 'wizard.pago.cuota.amortizacion.contrato'
    
    tabla_amortizacion_id = fields.Many2one('contrato.estado.cuenta')
    payment_date = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', required=True, string='Diario', domain=[('type', 'in', ('bank', 'cash'))])
    payment_method_id = fields.Many2one('account.payment.method', string='Método de Pago', required=True)
    amount = fields.Float(required=True, string="Monto")


    @api.onchange('journal_id')
    def onchange_payment_method(self):
        if self.journal_id:
            self.env.cr.execute("""select inbound_payment_method from account_journal_inbound_payment_method_rel where journal_id={0}""".format(self.journal_id.id))
            res = self.env.cr.dictfetchall()
            if res:
                list_method=[]
                for l in res:
                    list_method.append(l['inbound_payment_method'])
                list_method=list(set(list_method))
                

                    
                return {'domain': {'payment_method_id': [('payment_type', '=', 'inbound'),('id', 'in', list_method)]}}



    
    def validar_pago_cobranzas(self,pago_obj):


        transacciones=self.env['transaccion.grupo.adjudicado']


        dct={
        'grupo_id':self.tabla_amortizacion_id.contrato_id.grupo.id,
        'haber':self.amount ,
        'adjudicado_id':self.tabla_amortizacion_id.contrato_id.cliente.id,
        'contrato_id':self.tabla_amortizacion_id.contrato_id.id,
        'state':self.tabla_amortizacion_id.contrato_id.state
        }


        transacciones.create(dct)

        pago = pago_obj

        self.tabla_amortizacion_id.calcular_monto_pagado()
        self.tabla_amortizacion_id.estado_pago='pendiente'


        if self.tabla_amortizacion_id.saldo==0:
            
            self.tabla_amortizacion_id.estado_pago='pagado'



            hoy=date.today()
            self.tabla_amortizacion_id.fecha_pagada=hoy



            obj_calificador=self.env['calificador.cliente']

            if hoy<self.tabla_amortizacion_id.fecha:
                motivo=self.env.ref('gzl_adjudicacion.calificacion_4')
            else:
                motivo=self.env.ref('gzl_adjudicacion.calificacion_5')

            obj_calificador.create({'partner_id': self.tabla_amortizacion_id.contrato_id.cliente.id,'motivo':motivo.motivo,'calificacion':motivo.calificacion})