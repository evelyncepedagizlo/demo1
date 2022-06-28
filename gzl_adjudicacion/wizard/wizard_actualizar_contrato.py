# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError
#import numpy_financial as npf
import math


class WizardContratoAct(models.Model):
    _name = 'actualizacion.contrato.valores'
    _description = 'Modificar Contrato'


    contrato_id = fields.Many2one('contrato',string="Contrato")
    socio_id = fields.Many2one('res.partner',string="Socio")
    ejecutado = fields.Boolean(string="Ejecutado", default = False)
    monto_financiamiento = fields.Monetary(
        string='Monto Financiamiento', currency_field='currency_id', track_visibility='onchange')

    
    currency_id = fields.Many2one(
        'res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    ##valores anteriores
    monto_financiamiento_anterior = fields.Monetary(
        string='Monto Financiamiento', currency_field='currency_id', track_visibility='onchange')

    observacion = fields.Char(string='Observacion')
    def ejecutar_cambio(self):
        monto_programado_anterior=0
        nuevo_monto=0
        if self.contrato_id.tiene_cuota:
            nuevo_monto=self.monto_financiamiento*(self.contrato_id.porcentaje_programado/100)
            monto_programado_anterior=self.contrato_id.monto_programado
            self.contrato_id.monto_programado=nuevo_monto
        monto_excedente=self.monto_financiamiento_anterior-monto_programado_anterior-self.monto_financiamiento+nuevo_monto
        #raise ValidationError('{0}**{1}**{2}**{3}'.format(self.monto_financiamiento_anterior,monto_programado_anterior,self.monto_financiamiento,nuevo_monto))
        obj=self.contrato_id
        monto_restado=0
        cuota_ultima=self.contrato_id.plazo_meses.numero
        while(monto_restado<monto_excedente):
            valor_cuota=self.env['contrato.estado.cuenta'].search([('contrato_id','=',self.contrato_id.id),('numero_cuota','=',cuota_ultima),('cuota_capital','!=',0)])

            if valor_cuota.cuota_capital:
                if (monto_restado+valor_cuota.cuota_capital)>monto_excedente:
                    diferencia=monto_excedente-monto_restado
                    monto_restado+=diferencia
                    valor_cuota.cuota_capital=valor_cuota.cuota_capital-diferencia
                    valor_cuota.fecha_pagada=date.today()
                else:
                    monto_restado+=valor_cuota.cuota_capital
                    valor_cuota.cuota_capital=0
                    valor_cuota.cuota_adm=0
                    valor_cuota.iva_adm=0
                    valor_cuota.fecha_pagada=date.today()
                cuota_ultima=cuota_ultima-1
        self.ejecutado=True
        self.contrato_id.monto_financiamiento=self.monto_financiamiento
        cuota_inscripcion_anterior=self.contrato_id.valor_inscripcion
        nuevo_valor_inscripcion=self.monto_financiamiento*0.05
        if nuevo_valor_inscripcion>cuota_inscripcion_anterior:
            self.contrato_id.valor_inscripcion=nuevo_valor_inscripcion