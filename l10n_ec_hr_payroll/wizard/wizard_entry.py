# -*- coding:utf-8 -*-

from odoo import api, models, fields,_
from datetime import date, timedelta
import datetime

from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, ValidationError
import calendar
import pytz

class entryworkwizard(models.TransientModel):
    _name = 'wizard.entry'
    _description = 'Entradas de Trabajo'


    #name = fields.Many2one('hr.employee',string='Empleado', domain=compute_employee, required=True)
    date_start = fields.Date('Fecha Inicio', required=True)
    date_end = fields.Date('Fecha Corte', required=True, default = date.today())
    employee_id = fields.Many2one('hr.employee')
    





    def actualizar_work_entry(self):
        hoy=date.today()        
        
        fecha_actual="%s-%s-01" % (hoy.year, hoy.month)
        fecha_fin_tarea="%s-%s-%s" % (hoy.year, hoy.month,(calendar.monthrange(hoy.year, hoy.month)[1]))



        entrada=self.env['wizard.entry'].create({'date_start':fecha_actual,'date_end':fecha_fin_tarea})
        entrada.generar_work_entry()












    def generar_work_entry(self):
        
        date_start = fields.Datetime.to_datetime(self.date_start)
        date_stop = datetime.datetime.combine(fields.Datetime.to_datetime(self.date_end), datetime.datetime.max.time())
        if self.employee_id.id:
            
            obj_contract=self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)])
            obj_entrywork=self.env['hr.work.entry'].search([('employee_id','=',self.employee_id.id),('date_start','>=',self.date_start),('date_stop','<=',self.date_end)])
        else:
            obj_contract=self.env['hr.contract'].search([])
            obj_entrywork=self.env['hr.work.entry'].search([('date_start','>=',self.date_start),('date_stop','<=',self.date_end)])

        
        
        
        if len(obj_entrywork)>0:
            obj_entrywork.unlink()

        lista=[]
    
        for contrato in obj_contract:
            if contrato.date_start > self.date_start:

                valor=contrato._get_work_entries_values(   fields.Datetime.to_datetime(contrato.date_start),date_stop)
            else:
                valor=contrato._get_work_entries_values(date_start,date_stop)
            
            #raise ValidationError(str(valor))
            self.env['hr.work.entry'].create(valor)
        

    def generar_alimentacion(self):
        
        date_start = fields.Datetime.to_datetime(self.date_start)
        date_stop = datetime.datetime.combine(fields.Datetime.to_datetime(self.date_end), datetime.datetime.max.time())

            
            
        if self.employee_id.id:
            obj_contract=self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)])
        else:
            obj_contract=self.env['hr.contract'].search([])        
        
        
        lista=[]

        for contrato in obj_contract:
            if contrato.date_start > self.date_start:

                valor=contrato._get_work_entries_values(   fields.Datetime.to_datetime(contrato.date_start),date_stop)
            else:
                valor=contrato._get_work_entries_values(date_start,date_stop)


            comision=self.env['hr.payslip.input.type'].search([('code','=','DALI')])
            for linea in valor:
                dct={
                'date':  linea['date_start']  ,
                'input_type_id': comision.id   ,
                'employee_id':contrato.employee_id.id  ,
                'amount':2  ,

                }

                input_anteriores=self.env['hr.input'].search([('employee_id','=',contrato.employee_id.id),('date','=',linea['date_start'].date())])
                if len(input_anteriores)==0:
                    comision_input=self.env['hr.input'].create(dct)
                else:
                    pass