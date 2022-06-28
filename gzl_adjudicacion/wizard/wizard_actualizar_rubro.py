# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError

import numpy_financial as npf
import math


class WizardActualizarRubro(models.Model):
    _name = 'wizard.actualizar.rubro'
    
    contrato_id = fields.Many2one('contrato')
    partner_id = fields.Many2one('res.partner', string="Proveedor")
    monto = fields.Float(string='Monto')
    mes = fields.Integer(string='Mes',default=1)
    anio = fields.Integer(string='Año',default=2022)
    diferido=fields.Integer(string='Numero de meses diferido',default=12)
    rubro = fields.Selection(selection=[
        ('rastreo', 'Rastreo'),
        ('seguro', 'Seguro'),
        ('otro', 'Otro')
    ], string='Rubro', default='rastreo', track_visibility='onchange')


    def actualizar_contrato(self,):
        if self.diferido==0:
            raise ValidationError('El número de meses a diferir debe ser mayor a 0')

        numero_cuota=self.diferido
        month=self.mes
        year=self.anio
        valor=self.monto/self.diferido

        self.funcion_modificar_contrato_por_rubro_seguro(valor,self.rubro,numero_cuota,month,year,self.diferido)



    def funcion_modificar_contrato_por_rubro_seguro(self,valor,variable,numero_cuota,month,year,diferido):


        month=month
        year=year


        #obj_detalle=self.contrato_id.tabla_amortizacion.filtered(lambda l: l.fecha.year==year and l.fecha.month==month)
        obj_detalle=self.contrato_id.tabla_amortizacion.filtered(lambda l: int(l.numero_cuota)==int(month) and l.cuota_capital>0)
        cuota_inicial=int(obj_detalle.numero_cuota)
        detalle_a_pagar=self.contrato_id.tabla_amortizacion.filtered(lambda l: int(l.numero_cuota)>=int(obj_detalle.numero_cuota) and l.cuota_capital>0)
        id_detalles=[]
        for i in range(0,diferido):

            obj_detalle=self.contrato_id.tabla_amortizacion.filtered(lambda l: int(l.numero_cuota)==cuota_inicial and l.cuota_capital>0)
            obj_detalle.write({variable:valor})
            if variable=='rastreo':
                obj_detalle.write({'saldo_rastreo':valor})
            elif variable=='seguro':
                obj_detalle.write({'saldo_seguro':valor})
            elif variable=='otro':
                obj_detalle.write({'saldo_otros':valor})

            cuota_inicial+=1
            id_detalles.append(obj_detalle.id)

        vls=[]                                                

        monto_finan_contrato = sum(self.contrato_id.tabla_amortizacion.mapped(variable))
        monto_finan_contrato = round(monto_finan_contrato,2)
        #raise ValidationError(str(monto_finan_contrato))
        if  monto_finan_contrato  > self.monto:
            valor_sobrante = monto_finan_contrato - self.monto 
            valor_sobrante = round(valor_sobrante,2)
            parte_decimal, parte_entera = math.modf(valor_sobrante)
            if parte_decimal==0:
                valor_a_restar=0
            elif parte_decimal >=1:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.1
            else:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.01

            obj_contrato=self.env['contrato.estado.cuenta'].browse(id_detalles)
            for c in obj_contrato:
                if valor_sobrante != 0.00 or valor_sobrante != 0 or valor_sobrante != 0.0:
                    if variable=='rastreo':
                        c.update({'saldo_rastreo':c.mapped(variable)[0] - valor_a_restar})
                    elif variable=='seguro':
                        c.update({'saldo_seguro':c.mapped(variable)[0] - valor_a_restar})
                    elif variable=='otro':
                        c.update({'saldo_otros':c.mapped(variable)[0] - valor_a_restar})

                    c.update({
                        variable: c.mapped(variable)[0] - valor_a_restar,
                        'contrato_id':self.contrato_id.id,
                    })
                    vls.append(valor_sobrante)
                    valor_sobrante = valor_sobrante -valor_a_restar
                    valor_sobrante = round(valor_sobrante,2)
                            
                            
        if  monto_finan_contrato  < self.monto:
            valor_sobrante = self.monto  - monto_finan_contrato 
            valor_sobrante = round(valor_sobrante,2)
            parte_decimal, parte_entera = math.modf(valor_sobrante)
            if parte_decimal==0:
                valor_a_restar=0
            if parte_decimal >=1:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.1
            else:
                valor_a_restar= (valor_sobrante/parte_decimal)*0.01

            obj_contrato=self.env['contrato.estado.cuenta'].browse(id_detalles)

            for c in obj_contrato:
                if variable=='rastreo':
                    c.update({'saldo_rastreo':c.mapped(variable)[0] + valor_a_restar})
                elif variable=='seguro':
                    c.update({'saldo_seguro':c.mapped(variable)[0] + valor_a_restar})
                elif variable=='otro':
                    c.update({'saldo_otros':c.mapped(variable)[0] + valor_a_restar})


                if valor_sobrante != 0.00 or valor_sobrante != 0 or valor_sobrante != 0.0:
                    #raise ValidationError(str(valor_sobrante)+'--'+str(parte_decimal)+'----'+str(valor_a_restar))
                    c.update({
                        variable: c.mapped(variable)[0] + valor_a_restar,
                        'contrato_id':self.contrato_id.id,
                    })  
                    vls.append(valor_sobrante)
                    valor_sobrante = valor_sobrante -valor_a_restar
                    valor_sobrante = round(valor_sobrante,2)


