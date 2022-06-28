# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import *
import calendar

class Comision(models.Model):
    _name = 'comision'

    cargo_id = fields.Many2one('hr.job',string="Cargo")
    valor_max = fields.Float('Máximo')
    valor_min = fields.Float('Mìnimo')


    comision = fields.Float('Comisión')
    bono = fields.Float('Bono')
    logica = fields.Selection(selection=[
        ('asesor', 'Asesor'),
        ('supervisor', 'Supervisor'),
        ('jefe', 'Jefe'),
        ('gerente', 'Gerente'),

    ], string='Logica', default='asesor', track_visibility='onchange')

    active = fields.Boolean('Bono',default=True)










    def job_para_crear_comisiones_por_contrato(self, ):

        hoy=date.today()
        comisiones=self.env['comision'].search([('active','=',True)])

        cargos_comisiones=list(set(self.env['comision'].search([('active','=',True)]).mapped('cargo_id').ids))

 
        fecha_actual="%s-%s-01" % (hoy.year, hoy.month)
        fecha_fin="%s-%s-%s" %(hoy.year, hoy.month,(calendar.monthrange(hoy.year, hoy.month)[1]))


        listaComision=[]

        for cargo in cargos_comisiones:
            
            empleados=self.env['hr.employee'].search([('job_id','=',cargo)])

            tipo_comision=self.env['comision'].search([('cargo_id','=',cargo)],limit=1)
            

            if len(tipo_comision)>0:
                
                if tipo_comision.logica=='supervisor':

                    for empleado in empleados:
                        monto_comision=0
                        leads = self.env['crm.lead'].search([('supervisor','=',empleados.user_id.id),('active','=',True),('fecha_ganada','>=',fecha_actual),('fecha_ganada','<=',fecha_fin)])
                        monto_ganado= sum(leads.mapped("factura_inscripcion_id.amount_untaxed"))

                        
                        comision_tabla=self.env['comision'].search([('cargo_id','=',cargo),('valor_min','<=',monto_ganado),('valor_max','>=',monto_ganado)],limit=1)
                        if len(comision_tabla)>0 and monto_ganado>0:
                            monto_comision=comision_tabla.comision*monto_ganado + comision_tabla.bono

                            listaComision.append({'empleado_id':empleado.id,'nombre':empleado.name,'monto_total':monto_ganado,'comision':monto_comision,'cargo':empleado.job_id.id,'tipo_comision':'supervisor','porcentaje_comision':comision_tabla.comision,'bono': comision_tabla.bono})




                if tipo_comision.logica=='jefe' or tipo_comision.logica=='gerente':
                    for empleado in empleados:
                        monto_comision=0
                        leads = self.env['crm.lead'].search([('fecha_ganada','>=',fecha_actual),('fecha_ganada','<=',fecha_fin)])
                        
                        
                        monto_ganado= sum(leads.mapped("factura_inscripcion_id.amount_untaxed"))

                        
                        comision_tabla=self.env['comision'].search([('cargo_id','=',cargo),('valor_min','<=',monto_ganado),('valor_max','>=',monto_ganado)],limit=1)
                        if len(comision_tabla)>0 and monto_ganado>0:
                            monto_comision=(comision_tabla.comision*monto_ganado/100) + comision_tabla.bono

                            listaComision.append({'empleado_id':empleado.id,'nombre':empleado.name,'comision':monto_comision,'monto_total':monto_ganado,'cargo':empleado.job_id.id,'tipo_comision':'supervisor','porcentaje_comision':comision_tabla.comision,'bono': comision_tabla.bono})


        comision=self.env['hr.payslip.input.type'].search([('code','=','COMI')])
        for empleado in listaComision:
            dct={
            'date':  hoy  ,
            'input_type_id': comision.id   ,
            'employee_id':empleado['empleado_id']  ,
            'amount':empleado['comision']   ,

            }


            comision_input=self.env['hr.input'].create(dct)


            dct2={
                
                'valor_inscripcion': empleado['monto_total']   ,
                'comision': empleado['comision']   ,
                'cargo':   empleado['cargo']  ,
                'empleado_id':   empleado['empleado_id'],
                'porcentaje_comision':   empleado['porcentaje_comision'],
                'bono':   empleado['bono'] }


            comision_bitacora=self.env['comision.bitacora'].create(dct2)



